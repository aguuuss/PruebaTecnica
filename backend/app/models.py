from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, func

from app.db import Base


class Place(Base):
    __tablename__ = "places"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True, nullable=False)
    normalized_name = Column(String(255), index=True, nullable=False)
    address = Column(String(255), nullable=True)
    normalized_address = Column(String(255), nullable=True)
    city = Column(String(120), nullable=True)
    category = Column(String(80), default="bar", nullable=False)
    source = Column(String(120), default="Tucuman Turismo", nullable=False)
    source_url = Column(String(500), nullable=False)
    contact = Column(String(255), nullable=True)
    opening_hours = Column(String(255), nullable=True)
    services = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    fetched_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)


class ImportLog(Base):
    __tablename__ = "import_logs"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(120), default="Tucuman Turismo", nullable=False)
    status = Column(String(40), default="running", nullable=False)
    items_found = Column(Integer, default=0, nullable=False)
    created_count = Column(Integer, default=0, nullable=False)
    updated_count = Column(Integer, default=0, nullable=False)
    duplicate_count = Column(Integer, default=0, nullable=False)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    finished_at = Column(DateTime, nullable=True)
