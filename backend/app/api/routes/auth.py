from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.core.security import generate_session_token, verify_password
from backend.app.db.connection import Database
from backend.app.schemas.auth import LoginRequest, SessionResponse
from backend.app.core.dependencies import get_current_session

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=SessionResponse)
def login(payload: LoginRequest) -> SessionResponse:
    database = Database()

    with database.connect() as connection:
        user = connection.execute(
            """
            SELECT id, client_id, email, username, full_name, password_hash, is_active
            FROM users
            WHERE username = ? OR email = ?
            """,
            (payload.login, payload.login),
        ).fetchone()

        if user is None or not user["is_active"]:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        if not verify_password(payload.password, user["password_hash"]):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

        token = generate_session_token()
        expires_at = (datetime.now(timezone.utc) + timedelta(hours=12)).isoformat()
        connection.execute(
            """
            INSERT INTO sessions (token, user_id, client_id, expires_at)
            VALUES (?, ?, ?, ?)
            """,
            (token, user["id"], user["client_id"], expires_at),
        )
        connection.commit()

    return SessionResponse(
        token=token,
        user_id=user["id"],
        client_id=user["client_id"],
        username=user["username"],
        full_name=user["full_name"],
        email=user["email"],
    )


@router.get("/me")
def current_session(current_user: dict = Depends(get_current_session)) -> dict:
    return current_user
