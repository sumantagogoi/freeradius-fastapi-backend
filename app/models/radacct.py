from sqlalchemy import Column, BigInteger, Integer, Text, DateTime, Index
from ..database import RadiusBase


class RadAcct(RadiusBase):
    __tablename__ = "radacct"
    __table_args__ = {"extend_existing": True}

    radacctid = Column(BigInteger, primary_key=True)
    acctsessionid = Column(Text, nullable=False)
    acctuniqueid = Column(Text, nullable=False)
    username = Column(Text, nullable=True, index=True)
    realm = Column(Text, nullable=True)
    nasipaddress = Column(Text, nullable=False)
    nasportid = Column(Text, nullable=True)
    nasporttype = Column(Text, nullable=True)
    acctstarttime = Column(DateTime(timezone=True), nullable=True)
    acctupdatetime = Column(DateTime(timezone=True), nullable=True)
    acctstoptime = Column(DateTime(timezone=True), nullable=True)
    acctinterval = Column(BigInteger, nullable=True)
    acctsessiontime = Column(BigInteger, nullable=True)
    acctauthentic = Column(Text, nullable=True)
    connectinfo_start = Column(Text, nullable=True)
    connectinfo_stop = Column(Text, nullable=True)
    acctinputoctets = Column(BigInteger, nullable=True)
    acctoutputoctets = Column(BigInteger, nullable=True)
    calledstationid = Column(Text, nullable=True)
    callingstationid = Column(Text, nullable=True)
    acctterminatecause = Column(Text, nullable=True)
    servicetype = Column(Text, nullable=True)
    framedprotocol = Column(Text, nullable=True)
    framedipaddress = Column(Text, nullable=True)
    framedipv6address = Column(Text, nullable=True)
    framedipv6prefix = Column(Text, nullable=True)
    framedinterfaceid = Column(Text, nullable=True)
    delegatedipv6prefix = Column(Text, nullable=True)
    class_text = Column("class", Text, nullable=True)
