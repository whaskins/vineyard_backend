from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

# Check for Pydantic v2
try:
    from pydantic import field_validator
    validate_pydantic_v2 = True
except ImportError:
    validate_pydantic_v2 = False


# Shared properties
class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = True
    is_superuser: bool = False
    full_name: Optional[str] = None
    user_name: Optional[str] = None
    user_role: Optional[str] = "user"


# Properties to receive via API on creation
class UserCreate(UserBase):
    email: EmailStr  # We'll use this as user_name in the DB
    password: str


# Properties to receive via API on update
class UserUpdate(UserBase):
    password: Optional[str] = None


class UserInDBBase(UserBase):
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Configuration for model
    if validate_pydantic_v2:
        model_config = {
            'from_attributes': True
        }
    else:
        class Config:
            from_attributes = True


# Additional properties to return via API
class User(UserInDBBase):
    pass


# Additional properties stored in DB
class UserInDB(UserInDBBase):
    hashed_password: str