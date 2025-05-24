from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship, backref

from app.db.base_class import Base


class Vine(Base):
    __tablename__ = "vines"
    
    id = Column("vine_id", Integer, primary_key=True, index=True)
    alpha_numeric_id = Column(String, unique=True, index=True, nullable=True)
    year_of_planting = Column(Integer, nullable=True)
    nursery = Column(String, nullable=True)
    variety = Column(String, nullable=True)
    rootstock = Column(String, nullable=True)
    is_dead = Column(Boolean, default=False, nullable=False)
    date_died = Column(DateTime, nullable=True)
    record_created = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationship to vine locations
    locations = relationship("VineLocation", back_populates="vine")


class VineLocation(Base):
    __tablename__ = "vine_locations"
    
    id = Column("location_id", Integer, primary_key=True, index=True)
    alpha_numeric_id = Column(String, nullable=True, index=True)
    vineyard_name = Column(String, nullable=True)
    field_name = Column(String, nullable=True)
    row_number = Column(Integer, nullable=True)
    spot_number = Column(Integer, nullable=True)
    year_of_planting = Column(Integer, nullable=True)
    vine_id = Column(Integer, ForeignKey("vines.vine_id"), nullable=True)
    record_created = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationship to vine
    vine = relationship("Vine", back_populates="locations")