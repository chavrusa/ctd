# CTD Document Archive

A public archive of regulatory documents for drug trials. Makes clinical trial data navigable and understandable for researchers, patients, and AI agents.

**Live site:** https://archive.icosian.net

## Data Sources

| Accession | Drug | Indication | Source | License |
|-----------|------|------------|--------|---------|
| RDCP-26-0001 | ALLN-177 (Reloxaliase) | Enteric hyperoxaluria | Allena Pharmaceuticals | Donated by Lumen Biosciences |
| RDCP-26-0002 | ALLN-346 (Urate Oxidase) | Hyperuricemia/gout in CKD | Allena Pharmaceuticals | Donated by Lumen Biosciences |
| RDCP-26-0003 | Divalent siRNA | Prion disease | [Eric Minikel et al.](https://github.com/ericminikel/divalent) | CC-BY-4.0 |

### Divalent siRNA Attribution

The Divalent siRNA IND application and research data are provided under CC-BY-4.0 license:

> Gentile JE, Corridon TL, Serack FE, et al. **Divalent siRNA for prion disease.** bioRxiv. 2024 Dec 5;2024.12.05.627039.
> https://doi.org/10.1101/2024.12.05.627039

## Quick Start

```bash
# Clone the repo
git clone https://github.com/chavrusa/ctd.git
cd ctd

# Build (download, extract, reorganize, generate views + toc)
python scripts/build.py --service-account /path/to/key.json

# Run the web app
cd web
npm install
npm run dev
# Open http://localhost:5173
```

## Document Download Setup

The download script uses [rclone](https://rclone.org/) with a Google Cloud service account to fetch documents from Google Drive.

### One-time setup:

1. **Install rclone**
   ```bash
   curl https://rclone.org/install.sh | sudo bash
   ```

2. **Create a Google Cloud service account**
   - Go to [console.cloud.google.com](https://console.cloud.google.com)
   - Create a new project (or use existing)
   - Enable the **Google Drive API**
   - Go to **IAM & Admin > Service Accounts**
   - Create a service account, then create a JSON key
   - Download the JSON key file

3. **Share Drive folders with the service account** (only if folders are private)
   - Copy the service account email (looks like `name@project.iam.gserviceaccount.com`)
   - Open each source Google Drive folder
   - Click Share and add the service account email as a Viewer
   - *Skip this step if folders are already public*

### Download documents:

```bash
python scripts/download.py --service-account /path/to/key.json

# Or place key at ./service-account.json and run without arg:
python scripts/download.py

# Fresh download (delete _raw and re-download everything):
python scripts/download.py --clean
```

This downloads from all sources, extracts ZIPs, reorganizes into accession structure, and generates the TOC.

## Build Options

The `build.py` script orchestrates all build steps:

```bash
# Full build
python scripts/build.py --service-account /path/to/key.json

# Fresh build (clean all generated directories first)
python scripts/build.py --clean --service-account /path/to/key.json

# Regenerate views and TOC only (skip download/extract/reorganize)
python scripts/build.py --views-only

# Regenerate TOC only
python scripts/build.py --toc-only
```

## Project Structure

```
/
├── documents/          # Document files (not in git, downloaded separately)
│   ├── RDCP-26-0001/   # ALLN-177 (Reloxaliase)
│   ├── RDCP-26-0002/   # ALLN-346
│   └── RDCP-26-0003/   # Divalent siRNA
├── scripts/            # Python scripts for data processing
│   ├── build.py            # Main build script (runs all steps)
│   ├── download.py         # Downloads documents from source locations
│   ├── extract_zips.py     # Extracts ZIP archives in documents/
│   ├── reorganize.py       # Reorganizes downloaded files into standard structure
│   ├── generate_ctd_view.py    # Generates CTD module view (symlinks)
│   ├── generate_date_view.py   # Generates chronological view (symlinks)
│   └── generate_toc.py     # Generates toc.json and toc.md from documents/
├── requirements.txt    # Python dependencies
├── web/                # SvelteKit web application
│   ├── src/
│   │   ├── routes/     # Page components
│   │   └── lib/        # Shared components and utilities
│   └── static/         # Static assets
├── toc.json            # Generated TOC for web app (not in git)
├── toc.md              # Generated TOC for LLM consumption
├── METADATA.md         # Metadata format specification
└── ROADMAP.md          # Development plan
```

## Metadata

Each directory in `documents/` can have a `metadata.json` file providing titles, descriptions, dates, and tags. See [METADATA.md](METADATA.md) for the full spec.

Example:
```json
{
  "_folder": {
    "drug": "ALLN-346",
    "summary": "Engineered uricase for hyperuricemia"
  },
  "CSR.pdf": {
    "title": "Clinical Study Report",
    "summary": "Phase 1 SAD study results",
    "date": "2023-06-15",
    "tags": ["csr", "phase-1"]
  }
}
```

## Contributing

1. Fork the repo
2. Add/update metadata.json files to improve document descriptions
3. Submit a PR

## License

This repository contains code and metadata under MIT license.

Document files have individual licenses per accession:
- **RDCP-26-0001, RDCP-26-0002**: Donated by Lumen Biosciences
- **RDCP-26-0003**: CC-BY-4.0 (see attribution above)
