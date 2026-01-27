#!/usr/bin/env python3
"""Download EMA (European Medicines Agency) documents.

Downloads files to paths matching their URL structure:
  https://www.ema.europa.eu/en/documents/report/foo.json
  -> documents/_raw/www.ema.europa.eu/en/documents/report/foo.json

Usage:
  python scripts/download_ema.py                    # Download JSON catalogs only
  python scripts/download_ema.py --reports 10       # Also download 10 assessment reports
  python scripts/download_ema.py --skip-json-catalog  # Skip JSON, just download reports
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

import requests

PROJECT_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_DIR / "documents" / "_raw"

# EMA JSON index files to download
EMA_JSON_FILES = [
    "https://www.ema.europa.eu/en/documents/report/documents-output-epar_documents_json-report_en.json",
    "https://www.ema.europa.eu/en/documents/report/medicines-output-medicines_json-report_en.json",
    "https://www.ema.europa.eu/en/documents/report/medicines-output-orphan_designations-json-report_en.json",
]

# Request settings
HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}
TIMEOUT = 300
RETRY_DELAY = 5
MAX_RETRIES = 3


def url_to_local_path(url: str) -> Path:
    """Convert a URL to a local file path under _raw/."""
    parsed = urlparse(url)
    # Combine host and path: www.ema.europa.eu/en/documents/report/file.json
    rel_path = parsed.netloc + parsed.path
    return RAW_DIR / rel_path


def download_file(url: str, dest: Path, retries: int = MAX_RETRIES) -> bool:
    """Download a file from URL to destination path.

    Returns True on success, False on failure.
    """
    dest.parent.mkdir(parents=True, exist_ok=True)

    for attempt in range(retries):
        try:
            print(f"  Downloading: {url}")
            response = requests.get(
                url,
                headers=HEADERS,
                timeout=TIMEOUT,
                stream=True
            )
            response.raise_for_status()

            # Write content
            with open(dest, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            size = dest.stat().st_size
            print(f"  Saved: {dest.relative_to(RAW_DIR)} ({size:,} bytes)")
            return True

        except requests.exceptions.RequestException as e:
            print(f"  Error (attempt {attempt + 1}/{retries}): {e}")
            if attempt < retries - 1:
                print(f"  Retrying in {RETRY_DELAY}s...")
                time.sleep(RETRY_DELAY)

    print(f"  FAILED: {url}")
    return False


def fix_json_if_needed(path: Path) -> bool:
    """Fix truncated JSON files if possible.

    Some EMA JSON files arrive as raw arrays or with minor truncation.
    Returns True if file is valid JSON after fixing.
    """
    try:
        with open(path, 'rb') as f:
            content = f.read()

        # Try to parse as-is first
        try:
            json.loads(content)
            return True
        except json.JSONDecodeError:
            pass

        # Try to extract valid JSON using raw_decode
        decoder = json.JSONDecoder()
        try:
            obj, idx = decoder.raw_decode(content.decode('utf-8'))
            # Re-save as clean JSON
            with open(path, 'w') as f:
                json.dump(obj, f)
            print(f"  Fixed truncated JSON: {path.name}")
            return True
        except json.JSONDecodeError as e:
            print(f"  Could not fix JSON: {e}")
            return False

    except Exception as e:
        print(f"  Error reading file: {e}")
        return False


def download_json_indexes() -> dict:
    """Download EMA JSON index files.

    Returns dict mapping URL to local path for successfully downloaded files.
    """
    print("Downloading EMA JSON index files...")
    results = {}

    for url in EMA_JSON_FILES:
        dest = url_to_local_path(url)
        if download_file(url, dest):
            if fix_json_if_needed(dest):
                results[url] = dest
            else:
                print(f"  Warning: {dest.name} is not valid JSON")

    return results


def get_assessment_reports(epar_path: Path, limit: int = 10) -> list:
    """Extract assessment report URLs from EPAR documents JSON.

    Returns list of URLs for documents with type 'assessment-report'.
    """
    try:
        with open(epar_path) as f:
            data = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error reading EPAR documents: {e}")
        return []

    records = data.get('data', []) if isinstance(data, dict) else data
    reports = [r.get('url') for r in records
               if r.get('type') == 'assessment-report' and r.get('url')]

    return reports[:limit]


def download_assessment_reports(limit: int = 10) -> int:
    """Download assessment reports from EMA.

    Returns count of successfully downloaded files.
    """
    # Find the EPAR documents JSON
    epar_url = [u for u in EMA_JSON_FILES if 'epar_documents' in u][0]
    epar_path = url_to_local_path(epar_url)

    if not epar_path.exists():
        print("EPAR documents JSON not found. Run with --json-only first.")
        return 0

    print(f"\nFinding assessment reports in {epar_path.name}...")
    report_urls = get_assessment_reports(epar_path, limit)

    if not report_urls:
        print("No assessment reports found.")
        return 0

    print(f"Found {len(report_urls)} assessment reports to download.\n")

    success_count = 0
    for i, url in enumerate(report_urls, 1):
        print(f"[{i}/{len(report_urls)}]")
        dest = url_to_local_path(url)
        if download_file(url, dest):
            success_count += 1
        # Small delay between downloads to be polite
        if i < len(report_urls):
            time.sleep(1)

    return success_count


def main():
    parser = argparse.ArgumentParser(
        description="Download EMA documents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        "--reports",
        type=int,
        default=0,
        metavar="N",
        help="Number of assessment reports to download (default: 0)"
    )
    parser.add_argument(
        "--skip-json-catalog",
        action="store_true",
        help="Skip downloading JSON catalog files"
    )

    args = parser.parse_args()

    print("EMA Document Downloader")
    print("=" * 60)
    print(f"Output directory: {RAW_DIR}")
    print()

    # Download JSON catalogs
    if not args.skip_json_catalog:
        json_results = download_json_indexes()
        print(f"\nDownloaded {len(json_results)}/{len(EMA_JSON_FILES)} JSON catalog files.")

    # Download assessment reports
    if args.reports > 0:
        print()
        count = download_assessment_reports(args.reports)
        print(f"\nDownloaded {count}/{args.reports} assessment reports.")

    print("\nDone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
