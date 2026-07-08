from pydantic import BaseModel


class DatabaseStatus(BaseModel):
    initialized: bool
    database_path: str
