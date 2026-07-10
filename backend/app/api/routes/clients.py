from fastapi import APIRouter, Depends

from backend.app.core.dependencies import get_current_session
from backend.app.services.knowledge_base import KnowledgeBaseService

router = APIRouter(prefix="/clients", tags=["clients"])
service = KnowledgeBaseService()


@router.get("")
def list_clients(current_user: dict = Depends(get_current_session)) -> dict:
    """List all clients (admin view - shows all clients)."""
    return {"items": service.list_clients()}


@router.post("")
def create_client(
    payload: dict,
    current_user: dict = Depends(get_current_session),
) -> dict:
    """Create a new client organization with an admin user."""
    name = payload.get("name", "").strip()
    slug = payload.get("slug")
    admin_username = payload.get("admin_username", "admin")
    admin_password = payload.get("admin_password")
    return service.create_client(
        name=name,
        slug=slug,
        admin_username=admin_username,
        admin_password=admin_password,
    )


@router.delete("/{client_id}")
def delete_client(
    client_id: int,
    current_user: dict = Depends(get_current_session),
) -> dict:
    """Delete a client and ALL its associated data."""
    return service.delete_client(client_id)
