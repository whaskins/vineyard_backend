from datetime import datetime
import os

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, LargeBinary
from sqlalchemy.orm import relationship, backref

from app.db.base_class import Base


class VineIssue(Base):
    __tablename__ = "vine_issues"  # Explicitly set the table name to match the database
    
    id = Column("issue_id", Integer, primary_key=True, index=True)
    vine_id = Column(Integer, ForeignKey("vines.vine_id", ondelete="CASCADE"), nullable=True)  # Keep for backward compatibility
    vine_location_id = Column(Integer, ForeignKey("vine_locations.location_id", ondelete="CASCADE"), nullable=True)
    description = Column("issue_description", Text, nullable=False)
    # Path to the stored image file - we'll use this for the relative path to the image
    photo_path = Column(String, nullable=True)
    # Keep photo_data for backward compatibility
    photo_data = Column(LargeBinary, nullable=True)
    # Image MIME type
    photo_content_type = Column(String, nullable=True)
    date_reported = Column(DateTime, default=datetime.utcnow, nullable=False)
    reported_by = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    is_resolved = Column(Boolean, default=False, nullable=False)
    date_resolved = Column(DateTime, nullable=True)
    resolved_by = Column(Integer, ForeignKey("users.user_id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    vine = relationship("Vine", backref=backref("issues", cascade="all, delete-orphan"))
    vine_location = relationship("VineLocation", backref=backref("issues", cascade="all, delete-orphan"))
    reporter = relationship("User", foreign_keys=[reported_by], backref=backref("reported_issues"))
    resolver = relationship("User", foreign_keys=[resolved_by], backref=backref("resolved_issues"))
    
    def get_photo_url(self) -> str:
        """
        Generate a URL for the photo if available
        """
        if self.photo_path:
            # Convert the path to a URL
            return f"/api/v1/issues/{self.id}/photo"
        return None