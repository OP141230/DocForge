# DocForge

**Plan. Generate. Edit. Export.**

DocForge is an all-round documentation agent that helps you plan, generate, research, edit, verify, organize, and export documents in formats appropriate to your needs.

## Features (Phase 1)

- 📝 **Conversational Planning**: Describe your document needs naturally
- 🤖 **AI-Powered Generation**: Generate structured outlines and content
- ✏️ **Rich Editing**: Full-featured document editor with formatting, tables, code blocks
- 📚 **Version History**: Save and restore previous versions
- 📤 **Multi-Format Export**: Export to DOCX, PDF, Markdown, HTML, and plain text
- 💾 **Auto-Save**: Never lose your work
- 🎨 **Modern UI**: Clean, responsive, accessible interface

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

### 5. Run the Application

**Using Startup Script (Easiest with Groq):**
```powershell
.\start_backend.ps1
```

**Or Manually:**

**Terminal 1 - Backend:**
```powershell
# Set environment variables (if using Groq)
$env:AI_PROVIDER = "groq"
$env:GROQ_API_KEY = "your-key-here"
$env:GROQ_MODEL = "openai/gpt-oss-120b"

cd backend
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

- **Phase 1** (Current): Core platform and generation ✅
- **Phase 2** (Planned): RAG, web research, advanced verification
- **Phase 3** (Planned): Collaboration, plugins, advanced features

---

Built with ❤️ using modern web technologies
