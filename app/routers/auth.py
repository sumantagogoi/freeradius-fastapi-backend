from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_admin_db
from ..models.admin import AdminUser
from ..schemas import LoginRequest, Token, AdminUserCreate, AdminUserOut
from ..dependencies import hash_password, verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
def login(body: LoginRequest, db: Session = Depends(get_admin_db)):
    user = db.query(AdminUser).filter(AdminUser.username == body.username).first()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")
    return Token(access_token=create_access_token(user.username))


@router.get("/me", response_model=AdminUserOut)
def me(current_user: AdminUser = Depends(get_current_user)):
    return current_user


@router.post("/seed", response_model=AdminUserOut)
def seed_admin(body: AdminUserCreate, db: Session = Depends(get_admin_db)):
    count = db.query(AdminUser).count()
    if count > 0:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Admin user already exists. Use /auth/login instead.")
    existing = db.query(AdminUser).filter(AdminUser.username == body.username).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username taken")
    user = AdminUser(username=body.username, hashed_password=hash_password(body.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
