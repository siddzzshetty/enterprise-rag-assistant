from datetime import datetime
from typing import Any

from fastapi import Header, HTTPException, status

from backend.app.db.connection import Database


def _extract_token(auth_token: str | None, authorization: str | None) -> str:
    if auth_token:
        return auth_token.strip()
    if authorization and authorization.lower().startswith("bearer "):
        return authorization.split(" ", 1)[1].strip()
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing authentication token")


def get_current_session(
    x_auth_token: str | None = Header(default=None, alias="X-Auth-Token"),
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> dict[str, Any]:
    token = _extract_token(x_auth_token, authorization)
    database = Database()

    with database.connect() as connection:
        session = connection.execute(
            """
            SELECT
                s.token,
                s.user_id,
                s.client_id,
                s.expires_at,
                u.email,
                u.username,
                u.full_name,
                c.name AS client_name,
                c.slug AS client_slug
            FROM sessions s
            JOIN users u ON u.id = s.user_id
            JOIN clients c ON c.id = s.client_id
            WHERE s.token = ?
            """,
            (token,),
        ).fetchone()

        if session is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")

        try:
            expires_at = datetime.fromisoformat(session["expires_at"])
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session") from exc

        if expires_at < datetime.now(expires_at.tzinfo):
            connection.execute("DELETE FROM sessions WHERE token = ?", (token,))
            connection.commit()
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired")

        return {
            "token": session["token"],
            "user_id": session["user_id"],
            "client_id": session["client_id"],
            "email": session["email"],
            "username": session["username"],
            "full_name": session["full_name"],
            "client_name": session["client_name"],
            "client_slug": session["client_slug"],
        }
