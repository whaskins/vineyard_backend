from datetime import datetime
from typing import Optional

from pydantic import BaseModel


# Maintenance Type schemas
class MaintenanceTypeBase(BaseModel):
    name: str
    description: Optional[str] = None


class MaintenanceTypeCreate(MaintenanceTypeBase):
    pass


class MaintenanceTypeUpdate(MaintenanceTypeBase):
    name: Optional[str] = None


class MaintenanceTypeInDBBase(MaintenanceTypeBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class MaintenanceType(MaintenanceTypeInDBBase):
    pass


# Maintenance Activity schemas
class MaintenanceActivityBase(BaseModel):
    vine_id: Optional[int] = None  # Keep for backward compatibility
    vine_location_id: Optional[int] = None  # New primary foreign key
    type_id: int
    activity_date: datetime
    notes: Optional[str] = None


class MaintenanceActivityCreate(MaintenanceActivityBase):
    pass


class MaintenanceActivityUpdate(BaseModel):
    vine_id: Optional[int] = None
    vine_location_id: Optional[int] = None
    type_id: Optional[int] = None
    activity_date: Optional[datetime] = None
    notes: Optional[str] = None


class MaintenanceActivityInDBBase(MaintenanceActivityBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MaintenanceActivity(MaintenanceActivityInDBBase):
    pass


class MaintenanceActivityWithType(MaintenanceActivity):
    type: MaintenanceType