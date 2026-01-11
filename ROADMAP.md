# CTD Document Archive - Development Roadmap

## Overview
A public archive of regulatory documents for drug trials (ALLN-177/Reloxaliase, ALLN-346). Goal: make clinical trial data navigable and understandable for researchers, patients, and AI agents.

---

## Phase 1: Infrastructure & GitHub Setup
**Goal: Get code on GitHub, set up proper dev environment**

- [ ] Initialize git repo (code only, .gitignore for /documents)
- [ ] Create GitHub repo
- [ ] Set up basic project structure:
  ```
  /
  ├── src/              # Svelte app
  ├── scripts/          # Python scripts (generate_toc.py, etc.)
  ├── public/           # Static assets
  ├── documents/        # .gitignored - data lives here
  └── README.md
  ```
- [ ] Add README with setup instructions
- [ ] Define metadata format (data contract for all phases):
  ```
  documents/ALLN-346/Clinical-Studies/metadata.json
  {
    "CSR.pdf": {
      "title": "Clinical Study Report",
      "summary": "Phase 1 single ascending dose safety study...",
      "tags": ["csr", "phase-1"]
    }
  }
  ```
  - One `metadata.json` per directory
  - Scripts and UI both read from this format

---

## Phase 2: HTTPS & Production Setup
**Goal: Secure site with Let's Encrypt**

- [ ] Set up Nginx as reverse proxy
- [ ] Install certbot
- [ ] Configure SSL certificate for domain
- [ ] Auto-renewal cron job
- [ ] Redirect HTTP → HTTPS

---

## Phase 3: Svelte + Vite + shadcn Rebuild
**Goal: Modern, pretty frontend with shareable URLs**

- [ ] Initialize Vite + Svelte project
- [ ] Add shadcn-svelte components
- [ ] Implement layout from sketch:
  - Header with welcome message + contribute CTA
  - Left sidebar with TOC tree
  - Main viewer area
  - Mobile: hamburger → file selector
- [ ] Style with Tailwind (comes with shadcn)
- [ ] Dark mode support
- [ ] URL state & deep linking (bake in from the start):
  - URL structure: `/#/drug/study/file?page=5`
  - Browser back/forward navigation
  - Copy link button

---

## Phase 4: Enhanced File Support
**Goal: Render more file types inline**

| Format | Viewer |
|--------|--------|
| PDF | iframe / PDF.js |
| PNG/JPG/GIF | `<img>` tag |
| MP3/WAV | `<audio>` player |
| MP4/WebM | `<video>` player |
| XLS/XLSX | Parse with SheetJS, render as table |
| CSV | Parse and render as table |
| TXT/RTF | Text viewer |
| DOCX | Render with mammoth.js or download |
| Others | Download link |

---

## Phase 5: Agent-Friendly TOC
**Goal: Make data accessible to AI agents**

*Reads from metadata.json files defined in Phase 1*

- [ ] Update `generate_toc.py` to include descriptions from metadata
- [ ] Generate `toc.json` with full URLs and descriptions
- [ ] Generate `toc.md` (markdown) for LLM consumption
- [ ] Structure:
  ```json
  {
    "url": "https://example.com/documents/ALLN-346/Clinical-Studies/101-SAD/CSR.pdf",
    "title": "Study 101-SAD Clinical Study Report",
    "description": "Phase 1 single ascending dose safety study...",
    "type": "pdf",
    "study": "101-SAD",
    "drug": "ALLN-346"
  }
  ```

---

## Phase 6: Inline Context & Descriptions
**Goal: Help visitors understand what they're looking at**

*Uses metadata format defined in Phase 1*

- [ ] Per-file context displayed in two places:
  - **Sidebar**: One-sentence summary beneath each file name
  - **Viewer header**: Paragraph of context at top of viewer (fades/collapses on scroll)
- [ ] Landing view (when no file selected):
  - What is this archive?
  - What drugs are included?
  - How to navigate
  - How to contribute data
- [ ] Glossary of terms (CSR, TLF, ADaM, SDTM, etc.) - inline tooltips or expandable

---

## Phase 7: Curated Views (Optional)
**Goal: Allow flexible organization without duplicating files**

Two approaches (pick one):

**Option A: Symlinks** (simpler but less portable)
- [ ] Support symlinks in document scanning
- [ ] Create view directories with symlinks to source files
- [ ] Note: Won't work on Windows, can break during backups

**Option B: Metadata tags** (recommended)
- [ ] Add `tags` field to file metadata (e.g., `["phase-1", "csr"]`)
- [ ] UI filter/search by tags
- [ ] Curated views are just saved filter presets

---

## Technical Notes

### .gitignore
```
/documents/
*.sas7bdat
*.zip
node_modules/
.env
```

### Nginx config (rough)
```nginx
server {
    listen 443 ssl;
    server_name yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    root /home/ari/doc-archive;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /documents/ {
        alias /home/ari/doc-archive/documents/;
    }
}
```

---

## Priority Order

1. **GitHub setup + metadata format** (unblocks everything)
2. **HTTPS** (security baseline)
3. **Svelte rebuild + deep linking** (user experience)
4. **File format support** (usability)
5. **Agent TOC generation** (AI accessibility)
6. **Inline context** (understanding)
7. **Curated views** (optional, nice-to-have)
