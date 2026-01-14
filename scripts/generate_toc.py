#!/usr/bin/env python3
"""Generate toc.json and toc.md from the documents folder structure.

Supports the accession-based structure:
  documents/
  ├── RDCP-26-0001/           # Accession folder
  │   ├── metadata.json       # Accession-level metadata
  │   └── files/              # Document files
  ├── RDCP-26-0002/
  └── Supporting/             # Non-accession content
"""

import json
import os
import re
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
DOCS_DIR = PROJECT_DIR / "documents"
OUTPUT_JSON = PROJECT_DIR / "toc.json"
OUTPUT_MD = PROJECT_DIR / "toc.md"
BASE_URL = "https://archive.icosian.net"

# Accession number pattern
ACCESSION_PATTERN = re.compile(r'^RDCP-\d{2}-\d{4}$')

# Custom sort orders for drug development workflow
# Lower number = appears first

# Top-level folders (accessions sorted by number, Supporting last)
TOP_LEVEL_ORDER = {
    "Supporting": 99,
}

# Drug development stages (subfolders under each accession/files/)
DEVELOPMENT_STAGE_ORDER = {
    "Preclinical": 1,
    "Preclinical Development": 1,
    "CMC": 2,
    "Regulatory": 3,
    "Clinical-Studies": 4,
    "Clinical Studies": 4,
    "Clinical Development": 5,
    "Development-Plans": 5,
    "IND-Application": 6,
    "Research-Data": 7,
    "Medpace-Data-2024": 8,
    "Additional-Items": 9,
    "Additional-Items-Backup": 10,
    "Commercial": 11,
}

# Within a study folder
STUDY_CONTENT_ORDER = {
    "CSR": 1,
    "Protocol": 2,
    "TLFs": 3,
    "CSR-TLFs": 3,
    "Statistics": 4,
    "Datasets": 5,
    "ADaM-Data": 5,
    "SDTM-Data": 5,
    "Datalab-Report": 6,
    "DSMB-SSR1": 7,
}


def get_file_type(filename):
    """Return file type based on extension."""
    ext = Path(filename).suffix.lower()
    return ext[1:] if ext else "unknown"


def natural_sort_key(name):
    """
    Generate a sort key for natural sorting.

    Handles CTD-style names like "1.2-Cover-Letters", "1.12-Other-Correspondence".

    Rules:
    - Split on dots and hyphens to get segments
    - Within each position, letters sort before numbers (so 1.FDA before 1.2)
    - Numbers sort numerically (1.2 before 1.12)
    """
    # Split into segments by dots, hyphens, colons, parens, and spaces
    # "1.12) Other-Correspondence.pdf" -> ["1", "12", "Other", "Correspondence", "pdf"]
    segments = re.split(r'[\.\-:\)\(\s]+', name)

    key = []
    for seg in segments:
        if not seg:
            continue
        # Check if segment is purely numeric
        if seg.isdigit():
            # Numbers sort after letters: (1, number)
            key.append((1, int(seg), seg.lower()))
        else:
            # Letters/mixed sort before numbers: (0, 0, text)
            key.append((0, 0, seg.lower()))

    return key


def get_sort_key(name, parent_path):
    """Get sort key for a folder/file based on context."""
    # Accession numbers: sort by the numeric part
    if ACCESSION_PATTERN.match(name):
        # Extract NNNN from RDCP-YY-NNNN
        num = int(name.split('-')[-1])
        return (0, num, name.lower())

    # Check if this is a top-level folder
    try:
        if str(parent_path) == str(DOCS_DIR) or os.path.samefile(parent_path, DOCS_DIR):
            return (0, TOP_LEVEL_ORDER.get(name, 50), name.lower())
    except (OSError, ValueError):
        pass

    # Check if this is a development stage folder
    if name in DEVELOPMENT_STAGE_ORDER:
        return (0, DEVELOPMENT_STAGE_ORDER[name], name.lower())

    # Check if this is study content
    if name in STUDY_CONTENT_ORDER:
        return (0, STUDY_CONTENT_ORDER[name], name.lower())

    # For study numbers (101-SAD, 202, 301, etc.), extract the number
    match = re.match(r'^(\d+)', name)
    if match:
        study_num = int(match.group(1))
        return (0, study_num, name.lower())

    # Default: use natural sort
    return (1, natural_sort_key(name))


