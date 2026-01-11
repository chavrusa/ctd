#!/usr/bin/env python3
"""
Reorganize document archive into a cleaner structure.

New structure:
  documents/
  ├── ALLN-346/
  │   ├── CMC/
  │   ├── Clinical-Studies/
  │   │   ├── 101-SAD/
  │   │   ├── 102-MAD/
  │   │   ├── 103-BBD/
  │   │   ├── 201/
  │   │   └── 202/
  │   ├── Preclinical/
  │   ├── Regulatory/
  │   └── Commercial/
  │
  ├── ALLN-177-Reloxaliase/
  │   ├── Clinical-Studies/
  │   │   ├── 204/
  │   │   ├── 206/
  │   │   ├── 301/
  │   │   ├── 302/
  │   │   ├── 396/
  │   │   ├── 649/
  │   │   └── 713/
  │   └── Additional-Data/
  │
  └── Supporting/
      └── Health-Advances/
"""

import os
import shutil
from pathlib import Path

DOCS_DIR = Path(__file__).parent / "documents"
DRY_RUN = False  # Set to False to actually move files

def log_action(action, src, dst=None):
    if dst:
        print(f"  {action}: {src} -> {dst}")
    else:
        print(f"  {action}: {src}")

def move_dir(src, dst):
    """Move a directory to a new location."""
    if not src.exists():
        return False

    if DRY_RUN:
        log_action("MOVE", src.relative_to(DOCS_DIR), dst.relative_to(DOCS_DIR))
    else:
        dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.exists():
            # Merge contents if destination exists
            for item in src.iterdir():
                target = dst / item.name
                if target.exists():
                    log_action("SKIP (exists)", item.relative_to(DOCS_DIR))
                else:
                    shutil.move(str(item), str(target))
            # Remove empty source
            if not any(src.iterdir()):
                src.rmdir()
        else:
            shutil.move(str(src), str(dst))
        log_action("MOVED", src.relative_to(DOCS_DIR), dst.relative_to(DOCS_DIR))
    return True

def remove_empty_dirs(path):
    """Remove empty directories recursively."""
    if not path.is_dir():
        return

    for child in list(path.iterdir()):
        if child.is_dir():
            remove_empty_dirs(child)

    if path.is_dir() and not any(path.iterdir()):
        if DRY_RUN:
            log_action("REMOVE (empty)", path.relative_to(DOCS_DIR))
        else:
            path.rmdir()
            log_action("REMOVED (empty)", path.relative_to(DOCS_DIR))

def reorganize():
    print("=" * 60)
    print("DOCUMENT ARCHIVE REORGANIZATION")
    print("=" * 60)
    if DRY_RUN:
        print(">>> DRY RUN - No files will be moved <<<")
        print(">>> Run with DRY_RUN=False to execute <<<")
    print()

    # =========================================
    # 1. ALLN-346 REORGANIZATION
    # =========================================
    print("1. ALLN-346 Reorganization")
    print("-" * 40)

    alln346_main = DOCS_DIR / "ALLN-346"
    alln346_backup = DOCS_DIR / "Back-up" / "ALLN-346"
    alln346_clinical = alln346_main / "Clinical-Studies"

    # Create Clinical-Studies folder and move existing Clinical Development content
    if (alln346_main / "Clinical Development").exists():
        move_dir(
            alln346_main / "Clinical Development",
            alln346_clinical / "Development-Plans"
        )

    # Move study folders from Back-up
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
        move_dir(src, dst)

    print()

    # =========================================
    # 2. ALLN-177 / RELOXALIASE REORGANIZATION
    # =========================================
    print("2. ALLN-177 (Reloxaliase) Reorganization")
    print("-" * 40)

    relox_new = DOCS_DIR / "ALLN-177-Reloxaliase"
    relox_clinical = relox_new / "Clinical-Studies"
    relox_backup = DOCS_DIR / "Back-up" / "Reloxaliase"
    relox_main = DOCS_DIR / "Reloxaliase"
    relox_additional = DOCS_DIR / "Reloxaliase - Additional Items"
    relox_backup_additional = DOCS_DIR / "Back-up" / "Reloxaliase - Additional Items"
    medpace_data = DOCS_DIR / "Additional Allena Pharma data received from Medpace (Dec 2023 to Jan 2024)"

    # Move main Reloxaliase folder content
    if relox_main.exists():
        for item in relox_main.iterdir():
            move_dir(item, relox_new / item.name)

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
        move_dir(src, dst)

    # Move loose files from Back-up/Reloxaliase
    if relox_backup.exists():
        for item in relox_backup.iterdir():
            if item.is_file():
                if DRY_RUN:
                    log_action("MOVE FILE", item.relative_to(DOCS_DIR), relox_clinical / item.name)
                else:
                    shutil.move(str(item), str(relox_clinical / item.name))

    # Move Additional Items
    if relox_additional.exists():
        move_dir(relox_additional, relox_new / "Additional-Items")
    if relox_backup_additional.exists():
        move_dir(relox_backup_additional, relox_new / "Additional-Items-Backup")

    # Move Medpace additional data
    if medpace_data.exists():
        # This has ALLN-177 and ALLN-346 subfolders, plus raw data
        for item in medpace_data.iterdir():
            if item.name == "ALLN-177":
                move_dir(item, relox_new / "Medpace-Data-2024" / "ALLN-177")
            elif item.name == "ALLN-346":
                move_dir(item, alln346_main / "Medpace-Data-2024")
            else:
                move_dir(item, relox_new / "Medpace-Data-2024" / item.name)

    print()

    # =========================================
    # 3. SUPPORTING DOCUMENTS
    # =========================================
    print("3. Supporting Documents")
    print("-" * 40)

    supporting = DOCS_DIR / "Supporting"
    health_advances = DOCS_DIR / "Health Advances Data"
    health_advances_backup = DOCS_DIR / "Back-up" / "Health Advances"

    if health_advances.exists():
        move_dir(health_advances, supporting / "Health-Advances")
    if health_advances_backup.exists():
        move_dir(health_advances_backup, supporting / "Health-Advances-Backup")

    print()

    # =========================================
    # 4. CLEANUP
    # =========================================
    print("4. Cleanup Empty Folders")
    print("-" * 40)

    # Remove emptied folders
    for folder in [relox_main, relox_additional, medpace_data, DOCS_DIR / "Back-up"]:
        if folder.exists():
            remove_empty_dirs(folder)

    # Also check for leftover xlsx file at root
    root_xlsx = DOCS_DIR / "ALLN-346 -177 Documents in Exhibit I - present missing additonal_RH.xlsx"
    if root_xlsx.exists():
        dst = supporting / "Reference" / root_xlsx.name
        if DRY_RUN:
            log_action("MOVE FILE", root_xlsx.name, dst.relative_to(DOCS_DIR))
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(root_xlsx), str(dst))

    print()
    print("=" * 60)
    if DRY_RUN:
        print("DRY RUN COMPLETE - No changes made")
        print("To execute, edit this script and set DRY_RUN = False")
    else:
        print("REORGANIZATION COMPLETE")
        print("Run generate_toc.py to update the table of contents")
    print("=" * 60)

if __name__ == "__main__":
    reorganize()
