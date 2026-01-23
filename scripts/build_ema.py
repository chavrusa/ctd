#!/usr/bin/env python3
"""Build EMA (European Medicines Agency) accession structure.

Creates the RDCP-E26-EMA accession with:
- files/{product-number}/EMA/ - toc.json entries with URLs to EMA documents
- By-ATC/ - hierarchical view by ATC classification codes

Documents are not downloaded; instead, toc.json files contain URLs that
the web app uses to link directly to EMA.

Usage:
    python scripts/build_ema.py              # Build structure
    python scripts/build_ema.py --clean      # Remove and rebuild
    python scripts/build_ema.py --dry-run    # Show what would be created
"""

import argparse
import json
import os
import re
import shutil
import unicodedata
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

# Import our modules
from ema_atc_codes import get_atc_hierarchy
from view_utils import (
    ViewStatistics,
    create_symlink_safe,
    escape_for_path,
    extract_title_from_ema_name,
    format_dated_filename,
)

PROJECT_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_DIR / "documents" / "_raw"
DOCUMENTS_DIR = PROJECT_DIR / "documents"
EMA_ACCESSION = "RDCP-E26-EMA"
EMA_ACCESSION_DIR = DOCUMENTS_DIR / EMA_ACCESSION

# Paths to EMA JSON index files
EMA_JSON_DIR = RAW_DIR / "www.ema.europa.eu" / "en" / "documents" / "report"
MEDICINES_JSON = EMA_JSON_DIR / "medicines-output-medicines_json-report_en.json"
EPAR_DOCS_JSON = EMA_JSON_DIR / "documents-output-epar_documents_json-report_en.json"


@dataclass
class Medicine:
    """Represents an EMA medicine product."""
    product_number: str
    name: str
    category: str  # Human, Veterinary
    status: str    # Authorised, Withdrawn, etc.
    atc_code: str
    url: str
    marketing_auth_date: str | None = None

    @classmethod
    def from_json(cls, data: dict) -> "Medicine":
        return cls(
            product_number=data.get("ema_product_number", ""),
            name=data.get("name_of_medicine", ""),
            category=data.get("category", ""),
            status=data.get("medicine_status", ""),
            atc_code=data.get("atc_code_human", "") or data.get("atcvet_code_veterinary", ""),
            url=data.get("medicine_url", ""),
            marketing_auth_date=data.get("marketing_authorisation_date"),
        )


@dataclass
class Document:
    """Represents an EMA EPAR document."""
    id: str
    name: str
    doc_type: str
    url: str
    publish_date: str | None
    last_update_date: str | None
    medicine_name: str | None = None  # Extracted from name
    product_number: str | None = None  # Matched from medicines

    @classmethod
    def from_json(cls, data: dict) -> "Document":
        doc = cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            doc_type=data.get("type", ""),
            url=data.get("url", ""),
            publish_date=data.get("publish_date"),
            last_update_date=data.get("last_update_date"),
        )
        # Extract medicine name from document name
        doc.medicine_name = cls._extract_medicine_name(doc.name)
        return doc

    @staticmethod
    def _extract_medicine_name(name: str) -> str | None:
        """Extract medicine name from document name.

        Document names often have format:
        "Medicine Name : EPAR - Document Type"
        "Medicine Name - Document Type"
        """
        if not name:
            return None

        # Try "Name : EPAR" pattern first
        if " : EPAR" in name:
            return name.split(" : EPAR")[0].strip()

        # Try "Name :" pattern
        if " : " in name:
            return name.split(" : ")[0].strip()

        # Try "Name -" pattern (but not if it's "EPAR - ")
        if " - " in name and not name.startswith("EPAR - "):
            parts = name.split(" - ")
            # If first part looks like a medicine name (not a document type)
            first_part = parts[0].strip()
            doc_type_words = ['epar', 'public', 'assessment', 'report', 'scientific',
                             'product', 'information', 'summary', 'annex']
            if not any(word in first_part.lower() for word in doc_type_words):
                return first_part

        return None

    def get_date(self) -> str:
        """Get the document date in YYYY-MM-DD format."""
        date_str = self.publish_date or self.last_update_date
        if not date_str:
            return "0000-00-00"

        # Parse ISO format: "2009-12-17T01:00:00Z"
        try:
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            return "0000-00-00"

    def get_title(self) -> str:
        """Get human-readable title for symlink name."""
        return extract_title_from_ema_name(self.name)

    def get_filename(self) -> str:
        """Get filename with date prefix."""
        date = self.get_date()
        title = self.get_title()
        # Get extension from URL
        ext = Path(urlparse(self.url).path).suffix or ".pdf"
        return format_dated_filename(date, title, ext)


def normalize_name(name: str) -> str:
    """Normalize a medicine name for matching.

    - Lowercase
    - Remove accents
    - Remove punctuation
    - Collapse whitespace
    """
    if not name:
        return ""

    # Lowercase
    name = name.lower()

    # Remove accents (NFD decomposition + strip combining marks)
    name = unicodedata.normalize("NFD", name)
    name = "".join(c for c in name if unicodedata.category(c) != "Mn")

    # Remove punctuation except spaces
    name = re.sub(r"[^\w\s]", " ", name)

    # Collapse whitespace
    name = " ".join(name.split())

    return name


