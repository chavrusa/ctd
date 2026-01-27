#!/usr/bin/env python3
"""
Reorganize document archive into accession-numbered structure.

Uses symlinks to preserve original files in _raw/ while creating
a clean structure under accession folders. This makes re-downloads
idempotent (rclone sees files still exist in _raw/).

Accession numbers (RDCP = Regulatory Data Commons Project):
  RDCP-26-0001 = ALLN-177 (Reloxaliase)
  RDCP-26-0002 = ALLN-346
  RDCP-26-0003 = Divalent siRNA

New structure:
  documents/
  ├── _raw/                      # Original downloads (preserved)
  │   ├── allena/                # Allena Pharmaceuticals data
  │   ├── divalent-ind/          # Divalent IND application
  │   └── divalent-research/     # Divalent research data (GitHub)
  │
  ├── RDCP-26-0001/              # ALLN-177 (Reloxaliase)
  │   └── files/
  │       ├── Clinical-Studies/  # -> symlinks to _raw/allena/...
  │       └── ...
  │
  ├── RDCP-26-0002/              # ALLN-346
  │   └── files/
  │       ├── Clinical-Studies/  # -> symlinks to _raw/allena/...
  │       └── ...
  │
  ├── RDCP-26-0003/              # Divalent siRNA
  │   └── files/
  │       ├── IND-Application/   # -> symlink to _raw/divalent-ind
  │       └── Research-Data/     # -> symlinks to _raw/divalent-research/...
  │
  └── Supporting/                 # Cross-cutting documents (no accession)
      └── Health-Advances/
"""

import os
from pathlib import Path

DOCS_DIR = Path(__file__).resolve().parent.parent / "documents"
RAW_DIR = DOCS_DIR / "_raw"
DRY_RUN = False  # Set to True for dry run

# Accession number assignments
ACCESSIONS = {
    "ALLN-177": "RDCP-26-0001",
    "ALLN-346": "RDCP-26-0002",
    "Divalent-siRNA": "RDCP-26-0003",  # Handled by download_all.py
}


def log_action(action, src, dst=None):
    if dst:
        print(f"  {action}: {src} -> {dst}")
    else:
        print(f"  {action}: {src}")


def link_dir(src, dst):
    """Create an absolute symlink at dst pointing to src directory."""
    if not src.exists():
        return False

    if dst.exists() or dst.is_symlink():
        if dst.is_symlink():
            log_action("SKIP (symlink exists)", dst.relative_to(DOCS_DIR))
        else:
            log_action("SKIP (exists)", dst.relative_to(DOCS_DIR))
        return True

    if DRY_RUN:
        log_action("LINK", src.relative_to(DOCS_DIR), dst.relative_to(DOCS_DIR))
    else:
        dst.parent.mkdir(parents=True, exist_ok=True)
        # Use absolute path to avoid nested symlink resolution issues
        dst.symlink_to(src.resolve())
        log_action("LINKED", src.relative_to(DOCS_DIR), dst.relative_to(DOCS_DIR))
    return True


def link_file(src, dst):
    """Create an absolute symlink at dst pointing to src file."""
    if not src.exists():
        return False

    if dst.exists() or dst.is_symlink():
        if dst.is_symlink():
            log_action("SKIP (symlink exists)", dst.relative_to(DOCS_DIR))
        else:
            log_action("SKIP (exists)", dst.relative_to(DOCS_DIR))
        return True

    if DRY_RUN:
        log_action("LINK FILE", src.relative_to(DOCS_DIR), dst.relative_to(DOCS_DIR))
    else:
        dst.parent.mkdir(parents=True, exist_ok=True)
        # Use absolute path to avoid nested symlink resolution issues
        dst.symlink_to(src.resolve())
        log_action("LINKED FILE", src.relative_to(DOCS_DIR), dst.relative_to(DOCS_DIR))
    return True


