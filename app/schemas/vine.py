from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

# Check for Pydantic v2
try:
    from pydantic import field_validator
    validate_pydantic_v2 = True
except ImportError:
    validate_pydantic_v2 = False


# Shared properties
class VineBase(BaseModel):
    alpha_numeric_id: Optional[str] = None
    year_of_planting: Optional[int] = None
    nursery: Optional[str] = None
    variety: Optional[str] = None
    rootstock: Optional[str] = None
    vineyard_name: Optional[str] = None
    field_name: Optional[str] = None
    row_number: Optional[int] = None
    spot_number: Optional[int] = None
    is_dead: Optional[bool] = False
    date_died: Optional[datetime] = None


# Properties to receive on vine creation
class VineCreate(VineBase):
    alpha_numeric_id: str


# Properties to receive on vine update
class VineUpdate(VineBase):
    pass


# Properties shared by models stored in DB
class VineInDBBase(VineBase):
    id: int
    alpha_numeric_id: str
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


# Properties to return to client
class Vine(VineInDBBase):
    pass


# Properties properties stored in DB
class VineInDB(VineInDBBase):
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