def load_metadata(path):
    """Load metadata from a directory if it exists.

    Checks for both metadata.json and __metadata.json (for downloaded folders
    where __metadata.json avoids conflicts with source files).
    """
    # Try standard metadata.json first
    metadata_file = os.path.join(path, "metadata.json")
    if os.path.exists(metadata_file):
        try:
            with open(metadata_file, "r") as f:
                metadata = json.load(f)
        except (json.JSONDecodeError, IOError):
            metadata = {}
    else:
        metadata = {}

    # Also check __metadata.json (for downloaded folders)
    dunder_metadata_file = os.path.join(path, "__metadata.json")
    if os.path.exists(dunder_metadata_file):
        try:
            with open(dunder_metadata_file, "r") as f:
                dunder_metadata = json.load(f)
            # Merge: __metadata.json can add _folder info
            if "_folder" in dunder_metadata and "_folder" not in metadata:
                metadata["_folder"] = dunder_metadata["_folder"]
        except (json.JSONDecodeError, IOError):
            pass

    return metadata


def load_accession_metadata(accession_path):
    """Load accession-level metadata (top-level metadata.json in accession folder)."""
    return load_metadata(accession_path)


def merge_inherited(parent_inherited, folder_meta, accession_meta=None):
    """Merge inherited properties from parent with current folder's metadata."""
    inherited = parent_inherited.copy()

    # Accession-level properties take precedence
    if accession_meta:
        if "drug" in accession_meta:
            inherited["drug"] = accession_meta["drug"]
        if "drugName" in accession_meta:
            inherited["drugName"] = accession_meta["drugName"]
        if "accession" in accession_meta:
            inherited["accession"] = accession_meta["accession"]
        if "license" in accession_meta:
            inherited["license"] = accession_meta["license"]

    # Folder metadata can override
    if folder_meta:
        if "drug" in folder_meta:
            inherited["drug"] = folder_meta["drug"]
        if "drugName" in folder_meta:
            inherited["drugName"] = folder_meta["drugName"]

    return inherited


def scan_directory(path, inherited=None, is_accession_root=False):
    """Recursively scan directory and build tree structure."""
    if inherited is None:
        inherited = {}

    items = []

    # Load metadata for this directory
    metadata = load_metadata(path)

    # Check if this is an accession folder (has accession-level metadata)
    accession_meta = None
    if is_accession_root or metadata.get("accession"):
        accession_meta = metadata
        folder_meta = {}  # Accession metadata is not _folder metadata
    else:
        folder_meta = metadata.get("_folder", {})

    # Update inherited properties
    current_inherited = merge_inherited(inherited, folder_meta, accession_meta)

    try:
        entries = os.listdir(path)
    except PermissionError:
        return items

    # Collect all entries (folders and files together)
    all_entries = []  # List of (name, is_folder)

    # At top level (documents/), only include accession folders
    is_top_level = (str(path) == str(DOCS_DIR))

    for entry in entries:
        if entry in ("metadata.json", "__metadata.json", ".gitignore", ".gitkeep"):
            continue
        if is_top_level and not ACCESSION_PATTERN.match(entry):
            continue
        full_path = os.path.join(path, entry)
        is_folder = os.path.isdir(full_path)
        all_entries.append((entry, is_folder))

    # Sort all entries together using natural sort
    # Don't separate folders and files - sort them together
    all_entries.sort(key=lambda x: natural_sort_key(x[0]))

    # Process all entries in sorted order
    for entry, is_folder in all_entries:
        full_path = os.path.join(path, entry)
        rel_path = os.path.relpath(full_path, DOCS_DIR.parent)

        if is_folder:
            # Check if this is an accession folder
            is_accession = ACCESSION_PATTERN.match(entry)

            # Load child folder's metadata
            child_metadata = load_metadata(full_path)

            if is_accession:
                # Accession folder: use accession metadata
                child_folder_meta = {}
                child_accession_meta = child_metadata
            else:
                child_folder_meta = child_metadata.get("_folder", {})
                child_accession_meta = None

            children = scan_directory(full_path, current_inherited, is_accession_root=is_accession)

            item = {
                "name": entry,
                "type": "folder",
                "path": rel_path,
                "children": children
            }

            # Add metadata
            if is_accession and child_accession_meta:
                # Accession folder gets special treatment
                if child_accession_meta.get("title"):
                    item["title"] = child_accession_meta["title"]
                if child_accession_meta.get("description"):
                    item["summary"] = child_accession_meta["description"]
                if child_accession_meta.get("accession"):
                    item["accession"] = child_accession_meta["accession"]
                if child_accession_meta.get("drug"):
                    item["drug"] = child_accession_meta["drug"]
                if child_accession_meta.get("license"):
                    item["license"] = child_accession_meta["license"]
            else:
                if child_folder_meta.get("title"):
                    item["title"] = child_folder_meta["title"]
                if child_folder_meta.get("summary"):
                    item["summary"] = child_folder_meta["summary"]

        else:
            # File
            # Get file-specific metadata
            file_meta = metadata.get(entry, {})

            item = {
                "name": entry,
                "type": get_file_type(entry),
                "path": rel_path
            }

            # Add file metadata if present
            if file_meta.get("title"):
                item["title"] = file_meta["title"]
            if file_meta.get("summary"):
                item["summary"] = file_meta["summary"]
            if file_meta.get("tags"):
                item["tags"] = file_meta["tags"]
            if file_meta.get("date"):
                item["date"] = file_meta["date"]
            if file_meta.get("ctdModule"):
                item["ctdModule"] = file_meta["ctdModule"]
            if file_meta.get("ctdTitle"):
                item["ctdTitle"] = file_meta["ctdTitle"]

            # Add inherited properties
            if current_inherited.get("drug"):
                item["drug"] = current_inherited["drug"]
            if current_inherited.get("accession"):
                item["accession"] = current_inherited["accession"]

        items.append(item)

    return items


