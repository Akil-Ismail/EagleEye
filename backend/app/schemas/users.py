from datetime import datetime

from pydantic import BaseModel


class UserCreate(BaseModel):
    full_name: str
    role: str | None = None
    notes: str | None = None


class UserResponse(BaseModel):
    id: int
    full_name: str
    role: str | None
    is_active: bool
    enrolled_at: datetime
    notes: str | None
