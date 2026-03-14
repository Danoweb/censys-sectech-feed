from sqlalchemy import Column, Integer, BigInteger, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from api.v1.database import Base

class Sync(Base):
    __tablename__ = "sync"

    id = Column(Integer, primary_key=True, index=True)
    sync__at = Column(DateTime(timezone=True), server_default=func.now())
    sync_status = Column(String(10), nullable=False)