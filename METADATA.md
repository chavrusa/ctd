# Metadata Format Specification

This document defines the metadata format used throughout the CTD Document Archive.

## Overview

The archive uses a hierarchical metadata system:
1. **Accession-level** metadata (`documents/RDCP-26-XXXX/metadata.json`)
2. **Folder-level** metadata (`documents/RDCP-26-XXXX/files/.../metadata.json`)
3. **File-level** metadata (entries within folder metadata.json files)

## Directory Structure

```
documents/
├── RDCP-26-0001/                    # Accession folder
│   ├── metadata.json                # Accession-level metadata
│   └── files/
│       ├── Clinical-Studies/
│       │   ├── metadata.json        # Folder metadata
│       │   └── 204/
│       │       ├── metadata.json    # Folder + file metadata
│       │       └── CSR.pdf
│       └── ...
├── RDCP-26-0002/
│   ├── metadata.json
│   └── files/
│       └── ...
└── Supporting/                       # Non-accession content
    └── ...
```

## Accession Numbers

Format: `RDCP-YY-NNNN`
- **RDCP** = Regulatory Data Commons Project
- **YY** = Year (e.g., 26 = 2026)
- **NNNN** = Sequential number within year

Current assignments:
| Accession | Drug | Description |
|-----------|------|-------------|
| RDCP-26-0001 | ALLN-177 (Reloxaliase) | Oral enzyme for enteric hyperoxaluria |
| RDCP-26-0002 | ALLN-346 | Engineered uricase for hyperuricemia/gout |
| RDCP-26-0003 | Divalent siRNA | Gene therapy for prion disease |

---

## Accession-Level Metadata

Located at `documents/RDCP-26-XXXX/metadata.json`:

```json
{
  "accession": "RDCP-26-0001",
  "title": "ALLN-177 (Reloxaliase) Clinical Development Package",
  "drug": "ALLN-177",
  "drugName": "Reloxaliase",
  "description": "Oral enzyme therapeutic for enteric hyperoxaluria...",
  "license": {
    "spdx": "LicenseRef-FDA-Public",
    "name": "FDA Public Disclosure",
    "url": "https://www.fda.gov/...",
    "attribution": "Source: FDA public records via Allena Pharmaceuticals"
  },
  "source": {
    "name": "Allena Pharmaceuticals",
    "url": "https://drive.google.com/drive/folders/..."
  },
  "dateRange": {
    "earliest": "2018-01-15",
    "latest": "2024-03-20"
  }
}
```

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `accession` | string | Yes | Accession number (e.g., `RDCP-26-0001`) |
| `title` | string | Yes | Human-readable title for the collection |
| `drug` | string | Yes | Drug identifier (inherited by all files) |
| `drugName` | string | No | Brand/generic name |
| `description` | string | No | Multi-sentence description of the collection |
| `license` | object | Yes | Licensing information (see below) |
| `source` | object | No | Data source information |
| `dateRange` | object | No | Date range of documents in collection |

### License Object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `spdx` | string | Yes | SPDX identifier or `LicenseRef-*` for custom |
| `name` | string | Yes | Human-readable license name |
| `url` | string | No | Link to full license text |
| `attribution` | string | No | Required attribution text |

Common license values:
- `CC-BY-4.0` - Creative Commons Attribution 4.0
- `LicenseRef-FDA-Public` - FDA public disclosure records

---

## Folder-Level Metadata

Located in `metadata.json` within any folder under `files/`:

```json
{
  "_folder": {
    "title": "Clinical Studies",
    "summary": "Phase 1-3 clinical trial documentation"
  }
}
```

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | string | No | Display name for the folder |
| `summary` | string | No | One-sentence description |
| `drug` | string | No | Override inherited drug (rare) |
| `source` | object | No | Where this folder's content came from |

### Source Object

For folders created by the download scripts:

```json
{
  "_folder": {
    "title": "IND Application",
    "summary": "FDA Investigational New Drug application...",
    "source": {
      "type": "google-drive",
      "url": "https://drive.google.com/drive/folders/..."
    }
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `type` | string | Source type: `google-drive`, `github`, or other |
| `url` | string | Original URL where content was downloaded from |

### Downloaded Folder Metadata (`__metadata.json`)

For folders containing downloaded source files, use `__metadata.json` (double underscore prefix) instead of `metadata.json`. This prevents conflicts with any `metadata.json` files that may exist in the source data itself.

The `generate_toc.py` script reads both `metadata.json` and `__metadata.json`, merging their contents (with `metadata.json` taking precedence if both exist).

---

## File-Level Metadata

Included in the same `metadata.json` as folder metadata, keyed by filename:

```json
{
  "_folder": {
    "title": "Study 204"
  },
  "CSR.pdf": {
    "title": "Clinical Study Report",
    "summary": "Phase 2 efficacy and safety results",
    "date": "2023-06-15",
    "tags": ["csr", "phase-2", "efficacy"],
    "ctdModule": "5.3.5.1",
    "ctdTitle": "Reports of Controlled Clinical Studies"
  },
  "Protocol.pdf": {
    "title": "Study Protocol v3.0",
    "date": "unknown",
    "tags": ["protocol"],
    "ctdModule": "5.3.5.1"
  }
}
```

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | string | No | Display name (instead of filename) |
| `summary` | string | No | One-sentence description |
| `date` | string | No | Document date as `YYYY-MM-DD` or `"unknown"` |
| `tags` | array | No | Labels for filtering and categorization |
| `ctdModule` | string | No | CTD module number (e.g., `5.3.5.1`) |
| `ctdTitle` | string | No | CTD module title |

---

## Standard Tag Vocabulary

Use consistent tags for filtering and organization:

### Document Types
- `csr` - Clinical Study Report
- `protocol` - Study protocol
- `tlf` - Tables, Listings, Figures
- `dataset` - Raw data files
- `investigator-brochure` - IB document
- `informed-consent` - ICF documents
- `statistical-analysis-plan` - SAP

### Development Phases
- `preclinical` - Nonclinical studies
- `phase-1` - Phase 1 clinical
- `phase-2` - Phase 2 clinical
- `phase-3` - Phase 3 clinical
- `cmc` - Chemistry, Manufacturing, Controls

### CTD Modules
- `module-1` - Administrative
- `module-2` - Summaries
- `module-3` - Quality
- `module-4` - Nonclinical
- `module-5` - Clinical

### Data Standards
- `adam` - ADaM datasets
- `sdtm` - SDTM datasets

---

## Inheritance

Properties flow down the hierarchy:

1. `drug` from accession-level is inherited by all files
2. Folder `_folder` properties apply to that folder
3. File-level metadata overrides inherited values

Example:
```
RDCP-26-0001/metadata.json        → drug: "ALLN-177"
RDCP-26-0001/files/Clinical-Studies/204/CSR.pdf
                                  → inherits drug: "ALLN-177"
```

---

## Fallbacks

When metadata is missing:
- **File title**: Use filename
- **Folder title**: Use directory name
- **Date**: Omit from display (not `"unknown"` unless explicitly set)
- **Tags**: Empty array `[]`
- **CTD module**: Omit (file not mapped to CTD structure)

---

## Consumption

The `generate_toc.py` script reads metadata to build:
- `toc.json` - Tree structure for web UI navigation
- `toc.md` - Markdown format for LLM consumption

The web UI displays:
- Titles and summaries in sidebar
- Document dates in viewer header
- License badges per accession
- Tags for filtering (future)
