#!/usr/bin/env python3
"""Generate toc.json and toc.md from the documents folder structure."""

import json
import os
import re
from pathlib import Path

DOCS_DIR = Path(__file__).parent / "documents"
OUTPUT_JSON = Path(__file__).parent / "toc.json"
OUTPUT_MD = Path(__file__).parent / "toc.md"
BASE_URL = "https://archive.icosian.net"

# Custom sort orders for drug development workflow
# Lower number = appears first

# Top-level folders
TOP_LEVEL_ORDER = {
    "ALLN-346": 1,
    "ALLN-177-Reloxaliase": 2,
    "Supporting": 99,
}

# Drug development stages (subfolders under each drug)
DEVELOPMENT_STAGE_ORDER = {
    "Preclinical": 1,
    "Preclinical Development": 1,
    "CMC": 2,
    "Regulatory": 3,
    "Clinical-Studies": 4,
    "Clinical Studies": 4,
    "Clinical Development": 5,
    "Development-Plans": 5,
    "Medpace-Data-2024": 6,
    "Additional-Items": 7,
    "Additional-Items-Backup": 8,
    "Commercial": 9,
}

# Within a study folder
STUDY_CONTENT_ORDER = {
    "CSR": 1,           # Clinical Study Report - the main document
    "Protocol": 2,
    "TLFs": 3,          # Tables, Listings, Figures
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

def get_sort_key(name, parent_path):
    """Get sort key for a folder/file based on context."""
    # Check if this is a top-level folder (normalize paths for comparison)
    if str(parent_path) == str(DOCS_DIR) or os.path.samefile(parent_path, DOCS_DIR):
        return (TOP_LEVEL_ORDER.get(name, 50), name.lower())

    # Check if this is a development stage folder
    if name in DEVELOPMENT_STAGE_ORDER:
        return (DEVELOPMENT_STAGE_ORDER[name], name.lower())

    # Check if this is study content
    if name in STUDY_CONTENT_ORDER:
        return (STUDY_CONTENT_ORDER[name], name.lower())

    # For study numbers (101-SAD, 202, 301, etc.), extract the number
    match = re.match(r'^(\d+)', name)
    if match:
        study_num = int(match.group(1))
        return (study_num, name.lower())

    # Default: alphabetical but after numbered items
    return (1000, name.lower())

def load_metadata(path):
    """Load metadata.json from a directory if it exists."""
    metadata_file = os.path.join(path, "metadata.json")
    if os.path.exists(metadata_file):
        try:
            with open(metadata_file, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}

def merge_inherited(parent_inherited, folder_meta):
    """Merge inherited properties from parent with current folder's _folder metadata."""
    inherited = parent_inherited.copy()
    if folder_meta:
        # drug is the main inherited property
        if "drug" in folder_meta:
            inherited["drug"] = folder_meta["drug"]
        if "drugName" in folder_meta:
            inherited["drugName"] = folder_meta["drugName"]
    return inherited

def scan_directory(path, inherited=None):
    """Recursively scan directory and build tree structure."""
    if inherited is None:
        inherited = {}

    items = []

    # Load metadata for this directory
    metadata = load_metadata(path)
    folder_meta = metadata.get("_folder", {})

    # Update inherited properties
    current_inherited = merge_inherited(inherited, folder_meta)

    try:
        entries = os.listdir(path)
    except PermissionError:
        return items

    # Separate folders and files, skip metadata.json
    folders = []
    files = []

    for entry in entries:
        if entry == "metadata.json":
            continue
        full_path = os.path.join(path, entry)
        if os.path.isdir(full_path):
            folders.append(entry)
        else:
            files.append(entry)

    # Sort folders with custom logic, files alphabetically
    folders.sort(key=lambda x: get_sort_key(x, path))
    files.sort(key=lambda x: x.lower())

    # Process folders first, then files
    for entry in folders:
        full_path = os.path.join(path, entry)
        rel_path = os.path.relpath(full_path, DOCS_DIR.parent)

        # Load child folder's metadata for its title/summary
        child_metadata = load_metadata(full_path)
        child_folder_meta = child_metadata.get("_folder", {})

        children = scan_directory(full_path, current_inherited)

        item = {
            "name": entry,
            "type": "folder",
            "path": rel_path,
            "children": children
        }

        # Add metadata if present
        if child_folder_meta.get("title"):
            item["title"] = child_folder_meta["title"]
        if child_folder_meta.get("summary"):
            item["summary"] = child_folder_meta["summary"]

        items.append(item)

    for entry in files:
        full_path = os.path.join(path, entry)
        rel_path = os.path.relpath(full_path, DOCS_DIR.parent)

        # Get file-specific metadata
        file_meta = metadata.get(entry, {})

        item = {
            "name": entry,
            "type": get_file_type(entry),
            "path": rel_path
        }

        # Add metadata if present
        if file_meta.get("title"):
            item["title"] = file_meta["title"]
        if file_meta.get("summary"):
            item["summary"] = file_meta["summary"]
        if file_meta.get("tags"):
            item["tags"] = file_meta["tags"]

        # Add inherited properties
        if current_inherited.get("drug"):
            item["drug"] = current_inherited["drug"]

        items.append(item)

    return items

def generate_markdown(node, depth=0):
    """Generate markdown representation of the TOC tree."""
    lines = []
    indent = "  " * depth

    if node.get("type") == "folder":
        title = node.get("title", node["name"])
        summary = node.get("summary", "")

        if depth == 0:
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
        file_type = node.get("type", "")

        # Build URL with hash for deep linking
        url_path = node["path"].replace(" ", "%20")
        url = f"{BASE_URL}/#{url_path}"

        # Format: - [Title](url) (type) - summary
        line = f"{indent}- [{title}]({url})"
        if file_type:
            line += f" ({file_type})"
        if drug:
            line += f" [{drug}]"
        lines.append(line)

        if summary:
            lines.append(f"{indent}  {summary}")

    return lines

def flatten_files(node, files=None):
    """Flatten the tree into a list of files for agent consumption."""
    if files is None:
        files = []

    if node.get("type") != "folder":
        url_path = node["path"].replace(" ", "%20")
        file_entry = {
            "url": f"{BASE_URL}/#{url_path}",
            "title": node.get("title", node["name"]),
            "type": node.get("type", "unknown"),
            "path": node["path"]
        }
        if node.get("summary"):
            file_entry["description"] = node["summary"]
        if node.get("drug"):
            file_entry["drug"] = node["drug"]
        if node.get("tags"):
            file_entry["tags"] = node["tags"]
        files.append(file_entry)
    else:
        for child in node.get("children", []):
            flatten_files(child, files)

    return files

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

    # Write JSON (tree structure for UI)
    with open(OUTPUT_JSON, "w") as f:
        json.dump(toc, f, indent=2)

    # Write Markdown (for LLM consumption)
    md_lines = [
        "# CTD Document Archive",
        "",
        "This archive contains regulatory documents for ALLN-177 (Reloxaliase) and ALLN-346 drug trials.",
        "",
        "## Documents",
        ""
    ]
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

if __name__ == "__main__":
    main()
