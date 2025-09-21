from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
import uuid
from database import Base

class Submission(Base):
    __tablename__ = "submissions"
    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True)
    uploaded_on = Column(DateTime(timezone=True), server_default=func.now())
    document_name = Column(String(255))
    document_url = Column(Text)

class Usage(Base):
    __tablename__ = "usage"
    id = Column(Integer, primary_key=True, index=True)
    total_docs_checked = Column(Integer, default=0)
    total_reports_generated = Column(Integer, default=0)
