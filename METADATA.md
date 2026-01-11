# Metadata Format Specification

This document defines the metadata format used throughout the CTD Document Archive.

## Overview

Each directory in `documents/` can contain a `metadata.json` file that provides human-readable titles, descriptions, and tags for files and folders.

## File Location

```
documents/
├── ALLN-346/
│   ├── metadata.json              # drug-level metadata
│   └── Preclinical Development/
│       ├── metadata.json          # section-level metadata
│       └── Nonclinical Pharmacology/
│           ├── metadata.json      # folder-level metadata
│           ├── 185507.pdf
│           └── ...
```

## Schema

```json
{
  "_folder": {
    "title": "string",
    "summary": "string",
    "drug": "string",
    "drugName": "string"
  },
  "filename.pdf": {
    "title": "string",
    "summary": "string",
    "tags": ["string"]
  }
}
```

## Fields

### Folder metadata (`_folder`)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | string | No | Display name for the folder |
| `summary` | string | No | One-sentence description |
| `drug` | string | No | Drug identifier (e.g., `ALLN-346`). Inherited by children. |
| `drugName` | string | No | Human-readable drug name (e.g., `Uricase variant`) |

### File metadata (`"filename.ext"`)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | string | No | Display name (instead of filename) |
| `summary` | string | No | One-sentence description for sidebar |
| `tags` | array | No | Labels for filtering (e.g., `["csr", "phase-1"]`) |

## Inheritance

Properties defined in a parent folder's `_folder` are inherited by all descendants:

```
documents/ALLN-346/metadata.json
{
  "_folder": {
    "drug": "ALLN-346",
    "drugName": "Uricase variant"
  }
}
```

All files under `documents/ALLN-346/` inherit `drug: "ALLN-346"` without needing to repeat it.

## Fallbacks

- If a file has no metadata entry, use the filename as the title
- If a folder has no `_folder` entry, use the directory name as the title
- If `drug` is not defined anywhere in the ancestor chain, leave it unset

## Examples

### Drug-level metadata
```json
// documents/ALLN-346/metadata.json
{
  "_folder": {
    "title": "ALLN-346",
    "summary": "Engineered uricase for hyperuricemia",
    "drug": "ALLN-346",
    "drugName": "Uricase variant"
  }
}
```

### Section-level metadata
```json
// documents/ALLN-346/Preclinical Development/metadata.json
{
  "_folder": {
    "title": "Preclinical Development",
    "summary": "Nonclinical studies supporting IND"
  }
}
```

### File-level metadata
```json
// documents/ALLN-346/Preclinical Development/Nonclinical Pharmacology/metadata.json
{
  "_folder": {
    "title": "Nonclinical Pharmacology",
    "summary": "In vitro and in vivo pharmacology studies"
  },
  "185507.pdf": {
    "title": "Primary Pharmacodynamics Study Report",
    "summary": "In vitro oxalate degradation assay results",
    "tags": ["pharmacology", "in-vitro", "study-report"]
  },
  "2.6.1 Pharmacology Intro FINAL 19Dec2019.pdf": {
    "title": "Pharmacology Introduction (CTD 2.6.1)",
    "summary": "Overview of ALLN-346 pharmacology program",
    "tags": ["ctd", "summary"]
  }
}
```

## Consumption

Scripts (`generate_toc.py`) and the UI both read these files:

1. Walk the directory tree
2. At each level, load `metadata.json` if present
3. Merge inherited properties (e.g., `drug`) from ancestors
4. Use metadata for display; fall back to filename/dirname if absent
