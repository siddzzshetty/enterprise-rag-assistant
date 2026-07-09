from typing import Any

from pydantic import BaseModel, Field


class ChatQuestionRequest(BaseModel):
    question: str = Field(..., min_length=2)


class ProjectCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    description: str = Field(default="", max_length=500)
    slug: str | None = Field(default=None, max_length=120)


class ProjectSummary(BaseModel):
    id: int
    name: str
    slug: str
    description: str
    is_active: bool
    document_count: int = 0
    chunk_count: int = 0
    chat_count: int = 0


class ProjectStats(BaseModel):
    project_id: int
    document_count: int
    chunk_count: int
    chat_count: int
    category_counts: dict[str, int]
    recent_uploads: list[dict[str, Any]]


class DocumentSummary(BaseModel):
    id: int
    file_name: str
    file_type: str
    category: str
    status: str
    uploaded_at: str
    chunk_count: int = 0


class IngestionResponse(BaseModel):
    document_id: int
    file_name: str
    file_type: str
    category: str
    chunk_count: int
    storage_path: str
    status: str


class ChatResponse(BaseModel):
    query: str
    answer: str
    project_id: int
    document_id: int | None = None
    sources: list[dict[str, Any]]
