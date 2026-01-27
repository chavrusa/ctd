#!/usr/bin/env python3
"""Download EMA files on demand.

Downloads a specific EMA file to make a broken symlink work.

Usage:
    # Download by URL
    python scripts/download_ema_file.py "https://www.ema.europa.eu/en/documents/..."

    # Download by local symlink path (resolves to URL)
    python scripts/download_ema_file.py documents/RDCP-E26-EMA/files/EMEA-H-C-003820/EMA/2017-05-11\ Public\ assessment\ report.pdf

    # Download all files for a product
    python scripts/download_ema_file.py --product EMEA/H/C/003820
    python scripts/download_ema_file.py --product EMEA-H-C-003820
"""

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

import requests

PROJECT_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_DIR / "documents" / "_raw"
DOCUMENTS_DIR = PROJECT_DIR / "documents"
EMA_ACCESSION = "RDCP-E26-EMA"
EMA_ACCESSION_DIR = DOCUMENTS_DIR / EMA_ACCESSION

# Request settings (from download_ema.py)
HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}
TIMEOUT = 300
RETRY_DELAY = 5
MAX_RETRIES = 3


def url_to_raw_path(url: str) -> Path:
    """Convert EMA URL to local _raw path."""
    parsed = urlparse(url)
    rel_path = parsed.netloc + parsed.path
    return RAW_DIR / rel_path


def raw_path_to_url(path: Path) -> str | None:
    """Convert _raw path back to EMA URL."""
    try:
        rel_path = path.relative_to(RAW_DIR)
    except ValueError:
        return None

    parts = rel_path.parts
    if len(parts) < 2:
        return None

    # First part should be the host (www.ema.europa.eu)
    host = parts[0]
    path_part = "/".join(parts[1:])

    return f"https://{host}/{path_part}"


def resolve_symlink_to_raw(symlink_path: Path) -> Path | None:
    """Follow symlink chain to find final target in _raw/.

    Handles two-level symlinks:
    By-ATC/.../file -> files/.../file -> _raw/www.ema.europa.eu/...
    """
    current = symlink_path

    # Follow symlink chain (up to 10 hops to prevent infinite loops)
    for _ in range(10):
        if not current.is_symlink():
            # Reached a real file or broken target
            break

        # Read symlink target
        target = current.readlink()

        # If target is relative, resolve from symlink's directory
        if not target.is_absolute():
            target = (current.parent / target).resolve()

        current = target

    # Check if we ended up in _raw/
    try:
        current.relative_to(RAW_DIR)
        return current
    except ValueError:
        # Not under _raw/, might be fully resolved path
        # Try to normalize it
        return current


def download_file(url: str, dest: Path, retries: int = MAX_RETRIES) -> bool:
    """Download a file from URL to destination path.

    Returns True on success, False on failure.
    """
    dest.parent.mkdir(parents=True, exist_ok=True)

    for attempt in range(retries):
        try:
            print(f"Downloading: {url}")
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
            print(f"Saved: {dest} ({size:,} bytes)")
            return True

        except requests.exceptions.RequestException as e:
            print(f"Error (attempt {attempt + 1}/{retries}): {e}")
            if attempt < retries - 1:
                print(f"Retrying in {RETRY_DELAY}s...")
                time.sleep(RETRY_DELAY)

    print(f"FAILED: {url}")
    return False


def download_from_url(url: str) -> bool:
    """Download an EMA file by URL."""
    dest = url_to_raw_path(url)

    if dest.exists():
        print(f"File already exists: {dest}")
        return True

    return download_file(url, dest)


def download_from_symlink(symlink_path: Path) -> bool:
    """Download an EMA file by following a symlink to find its URL."""
    if not symlink_path.is_symlink():
        print(f"Error: Not a symlink: {symlink_path}")
        return False

    # Resolve to raw path
    raw_path = resolve_symlink_to_raw(symlink_path)
    if not raw_path:
        print(f"Error: Could not resolve symlink to _raw path: {symlink_path}")
        return False

    # Convert to URL
    url = raw_path_to_url(raw_path)
    if not url:
        print(f"Error: Could not convert path to URL: {raw_path}")
        return False

    # Download
    return download_from_url(url)


def find_product_symlinks(product_id: str) -> list[Path]:
    """Find all symlinks for a product in files/{product}/EMA/."""
    # Normalize product ID (handle both EMEA/H/C/005824 and EMEA-H-C-005824)
    escaped = product_id.replace("/", "-")

    product_dir = EMA_ACCESSION_DIR / "files" / escaped / "EMA"

    if not product_dir.exists():
        print(f"Error: Product directory not found: {product_dir}")
        return []

    return list(product_dir.glob("*.pdf")) + list(product_dir.glob("*.PDF"))


def download_product_files(product_id: str) -> tuple[int, int]:
    """Download all files for a product.

    Returns (success_count, total_count).
    """
    symlinks = find_product_symlinks(product_id)

    if not symlinks:
        return 0, 0

    print(f"Found {len(symlinks)} files for product {product_id}")
    print()

    success = 0
    for i, symlink in enumerate(symlinks, 1):
        print(f"[{i}/{len(symlinks)}] {symlink.name}")
        if download_from_symlink(symlink):
            success += 1
        print()

        # Small delay between downloads
        if i < len(symlinks):
            time.sleep(1)

    return success, len(symlinks)


def verify_symlink(symlink_path: Path) -> bool:
    """Check if a symlink now resolves to an existing file."""
    if not symlink_path.is_symlink():
        return False

    # Follow the symlink chain
    try:
        resolved = symlink_path.resolve(strict=True)
        return resolved.exists()
    except OSError:
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Download EMA files on demand",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        "path",
        nargs="?",
        help="URL or local symlink path to download"
    )
    parser.add_argument(
        "--product",
        metavar="ID",
        help="Download all files for a product (e.g., EMEA/H/C/003820)"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify that symlinks resolve after download"
    )

    args = parser.parse_args()

    if not args.path and not args.product:
        parser.print_help()
        return 1

    success = False

    if args.product:
        # Download all files for a product
        count, total = download_product_files(args.product)
        print(f"Downloaded {count}/{total} files.")
        success = count > 0

    elif args.path:
        path = args.path

        if path.startswith("http://") or path.startswith("https://"):
            # Direct URL
            success = download_from_url(path)
        else:
            # Local path - could be symlink or absolute/relative path
            symlink_path = Path(path)
            if not symlink_path.is_absolute():
                symlink_path = Path.cwd() / symlink_path

            symlink_path = symlink_path.resolve()

            if symlink_path.is_symlink():
                success = download_from_symlink(symlink_path)
            elif symlink_path.exists():
                print(f"File already exists (not a symlink): {symlink_path}")
                success = True
            else:
                print(f"Error: File not found: {symlink_path}")
                success = False

        # Optionally verify symlink
        if args.verify and success and not path.startswith("http"):
            symlink_path = Path(path)
            if not symlink_path.is_absolute():
                symlink_path = Path.cwd() / symlink_path

            if verify_symlink(symlink_path):
                print(f"Verified: Symlink now resolves correctly")
            else:
                print(f"Warning: Symlink still broken: {symlink_path}")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
