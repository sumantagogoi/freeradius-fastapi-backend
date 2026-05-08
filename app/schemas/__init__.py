from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel


# ── Auth ──────────────────────────────────────────────

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    username: str
    password: str


# ── Admin user ───────────────────────────────────────

class AdminUserCreate(BaseModel):
    username: str
    password: str


class AdminUserOut(BaseModel):
    id: int
    username: str
    is_active: bool

    class Config:
        from_attributes = True


# ── RadCheck (user/password) ─────────────────────────

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


# ── RadReply (generic) ───────────────────────────────

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


class RadReplyUpdate(BaseModel):
    attribute: Optional[str] = None
    op: Optional[str] = None
    value: Optional[str] = None


# ── Unified user (radcheck + user_meta) ──────────────

class UserCreate(BaseModel):
    username: str
    password: str
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    notes: Optional[str] = None


class UserUpdate(BaseModel):
    password: Optional[str] = None
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    notes: Optional[str] = None


class UserOut(BaseModel):
    id: int
    username: str
    password: str
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True


# ── Bandwidth profile (via radreply) ─────────────────
# Common attributes:
#   Mikrotik-Rate-Limit   = "1M/2M" (up/down)
#   WISPr-Bandwidth-Max-Up   = "1000000"
#   WISPr-Bandwidth-Max-Down = "2000000"

class BandwidthProfileCreate(BaseModel):
    username: str
    rate_limit: Optional[str] = None       # MikroTik format: "1M/2M 1M/1M 8 4"
    bw_max_up: Optional[str] = None        # WISPr format (bps)
    bw_max_down: Optional[str] = None       # WISPr format (bps)


class BandwidthProfileOut(BaseModel):
    id: int
    username: str
    attribute: str
    value: str

    class Config:
        from_attributes = True


class BandwidthProfileUpdate(BaseModel):
    rate_limit: Optional[str] = None
    bw_max_up: Optional[str] = None
    bw_max_down: Optional[str] = None


class BandwidthProfileFullOut(BaseModel):
    username: str
    rate_limit: Optional[str] = None
    bw_max_up: Optional[str] = None
    bw_max_down: Optional[str] = None


# ── Static IP (via radreply) ─────────────────────────

class StaticIPCreate(BaseModel):
    username: str
    framed_ip: str                           # "Framed-IP-Address" value


class StaticIPOut(BaseModel):
    id: int
    username: str
    attribute: str
    value: str

    class Config:
        from_attributes = True


class StaticIPUpdate(BaseModel):
    framed_ip: Optional[str] = None


# ── RadUserGroup ─────────────────────────────────────

class RadUserGroupCreate(BaseModel):
    username: str
    groupname: str
    priority: int = 1


class RadUserGroupOut(BaseModel):
    id: int
    username: str
    groupname: str
    priority: int

    class Config:
        from_attributes = True


class RadUserGroupUpdate(BaseModel):
    groupname: Optional[str] = None
    priority: Optional[int] = None


# ── Group (radgroupcheck + radgroupreply) ────────────

class GroupCheckCreate(BaseModel):
    groupname: str
    attribute: str
    op: str = ":="
    value: str


class GroupCheckOut(BaseModel):
    id: int
    groupname: str
    attribute: str
    op: str
    value: str

    class Config:
        from_attributes = True


class GroupCheckUpdate(BaseModel):
    attribute: Optional[str] = None
    op: Optional[str] = None
    value: Optional[str] = None


class GroupReplyCreate(BaseModel):
    groupname: str
    attribute: str
    op: str = ":="
    value: str


class GroupReplyOut(BaseModel):
    id: int
    groupname: str
    attribute: str
    op: str
    value: str

    class Config:
        from_attributes = True


class GroupReplyUpdate(BaseModel):
    attribute: Optional[str] = None
    op: Optional[str] = None
    value: Optional[str] = None


# ── NAS ──────────────────────────────────────────────

class NasCreate(BaseModel):
    nasname: str
    shortname: Optional[str] = None
    type: str = "other"
    ports: Optional[int] = None
    secret: str
    server: Optional[str] = None
    community: Optional[str] = None
    description: Optional[str] = None


class NasOut(BaseModel):
    id: int
    nasname: str
    shortname: Optional[str] = None
    type: str
    ports: Optional[int] = None
    secret: str
    server: Optional[str] = None
    community: Optional[str] = None
    description: Optional[str] = None

    class Config:
        from_attributes = True


class NasUpdate(BaseModel):
    nasname: Optional[str] = None
    shortname: Optional[str] = None
    type: Optional[str] = None
    ports: Optional[int] = None
    secret: Optional[str] = None
    server: Optional[str] = None
    community: Optional[str] = None
    description: Optional[str] = None


# ── RadAcct (accounting) ─────────────────────────────

class AcctSessionOut(BaseModel):
    radacctid: int
    acctsessionid: str
    acctuniqueid: str
    username: Optional[str] = None
    nasipaddress: str
    nasidentifier: Optional[str] = None
    acctstarttime: Optional[datetime] = None
    acctstoptime: Optional[datetime] = None
    acctsessiontime: Optional[int] = None
    acctinputoctets: Optional[int] = None
    acctoutputoctets: Optional[int] = None
    acctterminatecause: Optional[str] = None
    framedipaddress: Optional[str] = None
    callingstationid: Optional[str] = None

    class Config:
        from_attributes = True


class UserBandwidthOut(BaseModel):
    username: str
    total_input_mb: float = 0
    total_output_mb: float = 0
    total_session_seconds: int = 0
    session_count: int = 0
    last_session: Optional[datetime] = None


# ── RadPostAuth (auth logs) ──────────────────────────

class AuthLogOut(BaseModel):
    id: int
    username: str
    pass_text: Optional[str] = None
    reply: Optional[str] = None
    calledstationid: Optional[str] = None
    callingstationid: Optional[str] = None
    authdate: datetime

    class Config:
        from_attributes = True