def make_doc_toc_entry(doc: Document, path_prefix: str) -> dict:
    """Create a TOC entry for a document with external URL.

    Args:
        doc: The Document object
        path_prefix: Path prefix (unused, kept for API compatibility)

    Returns:
        dict with name, type, url, and other metadata (no path for external docs)
    """
    filename = doc.get_filename()
    return {
        "name": filename,
        "type": "pdf",
        "url": doc.url,
        "date": doc.get_date(),
        "title": doc.get_title(),
        "drug": "Multiple (EMA database)",
        "accession": EMA_ACCESSION,
    }


def make_folder_toc_entry(name: str, path: str, children: list, title: str = None) -> dict:
    """Create a TOC folder entry.

    Args:
        name: Folder name
        path: Full path like "documents/RDCP-E26-EMA/files"
        children: List of child TOC entries
        title: Display title (if different from name)

    Returns:
        dict with folder structure
    """
    entry = {
        "name": name,
        "type": "folder",
        "path": path,
        "children": children,
    }
    if title and title != name:
        entry["title"] = title
    return entry


def sort_docs_with_par_first(doc_entries: list) -> list:
    """Sort document entries with the first PAR starred and at the top.

    Finds the first "Public Assessment Report" (case-insensitive), adds a star
    emoji to its title, and moves it to the top. Other documents remain sorted
    alphabetically by name (which starts with date).

    Args:
        doc_entries: List of document TOC entries

    Returns:
        Sorted list with starred PAR first
    """
    if not doc_entries:
        return doc_entries

    # Sort alphabetically by name first
    sorted_docs = sorted(doc_entries, key=lambda x: x["name"])

    # Find the first PAR (case-insensitive match)
    par_idx = None
    for i, doc in enumerate(sorted_docs):
        title = doc.get("title", "").lower()
        if "assessment report" in title and "public" in title:
            par_idx = i
            break

    if par_idx is not None:
        # Remove the PAR from its position
        par_doc = sorted_docs.pop(par_idx)
        # Add star to title
        par_doc["title"] = "⭐ " + par_doc.get("title", "")
        # Insert at the beginning
        sorted_docs.insert(0, par_doc)

    return sorted_docs


def load_medicines() -> dict[str, Medicine]:
    """Load medicines from JSON and return dict keyed by product number."""
    if not MEDICINES_JSON.exists():
        print(f"ERROR: Medicines JSON not found: {MEDICINES_JSON}")
        print("Run 'python scripts/download_ema.py' first.")
        return {}

    with open(MEDICINES_JSON) as f:
        data = json.load(f)

    # Handle both list and dict formats
    records = data if isinstance(data, list) else data.get("data", [])

    medicines = {}
    for record in records:
        med = Medicine.from_json(record)
        if med.product_number:
            medicines[med.product_number] = med

    return medicines


def load_documents() -> list[Document]:
    """Load EPAR documents from JSON."""
    if not EPAR_DOCS_JSON.exists():
        print(f"ERROR: EPAR documents JSON not found: {EPAR_DOCS_JSON}")
        print("Run 'python scripts/download_ema.py' first.")
        return []

    with open(EPAR_DOCS_JSON) as f:
        data = json.load(f)

    # Handle both list and dict formats
    records = data if isinstance(data, list) else data.get("data", [])

    return [Document.from_json(record) for record in records]


def match_documents_to_medicines(
    documents: list[Document],
    medicines: dict[str, Medicine]
) -> dict[str, list[Document]]:
    """Match documents to medicines by name.

    Returns dict mapping product_number to list of documents.
    """
    # Build name lookup: normalized_name -> product_number
    name_to_product = {}
    for product_num, med in medicines.items():
        normalized = normalize_name(med.name)
        if normalized:
            name_to_product[normalized] = product_num

    # Match documents
    matched: dict[str, list[Document]] = defaultdict(list)
    unmatched_count = 0

    for doc in documents:
        if not doc.medicine_name:
            unmatched_count += 1
            continue

        normalized = normalize_name(doc.medicine_name)

        # Try exact match first
        if normalized in name_to_product:
            product_num = name_to_product[normalized]
            doc.product_number = product_num
            matched[product_num].append(doc)
            continue

        # Try prefix match (for cases like "Drug Name Film-Coated Tablets")
        found = False
        for name, product_num in name_to_product.items():
            if normalized.startswith(name) or name.startswith(normalized):
                doc.product_number = product_num
                matched[product_num].append(doc)
                found = True
                break

        if not found:
            unmatched_count += 1

    print(f"Matched {len(matched)} products with documents")
    print(f"Unmatched documents: {unmatched_count}")

    return matched


