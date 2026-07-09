from fastapi import APIRouter, Depends

from backend.app.core.dependencies import get_current_session
from backend.app.services.knowledge_base import KnowledgeBaseService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])
service = KnowledgeBaseService()


@router.get("")
def dashboard_overview(current_user: dict = Depends(get_current_session)) -> dict:
    return service.dashboard_overview(current_user["client_id"])
