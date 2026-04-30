from sqlalchemy import Column, Integer, String, Text
from ..database import RadiusBase


class RadCheck(RadiusBase):
    __tablename__ = "radcheck"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True)
    username = Column(String(64), nullable=False, index=True)
    attribute = Column(String(64), nullable=False)
    op = Column(String(2), nullable=False)
    value = Column(String(253), nullable=False)


class RadReply(RadiusBase):
    __tablename__ = "radreply"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True)
    username = Column(String(64), nullable=False, index=True)
    attribute = Column(String(64), nullable=False)
    op = Column(String(2), nullable=False)
    value = Column(String(253), nullable=False)


class RadUserGroup(RadiusBase):
    __tablename__ = "radusergroup"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True)
    username = Column(String(64), nullable=False, index=True)
    groupname = Column(String(64), nullable=False)
    priority = Column(Integer, nullable=False, default=1)


class Nas(RadiusBase):
    __tablename__ = "nas"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True)
    nasname = Column(String(128), nullable=False)
    shortname = Column(String(32))
    type = Column(String(30), default="other")
    ports = Column(Integer)
    secret = Column(String(60), nullable=False)
    server = Column(String(64))
    community = Column(String(50))
    description = Column(String(200))