def filter_qualifying_products(
    medicines: dict[str, Medicine],
    product_docs: dict[str, list[Document]]
) -> dict[str, tuple[Medicine, list[Document]]]:
    """Filter to human medicines with assessment reports.

    Returns dict mapping product_number to (medicine, documents) tuple.
    """
    qualifying = {}

    for product_num, docs in product_docs.items():
        # Check if we have this medicine
        if product_num not in medicines:
            continue

        med = medicines[product_num]

        # Filter to Human only
        if med.category != "Human":
            continue

        # Filter to Authorised only
        if med.status != "Authorised":
            continue

        # Check for at least one assessment-report
        has_assessment = any(d.doc_type == "assessment-report" for d in docs)
        if not has_assessment:
            continue

        qualifying[product_num] = (med, docs)

    return qualifying


def url_to_raw_path(url: str) -> Path:
    """Convert EMA URL to local _raw path."""
    parsed = urlparse(url)
    # www.ema.europa.eu/en/documents/assessment-report/file.pdf
    rel_path = parsed.netloc + parsed.path
    return RAW_DIR / rel_path


def escape_product_number(product_num: str) -> str:
    """Escape product number for use in directory names.

    EMEA/H/C/005824 -> EMEA-H-C-005824
    """
    return escape_for_path(product_num)


def split_product_number(escaped_product: str) -> tuple[str, str]:
    """Split product number into group prefix and suffix.

    EMEA-H-C-000292 -> ("EMEA-H-C-000", "292")

    This creates grouping by first 3 digits of the product number,
    resulting in ~7 prefix groups for the current EMA data.
    """
    # Pattern: EMEA-H-C-NNNNNN (6 digits after EMEA-H-C-)
    # Group by first 3 digits (12 char prefix = "EMEA-H-C-" + "NNN")
    if len(escaped_product) >= 13:  # "EMEA-H-C-" + at least 4 chars
        prefix = escaped_product[:12]  # "EMEA-H-C-000"
        suffix = escaped_product[12:]  # "292"
        return prefix, suffix
    return escaped_product, ""


def build_files_toc_entry(
    product_num: str,
    docs: list[Document],
) -> tuple[str, str, dict]:
    """Build TOC entry for a product in files/{prefix}/{suffix}/EMA/.

    Returns tuple of (prefix, suffix, toc_entry) where toc_entry is the
    suffix folder containing EMA/ with document children.
    """
    escaped_product = escape_product_number(product_num)
    prefix, suffix = split_product_number(escaped_product)

    # Path: files/{prefix}/{suffix}/EMA
    path_prefix = f"documents/{EMA_ACCESSION}/files/{prefix}/{suffix}/EMA"

    # Build document entries
    doc_entries = []
    for doc in docs:
        if not doc.url:
            continue
        doc_entries.append(make_doc_toc_entry(doc, path_prefix))

    # Sort by date (name starts with date)
    doc_entries = sort_docs_with_par_first(doc_entries)

    # Build nested structure: {suffix}/EMA/
    ema_folder = make_folder_toc_entry(
        "EMA",
        path_prefix,
        doc_entries
    )

    suffix_folder = make_folder_toc_entry(
        suffix,
        f"documents/{EMA_ACCESSION}/files/{prefix}/{suffix}",
        [ema_folder]
    )

    return prefix, suffix, suffix_folder


