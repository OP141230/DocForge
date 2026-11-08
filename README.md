# DocForge

**Plan. Generate. Edit. Export.**

DocForge is an all-round documentation agent that helps you plan, generate, research, edit, verify, organize, and export documents in formats appropriate to your needs.

## Features

### Phase 1 (Complete ✅)
- 📝 **Conversational Planning**: Describe your document needs naturally
- 🤖 **AI-Powered Generation**: Generate structured outlines and content (Groq AI)
- ✏️ **Rich Editing**: Full-featured document editor with formatting
- 📚 **Version History**: Save and restore previous versions
- 📤 **Multi-Format Export**: Export to DOCX, PDF, Markdown, HTML, and plain text
- 💾 **Auto-Save**: Never lose your work
- 🎨 **Modern UI**: Clean, responsive, accessible interface

### Phase 2 (Complete ✅)
- 🔐 **User Authentication**: Secure registration and login with Argon2id hashing
- 👤 **Personal Workspace**: Each user has their own private documents and conversations
- 💬 **Conversation Management**: Create and manage document generation conversations
- 🗨️ **Chat Interface**: Beautiful chat-style interface for interacting with the AI
- 🔒 **Data Isolation**: Complete privacy - users can only see their own content
- 📱 **Responsive Design**: Works perfectly on desktop, tablet, and mobile
- 🔗 **Document-Conversation Links**: Associate documents with conversations for context

### Phase 3 (Complete ✅)
- 📋 **DocumentBrief System**: Structured document planning with guided wizard
- 🎯 **10 Document Types**: Technical guides, user manuals, API docs, proposals, reports, tutorials, whitepapers, case studies, policies, and standard documents
- 🧙 **6-Step Wizard**: Type selection, basic info, preferences, type-specific fields, outline generation, and review
- 📝 **AI-Powered Outlines**: Generate intelligent outlines based on your brief requirements
- ✏️ **Outline Editing**: Review, edit, add, and delete sections before approval
- ✅ **Approval Workflow**: Approve outlines before generating full documents
- 🗂️ **Brief Manager**: View, resume, and manage all your document briefs
- 🔗 **Brief-Document Linking**: Full traceability from planning to generated content

### Phase 4 (Complete ✅)
- 📂 **Knowledge Base**: Upload and manage reference documents
- 📄 **Multi-Format Support**: PDF, DOCX, TXT, Markdown, HTML, CSV extraction
- 🔍 **Full-Text Search**: FTS5-powered search across uploaded files
- 🧩 **Smart Chunking**: Automatic text chunking with overlap for better retrieval
- 🔗 **Source Attachments**: Link reference files to document briefs
- 🤖 **Source-Based Generation**: AI uses your uploaded documents as references
- 📝 **Source Citations**: Generated content references source files
- 🔐 **Secure Storage**: User-isolated file storage with deduplication
- 🎯 **RAG Implementation**: Retrieval-Augmented Generation with your own knowledge

### Phase 5 (Complete ✅)
- 🔬 **Research System**: 5 external providers (Wikipedia, arXiv, PubMed, Google Scholar, Web Search)
- 📚 **Research Sessions**: Create, configure, and manage research sessions
- ❓ **Question Planning**: Auto-generate research questions from briefs or add manually
- 📖 **Source Management**: Browse and select sources from providers and knowledge base
- 📝 **Evidence Collection**: Extract and manage evidence passages from sources
- 📎 **Citation Management**: 4 citation styles (APA, IEEE, MLA, Chicago) with auto-formatting
- 📋 **Reference Lists**: Generate formatted reference lists and in-text citations
- 🔄 **Style Switching**: Instantly reformat all citations to different styles
- ✅ **Factual Verification**: Extract claims and verify against research evidence
- 🎯 **Claim Review**: Flag claims for review, add notes, and recheck verification
- 🔒 **SSRF Protection**: URL validation and private IP blocking
- ⚡ **Rate Limiting**: Configurable per-user API rate limits

