# InsightHub

Enterprise Research Knowledge Assistant for multi-tenant market research repositories.

## What Is Implemented

The current build includes:
- FastAPI backend with SQLite persistence and tenant-scoped authentication
- Streamlit frontend with project selection, uploads, chat, exports, and dashboard views
- Ingestion pipeline for PDF, Word, PowerPoint, Excel, CSV, text, and audio assets
- Knowledge chunking, embeddings, ChromaDB indexing, and local fallback retrieval
- LangGraph-style intelligent RAG workflow with query rewriting, reranking, and grounding verification
- Chat export, summary export, and context export

## Architecture Overview

InsightHub follows a layered architecture with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                    Streamlit Frontend                       │
│  (app.py - UI, Navigation, API Communication)              │
├─────────────────────────────────────────────────────────────┤
│                    FastAPI Backend                         │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐ │
│  │ API Routes   │  │ Core         │  │ Workflows       │ │
│  │ (auth,       │  │ (config,     │  │ (RAG pipeline)  │ │
│  │  clients,    │  │  security,   │  └─────────────────┘ │
│  │  projects,   │  │  deps)       │                        │
│  │  dashboard)  │  └──────────────┘                        │
├─────────────────────────────────────────────────────────────┤
│                    Services                                │
│  (knowledge_base.py - Business Logic)                      │
├─────────────────────────────────────────────────────────────┤
│                    Data Layer                              │
│  ┌──────────────┐    ┌──────────────┐                     │
│  │ SQLite       │    │ ChromaDB     │                     │
│  │ (metadata,   │    │ (vectors,    │                     │
│  │  users,      │    │  chunks)     │                     │
│  │  projects)   │    │              │                     │
│  └──────────────┘    └──────────────┘                     │
└─────────────────────────────────────────────────────────────┘
```

### Intelligent RAG Pipeline

The core workflow orchestrated via LangGraph consists of 5 stages:

1. **Query Understanding**: Rewrites user queries to fix spelling, expand abbreviations
2. **Semantic Retrieval**: Fetches relevant chunks from project-scoped ChromaDB
3. **Context Reranking**: Re-ranks retrieved chunks for better relevance
4. **Grounded Response Generation**: Generates answers using LLM + retrieved context
5. **Grounding Verification**: Validates responses against evidence to prevent hallucinations

### Multi-Tenant Isolation

Each client has:
- Independent SQLite records (clients → projects → documents)
- Isolated ChromaDB collections (`{client_slug}__{project_slug}`)
- Scoped file storage under `data/uploads/{client_slug}/{project_slug}/`
- All queries include `client_id` and `project_id` filters

## Quick Setup

This project is designed to be ready in under 5 minutes on a machine that already has Python and pip installed, and where package/model downloads are either cached or fast on the local network.

### 1. Installation Steps

Clone or open the repository, then install the Python dependencies:

```bash
pip install -r requirements.txt
```

### 2. Dependency Setup

The main runtime dependencies are FastAPI, Streamlit, ChromaDB, sentence-transformers, pandas, Plotly, and the document parsers listed in [requirements.txt](requirements.txt).

If you want the optional audio transcription path, install `openai-whisper` separately.

### 3. Environment Configuration

Create a local `.env` file in the repository root using [`.env.example`](.env.example) as the template.

Minimum required values:

```bash
APP_NAME=InsightHub
APP_ENV=development
BACKEND_HOST=127.0.0.1
BACKEND_PORT=8000
FRONTEND_PORT=8501
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.1-70b-versatile
EMBEDDING_MODEL=BAAI/bge-m3
CHROMA_PATH=data/chroma
UPLOAD_PATH=data/uploads
SQLITE_PATH=data/insighthub.db
```

### 4. Vector Database Setup

No separate vector database server is required. ChromaDB runs locally in embedded mode and stores data under `data/chroma`.

The first time you ingest content, the app may download the `BAAI/bge-m3` embedding model unless it is already cached locally.

### 5. LLM Configuration

Set `GROQ_API_KEY` in `.env` to enable Groq-powered query rewriting, classification, answer generation, and grounding checks.

If `GROQ_API_KEY` is omitted, the app still runs, but it falls back to local heuristic behavior.

### 6. Initialize and Run

Run these commands from the repository root.

Initialize the database:

```bash
python scripts/initialize_database.py
```

Start the backend:

```bash
python backend/run_backend.py
```

Start the frontend:

```bash
python -m streamlit run frontend/app.py --server.port 8501
```

Open `http://127.0.0.1:8501` in your browser.

To use your own data, create a project from the sidebar first, then upload files into that project and ask questions in Chat.

## Non-Conda Setup

If you do not want to use Conda, use standard Python and a virtual environment:

```bash
python -m venv .venv
```

Activate it in `cmd`:

```bash
.venv\Scripts\activate
```

Activate it in PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Then install dependencies and continue with the same `.env` setup and run commands shown above:

```bash
pip install -r requirements.txt
python scripts/initialize_database.py
python backend/run_backend.py
python -m streamlit run frontend/app.py --server.port 8501
```

## Local Login

The initial database seed creates one local admin account for getting started:

- `local_admin` / `Password123!`

## Verification

Run the local verification script after setup:

```bash
python scripts/verify_install.py
```

## Features

### Document Support

| Format | Extension | Processing |
|--------|-----------|------------|
| PDF | .pdf | Text extraction via pdfplumber |
| Word | .docx | Text extraction via python-docx |
| PowerPoint | .pptx | Slide text extraction |
| Excel | .xlsx, .xls | Sheet data extraction |
| CSV | .csv | Columnar data extraction |
| Text | .txt, .md, .json | Direct text reading |
| Audio | .wav, .mp3, .m4a, .ogg, .flac, .aac | Whisper transcription |

### Document Categories

Documents are automatically classified into:
- Survey Dataset
- Research Report
- Final Report
- Presentation Deck
- Interview Transcript
- Focus Group Discussion
- Call Summary
- Audio Recording
- Other Research Documents

### Export Types

- **Chat Export**: Conversation history with sources
- **Summary Export**: Project statistics and metadata
- **Context Export**: All context used for responses

## Notes

- The application is designed to run locally without Docker. Docker is only needed for production deployments.
- ChromaDB is used as an embedded vector store. Qdrant can be used for production and large-scale data.
- SQLite stores application metadata and chat/export records.
- The sample login credentials only work with the seeded local database.

## Project Structure

```
InsightHub/
├── backend/
│   ├── app/
│   │   ├── api/routes/     # REST API endpoints
│   │   ├── core/           # Configuration, security, dependencies
│   │   ├── db/             # Database schema and connection
│   │   ├── models/         # Data models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── services/       # Business logic
│   │   └── workflows/      # RAG pipeline orchestration
│   └── run_backend.py      # Backend entry point
├── frontend/
│   └── app.py              # Streamlit UI
├── scripts/
│   ├── initialize_database.py
│   └── verify_install.py
├── data/
│   ├── insighthub.db       # SQLite database
│   ├── chroma/             # Vector collections
│   └── uploads/            # Uploaded documents
├── requirements.txt
└── README.md