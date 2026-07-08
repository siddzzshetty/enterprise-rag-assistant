from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    login: str = Field(..., description="Username or email")
    password: str = Field(..., min_length=1)


class SessionResponse(BaseModel):
    token: str
    user_id: int
    client_id: int
    username: str
    full_name: str
    email: str
