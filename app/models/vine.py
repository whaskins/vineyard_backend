from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship, backref

from app.db.base_class import Base


class Vine(Base):
    __tablename__ = "vine_inventory"  # Explicitly set the table name to match the database
    
    id = Column("vine_id", Integer, primary_key=True, index=True)
    alpha_numeric_id = Column(String, unique=True, index=True, nullable=False)
    year_of_planting = Column(Integer, nullable=True)
    nursery = Column(String, nullable=True)
    variety = Column(String, nullable=True)
    rootstock = Column(String, nullable=True)
    vineyard_name = Column(String, nullable=True)
    field_name = Column(String, nullable=True)
    row_number = Column(Integer, nullable=True)
    spot_number = Column(Integer, nullable=True)
    is_dead = Column(Boolean, default=False, nullable=False)
    date_died = Column(DateTime, nullable=True)
    record_created = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)