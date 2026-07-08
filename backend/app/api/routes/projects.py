from fastapi import APIRouter, Depends, File, UploadFile

from backend.app.core.dependencies import get_current_session
from backend.app.schemas.projects import ChatQuestionRequest
from backend.app.services.knowledge_base import KnowledgeBaseService

router = APIRouter(prefix="/projects", tags=["projects"])
service = KnowledgeBaseService()


@router.get("")
def list_projects(current_user: dict = Depends(get_current_session)) -> dict:
    return {
        "items": service.list_projects(current_user["client_id"]),
        "client": {
            "id": current_user["client_id"],
            "name": current_user["client_name"],
            "slug": current_user["client_slug"],
        },
    }


@router.get("/{project_id}")
def get_project(project_id: int, current_user: dict = Depends(get_current_session)) -> dict:
    return service.get_project(current_user["client_id"], project_id)


@router.get("/{project_id}/documents")
def list_documents(project_id: int, current_user: dict = Depends(get_current_session)) -> dict:
    return {"items": service.list_documents(current_user["client_id"], project_id)}


@router.get("/{project_id}/stats")
def project_stats(project_id: int, current_user: dict = Depends(get_current_session)) -> dict:
    return service.project_stats(current_user["client_id"], project_id)


@router.post("/{project_id}/documents/upload")
async def upload_document(
    project_id: int,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_session),
) -> dict:
    return service.ingest_upload(current_user["client_id"], project_id, file)


@router.post("/{project_id}/chat/ask")
def ask_question(
    project_id: int,
    payload: ChatQuestionRequest,
    current_user: dict = Depends(get_current_session),
) -> dict:
    return service.ask_question(
        client_id=current_user["client_id"],
        project_id=project_id,
        user_id=current_user["user_id"],
        question=payload.question,
    )
