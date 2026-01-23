#!/usr/bin/env python3
"""Generate hierarchical index.md and index.json files at each folder level.

Creates:
- index.md / index.json: 1-level deep listing of immediate children
- index-full.md / index-full.json: Full recursive tree from this point down

Single-item folder chains are collapsed inline for cleaner navigation.
"""

import json
import os
import re
import urllib.parse
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
DOCS_DIR = PROJECT_DIR / "documents"
BASE_URL = "https://archive.icosian.net"

# Files to skip
SKIP_FILES = {"metadata.json", "__metadata.json", ".gitignore", ".gitkeep",
              "index.md", "index.json", "index-full.md", "index-full.json"}

# Directories to skip entirely
SKIP_DIRS = {"_raw"}

# Accession pattern - matches RDCP-26-0001 and RDCP-E26-EMA
ACCESSION_PATTERN = re.compile(r'^RDCP-[A-Z]?\d{2}-\d{4}$|^RDCP-E26-EMA$')


def get_file_type(filename):
    """Return file type based on extension."""
    ext = Path(filename).suffix.lower()
    return ext[1:] if ext else "unknown"


def url_encode_path(path):
    """URL-encode a path, preserving slashes."""
    return "/".join(urllib.parse.quote(segment, safe='') for segment in path.split("/"))


def load_metadata(path):
    """Load metadata from a directory."""
    metadata = {}

    # Try metadata.json
    metadata_file = path / "metadata.json"
    if metadata_file.exists():
        try:
            with open(metadata_file) as f:
                metadata = json.load(f)
        except (json.JSONDecodeError, IOError):
            pass

    # Also check __metadata.json
    dunder_file = path / "__metadata.json"
    if dunder_file.exists():
        try:
            with open(dunder_file) as f:
                dunder = json.load(f)
            if "_folder" in dunder and "_folder" not in metadata:
                metadata["_folder"] = dunder["_folder"]
        except (json.JSONDecodeError, IOError):
            pass

    return metadata


def count_items_recursive(path):
    """Count total files recursively (following symlinks)."""
    count = 0
    try:
        for entry in os.scandir(path):
            if entry.name in SKIP_FILES or entry.name.startswith('.'):
                continue
            if entry.is_dir(follow_symlinks=True):
                count += count_items_recursive(entry.path)
            elif entry.is_file(follow_symlinks=True):
                count += 1
    except (PermissionError, OSError):
        pass
    return count


def get_collapsed_chain(path):
    """
    If a folder has a single child folder repeatedly, return the collapsed path.
    Returns (collapsed_relative_path, final_path) or (None, path) if no collapsing.
    """
    original = path
    chain = []

    while True:
        try:
            entries = [e for e in os.scandir(path)
                      if e.name not in SKIP_FILES and not e.name.startswith('.')]
        except (PermissionError, OSError):
            break

        # Check if exactly one entry and it's a folder
        if len(entries) == 1 and entries[0].is_dir(follow_symlinks=True):
            chain.append(entries[0].name)
            path = entries[0].path
        else:
            break

    if chain:
        return "/".join(chain), Path(path)
    return None, original


def list_children(path):
    """List immediate children of a folder, separating folders and files."""
    folders = []
    files = []

    try:
        entries = list(os.scandir(path))
    except (PermissionError, OSError):
        return folders, files

    for entry in sorted(entries, key=lambda e: e.name.lower()):
        if entry.name in SKIP_FILES or entry.name.startswith('.'):
            continue
        if entry.name in SKIP_DIRS:
            continue

        if entry.is_dir(follow_symlinks=True):
            # Check for collapsing
            collapsed_suffix, final_path = get_collapsed_chain(entry.path)

            # Get display title from metadata if available
            child_metadata = load_metadata(Path(entry.path))
            title_from_meta = child_metadata.get("_folder", {}).get("title")

            if collapsed_suffix:
                display_name = title_from_meta or f"{entry.name}/{collapsed_suffix}"
                item_count = count_items_recursive(final_path)
                folders.append({
                    "name": entry.name,
                    "display_name": display_name,
                    "collapsed_path": collapsed_suffix,
                    "final_path": final_path,
                    "item_count": item_count,
                })
            else:
                item_count = count_items_recursive(entry.path)
                folders.append({
                    "name": entry.name,
                    "display_name": title_from_meta or entry.name,
                    "collapsed_path": None,
                    "final_path": Path(entry.path),
                    "item_count": item_count,
                })
        elif entry.is_file(follow_symlinks=True):
            # Skip URL-escaped symlinks (created by create_url_symlinks.py)
            if '%' in entry.name:
                continue
            files.append({
                "name": entry.name,
                "type": get_file_type(entry.name),
            })

    return folders, files


