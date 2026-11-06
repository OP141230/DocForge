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

### 9. Run the Application

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
npm test
```

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

## Document Types Supported

- General Report
- Academic Report
- Project Report
- Technical Documentation
- Business Report
- Article/Essay
- Resume

## Export Formats

- **DOCX**: Microsoft Word with full formatting
- **PDF**: Professional layout with styling
- **Markdown**: GitHub-flavored Markdown
- **HTML**: Standalone HTML document
- **Plain Text**: Clean text with structure

## Architecture

### Document IR (Intermediate Representation)

All document content uses a canonical JSON schema validated with Pydantic. This ensures consistency across:
- Generation
- Editing
- Persistence
- Export

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

### Export System

Exporters use a registry pattern for extensibility. Each format implements the `Exporter` interface, making it easy to add new formats.

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
│   │   ├── models/   # Pydantic models
│   │   ├── repositories/  # Data access
│   │   ├── providers/     # AI providers
│   │   ├── exporters/     # Export formats
│   │   └── tests/    # Test suite
│   └── requirements.txt
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
- **Phase 5** (Planned): Research, Citations & Factual Verification
- **Phase 6** (Planned): Vector Search & Semantic Retrieval
- **Phase 7** (Planned): Production scaling & Cloud deployment

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
- 🔜 **Phase 5**: Research, Citations & Factual Verification (Planned)

## Contributing

This project follows engineering best practices:
- Clean architecture with separation of concerns
- Type safety with TypeScript and Pydantic
- Comprehensive testing (automated + manual)
- Security-first design
- Responsive and accessible UI

## License

MIT License - see LICENSE file for details
