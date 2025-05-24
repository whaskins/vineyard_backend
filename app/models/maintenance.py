from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship, backref

from app.db.base_class import Base


class MaintenanceType(Base):
    __tablename__ = "maintenance_types"  # Explicitly set the table name to match the database
    
    id = Column("type_id", Integer, primary_key=True, index=True)
    name = Column("type_name", String, unique=True, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class MaintenanceActivity(Base):
    __tablename__ = "maintenance_activities"  # Explicitly set the table name to match the database
    
    id = Column("activity_id", Integer, primary_key=True, index=True)
    vine_id = Column(Integer, ForeignKey("vines.vine_id", ondelete="CASCADE"), nullable=True)  # Keep for backward compatibility
    vine_location_id = Column(Integer, ForeignKey("vine_locations.location_id", ondelete="CASCADE"), nullable=True)
    type_id = Column(Integer, ForeignKey("maintenance_types.type_id", ondelete="CASCADE"), nullable=False)
    activity_date = Column(DateTime, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    vine = relationship("Vine", backref=backref("maintenance_activities", cascade="all, delete-orphan"))
    vine_location = relationship("VineLocation", backref=backref("maintenance_activities", cascade="all, delete-orphan"))
    type = relationship("MaintenanceType", backref=backref("activities"))