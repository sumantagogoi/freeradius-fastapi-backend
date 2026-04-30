from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from .config import settings

# --- FreeRADIUS database (existing tables, managed=False) ---
radius_engine = create_engine(settings.database_url, pool_pre_ping=True)
RadiusSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=radius_engine)
RadiusBase = declarative_base()

# --- Admin database (our tables, managed=True) ---
admin_engine = create_engine(settings.admin_db_url, pool_pre_ping=True)
AdminSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=admin_engine)
AdminBase = declarative_base()


def get_radius_db():
    db = RadiusSessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_admin_db():
    db = AdminSessionLocal()
    try:
        yield db
    finally:
        db.close()
