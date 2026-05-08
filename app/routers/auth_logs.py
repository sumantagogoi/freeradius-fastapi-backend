from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from ..database import get_radius_db
from ..models.radpostauth import RadPostAuth
from ..models.admin import AdminUser
from ..schemas import AuthLogOut
from ..dependencies import get_current_user

router = APIRouter(prefix="/radius/auth-logs", tags=["auth-logs"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[AuthLogOut])
def list_auth_logs(
    username: Optional[str] = Query(None),
    reply: Optional[str] = Query(None, description="Filter by reply: 'Access-Accept' or 'Access-Reject'"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_radius_db),
):
    """List authentication logs (radpostauth).

    Records every auth attempt including the password (in plaintext) and whether
    it was accepted or rejected.
    """
    q = db.query(RadPostAuth)
    if username:
        q = q.filter(RadPostAuth.username == username)
    if reply:
        q = q.filter(RadPostAuth.reply == reply)
    return q.order_by(desc(RadPostAuth.authdate)).offset(offset).limit(limit).all()


@router.get("/failed", response_model=list[AuthLogOut])
def failed_auth_logs(
    username: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_radius_db),
):
    """List failed authentication attempts."""
    q = db.query(RadPostAuth).filter(RadPostAuth.reply == "Access-Reject")
    if username:
        q = q.filter(RadPostAuth.username == username)
    return q.order_by(desc(RadPostAuth.authdate)).limit(limit).all()
