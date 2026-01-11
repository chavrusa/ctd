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
- [x] Add README with setup instructions
- [x] Define metadata format (data contract for all phases): see [METADATA.md](METADATA.md)
  - One `metadata.json` per directory
  - `_folder` key for folder-level metadata (title, summary, drug)
  - Filename keys for file-level metadata (title, summary, tags)
  - `drug` field inherits down the tree

---

## Phase 2: HTTPS & Production Setup
**Goal: Secure site with Let's Encrypt**

- [x] Set up Nginx as reverse proxy
- [x] Install certbot
- [x] Configure SSL certificate for domain
- [x] Auto-renewal cron job (certbot sets this up automatically)
- [x] Redirect HTTP → HTTPS

---

## Phase 3: Svelte + Vite + shadcn Rebuild
**Goal: Modern, pretty frontend with shareable URLs**

- [x] Initialize Vite + Svelte project
- [x] Add shadcn-svelte components
- [x] Implement layout:
  - Header with title + dark mode toggle
  - Left sidebar with TOC tree
  - Main viewer area
  - Mobile: hamburger → file selector
- [x] Style with Tailwind
- [x] Dark mode support
- [x] URL state & deep linking:
  - URL hash for document path
  - Browser back/forward navigation

---

## Phase 4: Enhanced File Support
**Goal: Render more file types inline**

- [x] PDF → iframe
- [x] PNG/JPG/GIF → `<img>` tag
- [x] MP3/WAV → `<audio>` player
- [x] MP4/WebM → `<video>` player
- [x] XLS/XLSX → SheetJS table viewer
- [x] CSV/TXT → text viewer
- [x] DOCX → mammoth.js HTML rendering
- [x] Others → download link

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
