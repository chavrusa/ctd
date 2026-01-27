#!/usr/bin/env python3
"""
Generate CTD (Common Technical Document) view from source files.

Creates a CTD folder structure with symlinks to source files, based on
the CTD module numbers in filenames (e.g., "3.2.P.1.description.pdf" -> CTD/3-Quality/3.2-Body-of-Data/3.2.P-Drug-Product/3.2.P.1-Description/).

Usage:
    python generate_ctd_view.py <source_dir> <target_dir>
    python generate_ctd_view.py  # Uses defaults for RDCP-26-0003

The script is idempotent - existing symlinks are skipped.
If a submodule has only one file, it becomes a symlink instead of a folder.
"""

import argparse
import os
import re
import shutil
from collections import defaultdict
from pathlib import Path

# CTD Module and submodule names (based on FDA M4 guidance)
# Format: "module.number" -> "Name"
CTD_NAMES = {
    # Module 1 - Administrative Information and Prescribing Information
    "1": "Administrative",
    "1.1": "Forms",
    "1.2": "Cover-Letters",
    "1.3": "Administrative-Information",
    "1.3.1": "Contact-Information",
    "1.3.2": "Field-Copy-Certification",
    "1.3.3": "Debarment-Certification",
    "1.3.4": "Financial-Certification",
    "1.3.5": "Patent-Information",
    "1.4": "References",
    "1.5": "Application-Status",
    "1.6": "Meetings",
    "1.7": "Fast-Track",
    "1.8": "Pediatric-Administrative",
    "1.9": "Additional-Info",
    "1.10": "Labeling",
    "1.10.1": "Draft-Labeling",
    "1.10.2": "Final-Labeling",
    "1.10.3": "Carton-Container-Labels",
    "1.11": "Pharmacovigilance",
    "1.12": "Other-Correspondence",
    "1.12.1": "Pre-IND-Correspondence",
    "1.12.2": "IND-Correspondence",
    "1.12.3": "NDA-BLA-Correspondence",
    "1.12.4": "ANDA-Correspondence",
    "1.12.5": "PMA-Correspondence",
    "1.12.10": "Type-A-Meeting",
    "1.12.11": "Type-B-Meeting",
    "1.12.12": "Type-C-Meeting",
    "1.12.13": "Pre-Submission-Meeting",
    "1.12.14": "Environmental-Assessment",
    "1.12.15": "Request-Inspection-Waiver",
    "1.13": "Annual-Reports",
    "1.14": "Labeling-Index",
    "1.15": "Promotional-Materials",
    "1.16": "Risk-Management",

    # Module 2 - CTD Summaries
    "2": "Summaries",
    "2.1": "Table-of-Contents",
    "2.2": "Introduction",
    "2.3": "Quality-Overall-Summary",
    "2.4": "Nonclinical-Overview",
    "2.5": "Clinical-Overview",
    "2.6": "Nonclinical-Summaries",
    "2.6.1": "Introduction",
    "2.6.2": "Pharmacology-Summary",
    "2.6.3": "Pharmacokinetics-Summary",
    "2.6.4": "Toxicology-Summary",
    "2.6.5": "Integrated-Summary",
    "2.6.6": "Pharmacology-Tables",
    "2.6.7": "Pharmacokinetics-Tables",
    "2.7": "Clinical-Summary",
    "2.7.1": "Biopharmaceutics-Summary",
    "2.7.2": "Clinical-Pharmacology-Summary",
    "2.7.3": "Efficacy-Summary",
    "2.7.4": "Safety-Summary",
    "2.7.5": "References",
    "2.7.6": "Individual-Study-Synopses",

    # Module 3 - Quality (CMC)
    "3": "Quality",
    "3.2": "Body-of-Data",
    "3.2.S": "Drug-Substance",
    "3.2.S.1": "General-Information",
    "3.2.S.2": "Manufacture",
    "3.2.S.3": "Characterisation",
    "3.2.S.4": "Control-of-Drug-Substance",
    "3.2.S.5": "Reference-Standards",
    "3.2.S.6": "Container-Closure-System",
    "3.2.S.7": "Stability",
    "3.2.P": "Drug-Product",
    "3.2.P.1": "Description-and-Composition",
    "3.2.P.2": "Pharmaceutical-Development",
    "3.2.P.3": "Manufacture",
    "3.2.P.4": "Control-of-Excipients",
    "3.2.P.5": "Control-of-Drug-Product",
    "3.2.P.6": "Reference-Standards",
    "3.2.P.7": "Container-Closure-System",
    "3.2.P.8": "Stability",
    "3.2.A": "Appendices",
    "3.2.A.1": "Facilities-and-Equipment",
    "3.2.A.2": "Adventitious-Agents",
    "3.2.A.3": "Novel-Excipients",
    "3.2.R": "Regional-Information",
    "3.3": "Literature-References",

    # Module 4 - Nonclinical Study Reports
    "4": "Nonclinical",
    "4.2": "Study-Reports",
    "4.2.1": "Pharmacology",
    "4.2.1.1": "Primary-Pharmacodynamics",
    "4.2.1.2": "Secondary-Pharmacodynamics",
    "4.2.1.3": "Safety-Pharmacology",
    "4.2.1.4": "Pharmacodynamic-Interactions",
    "4.2.2": "Pharmacokinetics",
    "4.2.2.1": "Analytical-Methods",
    "4.2.2.2": "Absorption",
    "4.2.2.3": "Distribution",
    "4.2.2.4": "Metabolism",
    "4.2.2.5": "Excretion",
    "4.2.2.6": "PK-Drug-Interactions",
    "4.2.2.7": "Other-PK-Studies",
    "4.2.3": "Toxicology",
    "4.2.3.1": "Single-Dose-Toxicity",
    "4.2.3.2": "Repeat-Dose-Toxicity",
    "4.2.3.3": "Genotoxicity",
    "4.2.3.4": "Carcinogenicity",
    "4.2.3.5": "Reproductive-Toxicity",
    "4.2.3.6": "Local-Tolerance",
    "4.2.3.7": "Other-Toxicity-Studies",
    "4.3": "Literature-References",

    # Module 5 - Clinical Study Reports
    "5": "Clinical",
    "5.2": "Tabular-Listing",
    "5.3": "Clinical-Study-Reports",
    "5.3.1": "Biopharmaceutic-Studies",
    "5.3.1.1": "Bioavailability",
    "5.3.1.2": "Comparative-BA-BE",
    "5.3.1.3": "In-Vitro-In-Vivo-Correlation",
    "5.3.1.4": "Bioanalytical-Reports",
    "5.3.2": "Human-Biomaterials",
    "5.3.2.1": "Plasma-Protein-Binding",
    "5.3.2.2": "Hepatic-Metabolism",
    "5.3.2.3": "Other-PK-Biomaterials",
    "5.3.3": "Human-PK-Studies",
    "5.3.3.1": "Healthy-Subject-PK",
    "5.3.3.2": "Patient-PK",
    "5.3.3.3": "Intrinsic-Factor-PK",
    "5.3.3.4": "Extrinsic-Factor-PK",
    "5.3.3.5": "Population-PK",
    "5.3.4": "Human-PD-Studies",
    "5.3.4.1": "Healthy-Subject-PD",
    "5.3.4.2": "Patient-PD",
    "5.3.5": "Efficacy-Safety-Studies",
    "5.3.5.1": "Controlled-Clinical-Studies",
    "5.3.5.1.1": "Symptomatic-Study",  # RDCP-26-0003 specific
    "5.3.5.2": "Uncontrolled-Clinical-Studies",
    "5.3.5.3": "Multiple-Dose-Studies",
    "5.3.5.4": "Other-Efficacy-Studies",
    "5.3.6": "Postmarketing-Experience",
    "5.3.7": "Case-Report-Forms",
    "5.4": "Literature-References",
}

