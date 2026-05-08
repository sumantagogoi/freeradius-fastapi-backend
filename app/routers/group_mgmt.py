from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from ..database import get_radius_db
from ..models.freeradius import RadUserGroup
from ..models.radgroup import RadGroupCheck, RadGroupReply
from ..models.admin import AdminUser
from ..schemas import (
    RadUserGroupCreate, RadUserGroupOut, RadUserGroupUpdate,
    GroupCheckCreate, GroupCheckOut, GroupCheckUpdate,
    GroupReplyCreate, GroupReplyOut, GroupReplyUpdate,
)
from ..dependencies import get_current_user

router = APIRouter(prefix="/radius/groups", tags=["groups"], dependencies=[Depends(get_current_user)])


# ── User-Group Membership ───────────────────────────────

@router.get("/membership", response_model=list[RadUserGroupOut])
def list_memberships(
    username: Optional[str] = Query(None),
    groupname: Optional[str] = Query(None),
    db: Session = Depends(get_radius_db),
):
    q = db.query(RadUserGroup)
    if username:
        q = q.filter(RadUserGroup.username == username)
    if groupname:
        q = q.filter(RadUserGroup.groupname == groupname)
    return q.order_by(RadUserGroup.username, RadUserGroup.priority).all()


@router.post("/membership", response_model=RadUserGroupOut, status_code=status.HTTP_201_CREATED)
def create_membership(body: RadUserGroupCreate, db: Session = Depends(get_radius_db)):
    existing = (
        db.query(RadUserGroup)
        .filter(RadUserGroup.username == body.username, RadUserGroup.groupname == body.groupname)
        .first()
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already in this group")
    entry = RadUserGroup(**body.model_dump())
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.put("/membership/{entry_id}", response_model=RadUserGroupOut)
def update_membership(entry_id: int, body: RadUserGroupUpdate, db: Session = Depends(get_radius_db)):
    entry = db.query(RadUserGroup).filter(RadUserGroup.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membership not found")
    updates = body.model_dump(exclude_unset=True)
    for k, v in updates.items():
        setattr(entry, k, v)
    db.commit()
    db.refresh(entry)
    return entry


@router.delete("/membership/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_membership(entry_id: int, db: Session = Depends(get_radius_db)):
    entry = db.query(RadUserGroup).filter(RadUserGroup.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membership not found")
    db.delete(entry)
    db.commit()


# ── Group Checks (auth conditions for a group) ──────────

@router.get("/{groupname}/checks", response_model=list[GroupCheckOut])
def list_group_checks(groupname: str, db: Session = Depends(get_radius_db)):
    return db.query(RadGroupCheck).filter(RadGroupCheck.groupname == groupname).all()


@router.post("/{groupname}/checks", response_model=GroupCheckOut, status_code=status.HTTP_201_CREATED)
def create_group_check(groupname: str, body: GroupCheckCreate, db: Session = Depends(get_radius_db)):
    entry = RadGroupCheck(groupname=groupname, **body.model_dump(exclude={"groupname"}))
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.put("/{groupname}/checks/{check_id}", response_model=GroupCheckOut)
def update_group_check(groupname: str, check_id: int, body: GroupCheckUpdate, db: Session = Depends(get_radius_db)):
    entry = db.query(RadGroupCheck).filter(RadGroupCheck.id == check_id, RadGroupCheck.groupname == groupname).first()
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group check not found")
    updates = body.model_dump(exclude_unset=True)
    for k, v in updates.items():
        setattr(entry, k, v)
    db.commit()
    db.refresh(entry)
    return entry


@router.delete("/{groupname}/checks/{check_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_group_check(groupname: str, check_id: int, db: Session = Depends(get_radius_db)):
    entry = db.query(RadGroupCheck).filter(RadGroupCheck.id == check_id, RadGroupCheck.groupname == groupname).first()
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group check not found")
    db.delete(entry)
    db.commit()


# ── Group Replies (attributes/values assigned to a group) ──

@router.get("/{groupname}/replies", response_model=list[GroupReplyOut])
def list_group_replies(groupname: str, db: Session = Depends(get_radius_db)):
    return db.query(RadGroupReply).filter(RadGroupReply.groupname == groupname).all()


@router.post("/{groupname}/replies", response_model=GroupReplyOut, status_code=status.HTTP_201_CREATED)
def create_group_reply(groupname: str, body: GroupReplyCreate, db: Session = Depends(get_radius_db)):
    entry = RadGroupReply(groupname=groupname, **body.model_dump(exclude={"groupname"}))
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.put("/{groupname}/replies/{reply_id}", response_model=GroupReplyOut)
def update_group_reply(groupname: str, reply_id: int, body: GroupReplyUpdate, db: Session = Depends(get_radius_db)):
    entry = db.query(RadGroupReply).filter(RadGroupReply.id == reply_id, RadGroupReply.groupname == groupname).first()
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group reply not found")
    updates = body.model_dump(exclude_unset=True)
    for k, v in updates.items():
        setattr(entry, k, v)
    db.commit()
    db.refresh(entry)
    return entry


@router.delete("/{groupname}/replies/{reply_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_group_reply(groupname: str, reply_id: int, db: Session = Depends(get_radius_db)):
    entry = db.query(RadGroupReply).filter(RadGroupReply.id == reply_id, RadGroupReply.groupname == groupname).first()
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group reply not found")
    db.delete(entry)
    db.commit()
