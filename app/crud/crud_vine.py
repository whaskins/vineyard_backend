from typing import Any, Dict, List, Optional, Union

from fastapi.encoders import jsonable_encoder
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.crud.base import CRUDBase
from app.models.vine import Vine, VineLocation
from app.schemas.vine import VineCreate, VineSearchParams, VineUpdate, VineLocationCreate, VineLocationUpdate


class CRUDVine(CRUDBase[Vine, VineCreate, VineUpdate]):
    async def create(self, db: AsyncSession, *, obj_in: Union[VineCreate, Dict[str, Any]]) -> Vine:
        if isinstance(obj_in, dict):
            obj_in_data = obj_in
        else:
            # Handle both Pydantic v1 and v2
            if hasattr(obj_in, "model_dump"):
                # Pydantic v2
                obj_in_data = obj_in.model_dump()
            else:
                # Pydantic v1
                obj_in_data = obj_in.dict()
        
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        
        # Reload with relationships to avoid lazy loading issues
        result = await db.execute(
            select(Vine)
            .options(selectinload(Vine.locations))
            .filter(Vine.id == db_obj.id)
        )
        return result.scalars().first()
    
    async def get(self, db: AsyncSession, id: Any) -> Optional[Vine]:
        result = await db.execute(
            select(Vine)
            .options(selectinload(Vine.locations))
            .filter(Vine.id == id)
        )
        return result.scalars().first()
    
    async def get_by_alpha_id(self, db: AsyncSession, *, alpha_id: str) -> Optional[Vine]:
        result = await db.execute(
            select(Vine)
            .options(selectinload(Vine.locations))
            .filter(Vine.alpha_numeric_id == alpha_id)
        )
        return result.scalars().first()
    
    async def get_multi_with_locations(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 1000
    ) -> List[Vine]:
        result = await db.execute(
            select(Vine)
            .options(selectinload(Vine.locations))
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def search(
        self, db: AsyncSession, *, params: VineSearchParams
    ) -> tuple[List[Vine], int]:
        """
        Search for vines with filters and pagination
        Returns a tuple of (results, total_count)
        """
        # Build base query with joins to vine_locations for location-based filtering
        query = select(Vine).options(selectinload(Vine.locations))
        
        # Apply filters
        filters = []
        if params.alpha_numeric_id:
            filters.append(Vine.alpha_numeric_id.contains(params.alpha_numeric_id))
        if params.variety:
            filters.append(Vine.variety.contains(params.variety))
        if params.is_dead is not None:
            filters.append(Vine.is_dead == params.is_dead)
        if params.year_min:
            filters.append(Vine.year_of_planting >= params.year_min)
        if params.year_max:
            filters.append(Vine.year_of_planting <= params.year_max)
        
        # Location-based filters require joining with vine_locations
        location_filters = []
        if params.vineyard_name:
            location_filters.append(VineLocation.vineyard_name.contains(params.vineyard_name))
        if params.field_name:
            location_filters.append(VineLocation.field_name.contains(params.field_name))
        if params.row_number:
            location_filters.append(VineLocation.row_number == params.row_number)
        
        if location_filters:
            query = query.join(VineLocation).filter(and_(*location_filters))
        
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
    
    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: Vine,
        obj_in: Union[VineUpdate, Dict[str, Any]]
    ) -> Vine:
        # Call the parent update method
        updated_obj = await super().update(db=db, db_obj=db_obj, obj_in=obj_in)
        
        # Reload with relationships to avoid lazy loading issues
        result = await db.execute(
            select(Vine)
            .options(selectinload(Vine.locations))
            .filter(Vine.id == updated_obj.id)
        )
        return result.scalars().first()


class CRUDVineLocation(CRUDBase[VineLocation, VineLocationCreate, VineLocationUpdate]):
    async def get_by_alpha_id(self, db: AsyncSession, *, alpha_id: str) -> Optional[VineLocation]:
        result = await db.execute(select(VineLocation).filter(VineLocation.alpha_numeric_id == alpha_id))
        return result.scalars().first()
    
    async def get_by_location(
        self, db: AsyncSession, *, vineyard_name: str, field_name: str, row_number: int, spot_number: int
    ) -> Optional[VineLocation]:
        result = await db.execute(
            select(VineLocation).filter(
                and_(
                    VineLocation.vineyard_name == vineyard_name,
                    VineLocation.field_name == field_name,
                    VineLocation.row_number == row_number,
                    VineLocation.spot_number == spot_number
                )
            )
        )
        return result.scalars().first()
    
    async def get_by_vine_id(self, db: AsyncSession, *, vine_id: int) -> List[VineLocation]:
        result = await db.execute(select(VineLocation).filter(VineLocation.vine_id == vine_id))
        return result.scalars().all()
    
    async def create_or_update_by_location(
        self, db: AsyncSession, *, obj_in: Union[VineLocationCreate, Dict[str, Any]]
    ) -> VineLocation:
        """
        Create or update a vine location based on location (vineyard, field, row, spot).
        This is used for vines without tags.
        """
        if isinstance(obj_in, dict):
            obj_in_data = obj_in
        else:
            # Handle both Pydantic v1 and v2
            if hasattr(obj_in, "model_dump"):
                # Pydantic v2
                obj_in_data = obj_in.model_dump()
            else:
                # Pydantic v1
                obj_in_data = obj_in.dict()
        
        # Check if a location already exists at this position
        existing_location = await self.get_by_location(
            db,
            vineyard_name=obj_in_data["vineyard_name"],
            field_name=obj_in_data["field_name"],
            row_number=obj_in_data["row_number"],
            spot_number=obj_in_data["spot_number"]
        )
        
        if existing_location:
            # Update existing location
            return await self.update(db=db, db_obj=existing_location, obj_in=obj_in)
        else:
            # Create new location
            return await self.create(db=db, obj_in=obj_in)


vine = CRUDVine(Vine)
vine_location = CRUDVineLocation(VineLocation)