def collect_accessions(toc):
    """Collect accession metadata from top-level folders."""
    accessions = []
    for child in toc.get("children", []):
        if child.get("accession"):
            accessions.append({
                "accession": child.get("accession"),
                "title": child.get("title", child.get("name")),
                "drug": child.get("drug"),
                "license": child.get("license", {}),
            })
    return accessions


def generate_markdown(node, depth=0):
    """Generate markdown representation of the TOC tree."""
    lines = []
    indent = "  " * depth

    if node.get("type") == "folder":
        title = node.get("title", node["name"])
        summary = node.get("summary", "")
        accession = node.get("accession", "")

        if depth == 0:
            if accession:
                lines.append(f"# {title} ({accession})\n")
            else:
                lines.append(f"# {title}\n")
        else:
            lines.append(f"{indent}- **{title}/**")

        if summary:
            lines.append(f"{indent}  {summary}")

        for child in node.get("children", []):
            lines.extend(generate_markdown(child, depth + 1))
    else:
        title = node.get("title", node["name"])
        summary = node.get("summary", "")
        drug = node.get("drug", "")
        accession = node.get("accession", "")
        file_type = node.get("type", "")
        date = node.get("date", "")

        # Build URL with hash for deep linking
        url_path = node["path"].replace(" ", "%20")
        url = f"{BASE_URL}/#{url_path}"

        # Format: - [Title](url) (type) [drug] [date]
        line = f"{indent}- [{title}]({url})"
        if file_type:
            line += f" ({file_type})"
        if drug:
            line += f" [{drug}]"
        if date and date != "unknown":
            line += f" ({date})"
        lines.append(line)

        if summary:
            lines.append(f"{indent}  {summary}")

    return lines


def generate_markdown_header(accessions):
    """Generate the markdown header with accession info."""
    lines = [
        "# CTD Document Archive",
        "",
        "This archive contains regulatory documents for drug trials.",
        "",
        "## Accessions",
        "",
        "| Accession | Drug | License |",
        "|-----------|------|---------|",
    ]

    for acc in accessions:
        accession = acc.get("accession", "")
        drug = acc.get("drug", "")
        title = acc.get("title", "")
        license_info = acc.get("license", {})
        license_name = license_info.get("name", "Unknown")

        lines.append(f"| {accession} | {drug} | {license_name} |")

    lines.extend([
        "",
        "### Divalent siRNA Attribution (RDCP-26-0003)",
        "",
        "> Gentile JE, Corridon TL, Serack FE, et al. **Divalent siRNA for prion disease.**",
        "> bioRxiv. 2024 Dec 5;2024.12.05.627039. https://doi.org/10.1101/2024.12.05.627039",
        "",
        "---",
        "",
        "## Documents",
        ""
    ])

    return lines


def main():
    if not DOCS_DIR.exists():
        print(f"Error: {DOCS_DIR} does not exist")
        return

    toc = {
        "name": "Documents",
        "type": "folder",
        "path": "documents",
        "children": scan_directory(DOCS_DIR)
    }

    # Collect accession info for header
    accessions = collect_accessions(toc)

    # Write JSON (tree structure for UI)
    with open(OUTPUT_JSON, "w") as f:
        json.dump(toc, f, indent=2)

    # Write Markdown (for LLM consumption)
    md_lines = generate_markdown_header(accessions)
    for child in toc.get("children", []):
        md_lines.extend(generate_markdown(child, 0))

    with open(OUTPUT_MD, "w") as f:
        f.write("\n".join(md_lines))

    # Count files
    def count_files(node):
        if node.get("type") != "folder":
            return 1
        return sum(count_files(child) for child in node.get("children", []))

    total = count_files(toc)
    print(f"Generated {OUTPUT_JSON} with {total} files")
    print(f"Generated {OUTPUT_MD}")
    if accessions:
        print(f"Found {len(accessions)} accession(s):")
        for acc in accessions:
            print(f"  - {acc['accession']}: {acc.get('drug', 'Unknown')}")


if __name__ == "__main__":
    main()
