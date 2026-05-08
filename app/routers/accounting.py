from typing import Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, desc, text
from sqlalchemy.orm import Session

from ..database import get_radius_db
from ..models.radacct import RadAcct
from ..models.admin import AdminUser
from ..schemas import AcctSessionOut, UserBandwidthOut
from ..dependencies import get_current_user

router = APIRouter(prefix="/radius/accounting", tags=["accounting"], dependencies=[Depends(get_current_user)])


def _attach_nasidentifier(db: Session, sessions: list[AcctSessionOut]) -> None:
    """
    If the database has a custom `nasidentifier` column, fetch and attach it.
    Silently no-op if the column doesn't exist — keeps things working on
    stock FreeRADIUS schemas.
    """
    if not sessions:
        return
    try:
        ids = tuple(s.radacctid for s in sessions)
        if not ids:
            return
        rows = db.execute(
            text("SELECT radacctid, nasidentifier FROM radacct WHERE radacctid IN :ids"),
            {"ids": ids},
        ).fetchall()
        mapping = {r[0]: r[1] for r in rows}
        for s in sessions:
            s.nasidentifier = mapping.get(s.radacctid)
    except Exception:
        pass  # Column doesn't exist or DB doesn't support it — no problem


def _to_acct_out(row: RadAcct) -> AcctSessionOut:
    """Convert an ORM row to AcctSessionOut, tolerating any missing attrs."""
    return AcctSessionOut(
        radacctid=row.radacctid,
        acctsessionid=row.acctsessionid,
        acctuniqueid=row.acctuniqueid,
        username=row.username,
        nasipaddress=row.nasipaddress,
        acctstarttime=row.acctstarttime,
        acctstoptime=row.acctstoptime,
        acctsessiontime=row.acctsessiontime,
        acctinputoctets=row.acctinputoctets,
        acctoutputoctets=row.acctoutputoctets,
        acctterminatecause=row.acctterminatecause,
        framedipaddress=row.framedipaddress,
        callingstationid=row.callingstationid,
    )


@router.get("/sessions", response_model=list[AcctSessionOut])
def list_sessions(
    username: Optional[str] = Query(None),
    active_only: bool = Query(False),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_radius_db),
):
    """List RADIUS accounting sessions."""
    q = db.query(RadAcct)
    if username:
        q = q.filter(RadAcct.username == username)
    if active_only:
        q = q.filter(RadAcct.acctstoptime.is_(None))
    rows = q.order_by(desc(RadAcct.acctstarttime)).offset(offset).limit(limit).all()

    results = [_to_acct_out(r) for r in rows]
    _attach_nasidentifier(db, results)
    return results


@router.get("/sessions/{session_id}", response_model=AcctSessionOut)
def get_session(session_id: int, db: Session = Depends(get_radius_db)):
    row = db.query(RadAcct).filter(RadAcct.radacctid == session_id).first()
    if not row:
        return None
    result = _to_acct_out(row)
    _attach_nasidentifier(db, [result])
    return result


@router.get("/bandwidth", response_model=list[UserBandwidthOut])
def user_bandwidth_usage(
    username: Optional[str] = Query(None),
    since_days: int = Query(30, ge=1, le=365),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_radius_db),
):
    """Get bandwidth usage summary per user."""
    since = datetime.now() - timedelta(days=since_days)

    q = (
        db.query(
            RadAcct.username,
            func.coalesce(func.sum(RadAcct.acctinputoctets), 0).label("total_input"),
            func.coalesce(func.sum(RadAcct.acctoutputoctets), 0).label("total_output"),
            func.coalesce(func.sum(RadAcct.acctsessiontime), 0).label("total_time"),
            func.count(RadAcct.radacctid).label("session_count"),
            func.max(RadAcct.acctstarttime).label("last_session"),
        )
        .filter(RadAcct.acctstarttime >= since)
        .group_by(RadAcct.username)
    )

    if username:
        q = q.filter(RadAcct.username == username)

    rows = q.order_by(desc("total_input")).limit(limit).all()

    return [
        UserBandwidthOut(
            username=row.username,
            total_input_mb=round((row.total_input or 0) / (1024 * 1024), 2),
            total_output_mb=round((row.total_output or 0) / (1024 * 1024), 2),
            total_session_seconds=row.total_time or 0,
            session_count=row.session_count or 0,
            last_session=row.last_session,
        )
        for row in rows
    ]


@router.get("/active", response_model=list[AcctSessionOut])
def active_sessions(
    db: Session = Depends(get_radius_db),
):
    """List currently active sessions (no stop time)."""
    rows = (
        db.query(RadAcct)
        .filter(RadAcct.acctstoptime.is_(None))
        .order_by(desc(RadAcct.acctstarttime))
        .all()
    )
    results = [_to_acct_out(r) for r in rows]
    _attach_nasidentifier(db, results)
    return results