def format_size(size_bytes):
    """Format byte size as human-readable string."""
    if size_bytes < 1024:
        return f"{size_bytes} bytes"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


def generate_index_md(folder_path, folders, files, metadata, inherited, full_md_size=0):
    """Generate index.md content."""
    lines = []

    rel_path = folder_path.relative_to(DOCS_DIR.parent)
    folder_url = f"{BASE_URL}/{url_encode_path(str(rel_path))}"

    name = folder_path.name
    title = metadata.get("title") or metadata.get("_folder", {}).get("title") or name

    lines.append(f"# {title}")
    lines.append("")
    lines.append(f"URL: {folder_url}")
    lines.append("")

    # Summary line
    parts = []
    if folders:
        parts.append(f"{len(folders)} folder{'s' if len(folders) != 1 else ''}")
    if files:
        parts.append(f"{len(files)} file{'s' if len(files) != 1 else ''}")
    if parts:
        lines.append(", ".join(parts))
        lines.append("")

    # Alternative formats
    lines.append(f"A JSON version is available at [index.json]({folder_url}/index.json).")
    if full_md_size > 0:
        lines.append(f"A full recursive listing is available at [index-full.md]({folder_url}/index-full.md) ({format_size(full_md_size)}).")
    lines.append("")

    # Inherited metadata
    if inherited.get("drug") or inherited.get("accession"):
        meta_parts = []
        if inherited.get("accession"):
            meta_parts.append(f"Accession: {inherited['accession']}")
        if inherited.get("drug"):
            meta_parts.append(f"Drug: {inherited['drug']}")
        lines.append(f"*{' | '.join(meta_parts)}*")
        lines.append("")

    # Folders section
    if folders:
        lines.append("## Folders")
        lines.append("")
        for folder in folders:
            display = folder["display_name"]
            # Use filesystem name for URL, display name for text
            fs_name = folder["name"]
            if folder["collapsed_path"]:
                fs_path = f"{fs_name}/{folder['collapsed_path']}"
            else:
                fs_path = fs_name
            encoded = url_encode_path(fs_path)
            count_str = f"({folder['item_count']} item{'s' if folder['item_count'] != 1 else ''})"
            lines.append(f"- [{display}/]({folder_url}/{encoded}/index.md) {count_str}")
        lines.append("")

    # Files section
    if files:
        lines.append("## Files")
        lines.append("")
        for f in files:
            encoded = urllib.parse.quote(f["name"], safe='')
            file_url = f"{folder_url}/{encoded}"
            lines.append(f"- [{f['name']}]({file_url}) ({f['type']})")
        lines.append("")

    return "\n".join(lines)


def generate_index_json(folder_path, folders, files, metadata, inherited):
    """Generate index.json content."""
    rel_path = folder_path.relative_to(DOCS_DIR.parent)
    folder_url = f"{BASE_URL}/{url_encode_path(str(rel_path))}"

    children = []

    for folder in folders:
        folder_rel = f"{rel_path}/{folder['name']}"
        if folder["collapsed_path"]:
            folder_rel += f"/{folder['collapsed_path']}"
        child = {
            "name": folder["name"],
            "type": "folder",
            "path": f"{folder_rel}/",
            "index": f"{BASE_URL}/{url_encode_path(folder_rel)}/index.json",
            "itemCount": folder["item_count"],
        }
        # Add title if display name differs from filesystem name
        if folder["display_name"] != folder["name"]:
            child["title"] = folder["display_name"]
        if folder["collapsed_path"]:
            child["collapsedPath"] = folder["collapsed_path"]
        children.append(child)

    for f in files:
        file_path = f"{rel_path}/{f['name']}"
        children.append({
            "name": f["name"],
            "type": f["type"],
            "path": str(file_path),
            "url": f"{folder_url}/{urllib.parse.quote(f['name'], safe='')}",
        })

    result = {
        "path": f"{rel_path}/",
        "url": folder_url,
        "name": folder_path.name,
        "fullIndex": "index-full.json",
        "children": children,
    }

    # Add metadata
    title = metadata.get("title") or metadata.get("_folder", {}).get("title")
    if title:
        result["title"] = title

    if inherited:
        result["metadata"] = inherited

    return result