def build_grouped_files_toc(
    qualifying: dict[str, tuple["Medicine", list[Document]]],
    output_dir: Path,
    dry_run: bool = False,
) -> tuple[dict, int]:
    """Build three-level grouped files TOC structure.

    Creates:
    - files/toc.json with $ref entries to each prefix group
    - files/{prefix}/toc.json with $ref entries to each product
    - files/{prefix}/{suffix}/toc.json with actual document entries

    Args:
        qualifying: dict mapping product_number to (medicine, documents) tuple
        output_dir: Path to the accession directory
        dry_run: If True, don't write files

    Returns:
        Tuple of (top-level files TOC entry, total document count)
    """
    files_dir = output_dir / "files"

    # Group products by prefix
    prefix_groups: dict[str, list[tuple[str, str, dict]]] = defaultdict(list)
    total_docs = 0

    for i, (product_num, (med, docs)) in enumerate(qualifying.items(), 1):
        if i % 100 == 0:
            print(f"  Processing {i}/{len(qualifying)}...")

        prefix, suffix, suffix_toc = build_files_toc_entry(product_num, docs)
        prefix_groups[prefix].append((suffix, suffix_toc, docs, med.name))

        # Count documents
        for doc in docs:
            if doc.url:
                total_docs += 1

    print(f"  Created {len(prefix_groups)} prefix groups")

    # Create directory structure and write toc.json files
    prefix_ref_entries = []

    for prefix in sorted(prefix_groups.keys()):
        products = prefix_groups[prefix]
        prefix_path = f"documents/{EMA_ACCESSION}/files/{prefix}"

        # Create prefix directory
        prefix_dir = files_dir / prefix
        if not dry_run:
            prefix_dir.mkdir(parents=True, exist_ok=True)

        # Build suffix-level entries with $ref markers for prefix toc.json
        suffix_ref_entries = []

        for suffix, suffix_toc, docs, med_name in sorted(products, key=lambda x: x[0]):
            suffix_path = f"{prefix_path}/{suffix}"

            # Create suffix directory
            suffix_dir = prefix_dir / suffix
            if not dry_run:
                suffix_dir.mkdir(parents=True, exist_ok=True)

                # Write product toc.json (actual document entries)
                product_toc_path = suffix_dir / "toc.json"
                with open(product_toc_path, "w") as f:
                    json.dump(suffix_toc, f, indent=2)

                # Add $ref entry for this product in prefix toc.json
            # Display title: EMEA/H/C/000292 (prefix digits + suffix)
            prefix_digits = prefix.replace("EMEA-H-C-", "")  # "000"
            full_number = prefix_digits + suffix  # "000292"
            suffix_ref_entry = {
                "name": suffix,
                "type": "folder",
                "path": suffix_path,
                "title": f"EMEA/H/C/{full_number} - {med_name}",
                "$ref": f"{suffix_path}/toc.json",
            }
            suffix_ref_entries.append(suffix_ref_entry)

        # Write prefix toc.json (with $ref to products)
        # Display title: EMEA/H/C/000XXX
        prefix_digits = prefix.replace("EMEA-H-C-", "")  # "000"
        prefix_title = f"EMEA/H/C/{prefix_digits}XXX"
        prefix_toc = {
            "name": prefix,
            "type": "folder",
            "path": prefix_path,
            "title": prefix_title,
            "children": suffix_ref_entries,
        }

        if not dry_run:
            prefix_toc_path = prefix_dir / "toc.json"
            with open(prefix_toc_path, "w") as f:
                json.dump(prefix_toc, f, indent=2)

        # Add $ref entry for this prefix in top-level files toc.json
        prefix_ref_entry = {
            "name": prefix,
            "type": "folder",
            "path": prefix_path,
            "title": prefix_title,
            "$ref": f"{prefix_path}/toc.json",
        }
        prefix_ref_entries.append(prefix_ref_entry)

    # Build top-level files toc.json
    files_toc = {
        "name": "files",
        "type": "folder",
        "path": f"documents/{EMA_ACCESSION}/files",
        "title": "All Files",
        "children": prefix_ref_entries,
        "_source": "ema-build",
    }

    if not dry_run:
        files_toc_path = files_dir / "toc.json"
        with open(files_toc_path, "w") as f:
            json.dump(files_toc, f, indent=2)
        print(f"  Written: {files_toc_path.relative_to(output_dir.parent)}")

    return files_toc, total_docs


def extract_common_name(names: list[str]) -> str | None:
    """Extract common substance name from a list of product names.

    For products like:
    - "Bortezomib Sun"
    - "Bortezomib Hospira"
    - "Bortezomib Fresenius Kabi"

    Returns "Bortezomib".
    """
    if not names:
        return None

    # Find common prefix word by word
    words_list = [name.split() for name in names]
    if not words_list:
        return None

    min_len = min(len(w) for w in words_list)
    common_words = []

    for i in range(min_len):
        first_word = words_list[0][i].lower()
        if all(w[i].lower() == first_word for w in words_list):
            common_words.append(words_list[0][i])  # Keep original case from first
        else:
            break

    if common_words:
        return " ".join(common_words)

    return None


