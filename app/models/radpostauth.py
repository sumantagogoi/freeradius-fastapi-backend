from sqlalchemy import Column, BigInteger, Text, DateTime
from ..database import RadiusBase


class RadPostAuth(RadiusBase):
    __tablename__ = "radpostauth"
    __table_args__ = {"extend_existing": True}

    id = Column(BigInteger, primary_key=True)
    username = Column(Text, nullable=False, index=True)
    pass_text = Column("pass", Text, nullable=True)
    reply = Column(Text, nullable=True)
    calledstationid = Column(Text, nullable=True)
    callingstationid = Column(Text, nullable=True)
    authdate = Column(DateTime(timezone=True), nullable=False)
    class_text = Column("class", Text, nullable=True)
