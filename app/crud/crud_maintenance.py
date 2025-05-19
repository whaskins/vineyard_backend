from typing import List, Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.crud.base import CRUDBase
from app.models.maintenance import MaintenanceActivity, MaintenanceType
from app.schemas.maintenance import (
    MaintenanceActivityCreate,
    MaintenanceActivityUpdate,
    MaintenanceTypeCreate,
    MaintenanceTypeUpdate,
)


class CRUDMaintenanceType(CRUDBase[MaintenanceType, MaintenanceTypeCreate, MaintenanceTypeUpdate]):
    async def get_by_name(self, db: AsyncSession, *, name: str) -> Optional[MaintenanceType]:
        result = await db.execute(select(MaintenanceType).filter(MaintenanceType.name == name))
        return result.scalars().first()


class CRUDMaintenanceActivity(CRUDBase[MaintenanceActivity, MaintenanceActivityCreate, MaintenanceActivityUpdate]):
    async def get_by_vine_id(
        self, db: AsyncSession, *, vine_id: int, skip: int = 0, limit: int = 100
    ) -> List[MaintenanceActivity]:
        result = await db.execute(
            select(MaintenanceActivity)
            .filter(MaintenanceActivity.vine_id == vine_id)
            .order_by(MaintenanceActivity.activity_date.desc())
            .offset(skip)
            .limit(limit)
            .options(joinedload(MaintenanceActivity.type))
        )
        return result.scalars().all()

    async def get_by_type(
        self, db: AsyncSession, *, type_id: int, skip: int = 0, limit: int = 100
    ) -> List[MaintenanceActivity]:
        result = await db.execute(
            select(MaintenanceActivity)
            .filter(MaintenanceActivity.type_id == type_id)
            .order_by(MaintenanceActivity.activity_date.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()


maintenance_type = CRUDMaintenanceType(MaintenanceType)
maintenance_activity = CRUDMaintenanceActivity(MaintenanceActivity)