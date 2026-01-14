#!/usr/bin/env python3
"""
Generate "By Date" view from source directories.

Creates a date-sorted folder structure with symlinks to source files/folders,
based on dates extracted from directory/file names.

Usage:
    python generate_date_view.py [accession] [--clean]
    python generate_date_view.py RDCP-26-0002 --clean
"""

import argparse
import os
import re
import shutil
from pathlib import Path

# Month name to number mapping
MONTHS = {
    'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04',
    'may': '05', 'jun': '06', 'jul': '07', 'aug': '08',
    'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12'
}


def parse_date(text):
    """
    Extract date from text in various formats.

    Supported formats:
        2019Dec31 -> 2019-12-31
        28Jan2022 -> 2022-01-28
        2021-08-24 -> 2021-08-24

    Returns (YYYY-MM-DD, remaining_text) or (None, original_text) if no date found.
    """
    # Pattern 1: YYYYMonDD (e.g., 2019Dec31)
    match = re.search(r'(\d{4})(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)(\d{1,2})', text, re.IGNORECASE)
    if match:
        year = match.group(1)
        month = MONTHS[match.group(2).lower()]
        day = match.group(3).zfill(2)
        date_str = f"{year}-{month}-{day}"
        remaining = text[:match.start()] + text[match.end():]
        return date_str, remaining.strip()

    # Pattern 2: DDMonYYYY (e.g., 28Jan2022)
    match = re.search(r'(\d{1,2})(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)(\d{4})', text, re.IGNORECASE)
    if match:
        day = match.group(1).zfill(2)
        month = MONTHS[match.group(2).lower()]
        year = match.group(3)
        date_str = f"{year}-{month}-{day}"
        remaining = text[:match.start()] + text[match.end():]
        return date_str, remaining.strip()

    # Pattern 3: YYYY-MM-DD already formatted
    match = re.search(r'(\d{4})-(\d{2})-(\d{2})', text)
    if match:
        date_str = match.group(0)
        remaining = text[:match.start()] + text[match.end():]
        return date_str, remaining.strip()

    return None, text


def clean_title(title, strip_patterns=None):
    """
    Clean up the title by removing common patterns.

    Removes:
        - "submitted" keyword
        - Redundant patterns passed in strip_patterns
        - Leading/trailing whitespace and underscores

    Keeps:
        - "SN NNNN" serial numbers (reformatted as "SN-NNNN")
    """
    if strip_patterns is None:
        strip_patterns = []

    # Normalize SN numbers: "SN 0001" -> "SN-0001"
    title = re.sub(r'\bSN\s*(\d+)\b', r'SN-\1', title, flags=re.IGNORECASE)

    # Remove "submitted"
    title = re.sub(r'\bsubmitted\b', '', title, flags=re.IGNORECASE)

    # Remove custom strip patterns
    for pattern in strip_patterns:
        title = title.replace(pattern, '')

    # Clean up multiple spaces, underscores, leading/trailing junk
    title = re.sub(r'[_\s]+', ' ', title)
    title = re.sub(r'^[\s_\-]+|[\s_\-]+$', '', title)

    return title


