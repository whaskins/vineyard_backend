from typing import Any, Dict, List, Optional, Union

from fastapi.encoders import jsonable_encoder
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.vine import Vine
from app.schemas.vine import VineCreate, VineSearchParams, VineUpdate


class CRUDVine(CRUDBase[Vine, VineCreate, VineUpdate]):
    async def get_by_alpha_id(self, db: AsyncSession, *, alpha_id: str) -> Optional[Vine]:
        result = await db.execute(select(Vine).filter(Vine.alpha_numeric_id == alpha_id))
        return result.scalars().first()
    
    async def get_by_location(
        self, db: AsyncSession, *, field_name: str, row_number: int, spot_number: int
    ) -> List[Vine]:
        result = await db.execute(
            select(Vine).filter(
                and_(
                    Vine.field_name == field_name,
                    Vine.row_number == row_number,
                    Vine.spot_number == spot_number
                )
            )
        )
        return result.scalars().all()
    
    async def search(
        self, db: AsyncSession, *, params: VineSearchParams
    ) -> tuple[List[Vine], int]:
        """
        Search for vines with filters and pagination
        Returns a tuple of (results, total_count)
        """
        query = select(Vine)
        
        # Apply filters
        filters = []
        if params.alpha_numeric_id:
            filters.append(Vine.alpha_numeric_id.contains(params.alpha_numeric_id))
        if params.variety:
            filters.append(Vine.variety.contains(params.variety))
        if params.vineyard_name:
            filters.append(Vine.vineyard_name.contains(params.vineyard_name))
        if params.field_name:
            filters.append(Vine.field_name.contains(params.field_name))
        if params.row_number:
            filters.append(Vine.row_number == params.row_number)
        if params.is_dead is not None:
            filters.append(Vine.is_dead == params.is_dead)
        if params.year_min:
            filters.append(Vine.year_of_planting >= params.year_min)
        if params.year_max:
            filters.append(Vine.year_of_planting <= params.year_max)
        
        if filters:
            query = query.filter(and_(*filters))
        
        # Count total results for pagination
        count_query = select(func.count()).select_from(query.subquery())
        total = await db.execute(count_query)
        total_count = total.scalar()
        
        # Apply pagination
        skip = (params.page - 1) * params.items_per_page
        query = query.offset(skip).limit(params.items_per_page)
        
        # Execute query and return results with total count
        result = await db.execute(query)
        return result.scalars().all(), total_count
    
    async def create_or_update(
        self, db: AsyncSession, *, obj_in: Union[VineCreate, VineUpdate]
    ) -> Vine:
        """
        Create a new vine if it doesn't exist, otherwise update the existing one
        This is particularly useful for syncing from mobile devices
        """
        existing_vine = await self.get_by_alpha_id(db, alpha_id=obj_in.alpha_numeric_id)
        
        if existing_vine:
            # Handle both Pydantic v1 and v2
            if hasattr(obj_in, "model_dump"):
                # Pydantic v2
                obj_data = obj_in.model_dump(exclude_unset=True)
            else:
                # Pydantic v1
                obj_data = obj_in.dict(exclude_unset=True)
            # Update without going through the base class update method
            obj_data_encoded = jsonable_encoder(existing_vine)
            for field in obj_data_encoded:
                if field in obj_data:
                    setattr(existing_vine, field, obj_data[field])
            db.add(existing_vine)
            await db.commit()
            await db.refresh(existing_vine)
            return existing_vine
        else:
            return await self.create(db, obj_in=obj_in)


vine = CRUDVine(Vine)