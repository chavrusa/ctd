#!/usr/bin/env python3
"""Create URL-escaped symlinks for files with special characters."""

import os
import urllib.parse
from pathlib import Path

# Characters that need escaping in URLs
SPECIAL_CHARS = {'#', '%', '?', '&', '+'}


def needs_escaping(name: str) -> bool:
    """Check if filename contains chars that need URL escaping."""
    return any(c in name for c in SPECIAL_CHARS)


def create_escaped_symlink(file_path: Path) -> bool:
    """Create a symlink with URL-escaped name if needed."""
    name = file_path.name
    if not needs_escaping(name):
        return False

    # URL-encode the filename
    escaped_name = urllib.parse.quote(name, safe='')
    escaped_path = file_path.parent / escaped_name

    # Skip if symlink already exists
    if escaped_path.exists() or escaped_path.is_symlink():
        return False

    # Create relative symlink
    escaped_path.symlink_to(name)
    return True


def process_directory(base_path: Path) -> int:
    """Recursively process directory, creating escaped symlinks."""
    count = 0
    for root, dirs, files in os.walk(base_path, followlinks=True):
        root_path = Path(root)
        for filename in files:
            file_path = root_path / filename
            if create_escaped_symlink(file_path):
                count += 1
                print(f"  Created: {urllib.parse.quote(filename, safe='')}")
    return count


def main():
    docs_dir = Path(__file__).parent.parent / 'documents'

    # Process each accession's files directory
    for accession_dir in sorted(docs_dir.iterdir()):
        if accession_dir.name.startswith('RDCP-'):
            files_dir = accession_dir / 'files'
            if files_dir.exists():
                print(f"Processing {accession_dir.name}...")
                count = process_directory(files_dir)
                print(f"  {count} symlinks created")


if __name__ == '__main__':
    main()
