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

## Notes

- The application is designed to run locally without Docker. Docker is only needed for production deployments.
- ChromaDB is used as an embedded vector store. Qdrant can be used for production and large-scale data.
- SQLite stores application metadata and chat/export records.
- The sample login credentials only work with the seeded local database.
