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
    settings = get_settings()
    initialize_database()
    service = KnowledgeBaseService()

    print(json.dumps({
        "app_name": settings.app_name,
        "sqlite_path": str(settings.sqlite_path),
        "chroma_path": str(settings.chroma_path),
        "upload_path": str(settings.upload_path),
        "clients": service.dashboard_overview(1)["total_clients"],
    }, indent=2))


if __name__ == "__main__":
    main()