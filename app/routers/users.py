from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from ..database import get_radius_db
from ..models.freeradius import RadCheck, RadReply, RadUserGroup
from ..models.admin import AdminUser
from ..schemas import RadCheckCreate, RadCheckOut, RadCheckUpdate, RadReplyCreate, RadReplyOut
from ..dependencies import get_current_user

router = APIRouter(prefix="/radius", tags=["radius"], dependencies=[Depends(get_current_user)])


# ── radcheck ──────────────────────────────────────────────

@router.get("/users", response_model=List[RadCheckOut])
def list_radius_users(
    username: Optional[str] = Query(None),
    all: Optional[bool] = Query(False),
    db: Session = Depends(get_radius_db),
    _: AdminUser = Depends(get_current_user),
):
    q = db.query(RadCheck)
    if not all:
        q = q.filter(RadCheck.attribute == "Cleartext-Password")
    if username:
        q = q.filter(RadCheck.username.ilike(f"%{username}%"))
    return q.order_by(RadCheck.username).all()


@router.post("/users", response_model=RadCheckOut, status_code=status.HTTP_201_CREATED)
def create_radius_user(
    body: RadCheckCreate,
    db: Session = Depends(get_radius_db),
    _: AdminUser = Depends(get_current_user),
):
    existing = (
        db.query(RadCheck)
        .filter(RadCheck.username == body.username, RadCheck.attribute == body.attribute)
        .first()
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Entry already exists")
    entry = RadCheck(**body.model_dump())
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.put("/users/{entry_id}", response_model=RadCheckOut)
def update_radius_user(
    entry_id: int,
    body: RadCheckUpdate,
    db: Session = Depends(get_radius_db),
    _: AdminUser = Depends(get_current_user),
):
    entry = db.query(RadCheck).filter(RadCheck.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entry not found")
    updates = body.model_dump(exclude_unset=True)
    for k, v in updates.items():
        setattr(entry, k, v)
    db.commit()
    db.refresh(entry)
    return entry


@router.delete("/users/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_radius_user(
    entry_id: int,
    db: Session = Depends(get_radius_db),
    _: AdminUser = Depends(get_current_user),
):
    entry = db.query(RadCheck).filter(RadCheck.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entry not found")
    db.delete(entry)
    db.commit()


# ── radreply ──────────────────────────────────────────────

@router.get("/replies", response_model=List[RadReplyOut])
def list_replies(
    username: Optional[str] = Query(None),
    db: Session = Depends(get_radius_db),
    _: AdminUser = Depends(get_current_user),
):
    q = db.query(RadReply)
    if username:
        q = q.filter(RadReply.username == username)
    return q.order_by(RadReply.username).all()


@router.post("/replies", response_model=RadReplyOut, status_code=status.HTTP_201_CREATED)
def create_reply(
    body: RadReplyCreate,
    db: Session = Depends(get_radius_db),
    _: AdminUser = Depends(get_current_user),
):
    entry = RadReply(**body.model_dump())
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.delete("/replies/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_reply(
    entry_id: int,
    db: Session = Depends(get_radius_db),
    _: AdminUser = Depends(get_current_user),
):
    entry = db.query(RadReply).filter(RadReply.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entry not found")
    db.delete(entry)
    db.commit()