def build_atc_trie(products: dict[str, tuple[Medicine, list[Document]]]) -> dict:
    """Build a trie of products grouped by ATC code prefixes.

    Returns nested dict where:
    - Keys are ATC code segments
    - Values are either dicts (more children) or lists of (med, docs) tuples (leaf products)
    """
    from ema_atc_codes import ATC_LEVEL1, ATC_LEVEL2, ATC_LEVEL3

    def normalize_atc(code: str) -> str:
        """Pad short ATC codes with XX to indicate unspecified subclass."""
        if not code:
            return "Z00XXXX"
        # Target length is 7 (e.g., L01FF02)
        # Pad with X at appropriate positions
        if len(code) < 7:
            return code + "X" * (7 - len(code))
        return code

    # Group products by ATC code (normalized)
    by_atc: dict[str, list[tuple[Medicine, list[Document]]]] = {}
    for product_num, (med, docs) in products.items():
        atc = normalize_atc(med.atc_code or "")
        if atc not in by_atc:
            by_atc[atc] = []
        by_atc[atc].append((med, docs))

    def get_atc_name(code: str) -> str:
        """Get name for an ATC code."""
        # First try exact match or progressively shorter prefixes
        # Check LEVEL3 (4-5+ char codes like L01X, L01XG, L01XG01)
        for length in [len(code), 5, 4]:
            prefix = code[:length] if len(code) >= length else code
            if prefix in ATC_LEVEL3:
                return ATC_LEVEL3[prefix]

        # Strip trailing X's and try again (X indicates unspecified subclass)
        base_code = code.rstrip('X')
        for length in [len(base_code), 5, 4]:
            prefix = base_code[:length] if len(base_code) >= length else base_code
            if prefix in ATC_LEVEL3:
                return ATC_LEVEL3[prefix]

        # Check LEVEL2 (3-char codes like L01, J05)
        if len(base_code) >= 3 and base_code[:3] in ATC_LEVEL2:
            return ATC_LEVEL2[base_code[:3]]

        # Check LEVEL1 (1-char codes like L, J)
        if len(base_code) >= 1 and base_code[0] in ATC_LEVEL1:
            return ATC_LEVEL1[base_code[0]]

        return "Unknown"

    def get_collapsed_prefix(code: str, length: int) -> str:
        """Get collapsed prefix for a code at given length.

        Collapses trailing X's to single X (e.g., L01XX -> L01X).
        """
        if length == 0:
            return ""
        prefix = code[:length] if len(code) >= length else code
        base = prefix.rstrip('X')
        if len(base) < len(prefix):
            return base + 'X' if base else 'X'
        return prefix

    def get_next_meaningful_level(code: str, current_len: int) -> int:
        """Find next level that produces a different collapsed prefix.

        Skips levels where X-padding would create identical collapsed prefixes.
        """
        levels = [1, 3, 4, 5, 7]
        current_collapsed = get_collapsed_prefix(code, current_len)

        for level in levels:
            if level > current_len:
                next_collapsed = get_collapsed_prefix(code, level)
                if next_collapsed != current_collapsed:
                    return level
        # No more meaningful levels - return beyond max to signal leaf
        return 999

    def build_level(codes_products: dict[str, list], prefix_len: int, parent_prefix: str = "") -> dict:
        """Recursively build trie level.

        Args:
            codes_products: dict mapping ATC code to list of (med, docs)
            prefix_len: current prefix length to group by
            parent_prefix: the collapsed prefix of the parent level (to avoid duplicates)
        """
        if not codes_products:
            return {}

        # Group by collapsed prefix of given length
        groups: dict[str, dict[str, list]] = {}
        for code, prods in codes_products.items():
            prefix = get_collapsed_prefix(code, prefix_len)
            if prefix not in groups:
                groups[prefix] = {}
            groups[prefix][code] = prods

        result = {}
        for prefix, sub_codes in groups.items():
            # Skip if this prefix is same as parent (would create duplicate folder)
            if prefix and prefix == parent_prefix:
                # Don't create folder, just recurse with higher level
                first_code = next(iter(sub_codes.keys()))
                next_level = get_next_meaningful_level(first_code, prefix_len)
                if next_level >= 999:
                    # Output as leaves
                    for code, prods in sub_codes.items():
                        for med, docs in prods:
                            escaped = escape_product_number(med.product_number)
                            atc = normalize_atc(med.atc_code or "")
                            display_name = f"{atc}) {med.name} - {med.product_number}"
                            fs_name = f"{atc}) {escape_for_path(med.name)} - {escaped}"
                            result[fs_name] = ("leaf", med, docs, display_name)
                else:
                    # Recurse but keep same parent_prefix
                    children = build_level(sub_codes, next_level, parent_prefix)
                    result.update(children)
                continue

            # Count total products in this group
            total_products = sum(len(prods) for prods in sub_codes.values())

            # If only one product, it's a leaf - don't create subdirectory
            if total_products == 1:
                # Get the single product
                for code, prods in sub_codes.items():
                    for med, docs in prods:
                        # Leaf node: key is product folder name
                        escaped = escape_product_number(med.product_number)
                        atc = normalize_atc(med.atc_code or "")
                        display_name = f"{atc}) {med.name} - {med.product_number}"
                        fs_name = f"{atc}) {escape_for_path(med.name)} - {escaped}"
                        result[fs_name] = ("leaf", med, docs, display_name)

            # If multiple products but they all have same code (no further splitting possible)
            elif len(sub_codes) == 1:
                code = list(sub_codes.keys())[0]
                prods = sub_codes[code]

                # Find next level that would produce a different prefix
                next_level = get_next_meaningful_level(code, prefix_len)

                if next_level >= 999 or len(code) <= prefix_len:
                    # No more meaningful splits by ATC prefix
                    if len(prods) > 1:
                        # Multiple products with same full ATC code - create subdirectory
                        # for the chemical substance
                        atc = normalize_atc(code)
                        # Try to get substance name from ATC dictionary, or extract from product names
                        substance_name = get_atc_name(atc)
                        # If name is generic (same as parent level), extract common name from products
                        parent_name = get_atc_name(atc[:5]) if len(atc) >= 5 else ""
                        if substance_name == parent_name:
                            # Extract common prefix from medicine names
                            names = [med.name for med, _ in prods]
                            common = extract_common_name(names)
                            if common:
                                substance_name = common
                        display_folder = f"{atc}) {substance_name}"
                        fs_folder = f"{atc}) {escape_for_path(substance_name)}"
                        children = {}
                        for med, docs in prods:
                            escaped = escape_product_number(med.product_number)
                            # Simpler leaf name since ATC is in parent folder
                            display_leaf = f"{med.name} - {med.product_number}"
                            fs_leaf = f"{escape_for_path(med.name)} - {escaped}"
                            children[fs_leaf] = ("leaf", med, docs, display_leaf)
                        result[fs_folder] = ("dir", children, display_folder)
                    else:
                        # Single product - output as leaf
                        for med, docs in prods:
                            escaped = escape_product_number(med.product_number)
                            atc = normalize_atc(med.atc_code or "")
                            display_name = f"{atc}) {med.name} - {med.product_number}"
                            fs_name = f"{atc}) {escape_for_path(med.name)} - {escaped}"
                            result[fs_name] = ("leaf", med, docs, display_name)
                else:
                    children = build_level(sub_codes, next_level, prefix)
                    if len(children) == 1:
                        # Single child - don't create intermediate directory
                        result.update(children)
                    else:
                        # Multiple children - create subdirectory
                        name = get_atc_name(prefix)
                        folder_name = f"{prefix}) {escape_for_path(name)}"
                        display_name = f"{prefix}) {name}"
                        result[folder_name] = ("dir", children, display_name)

            else:
                # Multiple different codes - need to split
                # Find next level - use first code to determine progression
                # (all codes in group share the prefix, so progression is same)
                first_code = next(iter(sub_codes.keys()))
                next_level = get_next_meaningful_level(first_code, prefix_len)

                # If no meaningful next level, output leaves (or group by full ATC)
                if next_level >= 999:
                    for code, prods in sub_codes.items():
                        if len(prods) > 1:
                            # Multiple products with same full ATC code - create subdirectory
                            atc = normalize_atc(code)
                            # Try to get substance name from ATC dictionary, or extract from product names
                            substance_name = get_atc_name(atc)
                            parent_name = get_atc_name(atc[:5]) if len(atc) >= 5 else ""
                            if substance_name == parent_name:
                                names = [med.name for med, _ in prods]
                                common = extract_common_name(names)
                                if common:
                                    substance_name = common
                            display_folder = f"{atc}) {substance_name}"
                            fs_folder = f"{atc}) {escape_for_path(substance_name)}"
                            children = {}
                            for med, docs in prods:
                                escaped = escape_product_number(med.product_number)
                                display_leaf = f"{med.name} - {med.product_number}"
                                fs_leaf = f"{escape_for_path(med.name)} - {escaped}"
                                children[fs_leaf] = ("leaf", med, docs, display_leaf)
                            result[fs_folder] = ("dir", children, display_folder)
                        else:
                            # Single product - output as leaf
                            for med, docs in prods:
                                escaped = escape_product_number(med.product_number)
                                atc = normalize_atc(med.atc_code or "")
                                display_name = f"{atc}) {med.name} - {med.product_number}"
                                fs_name = f"{atc}) {escape_for_path(med.name)} - {escaped}"
                                result[fs_name] = ("leaf", med, docs, display_name)
                    continue

                children = build_level(sub_codes, next_level, prefix)

                if prefix_len == 0:
                    # Top level - don't create a folder, just return children
                    result.update(children)
                elif len(children) == 1:
                    # Single child after recursion - collapse
                    result.update(children)
                else:
                    # Multiple children - create subdirectory for this prefix
                    name = get_atc_name(prefix)
                    folder_name = f"{prefix}) {escape_for_path(name)}"
                    display_name = f"{prefix}) {name}"
                    result[folder_name] = ("dir", children, display_name)

        return result

    return build_level(by_atc, 0)


