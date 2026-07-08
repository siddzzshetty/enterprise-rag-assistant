from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class Client:
    id: int
    name: str
    slug: str
    created_at: datetime | str


@dataclass(slots=True)
class Project:
    id: int
    client_id: int
    name: str
    slug: str
    description: str
    is_active: bool
    created_at: datetime | str


@dataclass(slots=True)
class User:
    id: int
    client_id: int
    email: str
    username: str
    full_name: str
    password_hash: str
    is_active: bool
    created_at: datetime | str
