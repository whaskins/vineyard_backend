from datetime import datetime
from typing import Optional, Union, Any
import base64
import os

from pydantic import BaseModel, Field, AnyHttpUrl
# Try importing Pydantic v2 validator, fall back to v1 if not available
try:
    from pydantic import field_validator
    validate_pydantic_v2 = True
except ImportError:
    from pydantic import validator
    validate_pydantic_v2 = False
from fastapi import UploadFile, Form


class IssueBase(BaseModel):
    vine_id: Optional[int] = None  # Keep for backward compatibility
    vine_location_id: Optional[int] = None  # New primary foreign key
    description: str
    # Photo storage fields
    photo_path: Optional[str] = None  # Path to the image file
    photo_data_base64: Optional[str] = None  # Base64 encoded photo data for API
    photo_content_type: Optional[str] = None  # MIME type of the image
    is_resolved: Optional[bool] = False
    date_resolved: Optional[datetime] = None
    resolved_by: Optional[int] = None
    
# Support both Pydantic v1 and v2 validator
try:
    # Try importing Pydantic v2 validator
    from pydantic import field_validator
    
    @field_validator('photo_data_base64')
    def validate_photo_data(cls, v, info):
        values = info.data if hasattr(info, 'data') else {}
except ImportError:
    # Fall back to Pydantic v1 validator
        # Validator function for photo data
    def _validate_photo_data(cls, v, values):
        if v is not None:
            try:
                if isinstance(v, str):
                    # Clean the string to ensure it's valid base64
                    v = v.strip()
                    
                    # If it's a data URL, strip the prefix
                    if v.startswith('data:'):
                        # Format: data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEA...
                        header, v = v.split(',', 1)
                        
                        # Extract content type from the header if available
                        if ';' in header:
                            content_type = header.split(';')[0].split(':')[1]
                            if not values.get('photo_content_type'):
                                values['photo_content_type'] = content_type
                    
                    # Ensure padding is correct
                    padding = len(v) % 4
                    if padding > 0:
                        v += "=" * (4 - padding)
                    
                    # Just try to decode to validate it's proper base64
                    base64.b64decode(v)
                else:
                    raise ValueError(f'photo_data_base64 must be a string, got {type(v)}')
            except Exception as e:
                raise ValueError(f'Invalid base64 encoded data for photo_data_base64: {str(e)}')
        return v

    # Use the appropriate validator based on Pydantic version
    if validate_pydantic_v2:
        @field_validator('photo_data_base64')
        def validate_photo_data(cls, v, info):
            values = info.data if hasattr(info, 'data') else {}
            return cls._validate_photo_data(v, values)
    else:
        @validator('photo_data_base64')
        def validate_photo_data(cls, v, values):
            return cls._validate_photo_data(v, values)


class IssueCreate(IssueBase):
    # Accept either reported_by or reported_by_id for compatibility with Flutter app
    reported_by: Optional[int] = None
    reported_by_id: Optional[int] = None
    
    # Validators don't seem to be working with the current setup, so we'll handle this
    # in the endpoint directly using getattr()
    # The endpoint will look for both fields and use whichever is available


class IssueUpdate(BaseModel):
    description: Optional[str] = None
    photo_path: Optional[str] = None
    photo_data_base64: Optional[str] = None
    photo_content_type: Optional[str] = None
    is_resolved: Optional[bool] = None
    date_resolved: Optional[datetime] = None
    resolved_by: Optional[int] = None
    resolved_by_id: Optional[int] = None  # For Flutter app compatibility
    
    # Validators don't seem to be working with the current setup, so we'll handle this
    # in the endpoint directly using getattr()


class IssueInDBBase(IssueBase):
    id: int
    reported_by: int
    date_reported: datetime
    created_at: datetime
    updated_at: datetime
    
    # Add a computed photo_url field
    photo_url: Optional[str] = None
    
    # Don't include binary data in responses by default
    photo_data_base64: Optional[str] = None
    
    # Configuration for model
    if validate_pydantic_v2:
        model_config = {
            'from_attributes': True
        }
    else:
        class Config:
            from_attributes = True
    
    # Use the appropriate validator based on Pydantic version
    if validate_pydantic_v2:
        # In Pydantic v2, 'mode' parameter is used instead of 'always'
        @field_validator('photo_url', mode='before')
        def set_photo_url(cls, v, info):
            """Auto-generate a photo URL if the photo path exists"""
            values = info.data if hasattr(info, 'data') else {}
            if v:
                return v
            
            # If we have an ID and a photo path, generate a URL
            if values.get('id') and values.get('photo_path'):
                return f"/api/v1/issues/{values['id']}/photo"
            return None
    else:
        @validator('photo_url', always=True)
        def set_photo_url(cls, v, values):
            """Auto-generate a photo URL if the photo path exists"""
            if v:
                return v
            
            # If we have an ID and a photo path, generate a URL
            if values.get('id') and values.get('photo_path'):
                return f"/api/v1/issues/{values['id']}/photo"
            return None


class Issue(IssueInDBBase):
    pass


class IssueWithDetails(Issue):
    reporter_name: str
    resolver_name: Optional[str] = None
    vine_alpha_numeric_id: str


# Special response model that includes the photo data
class IssueWithPhoto(Issue):
    # Override to include base64 encoded photo data if available
    photo_data_base64: Optional[str] = None
    
    
# Form-based issue creation for file uploads
class IssueCreateForm:
    def __init__(
        self,
        description: str = Form(...),
        reported_by: int = Form(...),
        vine_id: Optional[int] = Form(None),
        vine_location_id: Optional[int] = Form(None),
        is_resolved: bool = Form(False),
        photo: Optional[UploadFile] = None,
        resolved_by: Optional[int] = Form(None),
        date_resolved: Optional[datetime] = Form(None),
    ):
        self.vine_id = vine_id
        self.vine_location_id = vine_location_id
        self.description = description
        self.reported_by = reported_by
        self.is_resolved = is_resolved
        self.photo = photo
        self.resolved_by = resolved_by
        self.date_resolved = date_resolved


# Form-based issue update for file uploads
class IssueUpdateForm:
    def __init__(
        self,
        description: Optional[str] = Form(None),
        is_resolved: Optional[bool] = Form(None),
        photo: Optional[UploadFile] = None,
        resolved_by: Optional[int] = Form(None),
        date_resolved: Optional[datetime] = Form(None),
    ):
        self.description = description
        self.is_resolved = is_resolved
        self.photo = photo
        self.resolved_by = resolved_by
        self.date_resolved = date_resolved