def build_atc_toc(
    products: dict[str, tuple[Medicine, list[Document]]],
) -> dict:
    """Build TOC structure for By-ATC view.

    Returns TOC folder entry for By-ATC/.
    """
    # Build the trie
    trie = build_atc_trie(products)

    def trie_to_toc(node: dict, path_prefix: str) -> list:
        """Recursively convert trie to TOC entries."""
        entries = []

        for fs_name, value in sorted(node.items()):
            entry_path = f"{path_prefix}/{fs_name}"

            if value[0] == "leaf":
                # Leaf node - product with documents
                # value = ("leaf", med, docs, display_name)
                _, med, docs, display_name = value

                # Build document entries
                doc_entries = []
                for doc in docs:
                    if not doc.url:
                        continue
                    doc_entries.append(make_doc_toc_entry(doc, entry_path))

                # Sort by date
                doc_entries = sort_docs_with_par_first(doc_entries)

                entry = make_folder_toc_entry(fs_name, entry_path, doc_entries, display_name)
                entries.append(entry)

            elif value[0] == "dir":
                # Directory node - recurse
                # value = ("dir", children, display_name)
                _, children, display_name = value

                child_entries = trie_to_toc(children, entry_path)
                entry = make_folder_toc_entry(fs_name, entry_path, child_entries, display_name)
                entries.append(entry)

        return entries

    base_path = f"documents/{EMA_ACCESSION}/By-ATC"
    children = trie_to_toc(trie, base_path)

    return make_folder_toc_entry("By-ATC", base_path, children)


