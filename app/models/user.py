from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class User(Base):
    __tablename__ = "users"  # Explicitly set the table name to match the database
    
    id = Column("user_id", Integer, primary_key=True, index=True)  # Map to user_id column
    user_name = Column(String, nullable=False)  # This is the only actual column in the database
    user_role = Column(String, nullable=False)
    
    # These fields will not be persisted to the database, but are needed for FastAPI's security
    # They will be stored in memory only and used for authentication purposes
    email = None
    hashed_password = None
    full_name = None
    is_active = True
    is_superuser = False
    created_at = None
    updated_at = None
    
    # Use private variable to store email
    _email = None
    
    # Property to use user_name as email for authentication
    @property
    def email(self):
        return self._email or self.user_name
        
    @email.setter
    def email(self, value):
        self._email = value
    
    # For authentication only - not stored in DB
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Set email through the property setter
        if "email" in kwargs:
            self._email = kwargs.get("email")
        self.hashed_password = kwargs.get("hashed_password")
        self.full_name = kwargs.get("full_name", self.user_name)
        self.is_active = kwargs.get("is_active", True)
        self.is_superuser = kwargs.get("is_superuser", False) 
        self.created_at = kwargs.get("created_at", datetime.utcnow())
        self.updated_at = kwargs.get("updated_at", datetime.utcnow())