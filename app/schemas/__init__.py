from typing import Optional
from pydantic import BaseModel


# --- Auth ---
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    username: str
    password: str


# --- Admin user ---
class AdminUserCreate(BaseModel):
    username: str
    password: str


class AdminUserOut(BaseModel):
    id: int
    username: str
    is_active: bool

    class Config:
        from_attributes = True


# --- FreeRADIUS radcheck ---
class RadCheckCreate(BaseModel):
    username: str
    attribute: str = "Cleartext-Password"
    op: str = ":="
    value: str


class RadCheckOut(BaseModel):
    id: int
    username: str
    attribute: str
    op: str
    value: str

    class Config:
        from_attributes = True


class RadCheckUpdate(BaseModel):
    attribute: Optional[str] = None
    op: Optional[str] = None
    value: Optional[str] = None


# --- FreeRADIUS radreply ---
class RadReplyCreate(BaseModel):
    username: str
    attribute: str
    op: str = ":="
    value: str


class RadReplyOut(BaseModel):
    id: int
    username: str
    attribute: str
    op: str
    value: str

    class Config:
        from_attributes = True