def build_grouped_atc_toc(
    products: dict[str, tuple["Medicine", list[Document]]],
    output_dir: Path,
    dry_run: bool = False,
) -> dict:
    """Build grouped By-ATC TOC structure with toc.json at levels 0, 2, and 4.

    Creates:
    - By-ATC/toc.json with level 1 inline, $ref to level 2
    - By-ATC/{L1}/{L2}/toc.json with level 3 inline, $ref to level 4
    - By-ATC/{L1}/{L2}/{L3}/{L4}/toc.json with full content

    Args:
        products: dict mapping product_number to (medicine, documents) tuple
        output_dir: Path to the accession directory
        dry_run: If True, don't write files

    Returns:
        Top-level By-ATC TOC entry
    """
    trie = build_atc_trie(products)

    def trie_to_toc(node: dict, path_prefix: str) -> list:
        """Recursively convert trie to TOC entries (full inline content)."""
        entries = []
        for fs_name, value in sorted(node.items()):
            entry_path = f"{path_prefix}/{fs_name}"

            if value[0] == "leaf":
                _, med, docs, display_name = value
                doc_entries = [make_doc_toc_entry(doc, entry_path)
                               for doc in docs if doc.url]
                doc_entries = sort_docs_with_par_first(doc_entries)
                entries.append(make_folder_toc_entry(fs_name, entry_path, doc_entries, display_name))

            elif value[0] == "dir":
                _, children, display_name = value
                child_entries = trie_to_toc(children, entry_path)
                entries.append(make_folder_toc_entry(fs_name, entry_path, child_entries, display_name))

        return entries

    def make_ref_entry(fs_name: str, path: str, display_name: str = None) -> dict:
        """Create a $ref entry pointing to a toc.json file."""
        entry = {
            "name": fs_name,
            "type": "folder",
            "path": path,
            "$ref": f"{path}/toc.json",
        }
        if display_name and display_name != fs_name:
            entry["title"] = display_name
        return entry

    def make_leaf_entry(fs_name: str, path: str, med, docs, display_name: str) -> dict:
        """Create inline entry for a leaf (product with documents)."""
        doc_entries = [make_doc_toc_entry(doc, path) for doc in docs if doc.url]
        doc_entries = sort_docs_with_par_first(doc_entries)
        return make_folder_toc_entry(fs_name, path, doc_entries, display_name)

    atc_dir = output_dir / "By-ATC"
    base_path = f"documents/{EMA_ACCESSION}/By-ATC"

    # Build level 0 (By-ATC) with level 1 inline
    level1_entries = []

    for l1_name, l1_value in sorted(trie.items()):
        if l1_value[0] != "dir":
            continue

        _, l1_children, l1_display = l1_value
        l1_path = f"{base_path}/{l1_name}"
        l1_dir = atc_dir / l1_name

        # Build level 1 entry with level 2 as $ref
        level2_entries = []

        for l2_name, l2_value in sorted(l1_children.items()):
            l2_path = f"{l1_path}/{l2_name}"
            l2_dir = l1_dir / l2_name

            if l2_value[0] == "leaf":
                # Level 2 leaf - inline
                _, med, docs, display_name = l2_value
                level2_entries.append(make_leaf_entry(l2_name, l2_path, med, docs, display_name))

            elif l2_value[0] == "dir":
                # Level 2 dir - create toc.json, use $ref
                _, l2_children, l2_display = l2_value

                if not dry_run:
                    l2_dir.mkdir(parents=True, exist_ok=True)

                # Build level 2 toc.json with level 3 inline
                level3_entries = []

                for l3_name, l3_value in sorted(l2_children.items()):
                    l3_path = f"{l2_path}/{l3_name}"
                    l3_dir = l2_dir / l3_name

                    if l3_value[0] == "leaf":
                        # Level 3 leaf - inline
                        _, med, docs, display_name = l3_value
                        level3_entries.append(make_leaf_entry(l3_name, l3_path, med, docs, display_name))

                    elif l3_value[0] == "dir":
                        # Level 3 dir - build level 4 entries
                        _, l3_children, l3_display = l3_value

                        level4_entries = []

                        for l4_name, l4_value in sorted(l3_children.items()):
                            l4_path = f"{l3_path}/{l4_name}"
                            l4_dir = l3_dir / l4_name

                            if l4_value[0] == "leaf":
                                # Level 4 leaf - inline in level 3
                                _, med, docs, display_name = l4_value
                                level4_entries.append(make_leaf_entry(l4_name, l4_path, med, docs, display_name))

                            elif l4_value[0] == "dir":
                                # Level 4 dir - create toc.json, use $ref
                                _, l4_children, l4_display = l4_value

                                if not dry_run:
                                    l4_dir.mkdir(parents=True, exist_ok=True)

                                # Write level 4 toc.json with full content
                                l4_child_entries = trie_to_toc(l4_children, l4_path)
                                l4_toc = make_folder_toc_entry(l4_name, l4_path, l4_child_entries, l4_display)

                                if not dry_run:
                                    with open(l4_dir / "toc.json", "w") as f:
                                        json.dump(l4_toc, f, indent=2)

                                level4_entries.append(make_ref_entry(l4_name, l4_path, l4_display))

                        # Level 3 entry with level 4 children (inline)
                        l3_entry = make_folder_toc_entry(l3_name, l3_path, level4_entries, l3_display)
                        level3_entries.append(l3_entry)

                # Write level 2 toc.json
                l2_toc = make_folder_toc_entry(l2_name, l2_path, level3_entries, l2_display)

                if not dry_run:
                    with open(l2_dir / "toc.json", "w") as f:
                        json.dump(l2_toc, f, indent=2)

                level2_entries.append(make_ref_entry(l2_name, l2_path, l2_display))

        # Level 1 entry (inline in level 0)
        l1_entry = make_folder_toc_entry(l1_name, l1_path, level2_entries, l1_display)
        level1_entries.append(l1_entry)

    # Build top-level By-ATC toc.json
    atc_toc = {
        "name": "By-ATC",
        "type": "folder",
        "path": base_path,
        "children": level1_entries,
        "_source": "ema-build",
    }

    if not dry_run:
        atc_toc_path = atc_dir / "toc.json"
        with open(atc_toc_path, "w") as f:
            json.dump(atc_toc, f, indent=2)
        print(f"  Written: {atc_toc_path.relative_to(output_dir.parent)}")

    return atc_toc