def scan_tree(path, inherited=None):
    """Recursively scan and build full tree (for index-full)."""
    if inherited is None:
        inherited = {}

    metadata = load_metadata(path)

    # Update inherited from accession metadata
    if metadata.get("accession"):
        inherited = inherited.copy()
        inherited["accession"] = metadata.get("accession")
        inherited["drug"] = metadata.get("drug")

    children = []

    try:
        entries = list(os.scandir(path))
    except (PermissionError, OSError):
        return None

    for entry in sorted(entries, key=lambda e: e.name.lower()):
        if entry.name in SKIP_FILES or entry.name.startswith('.'):
            continue
        if entry.name in SKIP_DIRS:
            continue
        # Skip URL-escaped symlinks
        if '%' in entry.name:
            continue

        if entry.is_dir(follow_symlinks=True):
            subtree = scan_tree(Path(entry.path), inherited)
            if subtree:
                children.append(subtree)
        elif entry.is_file(follow_symlinks=True):
            rel_path = Path(entry.path).relative_to(DOCS_DIR.parent)
            file_meta = metadata.get(entry.name, {})

            child = {
                "name": entry.name,
                "type": get_file_type(entry.name),
                "path": str(rel_path),
                "url": f"{BASE_URL}/{url_encode_path(str(rel_path))}",
            }
            if file_meta.get("title"):
                child["title"] = file_meta["title"]
            if inherited.get("drug"):
                child["drug"] = inherited["drug"]

            children.append(child)

    rel_path = path.relative_to(DOCS_DIR.parent)
    return {
        "name": path.name,
        "type": "folder",
        "path": f"{rel_path}/",
        "index": f"{BASE_URL}/{url_encode_path(str(rel_path))}/index.json",
        "summaryIndex": "index.json",
        "children": children,
    }


def generate_full_md(tree, depth=0, is_root=False):
    """Generate full recursive markdown from tree."""
    lines = []
    indent = "  " * depth

    if tree["type"] == "folder":
        if depth == 0:
            lines.append(f"# {tree['name']} (Full Tree)")
            lines.append("")
            lines.append(f"Index: {tree['index'].replace('index.json', 'index.md')}")
            lines.append("")
            lines.append(f"[Summary view](index.md)")
            lines.append("")
        else:
            lines.append(f"{indent}- **{tree['name']}/**")

        for child in tree.get("children", []):
            lines.extend(generate_full_md(child, depth + 1))
    else:
        name = tree.get("title", tree["name"])
        url = tree.get("url", f"{BASE_URL}/{url_encode_path(tree['path'])}")
        drug = tree.get("drug", "")

        line = f"{indent}- [{name}]({url}) ({tree['type']})"
        if drug:
            line += f" [{drug}]"
        lines.append(line)

    return lines


def process_folder(path, inherited=None, is_root=False):
    """Process a folder and generate all index files."""
    if inherited is None:
        inherited = {}

    # Load metadata
    metadata = load_metadata(path)

    # Update inherited from accession metadata
    current_inherited = inherited.copy()
    if metadata.get("accession"):
        current_inherited["accession"] = metadata["accession"]
    if metadata.get("drug"):
        current_inherited["drug"] = metadata["drug"]

    # Get children
    folders, files = list_children(path)

    # Skip empty folders
    if not folders and not files:
        return

    # Generate index-full.md and index-full.json first (to get sizes)
    tree = scan_tree(path, inherited)
    full_md_size = 0
    if tree:
        full_md_content = "\n".join(generate_full_md(tree, 0))
        full_md_size = len(full_md_content.encode('utf-8'))
        (path / "index-full.md").write_text(full_md_content)
        (path / "index-full.json").write_text(json.dumps(tree, indent=2))

    # Generate index.md (with size info)
    index_md = generate_index_md(path, folders, files, metadata, current_inherited, full_md_size)
    (path / "index.md").write_text(index_md)

    # Generate index.json
    index_json = generate_index_json(path, folders, files, metadata, current_inherited)
    (path / "index.json").write_text(json.dumps(index_json, indent=2))

    # Recurse into subfolders (use final_path for collapsed chains)
    for folder in folders:
        process_folder(folder["final_path"], current_inherited)


def clean_indexes(path):
    """Remove all generated index files from a directory tree."""
    index_files = ["index.md", "index.json", "index-full.md", "index-full.json"]
    removed = 0
    for index_file in index_files:
        for f in path.rglob(index_file):
            try:
                f.unlink()
                removed += 1
            except OSError:
                pass
    return removed


