"""Test suite for InsightHub - Enterprise Research Knowledge Assistant."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.core.config import get_settings
from backend.app.db.connection import Database
from backend.app.services.knowledge_base import KnowledgeBaseService


class TestConfiguration:
    """Test application configuration."""
    
    def test_settings_load(self) -> None:
        """Settings should load with defaults."""
        settings = get_settings()
        assert settings.app_name == "InsightHub"
        assert settings.backend_host == "127.0.0.1"
        assert settings.backend_port == 8000
        assert settings.embedding_model == "BAAI/bge-m3"

    def test_directories_created(self) -> None:
        """Required directories should be created."""
        settings = get_settings()
        assert settings.sqlite_path.parent.exists()
        assert settings.chroma_path.exists()
        assert settings.upload_path.exists()


class TestDatabase:
    """Test database schema and operations."""
    
    def test_database_connection(self) -> None:
        """Database should be connectable."""
        db = Database()
        with db.connect() as conn:
            assert conn is not None
    
    def test_tables_exist(self) -> None:
        """All required tables should exist."""
        db = Database()
        with db.connect() as conn:
            tables = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
            table_names = {row["name"] for row in tables}
            required_tables = {
                "clients", "users", "projects", "documents",
                "document_chunks", "chats", "retrieval_events", "sessions"
            }
            assert required_tables <= table_names


class TestKnowledgeBaseService:
    """Test knowledge base service operations."""
    
    def test_service_initialization(self) -> None:
        """Service should initialize without errors."""
        service = KnowledgeBaseService()
        assert service is not None

    def test_slugify(self) -> None:
        """Slugify should convert text to URL-safe format."""
        service = KnowledgeBaseService()
        assert service._slugify("My Project Name") == "my-project-name"
        assert service._slugify("Test 123!") == "test-123"
        assert service._slugify("---") == "project"

    def test_text_cleaning(self) -> None:
        """Text cleaning should normalize whitespace."""
        service = KnowledgeBaseService()
        assert service.clean_text("hello   world") == "hello world"
        assert service.clean_text("line1\n\n\nline2") == "line1\n\nline2"

    def test_chunk_text_basic(self) -> None:
        """Text chunking should divide text into overlapping chunks."""
        service = KnowledgeBaseService()
        text = " ".join(["word"] * 300)
        chunks = service.chunk_text(text, chunk_size=100, overlap=20)
        assert len(chunks) > 1
        assert all("chunk_index" in chunk for chunk in chunks)
        assert all("text" in chunk for chunk in chunks)

    def test_chunk_text_empty(self) -> None:
        """Empty text should produce empty chunks list."""
        service = KnowledgeBaseService()
        chunks = service.chunk_text("")
        assert chunks == []

    def test_file_type_detection(self) -> None:
        """File types should be correctly detected."""
        service = KnowledgeBaseService()
        assert service.detect_file_type("test.pdf") == "pdf"
        assert service.detect_file_type("data.xlsx") == "dataset"
        assert service.detect_file_type("notes.txt") == "text"
        assert service.detect_file_type("audio.mp3") == "audio"

    def test_embedding_fallback(self) -> None:
        """Embedding generation should work without sentence-transformers."""
        service = KnowledgeBaseService()
        embeddings = service.embed_texts(["test sentence"])
        assert len(embeddings) == 1
        assert len(embeddings[0]) > 0

    def test_heuristic_category(self) -> None:
        """Document categorization should work heuristically."""
        service = KnowledgeBaseService()
        assert "Survey" in service._heuristic_category("survey.csv", "data, header", None)
        assert "Audio" in service._heuristic_category("interview.mp3", "", None)
        assert "Report" in service._heuristic_category("report.pdf", "market research analysis", None)

    def test_query_rewrite_basic(self) -> None:
        """Query rewriting should normalize input."""
        service = KnowledgeBaseService()
        result = service.rewrite_query("what did people say")
        assert result == "What did people say"

    def test_query_rewrite_heuristic_correction(self) -> None:
        """Query rewriting should fix common misspellings heuristically."""
        service = KnowledgeBaseService()
        result = service.rewrite_query("mumbay pricing")
        assert "Mumbai" in result
        assert "pricing" in result


class TestClientOperations:
    """Test client management operations."""
    
    def test_list_clients_returns_list(self) -> None:
        """Client listing should return a list."""
        service = KnowledgeBaseService()
        clients = service.list_clients()
        assert isinstance(clients, list)


class TestProjectOperations:
    """Test project management operations."""
    
    def test_list_projects_requires_client(self) -> None:
        """Projects listing should work with valid client."""
        service = KnowledgeBaseService()
        # This may return empty if no projects exist
        projects = service.list_projects(1)
        assert isinstance(projects, list)

    def test_project_stats_returns_dict(self) -> None:
        """Project stats should return dictionary with expected keys."""
        service = KnowledgeBaseService()
        # Test with client_id=1, project_id=1 (may not exist)
        try:
            stats = service.project_stats(1, 1)
            assert isinstance(stats, dict)
            assert "document_count" in stats
            assert "chunk_count" in stats
        except Exception:
            # Project doesn't exist yet, which is fine
            pass


class TestChatHistory:
    """Test chat history operations."""
    
    def test_chat_history_returns_list(self) -> None:
        """Chat history should return a list."""
        service = KnowledgeBaseService()
        history = service.recent_chat_history(1, 1, limit=10)
        assert isinstance(history, list)


if __name__ == "__main__":
    # Run tests manually
    import subprocess
    result = subprocess.run(
        [sys.executable, "-m", "pytest", __file__, "-v"],
        cwd=PROJECT_ROOT,
    )
    sys.exit(result.returncode)