def create_metadata(
    products: dict[str, tuple[Medicine, list[Document]]],
    doc_entries: int
):
    """Create metadata.json for the accession."""
    metadata = {
        "accession": EMA_ACCESSION,
        "title": "RDCP-E26-EMA - EMA PARs",
        "description": "Public assessment reports and other documents for human medicines authorized by the European Medicines Agency.",
        "drug": "Multiple (EMA database)",
        "source": "https://www.ema.europa.eu/en/medicines",
        "license": {
            "name": "EMA Public",
            "url": "https://www.ema.europa.eu/en/about-us/legal-notice"
        },
        "created": datetime.now().isoformat(),
        "stats": {
            "products": len(products),
            "document_entries": doc_entries,
        }
    }

    metadata_path = EMA_ACCESSION_DIR / "metadata.json"
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"  Written: {metadata_path.relative_to(DOCUMENTS_DIR)}")


def build_ema(clean: bool = False, dry_run: bool = False):
    """Build the EMA accession structure."""
    print("=" * 60)
    print("EMA Accession Build")
    print("=" * 60)
    print(f"Accession: {EMA_ACCESSION}")
    print(f"Output: {EMA_ACCESSION_DIR}")
    print()

    # Clean if requested
    if clean and EMA_ACCESSION_DIR.exists():
        if dry_run:
            print(f"[DRY-RUN] Would remove: {EMA_ACCESSION_DIR}")
        else:
            print(f"Cleaning: {EMA_ACCESSION_DIR}")
            shutil.rmtree(EMA_ACCESSION_DIR)
        print()

    # Load data
    print("Loading EMA data...")
    medicines = load_medicines()
    if not medicines:
        return False
    print(f"  Loaded {len(medicines)} medicines")

    documents = load_documents()
    if not documents:
        return False
    print(f"  Loaded {len(documents)} documents")
    print()

    # Match documents to medicines
    print("Matching documents to medicines...")
    product_docs = match_documents_to_medicines(documents, medicines)
    print()

    # Filter qualifying products
    print("Filtering to Human + Authorised + has assessment-report...")
    qualifying = filter_qualifying_products(medicines, product_docs)
    print(f"  Qualifying products: {len(qualifying)}")
    print()

    # Create directory structure
    if not dry_run:
        EMA_ACCESSION_DIR.mkdir(parents=True, exist_ok=True)
        (EMA_ACCESSION_DIR / "files").mkdir(exist_ok=True)
        (EMA_ACCESSION_DIR / "By-ATC").mkdir(exist_ok=True)

    # Build files/ TOC structure with three-level grouping
    print("Building files/ TOC with grouped structure...")
    files_toc, total_doc_entries = build_grouped_files_toc(
        qualifying, EMA_ACCESSION_DIR, dry_run
    )

    print()

    # Build By-ATC/ TOC structure with grouped toc.json files
    print("Building By-ATC/ TOC with grouped structure...")
    atc_toc = build_grouped_atc_toc(qualifying, EMA_ACCESSION_DIR, dry_run)

    print()

    # Create metadata
    if not dry_run:
        create_metadata(qualifying, total_doc_entries)

    # Print summary
    print()
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"Products: {len(qualifying)}")
    print(f"Document entries: {total_doc_entries}")

    return True


def main():
    parser = argparse.ArgumentParser(
        description="Build EMA accession structure",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Remove and rebuild the accession directory"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be created without making changes"
    )

    args = parser.parse_args()

    success = build_ema(clean=args.clean, dry_run=args.dry_run)
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
