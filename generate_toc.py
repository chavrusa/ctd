#!/usr/bin/env python3
"""Generate toc.json from the documents folder structure."""

import json
import os
import re
from pathlib import Path

DOCS_DIR = Path(__file__).parent / "documents"
OUTPUT_FILE = Path(__file__).parent / "toc.json"

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

def scan_directory(path):
    """Recursively scan directory and build tree structure."""
    items = []

    try:
        entries = os.listdir(path)
    except PermissionError:
        return items

    # Separate folders and files
    folders = []
    files = []

    for entry in entries:
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
        children = scan_directory(full_path)
        items.append({
            "name": entry,
            "type": "folder",
            "path": rel_path,
            "children": children
        })

    for entry in files:
        full_path = os.path.join(path, entry)
        rel_path = os.path.relpath(full_path, DOCS_DIR.parent)
        items.append({
            "name": entry,
            "type": get_file_type(entry),
            "path": rel_path
        })

    return items

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

    with open(OUTPUT_FILE, "w") as f:
        json.dump(toc, f, indent=2)

    # Count files
    def count_files(node):
        if node.get("type") != "folder":
            return 1
        return sum(count_files(child) for child in node.get("children", []))

    total = count_files(toc)
    print(f"Generated {OUTPUT_FILE} with {total} files")

if __name__ == "__main__":
    main()