def generate_date_view(source_dirs, target_dir, strip_patterns=None, recursive=False):
    """
    Generate date-sorted folder structure with symlinks.

    Args:
        source_dirs: List of source directories to scan
        target_dir: Target directory for the view
        strip_patterns: List of strings to strip from titles
        recursive: Whether to scan subdirectories
    """
    if strip_patterns is None:
        strip_patterns = []

    target_dir = Path(target_dir).resolve()

    print(f"Sources: {len(source_dirs)} director{'y' if len(source_dirs) == 1 else 'ies'}")
    for d in source_dirs:
        print(f"  - {d}")
    print(f"Target: {target_dir}")
    print(f"Strip patterns: {strip_patterns}")
    print()

    # Collect all items with dates
    items = []  # List of (date, title, source_path, is_dir)
    no_date = []

    for source_dir in source_dirs:
        source_dir = Path(source_dir).resolve()
        if not source_dir.exists():
            print(f"WARNING: Source not found: {source_dir}")
            continue

        # Get category from source directory name (e.g., "Clinical Submissions" -> "Clinical")
        category = source_dir.name.replace(" Submissions", "").replace(" Correspondence", "")

        for entry in os.listdir(source_dir):
            full_path = source_dir / entry

            # Parse date from name
            date_str, remaining = parse_date(entry)

            if not date_str:
                no_date.append(str(full_path.relative_to(source_dir.parent.parent.parent)))
                continue

            # Clean up title
            # Remove extension if it's a file
            if full_path.is_file():
                name_without_ext = Path(entry).stem
                ext = Path(entry).suffix
            else:
                name_without_ext = entry
                ext = ""

            _, title_part = parse_date(name_without_ext)
            title = clean_title(title_part, strip_patterns)

            # If title is empty after cleaning, use the category
            if not title:
                title = category

            items.append((date_str, title, full_path, full_path.is_dir(), ext, category))

    # Sort by date, then category, then title
    items.sort(key=lambda x: (x[0], x[5], x[1]))

    # Create target directory
    target_dir.mkdir(parents=True, exist_ok=True)

    # Group items by year, then by date
    items_by_year = {}
    for item in items:
        date_str = item[0]
        year = date_str[:4]
        if year not in items_by_year:
            items_by_year[year] = {}
        if date_str not in items_by_year[year]:
            items_by_year[year][date_str] = []
        items_by_year[year][date_str].append(item)

    linked = 0
    skipped = 0

    def create_date_links(date_str, date_items, parent_dir, prefix=""):
        """Create links for items on a specific date."""
        nonlocal linked, skipped

        if len(date_items) == 1:
            # Single item on this date: symlink directly with date prefix
            _, title, source_path, is_dir, ext, category = date_items[0]
            link_name = f"{date_str} {title}"
            if ext:
                link_name += ext

            link_path = parent_dir / link_name

            if link_path.exists() or link_path.is_symlink():
                print(f"  SKIP (exists): {prefix}{link_name}")
                skipped += 1
            else:
                link_path.symlink_to(source_path)
                print(f"  LINKED: {prefix}{link_name}")
                linked += 1
        else:
            # Multiple items on this date: create date directory
            date_dir = parent_dir / date_str
            date_dir.mkdir(exist_ok=True)

            # Check for title conflicts within this date
            title_counts = {}
            for _, title, _, _, ext, _ in date_items:
                key = f"{title}{ext}"
                title_counts[key] = title_counts.get(key, 0) + 1

            for _, title, source_path, is_dir, ext, category in date_items:
                key = f"{title}{ext}"

                # Add category suffix if there are duplicates
                if title_counts[key] > 1:
                    link_name = f"{title} ({category})"
                else:
                    link_name = title

                if ext:
                    link_name += ext

                link_path = date_dir / link_name

                if link_path.exists() or link_path.is_symlink():
                    print(f"  SKIP (exists): {prefix}{date_str}/{link_name}")
                    skipped += 1
                else:
                    link_path.symlink_to(source_path)
                    print(f"  LINKED: {prefix}{date_str}/{link_name}")
                    linked += 1

    for year in sorted(items_by_year.keys()):
        dates_in_year = items_by_year[year]
        total_items_in_year = sum(len(items) for items in dates_in_year.values())

        if total_items_in_year == 1:
            # Single item in this year: no year directory
            for date_str, date_items in dates_in_year.items():
                create_date_links(date_str, date_items, target_dir)
        else:
            # Multiple items in this year: create year directory
            year_dir = target_dir / year
            year_dir.mkdir(exist_ok=True)

            for date_str in sorted(dates_in_year.keys()):
                date_items = dates_in_year[date_str]
                create_date_links(date_str, date_items, year_dir, prefix=f"{year}/")

    # Report items without dates
    for entry in no_date:
        print(f"  SKIP (no date): {entry}")

    print()
    print(f"Done: {linked} linked, {skipped} skipped, {len(no_date)} without date")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Generate date-sorted view from source files"
    )
    parser.add_argument(
        "accession",
        nargs="?",
        default="RDCP-26-0002",
        help="Accession number (default: RDCP-26-0002)",
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

    # For now, only RDCP-26-0002 is configured
    # The source is in _raw because that's where the actual files are
    raw_dir = docs_dir / "_raw" / "allena" / "ALLN-346" / "Regulatory" / "IND 143,480"

    accession_configs = {
        "RDCP-26-0002": {
            "sources": [
                raw_dir / "Clinical Submissions",
                raw_dir / "CMC Submissions",
                raw_dir / "FDA Correspondence",
                raw_dir / "Preclinical Submissions",
            ],
            "target": docs_dir / "RDCP-26-0002" / "By-Date",
            "strip_patterns": ["IND 143,480", "IND 143480"],
        },
    }

    if args.accession not in accession_configs:
        print(f"ERROR: Unknown accession '{args.accession}'")
        print(f"Available: {', '.join(accession_configs.keys())}")
        return 1

    config = accession_configs[args.accession]

    print(f"\n{'='*60}")
    print(f"Processing {args.accession}")
    print(f"{'='*60}\n")

    target = config["target"]
    if args.clean and target.exists():
        print(f"Cleaning {target}")
        shutil.rmtree(target)

    generate_date_view(
        config["sources"],
        target,
        strip_patterns=config.get("strip_patterns", []),
    )

    return 0


if __name__ == "__main__":
    exit(main())
