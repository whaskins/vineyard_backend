from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field

# Check for Pydantic v2
try:
    from pydantic import field_validator
    validate_pydantic_v2 = True
except ImportError:
    validate_pydantic_v2 = False


# Shared properties for Vine
class VineBase(BaseModel):
    alpha_numeric_id: Optional[str] = None
    year_of_planting: Optional[int] = None
    nursery: Optional[str] = None
    variety: Optional[str] = None
    rootstock: Optional[str] = None
    is_dead: Optional[bool] = False
    date_died: Optional[datetime] = None


# Properties to receive on vine creation
class VineCreate(VineBase):
    alpha_numeric_id: Optional[str] = None


# Properties to receive on vine update
class VineUpdate(VineBase):
    pass


# Shared properties for VineLocation
class VineLocationBase(BaseModel):
    alpha_numeric_id: Optional[str] = None
    vineyard_name: Optional[str] = None
    field_name: Optional[str] = None
    row_number: Optional[int] = None
    spot_number: Optional[int] = None
    year_of_planting: Optional[int] = None
    vine_id: Optional[int] = None


# Properties to receive on vine location creation
class VineLocationCreate(VineLocationBase):
    pass


# Properties to receive on vine location update
class VineLocationUpdate(VineLocationBase):
    pass


# Properties shared by models stored in DB
class VineInDBBase(VineBase):
    id: int
    alpha_numeric_id: Optional[str] = None
    record_created: datetime
    updated_at: datetime

    # Configuration for model
    if validate_pydantic_v2:
        model_config = {
            'from_attributes': True
        }
    else:
        class Config:
            from_attributes = True


# Properties shared by vine location models stored in DB
class VineLocationInDBBase(VineLocationBase):
    id: int
    record_created: datetime
    updated_at: datetime

    # Configuration for model
    if validate_pydantic_v2:
        model_config = {
            'from_attributes': True
        }
    else:
        class Config:
            from_attributes = True


# Properties to return to client for VineLocation
class VineLocation(VineLocationInDBBase):
    pass


# Properties to return to client for Vine (with locations)
class Vine(VineInDBBase):
    locations: List[VineLocation] = []


# Properties properties stored in DB
class VineInDB(VineInDBBase):
    pass


# Properties stored in DB for VineLocation
class VineLocationInDB(VineLocationInDBBase):
    pass


# For search and filter functionality
class VineSearchParams(BaseModel):
    alpha_numeric_id: Optional[str] = None
    variety: Optional[str] = None
    vineyard_name: Optional[str] = None
    field_name: Optional[str] = None
    row_number: Optional[int] = None
    is_dead: Optional[bool] = None
    year_min: Optional[int] = None
    year_max: Optional[int] = None
    page: int = 1
    items_per_page: int = 10