# Manual CTD mappings for files that don't have CTD numbers in their names
# Format: {accession: {filename_pattern: (ctd_components, symlink_name or None)}}
# Use empty list [] for ctd_components to place at root level
MANUAL_CTD_MAPPINGS = {
    "RDCP-26-0003": {
        # Top-level documents (empty list = root)
        r"^__Table Of Contents": ([], "Table Of Contents.pdf"),
        r"^_Form_FDA_1571": ([], "Form FDA 1571.pdf"),
        # Toxicology studies from Table of Contents (SD-11755)
        # A-703 series: Repeat-dose toxicity studies
        r"^A-703-": (["4", "4.2", "4.2.3", "4.2.3.2"], None),
        # XT23 series: Genotoxicity studies
        r"^XT23\d+": (["4", "4.2", "4.2.3", "4.2.3.3"], None),
        # 5677 series: Genotoxicity studies (Ames, Micronucleus)
        r"^5677\d*": (["4", "4.2", "4.2.3", "4.2.3.3"], None),
    },
}


def get_ctd_folder_name(module_num):
    """Get the descriptive folder name for a CTD module number."""
    if module_num in CTD_NAMES:
        return f"{module_num}) {CTD_NAMES[module_num]}"
    return module_num


def parse_ctd_info(filename, accession=None):
    """
    Extract CTD module path and generate symlink name from filename.

    Handles various filename formats:
        "1.12.14.Environmental-Assessment.pdf" -> (["1", "1.12", "1.12.14"], None)
        "3.2.P.1.description.pdf" -> (["3", "3.2", "3.2.P", "3.2.P.1"], None)
        "2.6.6 Toxicology Written Summary FINAL.pdf" -> (["2", "2.6", "2.6.6"], "2.6.6-Toxicology Written Summary FINAL.pdf")
        "Module 2.5 Clinical Overview FINAL.pdf" -> (["2", "2.5"], "2.5-Clinical Overview FINAL.pdf")
        "Title1 Module 1.13.3 Title2.pdf" -> (["1", "1.13", "1.13.3"], "1.13.3-Title1 Title2.pdf")
        "16.2.1 Discontinued Patients.pdf" -> (["1", "16", "16.2", "16.2.1"], "16.2.1-Discontinued Patients.pdf")

    Also checks MANUAL_CTD_MAPPINGS for accession-specific overrides.

    Returns (components, symlink_name) or (None, None) if no CTD pattern found.
    symlink_name is None if the original filename should be used.
    """
    # Check manual mappings first
    if accession and accession in MANUAL_CTD_MAPPINGS:
        for pattern, (components, symlink_name) in MANUAL_CTD_MAPPINGS[accession].items():
            if re.match(pattern, filename):
                return (components, symlink_name)
    # Get the base name without extension, and the extension
    base = Path(filename).stem
    ext = Path(filename).suffix

    # Pattern 1: "Module X.Y.Z Title" - strip "Module " prefix
    match = re.match(r'^Module\s+([1-5](?:\.[0-9]+)*(?:\.[A-Z](?:\.[0-9]+)*)?)\s+(.+)$', base, re.IGNORECASE)
    if match:
        ctd_prefix = match.group(1)
        title = match.group(2)
        components = build_components(ctd_prefix)
        symlink_name = f"{ctd_prefix}) {title}{ext}"
        return (components, symlink_name) if components else (None, None)

    # Pattern 2: "Title1 Module X.Y.Z Title2" - CTD in middle
    match = re.match(r'^(.+?)\s+Module\s+([1-5](?:\.[0-9]+)*(?:\.[A-Z](?:\.[0-9]+)*)?)\s*(.*)$', base, re.IGNORECASE)
    if match:
        title1 = match.group(1)
        ctd_prefix = match.group(2)
        title2 = match.group(3)
        components = build_components(ctd_prefix)
        combined_title = f"{title1} {title2}".strip()
        symlink_name = f"{ctd_prefix}) {combined_title}{ext}"
        return (components, symlink_name) if components else (None, None)

    # Pattern 3: "X.Y.Z Title" - CTD number followed by space then title
    # Must start with 1-5 (or 16 for CSR appendices which map to module 5)
    match = re.match(r'^([1-5](?:\.[0-9]+)*(?:\.[A-Z](?:\.[0-9]+)*)?)\s+(.+)$', base)
    if match:
        ctd_prefix = match.group(1)
        title = match.group(2)
        components = build_components(ctd_prefix)
        symlink_name = f"{ctd_prefix}) {title}{ext}"
        return (components, symlink_name) if components else (None, None)

    # Pattern 3b: "16.X.Y Title" - CSR appendices (16.x maps to module 5 section 5.3.5)
    match = re.match(r'^(16(?:\.[0-9]+)+)\s+(.+)$', base)
    if match:
        ctd_prefix = match.group(1)
        title = match.group(2)
        # Map 16.x to 5.3.5.x (CSR appendices)
        components = build_components(ctd_prefix, csr_appendix=True)
        symlink_name = f"{ctd_prefix}) {title}{ext}"
        return (components, symlink_name) if components else (None, None)

    # Pattern 4: Original format "X.Y.Z.title" or "X.Y.Z-title"
    match = re.match(r'^([1-5](?:\.[0-9]+)*(?:\.[A-Z](?:\.[0-9]+)*)?)[\.\-](.+)$', filename, re.IGNORECASE)
    if match:
        ctd_prefix = match.group(1)
        rest = match.group(2)  # title.pdf or title-part.pdf
        components = build_components(ctd_prefix)
        if components:
            # Reconstruct with space: "1.20 General-Investigational-Plan.pdf"
            symlink_name = f"{ctd_prefix}) {rest}"
            return (components, symlink_name)
        return (None, None)

    return (None, None)


