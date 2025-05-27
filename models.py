# models.py
from sqlalchemy import Column, String, Boolean, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID, BYTEA
from sqlalchemy.sql import func
import uuid
from database import Base

class Email(Base):
    __tablename__ = "emails"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    department_label = Column(String, index=True)
    original_subject = Column(String)
    subject_encoding = Column(String, nullable=True)
    translated_subject = Column(String)
    body = Column(Text)
    attachments = Column(Text)
    raw_email = Column(BYTEA)
    is_read = Column(Boolean, default=False)
    forwarded_to_operator = Column(Boolean, default=False)
    email_received_at = Column(DateTime(timezone=True), nullable=True)  # ✅ NEW
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    department = Column(String, nullable=False)
