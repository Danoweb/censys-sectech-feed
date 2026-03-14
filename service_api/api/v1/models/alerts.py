from sqlalchemy import Column, Integer, BigInteger, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from api.v1.database import Base

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(String(255), unique=True, nullable=False)
    alert_type = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    severity = Column(String(50), nullable=False)
    source = Column(String(255), nullable=True)
    hostname = Column(String(255), nullable=True)
    ip_addressV4 = Column(String(15), nullable=True)  # IPv4 max length is 15 characters
    ip_addressV6 = Column(String(45), nullable=True)  # IPv6 max length is 45 characters
    port = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    