def build_components(ctd_prefix, csr_appendix=False):
    """
    Build hierarchical path components from a CTD prefix.

    e.g., "3.2.P.1" -> ["3", "3.2", "3.2.P", "3.2.P.1"]

    If csr_appendix=True, maps 16.x.y to module 5 (CSR appendices).
    """
    parts = re.split(r'(\.)', ctd_prefix)

    components = []
    current = ""
    for part in parts:
        if part == '.':
            continue
        if current:
            current += "." + part
        else:
            current = part
        components.append(current)

    if not components:
        return None

    # For CSR appendices (16.x), prepend with module 5 path
    if csr_appendix and components[0].startswith("16"):
        # 16.x.y appendices go under 5-Clinical/5.3.5-appendices/
        components = ["5", "5.3", "5.3.5"] + components

    return components


def parse_ctd_path(filename):
    """
    Extract CTD module path from filename (backward compatibility wrapper).

    Returns list of path components or None if no CTD pattern found.
    """
    components, _ = parse_ctd_info(filename)
    return components


def generate_ctd_view(source_dirs, target_dir, recursive=False, accession=None):
    """
    Generate CTD folder structure with symlinks to source files.

    Args:
        source_dirs: Path or list of paths to source files
        target_dir: Path to create CTD structure (e.g., CTD/)
        recursive: If True, scan source directories recursively
        accession: Accession number for manual mapping lookups
    """
    if isinstance(source_dirs, (str, Path)):
        source_dirs = [source_dirs]

    source_dirs = [Path(d).resolve() for d in source_dirs]
    target_dir = Path(target_dir).resolve()

    for source_dir in source_dirs:
        if not source_dir.exists():
            print(f"WARNING: Source directory not found: {source_dir}")

    print(f"Sources: {len(source_dirs)} director{'y' if len(source_dirs) == 1 else 'ies'}")
    for d in source_dirs:
        print(f"  - {d}")
    print(f"Target: {target_dir}")
    print(f"Recursive: {recursive}")
    print()

    # First pass: collect all files by their deepest CTD path
    # Key: tuple of CTD components, Value: list of (symlink_name, source_path)
    files_by_path = defaultdict(list)
    root_files = []  # Files to place at root level (empty components)
    no_ctd_files = []

    def scan_directory(dir_path, base_dir):
        """Scan a directory for files with CTD patterns."""
        if not dir_path.exists():
            return

        for entry in os.listdir(dir_path):
            full_path = dir_path / entry

            if full_path.is_file():
                ctd_components, symlink_name = parse_ctd_info(entry, accession=accession)

                if ctd_components is None:
                    try:
                        rel_path = str(full_path.relative_to(base_dir))
                    except ValueError:
                        rel_path = str(full_path)
                    no_ctd_files.append(rel_path)
                    continue

                # Use original filename if no symlink_name provided
                if symlink_name is None:
                    symlink_name = entry

                # Empty components means root level
                if len(ctd_components) == 0:
                    root_files.append((symlink_name, full_path))
                else:
                    # Use tuple of components as key
                    files_by_path[tuple(ctd_components)].append((symlink_name, full_path))

            elif full_path.is_dir() and recursive:
                scan_directory(full_path, base_dir)

    for source_dir in source_dirs:
        scan_directory(source_dir, source_dir)

    # Second pass: build a tree structure to analyze single-child branches
    # Tree node: {component: {"children": {...}, "files": [(name, path), ...]}}
    tree = {}

    for ctd_path, files in files_by_path.items():
        node = tree
        for comp in ctd_path:
            if comp not in node:
                node[comp] = {"children": {}, "files": []}
            node = node[comp]["children"]
        # Go back up one level to add files to the correct node
        node = tree
        for comp in ctd_path[:-1]:
            node = node[comp]["children"]
        if ctd_path:
            last_comp = ctd_path[-1]
            if last_comp not in node:
                node[last_comp] = {"children": {}, "files": []}
            node[last_comp]["files"].extend(files)

    # Third pass: create structure with single-child collapsing
    target_dir.mkdir(parents=True, exist_ok=True)

    linked = 0
    skipped = 0

    def create_links(node, parent_path, accumulated_names):
        """
        Recursively create symlinks, collapsing single-child branches.

        accumulated_names: list of folder names accumulated during single-child traversal
        """
        nonlocal linked, skipped

        for comp, data in sorted(node.items()):
            folder_name = get_ctd_folder_name(comp)
            children = data["children"]
            files = data["files"]

            # Count total items at this level
            num_children = len(children)
            num_files = len(files)
            total_items = num_children + num_files

            if total_items == 0:
                # Empty node, skip
                continue
            elif total_items == 1 and num_files == 1:
                # Single file at this level: collapse all accumulated names into symlink
                filename, source_file = files[0]

                # Use the original filename (which already has the correct title)
                # Goes directly into parent_path (no intermediate folders created)
                link_name = filename

                link_path = parent_path / link_name

                if link_path.exists() or link_path.is_symlink():
                    print(f"  SKIP (exists): {link_name}")
                    skipped += 1
                else:
                    link_path.symlink_to(source_file)
                    rel_path = link_path.relative_to(target_dir)
                    print(f"  LINKED: {rel_path}")
                    linked += 1

            elif total_items == 1 and num_children == 1:
                # Single child folder: accumulate name and recurse
                create_links(children, parent_path, accumulated_names + [folder_name])

            else:
                # Multiple items: create folder and process contents
                all_names = accumulated_names + [folder_name]
                folder_path = parent_path
                for name in all_names:
                    folder_path = folder_path / name
                folder_path.mkdir(parents=True, exist_ok=True)

                # Create symlinks for files at this level
                for filename, source_file in files:
                    link_path = folder_path / filename

                    if link_path.exists() or link_path.is_symlink():
                        print(f"  SKIP (exists): {filename}")
                        skipped += 1
                    else:
                        link_path.symlink_to(source_file)
                        rel_path = link_path.relative_to(target_dir)
                        print(f"  LINKED: {rel_path}")
                        linked += 1

                # Recurse into children (reset accumulated names since we created a folder)
                create_links(children, folder_path, [])

    create_links(tree, target_dir, [])

    # Create root-level symlinks
    for symlink_name, source_path in root_files:
        link_path = target_dir / symlink_name
        if link_path.exists() or link_path.is_symlink():
            print(f"  SKIP (exists): {symlink_name}")
            skipped += 1
        else:
            link_path.symlink_to(source_path)
            print(f"  LINKED: {symlink_name}")
            linked += 1

    # Report files without CTD pattern
    for entry in no_ctd_files:
        print(f"  SKIP (no CTD pattern): {entry}")

    print()
    print(f"Done: {linked} linked, {skipped} skipped, {len(no_ctd_files)} without CTD pattern")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Generate CTD view from source files"
    )
    parser.add_argument(
        "accession",
        nargs="?",
        help="Accession number (e.g., RDCP-26-0002) or 'all'",
    )
    parser.add_argument(
        "-r", "--recursive",
        action="store_true",
        help="Scan source directories recursively",
    )
    parser.add_argument(
        "-c", "--clean",
        action="store_true",
        help="Delete target directory before generating",
    )
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    project_dir = script_dir.parent
    docs_dir = project_dir / "documents"

    # Define source configurations for each accession
    accession_configs = {
        "RDCP-26-0003": {
            "sources": [docs_dir / "RDCP-26-0003" / "files" / "IND-Application"],
            "target": docs_dir / "RDCP-26-0003" / "CTD",
            "recursive": False,
        },
        "RDCP-26-0002": {
            "sources": [
                docs_dir / "RDCP-26-0002" / "files" / "Preclinical Development",
                docs_dir / "RDCP-26-0002" / "files" / "Regulatory",
                docs_dir / "RDCP-26-0002" / "files" / "Clinical-Studies",
            ],
            "target": docs_dir / "RDCP-26-0002" / "CTD",
            "recursive": True,
        },
    }

    # Determine which accessions to process
    if args.accession is None:
        # Default to RDCP-26-0003
        accessions = ["RDCP-26-0003"]
    elif args.accession.lower() == "all":
        accessions = list(accession_configs.keys())
    elif args.accession in accession_configs:
        accessions = [args.accession]
    else:
        print(f"ERROR: Unknown accession '{args.accession}'")
        print(f"Available: {', '.join(accession_configs.keys())}, or 'all'")
        return 1

    success = True
    for accession in accessions:
        config = accession_configs[accession]
        print(f"\n{'='*60}")
        print(f"Processing {accession}")
        print(f"{'='*60}\n")

        target = config["target"]
        if args.clean and target.exists():
            print(f"Cleaning {target}")
            shutil.rmtree(target)

        recursive = args.recursive or config.get("recursive", False)

        if not generate_ctd_view(config["sources"], target, recursive=recursive, accession=accession):
            success = False

    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
