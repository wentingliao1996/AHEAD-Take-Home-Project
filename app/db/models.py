from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    files = relationship('FileInfo', back_populates='owner')
    activities = relationship('ActivityLog', back_populates='user')

class FileInfo(Base):
    __tablename__ = 'files'
    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    original_filename = Column(String, nullable=False)
    stored_filename = Column(String, nullable=False, unique=True)
    size_bytes = Column(Numeric, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    fcs_version = Column(String, nullable=True)
    is_public = Column(Boolean, default=True)
    slug = Column(String, unique=True, index=True, nullable=False)

    owner = relationship('User', back_populates='files')

class TaskRecord(Base):
    __tablename__ = 'tasks'
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String, unique=True, index=True)
    status = Column(String, default='pending')
    created_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)
    result = Column(Text, nullable=True)

class ActivityLog(Base):
    __tablename__ = 'activity_logs'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    username = Column(String, nullable=False)
    activity_type = Column(String, nullable=False)  # login, logout, file_upload, file_public, etc.
    description = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    user = relationship('User', back_populates='activities')
