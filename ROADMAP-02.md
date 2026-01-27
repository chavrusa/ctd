# CTD Archive Roadmap v2

Development workstreams for public release and beyond.

---

## 1. Repo Hygiene & Landing Page

**Repo basics:**
- [ ] `LICENSE` file (MIT for code)
- [ ] `CONTRIBUTING.md` - how to submit metadata improvements, report issues
- [ ] `CODE_OF_CONDUCT.md`
- [ ] Favicon

**Contact & feedback:**
- [ ] "Give feedback" widget in UI
- [ ] Contact info for document contributions
- [ ] Issue templates for bug reports, feature requests, document requests
- [ ] Donation/sponsorship page or link

**Landing page improvements:**
- [ ] Copyediting and "start here" highlights

**Research features:**
- [ ] Citation export (BibTeX, RIS, clipboard-friendly)
- [ ] Social-share thumbnails / media cards / support

---

## 2. Agent & External Accessibility

**Static URLs:**
- [x] Escape filenames/paths with URL special characters (`scripts/create_url_symlinks.py`)
- [x] Ensure every document has a permanent, predictable URL
- [x] URL scheme: `/documents/RDCP-26-0001/files/Clinical-Studies/101-SAD/CSR.pdf`

**Hierarchical index files:**
- [x] `index.md` at each folder level (not one giant 4500-line file)
- [x] Machine-readable `index.json` per folder
- [x] Root-level `index.json` with accession listing
- [ ] Root `manifest.json` with checksums for caching/validation

**LLM web-tool accessibility:**
- [x] Visually-hidden div in HTML with site description and index pointers (survives text extraction)
- [x] MIME type `text/markdown` for `.md` files (nginx config)
- [x] Full URLs in link text (relative paths get mangled by extractors)

**MCP server:**
- [ ] `list_accessions()` - returns all accessions with metadata
- [ ] `list_documents(accession, path?)` - browse hierarchy
- [ ] `get_document_metadata(path)` - title, date, tags, CTD module
- [ ] `get_document_content(path)` - returns PDF or extracted text
- [ ] `search(query, accession?)` - fulltext search

**Other agent features:**
- [ ] OpenAPI spec for any REST endpoints
- [x] ~`llms.txt` or `ai.txt` at root~ (skipped; no standard exists, visually-hidden div approach works)
- [ ] Structured sitemap with document metadata

**Archival & redundancy:**
- [ ] Internet Archive backup (Wayback Machine submission)
- [ ] Archive.org collection for bulk access

---

## 3. Mobile Overhaul

**Responsiveness:**
- [ ] Collapsible sidebar (drawer pattern)
- [ ] Touch-friendly tree navigation
- [ ] Address reports that scrolling is slow and janky

**PDF viewing:**
- [ ] pdf.js with mobile-optimized controls
- [ ] Page thumbnails strip
- [ ] Pinch-to-zoom
- [ ] "Reader mode" showing extracted text instead of PDF
- [ ] Download button prominent on mobile

---

## 4. Fulltext & Search

**PDF processing pipeline:**
```
PDF → pdftotext/pymupdf → raw text
    → LLM for cleanup/structure → markdown
    → Extract dates, study IDs, drug names → metadata enrichment
    → Embed for vector search
```

**Storage:**
- [ ] `CSR.pdf` alongside `CSR.md` (or in separate `_text/` tree)
- [ ] Frontmatter in markdown with extracted metadata

**Search features:**
- [ ] Fulltext search across all documents
- [ ] Filter by accession, date range, document type, CTD module
- [ ] Highlight matches in PDF viewer
- [ ] "Similar documents" via embeddings

**Automated annotations:**
- [ ] Date extraction (submission dates, study dates)
- [ ] Study ID extraction (NCT numbers, protocol numbers)
- [ ] Document cross-reference extraction
- [ ] Document revision version extraction (for past and future revisions)

---

## 5. FDA Complete Response Letters

**Data source:**
- https://open.fda.gov/apis/transparency/completeresponseletters/
- ~400 letters, structured data

**Warehousing strategy:**
- [ ] For now, one-time sync job
- [ ] Store locally in `documents/RDCP-E26-FDACRL/` for unordered accession key for external datasets
- [ ] Track provenance (API version, fetch date)
- [ ] Diff detection for updates

**Integration:**
- [ ] Link CRLs to related drug programs if we have them
- [ ] New accession scheme? `FDA-CRL-YYYY-NNNN`?

**Considerations:**
- Terms of use for FDA data
- Attribution requirements

**Other external sources:**
- [ ] Integration with ClinicalTrials.gov (beginning with existing NCTs)

---

## 6. Analytics

**Usage analytics:**
- [ ] Page views, document downloads
- [ ] Search queries (what are people looking for?)
- [ ] Popular documents, underused sections

**Privacy-respecting options:**
- Plausible, Fathom, or Umami (self-hosted)
- No PII, aggregate only
- Clear privacy policy

---

## 7. Additional Views

Generated views (symlink-based) providing alternative organizational structures.

**By-Trial view:**
- [ ] Directory for each clinical trial referenced in the archive
- [ ] Extract trial identifiers (NCT numbers, protocol numbers, study codes)
- [ ] Aggregate all documents mentioning each trial
- [ ] Link to ClinicalTrials.gov where applicable

**Other potential views:**
- [ ] By-Document-Type - all CSRs together, all protocols together, etc.

---

## Priority Suggestions

**For initial public release (v1):**
- Group 1: LICENSE, CONTRIBUTING, accession-license documents clearly annotated
- Group 1: feedback link, citation export
- Group 1: Landing page copyediting, placeholder favicon
- Group 2: Hierarchical index.md files, stable URLs, llm.txt for context
- Group 3: Basic mobile responsiveness

**Near-term (v1.x):**
- Group 1: Project-wide brand identity, logo/favicon
- Group 2: Internet Archive schema set up / registered
- Group 4: Fulltext extraction and basic search
- Group 7: By-Trial view
- Group 6: Basic analytics

**Medium-term (v2):**
- Group 5: FDA Complete Response Letters
- Group 2: MCP server
- Group 3: Improved mobile support
- Group 3: CSV/TSV support, xlsx support, pptx-to-pdf(-to-md) support
