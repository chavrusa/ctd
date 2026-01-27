#!/usr/bin/env python3
"""Extract zip files and organize contents into folders.

Structure:
- Viewable files (PDF, docs, images, etc.) at top level
- Data files (.xpt, .sas7bdat) in a "Data" subfolder
"""

import os
import zipfile
import shutil
from pathlib import Path

DOCS_DIR = Path(__file__).resolve().parent.parent / "documents"

# File extensions considered "data" (go into Data subfolder)
DATA_EXTENSIONS = {'.xpt', '.sas7bdat'}

# File extensions that are viewable/documents (stay at top level)
VIEWABLE_EXTENSIONS = {
    '.pdf', '.doc', '.docx', '.rtf', '.txt',
    '.png', '.jpg', '.jpeg', '.gif', '.svg',
    '.xlsx', '.xls', '.csv',
    '.xml', '.xsl', '.html', '.htm',
    '.mp3', '.mp4', '.wav', '.webm'
}

def find_zips():
    """Find all zip files in the documents directory."""
    zips = []
    for root, dirs, files in os.walk(DOCS_DIR):
        for f in files:
            if f.lower().endswith('.zip'):
                zips.append(Path(root) / f)
    return zips

def extract_and_organize(zip_path: Path):
    """Extract a zip file and organize its contents."""
    # Create folder with same name as zip (minus extension)
    folder_name = zip_path.stem
    target_dir = zip_path.parent / folder_name
    data_dir = target_dir / "Data"

    # Skip if already extracted
    if target_dir.exists():
        print(f"  Skipping (already exists): {target_dir.name}")
        return False

    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            # Get list of files
            members = zf.namelist()
            if not members:
                print(f"  Empty zip: {zip_path.name}")
                return False

            # Create target directory
            target_dir.mkdir(parents=True, exist_ok=True)

            # Track if we need Data subfolder
            has_data_files = False

            # Extract each file
            for member in members:
                # Skip directories
                if member.endswith('/'):
                    continue

                # Get just the filename (strip any directory prefix from zip)
                filename = Path(member).name
                if not filename:
                    continue

                ext = Path(filename).suffix.lower()

                # Determine destination
                if ext in DATA_EXTENSIONS:
                    has_data_files = True
                    if not data_dir.exists():
                        data_dir.mkdir(parents=True, exist_ok=True)
                    dest = data_dir / filename
                else:
                    dest = target_dir / filename

                # Handle duplicate filenames
                if dest.exists():
                    base = dest.stem
                    suffix = dest.suffix
                    counter = 1
                    while dest.exists():
                        dest = dest.parent / f"{base}_{counter}{suffix}"
                        counter += 1

                # Extract file
                with zf.open(member) as src, open(dest, 'wb') as dst:
                    dst.write(src.read())

            print(f"  Extracted: {zip_path.name} -> {folder_name}/")
            return True

    except zipfile.BadZipFile:
        print(f"  Bad zip file: {zip_path.name}")
        return False
    except Exception as e:
        print(f"  Error extracting {zip_path.name}: {e}")
        return False

def main():
    zips = find_zips()
    print(f"Found {len(zips)} zip files\n")

    extracted = 0
    skipped = 0
    errors = 0

    for zp in sorted(zips):
        rel_path = zp.relative_to(DOCS_DIR)
        print(f"Processing: {rel_path}")

        result = extract_and_organize(zp)
        if result:
            extracted += 1
        elif result is False:
            skipped += 1

    print(f"\nDone! Extracted: {extracted}, Skipped: {skipped}")
    print("\nYou can now delete the original .zip files if extraction was successful.")
    print("Run: find documents -name '*.zip' -delete")

if __name__ == "__main__":
    main()