### Phase 6 (Complete ✅)
- 🤖 **AI Document Reviewer**: five review modes (quick, full, academic, technical, custom) over a whole document or a single section
- 🧾 **Deterministic Checks First**: repetition, heading order, filler phrasing and missing required sections are measured, not guessed
- 🎯 **Quote-Verified AI Findings**: every AI finding must quote text that really exists; invented quotes, unknown categories and bad severities are discarded
- 🏷️ **Honest Labelling**: each finding records whether it was checked automatically or suggested by AI
- 🧭 **Stable Anchors**: findings point at `section_id`/`block_id`, never at model-supplied offsets, so they survive edits and are marked stale when the text changes
- ✍️ **Reviewable Edits**: 25 operations (clarity, grammar, structure, tone, terminology…) proposed as diffs, applied only when you accept, with pre- and post-edit versions written in one transaction
- 🔒 **No Silent Rewrites**: whole-document rewrites are refused by design; every apply is a single reviewable change
- 📎 **Citation-Safe Editing**: citation markers are preserved, and affected citations and verified claims are queued for re-checking
- 📊 **Brief Compliance**: requirements from the DocumentBrief checked deterministically, with qualitative points clearly labelled as AI opinions
- 🕘 **Version History**: side-by-side comparison, provenance for each version, and undoable restores

### Phase 7 (Backend Complete ✅)
- 📐 **Document Templates**: 12 professional templates across 6 categories (academic, technical, business, documentation, project, general)
- 🎨 **Advanced Formatting**: Colors, font sizes, font families, strikethrough, background colors
- 🖼️ **Image Support**: Upload, store, optimize, and embed images in documents with captions and alignment
- 📄 **Page Layout**: Configure page size (A4, Letter, Legal), orientation, margins, headers/footers
- 🔄 **Page Breaks**: Insert page breaks for print formatting
- 📤 **Enhanced Exports**: All 5 exporters (PDF, DOCX, HTML, Markdown, Text) support Phase 7 features
- 📋 **Template System**: Pre-configured typography, heading styles, and color schemes
- 📊 **Export History**: Track all document exports with configuration and metadata
- 🎯 **Template Application**: Apply professional templates to existing documents
- 🔧 **Document IR v1.1.0**: Extended intermediate representation with backward compatibility


## Tech Stack

**Frontend**:
- React 18 + TypeScript
- Vite
- Tailwind CSS
- Tiptap Editor

**Backend**:
- Python 3.11+
- FastAPI
- Pydantic
- SQLite
- OpenAI API (optional, mock provider available)

## Prerequisites

- **Python**: 3.11 or higher
- **Node.js**: 18 or higher
- **npm**: 9 or higher

## Quick Start

### 1. Clone and Setup

```powershell
cd DocForge

# Copy environment template
Copy-Item .env.example .env
```

### 2. Configure AI Provider

**Option A: Groq (Free, Recommended)**
1. Get free API key: https://console.groq.com/keys
2. Edit `.env`:
   ```
   AI_PROVIDER=groq
   GROQ_API_KEY=your-key-here
   GROQ_MODEL=openai/gpt-oss-120b
   ```

**Option B: Mock (No API Key)**
- Edit `.env`: `AI_PROVIDER=mock`
- Generates placeholder content for testing

**Option C: OpenAI (Paid)**
- Edit `.env`: `AI_PROVIDER=openai`
- Add: `OPENAI_API_KEY=sk-your-key-here`

### 3. Backend Setup

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 4. Frontend Setup

```powershell
cd frontend
npm install
```

### 5. Initialize Database

```powershell
cd backend
.venv\Scripts\Activate.ps1
python migrate_db.py
```

### 6. Run Phase 3 Migration (DocumentBrief System)

```powershell
cd backend
.venv\Scripts\Activate.ps1
python migrate_phase3.py
```

### 7. Run Phase 4 Migration (Knowledge Base)

```powershell
python migrate_phase4.py
```

### 8. Install Phase 4 Dependencies

```powershell
pip install pypdf2 beautifulsoup4 lxml
```

### 9. Run Phase 5 Migration (Research, Citations & Verification)

```powershell
python migrate_phase5.py
```

### 9b. Phase 6 Tables (No Migration Needed)