def generate_static_documents_index():
    """Generate index files for web/static/documents/ with only exposed directories."""
    static_docs = PROJECT_DIR / "web" / "static" / "documents"
    if not static_docs.exists():
        return

    # Find all symlinked directories
    folders = []
    for entry in sorted(os.scandir(static_docs), key=lambda e: e.name.lower()):
        if entry.name.startswith('.') or entry.name in SKIP_FILES:
            continue
        if entry.is_dir(follow_symlinks=True):
            # Load metadata from the target
            target_path = Path(entry.path).resolve()
            metadata = load_metadata(target_path)
            title = metadata.get("title") or metadata.get("_folder", {}).get("title")
            item_count = count_items_recursive(entry.path)
            folders.append({
                "name": entry.name,
                "display_name": title or entry.name,
                "item_count": item_count,
            })

    if not folders:
        return

    # Generate index.json
    children = []
    for folder in folders:
        children.append({
            "name": folder["name"],
            "type": "folder",
            "path": f"documents/{folder['name']}/",
            "index": f"{BASE_URL}/documents/{folder['name']}/index.json",
            "itemCount": folder["item_count"],
            "title": folder["display_name"] if folder["display_name"] != folder["name"] else None,
        })
    # Remove None titles
    for child in children:
        if child.get("title") is None:
            del child["title"]

    index_json = {
        "path": "documents/",
        "url": f"{BASE_URL}/documents",
        "name": "documents",
        "children": children,
    }
    (static_docs / "index.json").write_text(json.dumps(index_json, indent=2))

    # Generate index.md
    lines = [
        "# Documents",
        "",
        f"URL: {BASE_URL}/documents",
        "",
        f"{len(folders)} folder{'s' if len(folders) != 1 else ''}",
        "",
        "## Folders",
        "",
    ]
    for folder in folders:
        display = folder["display_name"]
        encoded = urllib.parse.quote(folder["name"], safe='')
        count_str = f"({folder['item_count']} item{'s' if folder['item_count'] != 1 else ''})"
        lines.append(f"- [{display}/]({BASE_URL}/documents/{encoded}/index.md) {count_str}")
    lines.append("")

    (static_docs / "index.md").write_text("\n".join(lines))

    # Also generate top-level web/static/index.md
    static_root = PROJECT_DIR / "web" / "static"
    top_lines = [
        "# CTD Document Archive",
        "",
        "This archive contains regulatory documents organized in Common Technical Document (CTD) format, including clinical trial data, regulatory submissions, and European Medicines Agency (EMA) Public Assessment Reports.",
        "",
        "URL: https://archive.icosian.net",
        "",
        "## Documents",
        "",
        f"{len(folders)} accession{'s' if len(folders) != 1 else ''} available:",
        "",
    ]
    for folder in folders:
        display = folder["display_name"]
        encoded = urllib.parse.quote(folder["name"], safe='')
        count_str = f"({folder['item_count']} item{'s' if folder['item_count'] != 1 else ''})"
        top_lines.append(f"- [{display}/]({BASE_URL}/documents/{encoded}/index.md) {count_str}")
    top_lines.append("")
    top_lines.append("Each accession contains documents organized hierarchically. Use the index.md files for navigation.")
    top_lines.append("")

    (static_root / "index.md").write_text("\n".join(top_lines))


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate hierarchical index files")
    parser.add_argument("--clean", action="store_true",
                        help="Remove old index files before generating")
    args = parser.parse_args()

    if not DOCS_DIR.exists():
        print(f"Error: {DOCS_DIR} does not exist")
        return

    if args.clean:
        print("Cleaning old index files...")
        removed = clean_indexes(DOCS_DIR)
        print(f"  Removed {removed} files")

    # Process each accession
    total_indexes = 0
    for entry in sorted(DOCS_DIR.iterdir()):
        if ACCESSION_PATTERN.match(entry.name):
            print(f"Processing {entry.name}...")
            process_folder(entry, {}, is_root=True)

            # Count generated indexes
            count = sum(1 for _ in entry.rglob("index.md"))
            total_indexes += count
            print(f"  Generated {count} index sets")

    # Also generate at documents/ root level
    print("Processing documents/ root...")
    process_folder(DOCS_DIR, {}, is_root=True)
    total_indexes += 1

    # Generate index for web/static/documents/ (only exposed directories)
    print("Processing web/static/documents/...")
    generate_static_documents_index()

    print(f"\nTotal: {total_indexes} index sets generated")


if __name__ == "__main__":
    main()
