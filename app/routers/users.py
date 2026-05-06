from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from ..database import get_radius_db, get_admin_db
from ..models.freeradius import RadCheck, RadReply, RadUserGroup
from ..models.admin import AdminUser, UserMeta
from ..schemas import RadCheckCreate, RadCheckOut, RadCheckUpdate, RadReplyCreate, RadReplyOut, UserCreate, UserUpdate, UserOut
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


# ── Unified user management (user + metadata) ────────────

@router.get("/users/with-meta", response_model=List[UserOut])
def list_users_with_meta(
    username: Optional[str] = Query(None),
    radius_db: Session = Depends(get_radius_db),
    admin_db: Session = Depends(get_admin_db),
    _: AdminUser = Depends(get_current_user),
):
    q = radius_db.query(RadCheck).filter(RadCheck.attribute == "Cleartext-Password")
    if username:
        q = q.filter(RadCheck.username.ilike(f"%{username}%"))
    rad_entries = q.order_by(RadCheck.username).all()

    result = []
    for entry in rad_entries:
        meta = admin_db.query(UserMeta).filter(UserMeta.username == entry.username).first()
        result.append(UserOut(
            id=entry.id,
            username=entry.username,
            password=entry.value,
            full_name=meta.full_name if meta else None,
            email=meta.email if meta else None,
            phone=meta.phone if meta else None,
            notes=meta.notes if meta else None,
        ))
    return result


@router.post("/users/with-meta", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user_with_meta(
    body: UserCreate,
    radius_db: Session = Depends(get_radius_db),
    admin_db: Session = Depends(get_admin_db),
    _: AdminUser = Depends(get_current_user),
):
    # Check for existing
    existing = (
        radius_db.query(RadCheck)
        .filter(RadCheck.username == body.username, RadCheck.attribute == "Cleartext-Password")
        .first()
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already exists")

    # Create radcheck entry
    rad_entry = RadCheck(username=body.username, attribute="Cleartext-Password", op=":=", value=body.password)
    radius_db.add(rad_entry)
    radius_db.flush()

    # Create/update metadata
    meta = admin_db.query(UserMeta).filter(UserMeta.username == body.username).first()
    if not meta:
        meta = UserMeta(username=body.username)
    if body.full_name is not None:
        meta.full_name = body.full_name
    if body.email is not None:
        meta.email = body.email
    if body.phone is not None:
        meta.phone = body.phone
    if body.notes is not None:
        meta.notes = body.notes

    if not meta.id:
        admin_db.add(meta)

    radius_db.commit()
    admin_db.commit()

    return UserOut(
        id=rad_entry.id,
        username=rad_entry.username,
        password=rad_entry.value,
        full_name=meta.full_name,
        email=meta.email,
        phone=meta.phone,
        notes=meta.notes,
    )


@router.get("/users/with-meta/{username}", response_model=UserOut)
def get_user_with_meta(
    username: str,
    radius_db: Session = Depends(get_radius_db),
    admin_db: Session = Depends(get_admin_db),
    _: AdminUser = Depends(get_current_user),
):
    rad_entry = (
        radius_db.query(RadCheck)
        .filter(RadCheck.username == username, RadCheck.attribute == "Cleartext-Password")
        .first()
    )
    if not rad_entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    meta = admin_db.query(UserMeta).filter(UserMeta.username == username).first()
    return UserOut(
        id=rad_entry.id,
        username=rad_entry.username,
        password=rad_entry.value,
        full_name=meta.full_name if meta else None,
        email=meta.email if meta else None,
        phone=meta.phone if meta else None,
        notes=meta.notes if meta else None,
    )


@router.put("/users/with-meta/{username}", response_model=UserOut)
def update_user_with_meta(
    username: str,
    body: UserUpdate,
    radius_db: Session = Depends(get_radius_db),
    admin_db: Session = Depends(get_admin_db),
    _: AdminUser = Depends(get_current_user),
):
    rad_entry = (
        radius_db.query(RadCheck)
        .filter(RadCheck.username == username, RadCheck.attribute == "Cleartext-Password")
        .first()
    )
    if not rad_entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if body.password is not None:
        rad_entry.value = body.password

    meta = admin_db.query(UserMeta).filter(UserMeta.username == username).first()
    if not meta:
        meta = UserMeta(username=username)
        admin_db.add(meta)

    if body.full_name is not None:
        meta.full_name = body.full_name
    if body.email is not None:
        meta.email = body.email
    if body.phone is not None:
        meta.phone = body.phone
    if body.notes is not None:
        meta.notes = body.notes

    radius_db.commit()
    admin_db.commit()

    return UserOut(
        id=rad_entry.id,
        username=rad_entry.username,
        password=rad_entry.value,
        full_name=meta.full_name,
        email=meta.email,
        phone=meta.phone,
        notes=meta.notes,
    )


@router.delete("/users/with-meta/{username}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_with_meta(
    username: str,
    radius_db: Session = Depends(get_radius_db),
    admin_db: Session = Depends(get_admin_db),
    _: AdminUser = Depends(get_current_user),
):
    rad_entries = radius_db.query(RadCheck).filter(RadCheck.username == username).all()
    if not rad_entries:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    for entry in rad_entries:
        radius_db.delete(entry)

    meta = admin_db.query(UserMeta).filter(UserMeta.username == username).first()
    if meta:
        admin_db.delete(meta)

    radius_db.commit()
    admin_db.commit()