Phase 6 adds `review_sessions`, `review_findings`, `edit_proposals`, `document_version_notes` and
`compliance_checks`. They are declared with `CREATE TABLE IF NOT EXISTS` in
`app/core/db_schema.sql`, which runs automatically when the backend connects, so existing
databases pick them up on the next start. No separate migration script is required.

### 10. Phase 7 - No Migration Needed

Phase 7 extends the Document IR in-memory and adds new API routes. No database schema changes are required.

### 11. Run the Application

**Using Startup Script (Easiest with Groq):**
```powershell
.\start_backend.ps1
```

**Or Manually:**

**Terminal 1 - Backend:**
```powershell
cd backend
.venv\Scripts\Activate.ps1

# Set environment variables (if using Groq)
$env:AI_PROVIDER = "groq"
$env:GROQ_API_KEY = "your-key-here"
$env:GROQ_MODEL = "openai/gpt-oss-120b"

python -m uvicorn main:app --reload
.venv\Scripts\Activate.ps1
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

**Terminal 2 - Frontend:**
```powershell
cd frontend
npm run dev
```

Open your browser to: **http://localhost:5173**

## Testing

### Backend Tests
```powershell
cd backend
.venv\Scripts\Activate.ps1
pytest app/tests/ -v
```

### Frontend Tests
```powershell
cd frontend
npm test          # watch mode
npx vitest run    # single run (CI)
```

Phase 6 component tests live next to the components they cover
(`src/components/review/*.test.tsx`). They run in a jsdom environment configured by
`vitest.config.ts`.

## Building for Production

```powershell
cd frontend
npm run build
# Output in frontend/dist/
```

## API Documentation

Once the backend is running, visit:
- Interactive API docs: http://localhost:8000/docs
- Alternative docs: http://localhost:8000/redoc

### Phase 6 endpoints (all require an authenticated session and document ownership)

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/api/documents/{id}/reviews` | Run a review (mode, scope, categories, `use_ai`) |
| GET | `/api/documents/{id}/reviews/latest` | Latest report for a document |
| GET | `/api/reviews/{review_id}` | One report, filterable by category/severity/status |
| PATCH | `/api/findings/{finding_id}` | Accept, reject, ignore or resolve a finding |
| POST | `/api/documents/{id}/edit-proposals` | Propose an edit for a section or block |
| POST | `/api/edit-proposals/{id}/apply` | Apply an accepted edit (409 if the text changed) |
| POST | `/api/edit-proposals/{id}/reject` | Discard a proposal |
| POST | `/api/documents/{id}/compliance` | Check the document against its brief |
| GET | `/api/documents/{id}/compliance` | Latest compliance report |
| GET | `/api/documents/{id}/version-history` | Version list with provenance |
| GET | `/api/documents/{id}/version-compare` | Structured diff between two versions |
| POST | `/api/documents/{id}/version-restore/{n}` | Restore a version after snapshotting the current text |

### Phase 7 endpoints (all require authentication and document ownership)

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/templates/` | List all document templates (optional category filter) |
| GET | `/api/templates/categories` | List all template categories |
| GET | `/api/templates/{template_id}` | Get specific template details |
| POST | `/api/images/upload` | Upload image file (multipart/form-data) |
| POST | `/api/images/upload-base64` | Upload base64-encoded image |
| GET | `/api/images/{image_id}` | Retrieve uploaded image |
| DELETE | `/api/images/{image_id}` | Delete uploaded image |
| POST | `/api/documents/{id}/apply-template` | Apply template to document (query param: template_id) |
| GET | `/api/documents/{id}/export-history` | Get export history for document |
| GET | `/api/export-formats` | List supported export formats with capabilities |

## Document Types Supported

- General Report
- Academic Report
- Project Report
- Technical Documentation
- Business Report
- Article/Essay
- Resume

## Export Formats (Phase 7 Enhanced)

All export formats now support Phase 7 advanced features:

- **PDF**: Professional layout with images, page breaks, custom margins, colors, and fonts
- **DOCX**: Microsoft Word with full formatting, images, page layout, and advanced text styling
- **HTML**: Standalone HTML with inline styles, images in figures, and print media support
- **Markdown**: GitHub-flavored Markdown with images, strikethrough, and HTML formatting
- **Plain Text**: Clean text with structure (basic formatting only)

## Architecture

### Document IR (Intermediate Representation)

All document content uses a canonical JSON schema validated with Pydantic. This ensures consistency across:
- Generation
- Editing
- Persistence
- Export

**Current Version**: v1.1.0 (Phase 7)

**Phase 7 Enhancements**:
- **Image blocks**: url, alt_text, caption, width, height, alignment
- **PageBreak blocks**: Simple page break markers
- **Advanced inline formatting**: colors, font_size, font_family, strikethrough, background_color
- **Page layout**: page_size, orientation, margins, headers/footers, page_numbers
- **Template support**: template_id reference in metadata

See `backend/app/models/document_ir.py` for the complete schema.

### AI Provider Abstraction

DocForge supports multiple AI providers through a common interface:

#### 🆓 Groq (Recommended - Free!)
- **Cost**: Completely free
- **Quality**: High (Llama 3.3 70B)
- **Speed**: Very fast (2-5 seconds)
- **Setup**: Get free API key from https://console.groq.com/keys

See [GROQ_SETUP.md](GROQ_SETUP.md) for detailed setup instructions.

#### 💰 OpenAI (Paid)
- **Cost**: ~$0.01-0.03 per document
- **Quality**: Highest (GPT-4)
- **Setup**: Requires credit card

#### 🧪 Mock Provider (Testing Only)
- **Cost**: Free
- **Quality**: Placeholder text only
- **Speed**: Instant
- **Setup**: No API key needed (default for development)

Configure via `AI_PROVIDER` in `.env`.

### Export System (Phase 7 Enhanced)

Exporters use a registry pattern for extensibility. Each format implements the `Exporter` interface, making it easy to add new formats.

**Phase 7 Updates**:
- All exporters support Image blocks with captions and alignment
- Page breaks for print formatting
- Page layout configuration (size, orientation, margins)
- Advanced inline formatting (colors, fonts, strikethrough)
- Export history tracking with metadata
- Format capability reporting

## Project Structure

```
DocForge/
├── frontend/          # React + TypeScript + Vite
│   ├── src/
│   │   ├── api/      # API client
│   │   ├── components/  # UI components
│   │   ├── pages/    # Page components
│   │   ├── hooks/    # Custom hooks
│   │   └── types/    # TypeScript types
│   └── package.json
├── backend/           # Python + FastAPI
│   ├── app/
│   │   ├── api/      # API routes
│   │   │   ├── templates.py      # Phase 7: Template API
│   │   │   └── images.py         # Phase 7: Image upload API
│   │   ├── models/   # Pydantic models
│   │   │   ├── template.py       # Phase 7: Template models
│   │   │   └── export_config.py  # Phase 7: Export configuration
│   │   ├── services/              # Business logic
│   │   │   ├── template_service.py  # Phase 7: 12 built-in templates
│   │   │   ├── image_service.py     # Phase 7: Image processing
│   │   │   └── export_service.py    # Phase 7: Export history
│   │   ├── repositories/  # Data access
│   │   ├── providers/     # AI providers
│   │   ├── exporters/     # Export formats (Phase 7 enhanced)
│   │   └── tests/    # Test suite
│   ├── uploads/
│   │   └── images/   # Phase 7: Uploaded images
│   ├── data/
│   │   └── export_history/  # Phase 7: Export history JSON
│   └── requirements.txt
├── PHASE_7_TESTING_GUIDE.md  # Phase 7 testing instructions
└── README.md
```

## Development Workflow

1. Make changes to backend or frontend code
2. Both have hot-reload enabled
3. Run tests before committing
4. Keep `.env` file out of version control

## Known Limitations (Phase 1)

- Single-user only (no authentication)
- No real-time collaboration
- No web research or RAG capabilities
- SQLite database (suitable for local/small-scale use)
- No Docker configuration yet

## Troubleshooting

### Backend won't start
- Ensure Python 3.11+ is installed: `python --version`
- Ensure virtual environment is activated
- Check `.env` file exists (copy from `.env.example`)

### Frontend won't start
- Ensure Node.js 18+ is installed: `node --version`
- Delete `node_modules` and run `npm install` again
- Check that backend is running on port 8000

### AI Generation not working
- Check `AI_PROVIDER` in `.env`
- For mock provider: should work without any API key
- For OpenAI provider: verify `OPENAI_API_KEY` is set correctly

## Contributing

See `.kiro/steering/docforge-engineering-guide.md` for development guidelines and architecture principles.

## License

[Your license here]

## Phase Roadmap

- **Phase 1**: Core platform and generation ✅
- **Phase 2**: Authentication and personal workspace ✅
- **Phase 3**: DocumentBrief planning system ✅
- **Phase 4**: Knowledge Base & Source Ingestion ✅
- **Phase 5**: Research, Citations & Factual Verification ✅
- **Phase 6**: AI Reviewer & Advanced Editing ✅
- **Phase 7**: Advanced Formatting & Multi-format Exports (Backend ✅, Frontend ⏳)
- **Phase 8** (Planned): Advanced Analytics & Insights
- **Phase 9** (Planned): Production scaling & Cloud deployment

---

Built with ❤️ using modern web technologies


## Phase 2 Features Guide

### Authentication
1. **Register**: Create an account at `/register`
   - Secure password requirements enforced
   - Auto-login after registration
2. **Login**: Access at `/login`
   - Session-based authentication
   - HTTP-only cookies for security

### Conversations
1. **Create Conversation**: Click "New Conversation" in dashboard
2. **Send Messages**: Type and press Enter to chat with AI
3. **Edit Title**: Click on conversation title to rename
4. **View History**: All messages saved and displayed chronologically

### Documents
1. **Generate from Prompt**: Use "New Document" for quick generation
2. **Generate from Conversation**: Create documents within conversations
3. **Export**: Choose from DOCX, PDF, Markdown, HTML, or Text
4. **View All**: Dashboard shows all your documents

### Data Privacy
- All your data is private and isolated
- Other users cannot see your conversations or documents
- Secure session management with automatic expiry

## Testing

### Automated Tests
```powershell
# Test authentication
python test_auth.py

# Test data isolation
python test_isolation.py

# Test conversations
python test_conversations.py

# Complete integration test
python test_phase2_complete.py
```

### Manual Testing
See `TESTING_GUIDE.md` for complete manual testing checklist.

## Documentation

- **PHASE2_COMPLETE.md** - Complete Phase 2 documentation
- **PHASE3_COMPLETE.md** - Complete Phase 3 documentation (DocumentBrief system)
- **TESTING_GUIDE.md** - Manual testing instructions
- **PHASE2C_COMPLETE.md** - Data isolation documentation

## API Endpoints

### Authentication (Public)
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login
- `POST /api/auth/logout` - Logout
- `GET /api/auth/me` - Get current user

### Conversations (Protected)
- `POST /api/conversations` - Create conversation
- `GET /api/conversations` - List conversations
- `GET /api/conversations/{id}` - Get conversation with messages
- `PUT /api/conversations/{id}` - Update conversation title
- `DELETE /api/conversations/{id}` - Delete conversation
- `POST /api/conversations/{id}/messages` - Add message
- `GET /api/conversations/{id}/messages` - List messages

### Document Briefs (Protected)
- `POST /api/document-briefs` - Create document brief
- `GET /api/document-briefs` - List briefs (paginated)
- `GET /api/document-briefs/{id}` - Get brief by ID
- `PATCH /api/document-briefs/{id}` - Update brief
- `DELETE /api/document-briefs/{id}` - Delete brief
- `POST /api/document-briefs/{id}/generate-outline` - Generate outline
- `PATCH /api/document-briefs/{id}/outline` - Update outline
- `POST /api/document-briefs/{id}/approve-outline` - Approve outline
- `POST /api/document-briefs/{id}/generate-document` - Generate document from brief
- `PATCH /api/document-briefs/{id}/conversation` - Link brief to conversation

### Research & Citations (Protected - Phase 5)
- `GET /api/research/providers` - Check provider availability
- `POST /api/research/sessions` - Create research session
- `GET /api/research/sessions` - List sessions
- `GET /api/research/sessions/{id}` - Get session detail
- `PATCH /api/research/sessions/{id}` - Update session
- `DELETE /api/research/sessions/{id}` - Delete session
- `POST /api/research/sessions/{id}/plan` - Auto-generate questions
- `PUT /api/research/sessions/{id}/questions` - Update questions
- `POST /api/research/sessions/{id}/run` - Run research (async)
- `GET /api/research/sessions/{id}/sources` - List sources
- `GET /api/research/sessions/{id}/evidence` - List evidence
- `GET /api/documents/{id}/citations` - Get citations & references
- `PATCH /api/documents/{id}/citation-style` - Change citation style
- `POST /api/documents/{id}/verify` - Verify document claims
- `GET /api/documents/{id}/verifications` - Get verifications

### Documents (Protected)
- `POST /api/documents` - Create document
- `GET /api/documents` - List documents
- `GET /api/documents/{id}` - Get document
- `PUT /api/documents/{id}` - Update document
- `DELETE /api/documents/{id}` - Delete document
- `POST /api/documents/{id}/export` - Export document

### Generation (Protected)
- `POST /api/generate/outline` - Generate outline
- `POST /api/generate/content` - Generate content
- `POST /api/generate/section` - Generate section

## Database Schema

- **users** - User accounts with password hashes
- **sessions** - Session tokens for authentication
- **conversations** - User conversations
- **messages** - Messages within conversations (user + assistant)
- **documents** - Generated documents with user and conversation associations
- **document_versions** - Version history for documents
- **document_briefs** (Phase 3) - Document planning briefs with outlines and approval workflow
- **knowledge_files** (Phase 4) - Uploaded reference documents
- **content_chunks** (Phase 4) - Text chunks for semantic search
- **research_sessions** (Phase 5) - Research session metadata
- **research_questions** (Phase 5) - Questions guiding research
- **research_sources** (Phase 5) - Sources from providers and knowledge base
- **research_evidence** (Phase 5) - Extracted evidence passages
- **citations** (Phase 5) - In-text citations with formatting
- **claim_verifications** (Phase 5) - Factual claim verification results
- **claim_verification_evidence** (Phase 5) - Evidence-to-claim links
- **review_sessions** (Phase 6) - Document review sessions
- **review_findings** (Phase 6) - Review findings with anchors
- **edit_proposals** (Phase 6) - Proposed edits with diffs
- **document_version_notes** (Phase 6) - Version provenance metadata
- **compliance_checks** (Phase 6) - Brief compliance check results

**Phase 7 Notes**: No new database tables. Templates stored in-memory, images stored in filesystem (`uploads/images/`), export history stored as JSON files (`data/export_history/`).

## Security Features

- ✅ Argon2id password hashing (OWASP recommended)
- ✅ HTTP-only session cookies (XSS protection)
- ✅ Session expiry (30 days)
- ✅ User-scoped database queries
- ✅ 404 responses for unauthorized access (prevents enumeration)
- ✅ CORS configuration with credentials
- ✅ Password strength validation

## Project Status

- ✅ **Phase 1**: Document generation and export (Complete)
- ✅ **Phase 2**: Authentication and personal workspace (Complete)
- ✅ **Phase 3**: DocumentBrief planning system (Complete)
- ✅ **Phase 4**: Knowledge Base & Source Ingestion (Complete)
- ✅ **Phase 5**: Research, Citations & Factual Verification (Complete)
- ✅ **Phase 6**: AI Reviewer & Advanced Editing (Complete)
- ✅ **Phase 7**: Advanced Formatting & Multi-format Exports (Backend Complete, Frontend Pending)

## Contributing

This project follows engineering best practices:
- Clean architecture with separation of concerns
- Type safety with TypeScript and Pydantic
- Comprehensive testing (automated + manual)
- Security-first design
- Responsive and accessible UI

## License

MIT License - see LICENSE file for details
