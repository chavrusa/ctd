#!/usr/bin/env python3
"""
Download all source documents for the CTD Document Archive.

This script downloads documents from various sources and organizes them
into the expected structure for the archive.

Sources:
  - Allena Pharmaceuticals data (Google Drive)
  - Divalent siRNA IND application (Google Drive)
  - Divalent siRNA research data (GitHub)

Requirements:
  - rclone (https://rclone.org/install/)
  - Google Cloud service account with Drive API access

Setup:
  1. Create a Google Cloud project at console.cloud.google.com
  2. Enable the Google Drive API
  3. Create a Service Account and download the JSON key
  4. (If folders are private) Share them with the service account email

Usage:
  python download_all.py --service-account /path/to/key.json
  python download_all.py                    # Uses ./service-account.json
  python download_all.py --skip-download    # Just run processing steps
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

# Base paths (resolve to absolute paths so script works from any CWD)
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
DOCS_DIR = PROJECT_DIR / "documents"

# Default service account file search paths
DEFAULT_SA_FILE_PATHS = [
    PROJECT_DIR / "service-account.json",
    Path.home() / ".config" / "rclone" / "service-account.json",
]

# Google Drive folder IDs - all download to _raw/, then reorganize.py symlinks
GDRIVE_SOURCES = {
    "allena": {
        "id": "1U6Sh2ct6Vxb5gpo8lveOSe3hd1jvYfYo",
        "dest": "_raw/allena",
        "title": "Allena Pharmaceuticals Data",
        "description": "Clinical trial data for ALLN-177 (Reloxaliase) and ALLN-346",
    },
    "divalent_ind": {
        "id": "1aEKNHK5fXQ8-iuE2QDFtY6BKzn8eS-7d",
        "dest": "_raw/divalent-ind",
        "title": "IND Application",
        "description": "FDA Investigational New Drug application (IND 167326). 92 documents comprising the full IND submission, cleared March 14, 2025.",
    },
}

# GitHub sources - all download to _raw/, then reorganize.py symlinks
GITHUB_SOURCES = {
    "divalent_research": {
        "repo": "ericminikel/divalent",
        "paths": ["data", "display_items"],
        "dest": "_raw/divalent-research",
        "title": "Research Data",
        "description": "Raw datasets and figures from the divalent siRNA research project.",
    },
}


def find_service_account_file(explicit_path=None):
    """Find the Google service account JSON file."""
    if explicit_path:
        path = Path(explicit_path)
        if path.exists():
            return path
        return None

    for path in DEFAULT_SA_FILE_PATHS:
        if path.exists():
            return path
    return None


def check_rclone():
    """Check if rclone is installed."""
    try:
        result = subprocess.run(
            ["rclone", "version"],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def write_folder_metadata(dest_path, title, description, source_type, source_url):
    """Write a __metadata.json file with folder info and source attribution.

    Uses __metadata.json (with double underscore) to avoid conflicts with
    any metadata.json files that may exist in the source data.
    """
    import json

    metadata = {
        "_folder": {
            "title": title,
            "summary": description,
            "source": {
                "type": source_type,
                "url": source_url,
            }
        }
    }

    metadata_file = dest_path / "__metadata.json"

    # Merge with existing metadata if present
    if metadata_file.exists():
        try:
            with open(metadata_file, "r") as f:
                existing = json.load(f)
            # Only update _folder, preserve file-level metadata
            existing["_folder"] = metadata["_folder"]
            metadata = existing
        except (json.JSONDecodeError, IOError):
            pass

    with open(metadata_file, "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"  ✓ Created __metadata.json with source info")


def download_gdrive_folder(folder_id, dest_path, title, description, sa_file, write_metadata=True):
    """Download a Google Drive folder using rclone with service account."""
    print(f"\n{'='*60}")
    print(f"Downloading: {title}")
    print(f"  Google Drive ID: {folder_id}")
    print(f"  Destination: {dest_path}")
    print(f"{'='*60}")

    dest_path.mkdir(parents=True, exist_ok=True)

    url = f"https://drive.google.com/drive/folders/{folder_id}"

    # Use rclone with on-the-fly backend config (no rclone.conf needed)
    # Format: :drive,service_account_file=X,root_folder_id=Y:
    backend = f":drive,service_account_file={sa_file},root_folder_id={folder_id}:"

    try:
        result = subprocess.run(
            [
                "rclone", "copy",
                backend,
                str(dest_path),
                "--progress",
                "--drive-acknowledge-abuse",  # Download even if flagged
            ],
            text=True,
        )

        if result.returncode != 0:
            print(f"  ✗ rclone failed with exit code {result.returncode}")
            print(f"  You may need to download manually from:")
            print(f"    {url}")
            return False

        print(f"  ✓ Download complete")

        # Write metadata with source info
        if write_metadata:
            write_folder_metadata(dest_path, title, description, "google-drive", url)

        return True
    except Exception as e:
        print(f"  ✗ Download failed: {e}")
        print(f"  You may need to download manually from:")
        print(f"    {url}")
        return False


def download_github_paths(repo, paths, dest_path, title, description, write_metadata=True):
    """Download specific paths from a GitHub repository."""
    print(f"\n{'='*60}")
    print(f"Downloading: {title}")
    print(f"  Repository: {repo}")
    print(f"  Paths: {', '.join(paths)}")
    print(f"  Destination: {dest_path}")
    print(f"{'='*60}")

    dest_path.mkdir(parents=True, exist_ok=True)

    # Clone to temp directory, then copy specific paths
    temp_dir = DOCS_DIR / "_temp_github"

    try:
        # Clone the repo (shallow clone for speed)
        if temp_dir.exists():
            shutil.rmtree(temp_dir)

        clone_url = f"https://github.com/{repo}.git"
        print(f"  Cloning {clone_url}...")

        result = subprocess.run(
            ["git", "clone", "--depth", "1", clone_url, str(temp_dir)],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            print(f"  ✗ Clone failed: {result.stderr}")
            return False

        # Copy specified paths
        for path in paths:
            src = temp_dir / path
            dst = dest_path / path

            if src.exists():
                if src.is_dir():
                    if dst.exists():
                        shutil.rmtree(dst)
                    shutil.copytree(src, dst)
                else:
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dst)
                print(f"  ✓ Copied {path}")
            else:
                print(f"  ⚠ Path not found: {path}")

        print(f"  ✓ Download complete")

        # Write metadata with source info
        if write_metadata:
            repo_url = f"https://github.com/{repo}"
            write_folder_metadata(dest_path, title, description, "github", repo_url)

        return True

    except Exception as e:
        print(f"  ✗ Download failed: {e}")
        return False

    finally:
        # Cleanup temp directory
        if temp_dir.exists():
            shutil.rmtree(temp_dir)


def run_script(script_name, description):
    """Run a Python script in the same directory."""
    script_path = SCRIPT_DIR / script_name

    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"  Script: {script_name}")
    print(f"{'='*60}")

    if not script_path.exists():
        print(f"  ✗ Script not found: {script_path}")
        return False

    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=str(SCRIPT_DIR),
    )

    if result.returncode == 0:
        print(f"  ✓ Complete")
        return True
    else:
        print(f"  ✗ Failed with exit code {result.returncode}")
        return False


def create_accession_metadata():
    """Create initial metadata.json files for accessions."""
    print(f"\n{'='*60}")
    print("Creating accession metadata files")
    print(f"{'='*60}")

    accessions = [
        {
            "path": DOCS_DIR / "RDCP-26-0001",
            "metadata": {
                "accession": "RDCP-26-0001",
                "title": "RDCP-26-0001 - ALLN-177 Reloxaliase",
                "drug": "ALLN-177",
                "drugName": "Reloxaliase",
                "description": "Oral enzyme therapeutic for enteric hyperoxaluria. Reloxaliase is a recombinant oxalate decarboxylase enzyme designed to degrade dietary oxalate in the gastrointestinal tract.",
                "license": {
                    "spdx": "LicenseRef-FDA-Public",
                    "name": "FDA Public Disclosure",
                    "attribution": "Source: FDA public records via Allena Pharmaceuticals"
                },
                "source": {
                    "name": "Allena Pharmaceuticals",
                    "url": "https://drive.google.com/drive/folders/1U6Sh2ct6Vxb5gpo8lveOSe3hd1jvYfYo"
                }
            }
        },
        {
            "path": DOCS_DIR / "RDCP-26-0002",
            "metadata": {
                "accession": "RDCP-26-0002",
                "title": "RDCP-26-0002 - ALLN-346 Urate Oxidase",
                "drug": "ALLN-346",
                "drugName": "Urate Oxidase",
                "description": "Engineered uricase enzyme for treatment of hyperuricemia and gout in patients with chronic kidney disease. Received FDA Fast Track designation.",
                "license": {
                    "spdx": "LicenseRef-FDA-Public",
                    "name": "FDA Public Disclosure",
                    "attribution": "Source: FDA public records via Allena Pharmaceuticals"
                },
                "source": {
                    "name": "Allena Pharmaceuticals",
                    "url": "https://drive.google.com/drive/folders/1U6Sh2ct6Vxb5gpo8lveOSe3hd1jvYfYo"
                }
            }
        },
        {
            "path": DOCS_DIR / "RDCP-26-0003",
            "metadata": {
                "accession": "RDCP-26-0003",
                "title": "RDCP-26-0003 - Divalent siRNA",
                "drug": "Divalent siRNA",
                "drugName": "Divalent siRNA",
                "description": "Gene therapy for prion disease using divalent siRNA technology. IND cleared by FDA March 14, 2025. Open-source research project.",
                "license": {
                    "spdx": "CC-BY-4.0",
                    "name": "Creative Commons Attribution 4.0",
                    "url": "https://creativecommons.org/licenses/by/4.0/",
                    "attribution": "Gentile JE, Corridon TL, Serack FE, et al. Divalent siRNA for prion disease. bioRxiv. 2024 Dec 5;2024.12.05.627039. https://doi.org/10.1101/2024.12.05.627039"
                },
                "source": {
                    "name": "Eric Minikel et al.",
                    "url": "https://github.com/ericminikel/divalent"
                }
            }
        },
    ]

    import json

    for acc in accessions:
        path = acc["path"]
        metadata = acc["metadata"]

        path.mkdir(parents=True, exist_ok=True)
        metadata_file = path / "metadata.json"

        # Don't overwrite existing metadata
        if metadata_file.exists():
            print(f"  ⚠ Skipping {metadata['accession']} (metadata.json already exists)")
            continue

        with open(metadata_file, "w") as f:
            json.dump(metadata, f, indent=2)

        print(f"  ✓ Created {metadata['accession']}/metadata.json")


def main():
    parser = argparse.ArgumentParser(
        description="Download all source documents for the CTD Document Archive"
    )
    parser.add_argument(
        "--service-account",
        metavar="FILE",
        help="Path to Google service account JSON key file",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Delete _raw directory before downloading (fresh start)",
    )
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="Skip download steps, just run processing scripts",
    )
    parser.add_argument(
        "--skip-processing",
        action="store_true",
        help="Skip processing steps (extract, reorganize, generate_toc)",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("CTD DOCUMENT ARCHIVE - DOWNLOAD ALL")
    print("=" * 60)

    # Check dependencies
    sa_file = None
    if not args.skip_download:
        if not check_rclone():
            print("\n✗ Error: rclone is not installed.")
            print("  Install it with: curl https://rclone.org/install.sh | sudo bash")
            print("  Or see: https://rclone.org/install/")
            sys.exit(1)

        sa_file = find_service_account_file(args.service_account)
        if not sa_file:
            print("\n✗ Error: Google service account file not found.")
            if args.service_account:
                print(f"  Specified file does not exist: {args.service_account}")
            else:
                print("  Searched in:")
                for p in DEFAULT_SA_FILE_PATHS:
                    print(f"    - {p}")
            print("\n  Setup instructions:")
            print("    1. Create a Google Cloud project at console.cloud.google.com")
            print("    2. Enable the Google Drive API")
            print("    3. Create a Service Account, download the JSON key")
            print("    4. Run: python scripts/download_all.py --service-account /path/to/key.json")
            sys.exit(1)

        print(f"Using service account: {sa_file}")

    # Create documents directory
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    # Clean _raw directory if requested
    if args.clean:
        raw_dir = DOCS_DIR / "_raw"
        if raw_dir.exists():
            print(f"\nCleaning: {raw_dir}")
            shutil.rmtree(raw_dir)
            print("  ✓ Deleted _raw directory")

    success = True

    if not args.skip_download:
        # Download from Google Drive
        for name, source in GDRIVE_SOURCES.items():
            dest = DOCS_DIR / source["dest"]
            if not download_gdrive_folder(
                source["id"], dest, source["title"], source["description"], sa_file
            ):
                success = False

        # Download from GitHub
        for name, source in GITHUB_SOURCES.items():
            dest = DOCS_DIR / source["dest"]
            if not download_github_paths(
                source["repo"],
                source["paths"],
                dest,
                source["title"],
                source["description"],
            ):
                success = False

    if not args.skip_processing:
        # Create accession metadata files
        create_accession_metadata()

        # Run processing scripts
        if not run_script("extract_zips.py", "Extract ZIP archives"):
            success = False

        if not run_script("reorganize.py", "Reorganize into accession structure"):
            success = False

        if not run_script("generate_toc.py", "Generate table of contents"):
            success = False

    # Summary
    print(f"\n{'='*60}")
    if success:
        print("✓ ALL STEPS COMPLETED SUCCESSFULLY")
    else:
        print("⚠ COMPLETED WITH ERRORS (see above)")
    print(f"{'='*60}")

    print("\nNext steps:")
    print("  1. Review documents/ folder structure")
    print("  2. Add __metadata.json files to folders as needed")
    print("  3. Run: cd web && npm install && npm run dev")


if __name__ == "__main__":
    main()
