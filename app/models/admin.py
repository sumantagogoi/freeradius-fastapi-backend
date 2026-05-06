from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
from ..database import AdminBase


class AdminUser(AdminBase):
    __tablename__ = "admin_users"

    id = Column(Integer, primary_key=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    hashed_password = Column(String(128), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class UserMeta(AdminBase):
    __tablename__ = "user_meta"

    id = Column(Integer, primary_key=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    full_name = Column(String(128), nullable=True)
    email = Column(String(128), nullable=True)
    phone = Column(String(64), nullable=True)
    notes = Column(String(512), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
