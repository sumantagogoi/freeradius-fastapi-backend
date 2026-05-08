from sqlalchemy import Column, Integer, Text, String
from ..database import RadiusBase


class RadGroupCheck(RadiusBase):
    __tablename__ = "radgroupcheck"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True)
    groupname = Column(Text, nullable=False, index=True)
    attribute = Column(Text, nullable=False)
    op = Column(String(2), nullable=False)
    value = Column(Text, nullable=False)


class RadGroupReply(RadiusBase):
    __tablename__ = "radgroupreply"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True)
    groupname = Column(Text, nullable=False, index=True)
    attribute = Column(Text, nullable=False)
    op = Column(String(2), nullable=False)
    value = Column(Text, nullable=False)
