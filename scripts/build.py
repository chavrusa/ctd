#!/usr/bin/env python3
"""
Build script for CTD Document Archive.

Orchestrates the full build pipeline:
1. Download documents from sources (Google Drive, GitHub)
2. Extract ZIP archives
3. Reorganize files into accession structure
4. Generate views (CTD, By-Date)
5. Generate table of contents (toc.json, toc.md)

Usage:
    python scripts/build.py              # Full build
    python scripts/build.py --no-download  # Skip download step
    python scripts/build.py --views-only   # Just regenerate views + toc
    python scripts/build.py --toc-only     # Just regenerate toc
"""

import argparse
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent


def run_script(name, *args, **kwargs):
    """Run a Python script from the scripts directory."""
    script_path = SCRIPT_DIR / name
    if not script_path.exists():
        print(f"ERROR: Script not found: {script_path}")
        return False

    cmd = [sys.executable, str(script_path)] + list(args)
    print(f"\n{'='*60}")
    print(f"Running: {name} {' '.join(args)}")
    print(f"{'='*60}\n")

    result = subprocess.run(cmd, cwd=PROJECT_DIR)
    return result.returncode == 0


def build_download(service_account=None, clean=False):
    """Download documents from sources."""
    args = []
    if clean:
        args.append("--clean")
    if service_account:
        args.extend(["--service-account", service_account])
    return run_script("download.py", *args)


def build_extract():
    """Extract ZIP archives."""
    return run_script("extract_zips.py")


def build_reorganize():
    """Reorganize files into accession structure."""
    return run_script("reorganize.py")


def build_views(clean=False):
    """Generate all views (CTD, By-Date)."""
    success = True

    # CTD views for all accessions
    ctd_args = ["all"]
    if clean:
        ctd_args.insert(0, "--clean")
    if not run_script("generate_ctd_view.py", *ctd_args):
        success = False

    # By-Date view for RDCP-26-0002
    date_args = ["RDCP-26-0002"]
    if clean:
        date_args.insert(0, "--clean")
    if not run_script("generate_date_view.py", *date_args):
        success = False

    return success


def build_toc():
    """Generate table of contents."""
    return run_script("generate_toc.py")


def main():
    parser = argparse.ArgumentParser(
        description="Build CTD Document Archive",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    # Clean option
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clean directories before each step (fresh build)"
    )

    # Skip options
    parser.add_argument(
        "--no-download",
        action="store_true",
        help="Skip download step"
    )
    parser.add_argument(
        "--no-extract",
        action="store_true",
        help="Skip extract step"
    )
    parser.add_argument(
        "--no-reorganize",
        action="store_true",
        help="Skip reorganize step"
    )
    parser.add_argument(
        "--no-views",
        action="store_true",
        help="Skip view generation step"
    )
    parser.add_argument(
        "--no-toc",
        action="store_true",
        help="Skip TOC generation step"
    )

    # Shortcut options
    parser.add_argument(
        "--views-only",
        action="store_true",
        help="Only regenerate views and TOC (skip download/extract/reorganize)"
    )
    parser.add_argument(
        "--toc-only",
        action="store_true",
        help="Only regenerate TOC"
    )

    # Download options
    parser.add_argument(
        "--service-account",
        metavar="PATH",
        help="Path to Google Cloud service account JSON key"
    )

    args = parser.parse_args()

    # Handle shortcut options
    if args.toc_only:
        args.no_download = True
        args.no_extract = True
        args.no_reorganize = True
        args.no_views = True

    if args.views_only:
        args.no_download = True
        args.no_extract = True
        args.no_reorganize = True

    print("CTD Document Archive Build")
    print("="*60)

    steps = []
    if not args.no_download:
        steps.append(("Download", lambda: build_download(args.service_account, args.clean)))
    if not args.no_extract:
        steps.append(("Extract", build_extract))
    if not args.no_reorganize:
        steps.append(("Reorganize", build_reorganize))
    if not args.no_views:
        steps.append(("Views", lambda: build_views(args.clean)))
    if not args.no_toc:
        steps.append(("TOC", build_toc))

    if not steps:
        print("Nothing to do (all steps skipped)")
        return 0

    print(f"Steps: {', '.join(name for name, _ in steps)}")

    failed = []
    for name, func in steps:
        if not func():
            failed.append(name)
            print(f"\nWARNING: {name} step failed, continuing...")

    print(f"\n{'='*60}")
    if failed:
        print(f"Build completed with errors in: {', '.join(failed)}")
        return 1
    else:
        print("Build completed successfully!")
        return 0


if __name__ == "__main__":
    sys.exit(main())
