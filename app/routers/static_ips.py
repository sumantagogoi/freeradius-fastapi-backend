from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional
from sqlalchemy.orm import Session

from ..database import get_radius_db
from ..models.freeradius import RadReply
from ..models.admin import AdminUser
from ..schemas import StaticIPCreate, StaticIPOut, StaticIPUpdate
from ..dependencies import get_current_user

router = APIRouter(prefix="/radius/static-ips", tags=["static-ips"], dependencies=[Depends(get_current_user)])

ATTR_FRAMED_IP = "Framed-IP-Address"
ATTR_FRAMED_IPV6 = "Framed-IPv6-Address"


@router.get("", response_model=list[StaticIPOut])
def list_static_ips(
    username: Optional[str] = Query(None),
    db: Session = Depends(get_radius_db),
):
    q = db.query(RadReply).filter(RadReply.attribute.in_([ATTR_FRAMED_IP, ATTR_FRAMED_IPV6]))
    if username:
        q = q.filter(RadReply.username == username)
    return q.order_by(RadReply.username).all()


@router.get("/{username}", response_model=StaticIPOut)
def get_static_ip(username: str, db: Session = Depends(get_radius_db)):
    entry = (
        db.query(RadReply)
        .filter(RadReply.username == username, RadReply.attribute == ATTR_FRAMED_IP)
        .first()
    )
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No static IP found for user")
    return entry


@router.post("/{username}", response_model=StaticIPOut, status_code=status.HTTP_201_CREATED)
def set_static_ip(username: str, body: StaticIPCreate, db: Session = Depends(get_radius_db)):
    existing = (
        db.query(RadReply)
        .filter(RadReply.username == username, RadReply.attribute == ATTR_FRAMED_IP)
        .first()
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Static IP already exists. Use PUT to update.")

    entry = RadReply(username=username, attribute=ATTR_FRAMED_IP, op=":=", value=body.framed_ip)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.put("/{username}", response_model=StaticIPOut)
def update_static_ip(username: str, body: StaticIPUpdate, db: Session = Depends(get_radius_db)):
    entry = (
        db.query(RadReply)
        .filter(RadReply.username == username, RadReply.attribute == ATTR_FRAMED_IP)
        .first()
    )
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No static IP found")
    if body.framed_ip is not None:
        entry.value = body.framed_ip
    db.commit()
    db.refresh(entry)
    return entry


@router.delete("/{username}", status_code=status.HTTP_204_NO_CONTENT)
def delete_static_ip(username: str, db: Session = Depends(get_radius_db)):
    entries = (
        db.query(RadReply)
        .filter(
            RadReply.username == username,
            RadReply.attribute.in_([ATTR_FRAMED_IP, ATTR_FRAMED_IPV6]),
        )
        .all()
    )
    if not entries:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No static IPs found for user")
    for e in entries:
        db.delete(e)
    db.commit()
