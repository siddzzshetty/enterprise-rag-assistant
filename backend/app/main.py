from fastapi import FastAPI

from backend.app.api.routes.auth import router as auth_router
from backend.app.api.routes.clients import router as clients_router
from backend.app.api.routes.dashboard import router as dashboard_router
from backend.app.api.routes.projects import router as projects_router
from backend.app.api.routes.health import router as health_router
from backend.app.db.init_db import initialize_database
from backend.app.core.config import get_settings

settings = get_settings()
app = FastAPI(title=settings.app_name)


@app.on_event("startup")
def startup_event() -> None:
    initialize_database()


app.include_router(health_router)
app.include_router(auth_router)
app.include_router(clients_router)
app.include_router(projects_router)
app.include_router(dashboard_router)
