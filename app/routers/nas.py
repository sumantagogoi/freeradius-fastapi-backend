from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from ..database import get_radius_db
from ..models.freeradius import Nas
from ..models.admin import AdminUser
from ..schemas import NasCreate, NasOut, NasUpdate
from ..dependencies import get_current_user

router = APIRouter(prefix="/radius/nas", tags=["nas"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[NasOut])
def list_nas(
    search: Optional[str] = Query(None),
    db: Session = Depends(get_radius_db),
):
    q = db.query(Nas)
    if search:
        q = q.filter(Nas.nasname.ilike(f"%{search}%"))
    return q.order_by(Nas.nasname).all()


@router.get("/{nas_id}", response_model=NasOut)
def get_nas(nas_id: int, db: Session = Depends(get_radius_db)):
    entry = db.query(Nas).filter(Nas.id == nas_id).first()
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="NAS not found")
    return entry


@router.post("", response_model=NasOut, status_code=status.HTTP_201_CREATED)
def create_nas(body: NasCreate, db: Session = Depends(get_radius_db)):
    existing = db.query(Nas).filter(Nas.nasname == body.nasname).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="NAS entry already exists")
    entry = Nas(**body.model_dump())
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.put("/{nas_id}", response_model=NasOut)
def update_nas(nas_id: int, body: NasUpdate, db: Session = Depends(get_radius_db)):
    entry = db.query(Nas).filter(Nas.id == nas_id).first()
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="NAS not found")
    updates = body.model_dump(exclude_unset=True)
    for k, v in updates.items():
        setattr(entry, k, v)
    db.commit()
    db.refresh(entry)
    return entry


@router.delete("/{nas_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_nas(nas_id: int, db: Session = Depends(get_radius_db)):
    entry = db.query(Nas).filter(Nas.id == nas_id).first()
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="NAS not found")
    db.delete(entry)
    db.commit()
