"""Verification script for InsightHub installation."""
from __future__ import annotations

import json
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.core.config import get_settings
from backend.app.db.init_db import initialize_database
from backend.app.services.knowledge_base import KnowledgeBaseService


def main() -> None:
    """Verify the InsightHub installation is complete and ready."""
    print("🔍 Verifying InsightHub installation...")
    print()
    
    errors = []
    warnings = []
    
    # Check configuration
    try:
        settings = get_settings()
        print(f"✅ App: {settings.app_name}")
        print(f"✅ Backend: {settings.backend_host}:{settings.backend_port}")
        print(f"✅ Embedding model: {settings.embedding_model}")
    except Exception as exc:
        errors.append(f"Configuration failed: {exc}")
    
    # Initialize database
    try:
        initialize_database()
        print("✅ Database initialized")
    except Exception as exc:
        errors.append(f"Database initialization failed: {exc}")
    
    # Check directories
    try:
        assert settings.sqlite_path.parent.exists()
        print(f"✅ SQLite directory ready: {settings.sqlite_path.parent}")
    except Exception:
        errors.append("SQLite directory not found")
    
    try:
        assert settings.chroma_path.exists()
        print(f"✅ ChromaDB directory ready: {settings.chroma_path}")
    except Exception:
        warnings.append("ChromaDB directory not found (will be created on first run)")
    
    try:
        assert settings.upload_path.exists()
        print(f"✅ Upload directory ready: {settings.upload_path}")
    except Exception:
        warnings.append("Upload directory not found (will be created on first run)")
    
    # Check service
    try:
        service = KnowledgeBaseService()
        clients = service.list_clients()
        print(f"✅ Service ready with {len(clients)} client(s)")
    except Exception as exc:
        errors.append(f"Service initialization failed: {exc}")
    
    # Check optional dependencies
    try:
        import chromadb
        print("✅ ChromaDB available")
    except ImportError:
        warnings.append("chromadb not installed (vector search will not work)")
    
    try:
        from sentence_transformers import SentenceTransformer
        print("✅ SentenceTransformer available")
    except ImportError:
        warnings.append("sentence-transformers not installed (embeddings will use fallback)")
    
    try:
        import whisper
        print("✅ Whisper available (audio transcription works)")
    except ImportError:
        warnings.append("openai-whisper not installed (audio files will error on upload)")
    
    # Check Groq API key
    if settings.groq_api_key:
        print("✅ Groq API key configured")
    else:
        warnings.append("GROQ_API_KEY not set (LLM features will use heuristic fallbacks)")
    
    print()
    
    if errors:
        print("❌ Errors found:")
        for error in errors:
            print(f"   - {error}")
        sys.exit(1)
    
    if warnings:
        print("⚠️ Warnings:")
        for warning in warnings:
            print(f"   - {warning}")
    
    print("✅ InsightHub is ready to run!")
    print()
    print("Next steps:")
    print(f"  1. Run: python backend/run_backend.py")
    print(f"  2. Run: python -m streamlit run frontend/app.py --server.port 8501")
    print(f"  3. Open: http://{settings.backend_host}:{settings.backend_port}")


if __name__ == "__main__":
    main()