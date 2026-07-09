from typing import Any

from pydantic import BaseModel


class DashboardSummary(BaseModel):
    total_clients: int
    total_projects: int
    total_documents: int
    total_chunks: int
    total_chats: int
    total_retrievals: int
    recent_uploads: list[dict[str, Any]]
    recent_queries: list[dict[str, Any]]
    projects: list[dict[str, Any]]