def reorganize():
    print("=" * 60)
    print("DOCUMENT ARCHIVE REORGANIZATION (symlinks)")
    print("=" * 60)
    if DRY_RUN:
        print(">>> DRY RUN - No symlinks will be created <<<")
        print(">>> Run with DRY_RUN=False to execute <<<")
    print()
    print("Accession assignments:")
    for drug, accession in ACCESSIONS.items():
        print(f"  {accession} = {drug}")
    print()
    print(f"Source: {RAW_DIR}")
    print()

    if not RAW_DIR.exists():
        print(f"ERROR: Raw directory not found: {RAW_DIR}")
        print("Run download_all.py first to download source files.")
        return

    # Source directories
    allena_raw = RAW_DIR / "allena"
    divalent_ind_raw = RAW_DIR / "divalent-ind"
    divalent_research_raw = RAW_DIR / "divalent-research"

    # =========================================
    # 1. ALLN-346 -> RDCP-26-0002
    # =========================================
    print("1. ALLN-346 -> RDCP-26-0002")
    print("-" * 40)

    alln346_accession = DOCS_DIR / ACCESSIONS["ALLN-346"] / "files"
    alln346_main = allena_raw / "ALLN-346"
    alln346_backup = allena_raw / "Back-up" / "ALLN-346"
    alln346_clinical = alln346_accession / "Clinical-Studies"

    # Link main ALLN-346 folder content to accession
    if alln346_main.exists():
        for item in alln346_main.iterdir():
            if item.name == "Clinical Development":
                link_dir(item, alln346_clinical / "Development-Plans")
            else:
                link_dir(item, alln346_accession / item.name)

    # Link study folders from Back-up
    study_mapping_346 = {
        "ALLN-346-101-SAD Clinical Study": "101-SAD",
        "ALLN-346-102-MAD Clinical Study": "102-MAD",
        "ALLN-346-103 BBD Study": "103-BBD",
        "ALLN-346-201 Clinical Study": "201",
        "ALLN-346-202 Clinical Study": "202",
        "101 Datasets": "101-SAD/Datasets",
        "102 Datasets": "102-MAD/Datasets",
        "201 Datasets": "201/Datasets",
        "202 Datasets": "202/Datasets",
        "346 Investigators Brochure": "Investigators-Brochure",
    }

    for src_name, dst_name in study_mapping_346.items():
        src = alln346_backup / src_name
        dst = alln346_clinical / dst_name
        link_dir(src, dst)

    print()

    # =========================================
    # 2. ALLN-177 / RELOXALIASE -> RDCP-26-0001
    # =========================================
    print("2. ALLN-177 (Reloxaliase) -> RDCP-26-0001")
    print("-" * 40)

    relox_accession = DOCS_DIR / ACCESSIONS["ALLN-177"] / "files"
    relox_clinical = relox_accession / "Clinical-Studies"
    relox_backup = allena_raw / "Back-up" / "Reloxaliase"
    relox_main = allena_raw / "Reloxaliase"
    relox_additional = allena_raw / "Reloxaliase - Additional Items"
    relox_backup_additional = allena_raw / "Back-up" / "Reloxaliase - Additional Items"
    medpace_data = allena_raw / "Additional Allena Pharma data received from Medpace (Dec 2023 to Jan 2024)"

    # Link main Reloxaliase folder content
    if relox_main.exists():
        for item in relox_main.iterdir():
            link_dir(item, relox_accession / item.name)

    # Map study folders from Back-up/Reloxaliase
    study_mapping_relox = {
        "204 Datalab report": "204/Datalab-Report",
        "204 Statistics": "204/Statistics",
        "204 TLFs": "204/TLFs",
        "206 Datasets": "206/Datasets",
        "301 ADaM data": "301/ADaM-Data",
        "301 CSR": "301/CSR",
        "301 SDTM data": "301/SDTM-Data",
        "302 Final DSMB and SSR1": "302/DSMB-SSR1",
        "396 CSR and Data": "396",
        "649 CSR Draft and TLFs": "649/CSR-TLFs",
        "649 Datasets": "649/Datasets",
        "713 CSR": "713/CSR",
        "713 Datasets": "713/Datasets",
        "713 final TLFs": "713/TLFs",
    }

    for src_name, dst_name in study_mapping_relox.items():
        src = relox_backup / src_name
        dst = relox_clinical / dst_name
        link_dir(src, dst)

    # Link loose files from Back-up/Reloxaliase
    if relox_backup.exists():
        for item in relox_backup.iterdir():
            if item.is_file():
                link_file(item, relox_clinical / item.name)

    # Link Additional Items
    if relox_additional.exists():
        link_dir(relox_additional, relox_accession / "Additional-Items")
    if relox_backup_additional.exists():
        link_dir(relox_backup_additional, relox_accession / "Additional-Items-Backup")

    # Link Medpace additional data
    if medpace_data.exists():
        # This has ALLN-177 and ALLN-346 subfolders, plus raw data
        for item in medpace_data.iterdir():
            if item.name == "ALLN-177":
                link_dir(item, relox_accession / "Medpace-Data-2024" / "ALLN-177")
            elif item.name == "ALLN-346":
                link_dir(item, alln346_accession / "Medpace-Data-2024")
            else:
                link_dir(item, relox_accession / "Medpace-Data-2024" / item.name)

    print()

    # =========================================
    # 3. Divalent siRNA -> RDCP-26-0003
    # =========================================
    print("3. Divalent siRNA -> RDCP-26-0003")
    print("-" * 40)

    divalent_accession = DOCS_DIR / ACCESSIONS["Divalent-siRNA"] / "files"

    # Link IND application
    if divalent_ind_raw.exists():
        link_dir(divalent_ind_raw, divalent_accession / "IND-Application")

    # Link research data
    if divalent_research_raw.exists():
        for item in divalent_research_raw.iterdir():
            link_dir(item, divalent_accession / "Research-Data" / item.name)

    print()

    # =========================================
    # 4. SUPPORTING DOCUMENTS (no accession)
    # =========================================
    print("4. Supporting Documents")
    print("-" * 40)

    supporting = DOCS_DIR / "Supporting"
    health_advances = allena_raw / "Health Advances Data"
    health_advances_backup = allena_raw / "Back-up" / "Health Advances"

    if health_advances.exists():
        link_dir(health_advances, supporting / "Health-Advances")
    if health_advances_backup.exists():
        link_dir(health_advances_backup, supporting / "Health-Advances-Backup")

    # Link leftover xlsx file at root
    root_xlsx = allena_raw / "ALLN-346 -177 Documents in Exhibit I - present missing additonal_RH.xlsx"
    if root_xlsx.exists():
        link_file(root_xlsx, supporting / "Reference" / root_xlsx.name)

    print()
    print("=" * 60)
    if DRY_RUN:
        print("DRY RUN COMPLETE - No changes made")
        print("To execute, edit this script and set DRY_RUN = False")
    else:
        print("REORGANIZATION COMPLETE")
        print()
        print("Original files preserved in: _raw/")
        print()
        print("Next steps:")
        print("  1. Run generate_toc.py to update the table of contents")
        print("  2. Add __metadata.json files to folders as needed")
    print("=" * 60)


if __name__ == "__main__":
    reorganize()
