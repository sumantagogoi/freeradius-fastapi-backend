from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_radius_db
from ..models.freeradius import RadReply
from ..models.admin import AdminUser
from ..schemas import (
    BandwidthProfileCreate, BandwidthProfileOut, BandwidthProfileUpdate, BandwidthProfileFullOut,
)
from ..dependencies import get_current_user

router = APIRouter(prefix="/radius/bandwidth", tags=["bandwidth"], dependencies=[Depends(get_current_user)])

# Standard bandwidth RADIUS attribute names
ATTR_RATE_LIMIT = "Mikrotik-Rate-Limit"
ATTR_BW_UP = "WISPr-Bandwidth-Max-Up"
ATTR_BW_DOWN = "WISPr-Bandwidth-Max-Down"


def _get_bw_attrs(db: Session, username: str) -> dict:
    """Fetch all bandwidth-related radreply entries for a user."""
    entries = (
        db.query(RadReply)
        .filter(
            RadReply.username == username,
            RadReply.attribute.in_([ATTR_RATE_LIMIT, ATTR_BW_UP, ATTR_BW_DOWN]),
        )
        .all()
    )
    result = {"rate_limit": None, "bw_max_up": None, "bw_max_down": None, "_entries": entries}
    for e in entries:
        if e.attribute == ATTR_RATE_LIMIT:
            result["rate_limit"] = e
        elif e.attribute == ATTR_BW_UP:
            result["bw_max_up"] = e
        elif e.attribute == ATTR_BW_DOWN:
            result["bw_max_down"] = e
    return result


@router.get("/{username}", response_model=BandwidthProfileFullOut)
def get_bandwidth_profile(username: str, db: Session = Depends(get_radius_db)):
    bw = _get_bw_attrs(db, username)
    return BandwidthProfileFullOut(
        username=username,
        rate_limit=bw["rate_limit"].value if bw["rate_limit"] else None,
        bw_max_up=bw["bw_max_up"].value if bw["bw_max_up"] else None,
        bw_max_down=bw["bw_max_down"].value if bw["bw_max_down"] else None,
    )


@router.post("/{username}", response_model=BandwidthProfileFullOut, status_code=status.HTTP_201_CREATED)
def set_bandwidth_profile(username: str, body: BandwidthProfileCreate, db: Session = Depends(get_radius_db)):
    bw = _get_bw_attrs(db, username)

    attr_map = {
        ATTR_RATE_LIMIT: (body.rate_limit, "rate_limit"),
        ATTR_BW_UP: (body.bw_max_up, "bw_max_up"),
        ATTR_BW_DOWN: (body.bw_max_down, "bw_max_down"),
    }

    for attr, (new_val, key) in attr_map.items():
        if new_val is None:
            continue
        existing = bw[key]
        if existing:
            existing.value = new_val
        else:
            entry = RadReply(username=username, attribute=attr, op=":=", value=new_val)
            db.add(entry)

    db.commit()
    return get_bandwidth_profile(username, db)


@router.put("/{username}", response_model=BandwidthProfileFullOut)
def update_bandwidth_profile(username: str, body: BandwidthProfileUpdate, db: Session = Depends(get_radius_db)):
    bw = _get_bw_attrs(db, username)

    updates = {
        ATTR_RATE_LIMIT: ("rate_limit", body.rate_limit),
        ATTR_BW_UP: ("bw_max_up", body.bw_max_up),
        ATTR_BW_DOWN: ("bw_max_down", body.bw_max_down),
    }

    for attr, (key, val) in updates.items():
        if val is None:
            continue
        if bw[key]:
            bw[key].value = val
        else:
            entry = RadReply(username=username, attribute=attr, op=":=", value=val)
            db.add(entry)

    db.commit()
    return get_bandwidth_profile(username, db)


@router.delete("/{username}", status_code=status.HTTP_204_NO_CONTENT)
def delete_bandwidth_profile(username: str, db: Session = Depends(get_radius_db)):
    entries = (
        db.query(RadReply)
        .filter(
            RadReply.username == username,
            RadReply.attribute.in_([ATTR_RATE_LIMIT, ATTR_BW_UP, ATTR_BW_DOWN]),
        )
        .all()
    )
    if not entries:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No bandwidth profile found")
    for e in entries:
        db.delete(e)
    db.commit()
