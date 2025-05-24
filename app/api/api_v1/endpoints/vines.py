from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.crud import crud_vine
from app.models.user import User
from app.schemas.vine import Vine, VineCreate, VineSearchParams, VineUpdate, VineLocation, VineLocationCreate, VineLocationUpdate

router = APIRouter()


@router.get("/", response_model=List[Vine])
async def read_vines(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = Query(100, le=1000),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve all vines.
    """
    vines = await crud_vine.vine.get_multi_with_locations(db, skip=skip, limit=limit)
    return vines


@router.post("/search", response_model=Dict[str, Any])
async def search_vines(
    *,
    db: AsyncSession = Depends(deps.get_db),
    params: VineSearchParams,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Search vines with filters and pagination.
    """
    vines, total = await crud_vine.vine.search(db, params=params)
    return {
        "items": vines,
        "total": total,
        "page": params.page,
        "items_per_page": params.items_per_page,
        "pages": (total + params.items_per_page - 1) // params.items_per_page,
    }


@router.post("/", response_model=Vine)
async def create_vine(
    *,
    db: AsyncSession = Depends(deps.get_db),
    vine_in: VineCreate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create new vine.
    """
    # Check if vine with this ID already exists (only if alpha_numeric_id is provided)
    if vine_in.alpha_numeric_id:
        existing_vine = await crud_vine.vine.get_by_alpha_id(db, alpha_id=vine_in.alpha_numeric_id)
        if existing_vine:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Vine with ID {vine_in.alpha_numeric_id} already exists",
            )
    vine = await crud_vine.vine.create(db, obj_in=vine_in)
    return vine


@router.put("/sync", response_model=Vine)
async def sync_vine(
    *,
    db: AsyncSession = Depends(deps.get_db),
    vine_in: VineCreate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create or update a vine (for mobile app syncing).
    """
    vine = await crud_vine.vine.create_or_update(db, obj_in=vine_in)
    return vine


@router.get("/{vine_id}", response_model=Vine)
async def read_vine(
    *,
    db: AsyncSession = Depends(deps.get_db),
    vine_id: int,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get vine by ID.
    """
    vine = await crud_vine.vine.get(db, id=vine_id)
    if not vine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vine not found",
        )
    return vine


@router.get("/by-alpha-id/{alpha_id}", response_model=Vine)
async def read_vine_by_alpha_id(
    *,
    db: AsyncSession = Depends(deps.get_db),
    alpha_id: str,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get vine by alphanumeric ID.
    """
    vine = await crud_vine.vine.get_by_alpha_id(db, alpha_id=alpha_id)
    if not vine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vine not found",
        )
    return vine


@router.get("/by-location/{vineyard_name}/{field_name}/{row_number}/{spot_number}", response_model=VineLocation)
async def read_vine_location(
    *,
    db: AsyncSession = Depends(deps.get_db),
    vineyard_name: str,
    field_name: str,
    row_number: int,
    spot_number: int,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get vine location by position (vineyard, field, row, spot).
    """
    location = await crud_vine.vine_location.get_by_location(
        db, vineyard_name=vineyard_name, field_name=field_name, row_number=row_number, spot_number=spot_number
    )
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vine location not found",
        )
    return location


@router.put("/{vine_id}", response_model=Vine)
async def update_vine(
    *,
    db: AsyncSession = Depends(deps.get_db),
    vine_id: int,
    vine_in: VineUpdate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update a vine.
    """
    vine = await crud_vine.vine.get(db, id=vine_id)
    if not vine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vine not found",
        )
    vine = await crud_vine.vine.update(db, db_obj=vine, obj_in=vine_in)
    return vine


@router.delete("/{vine_id}", response_model=Vine)
async def delete_vine(
    *,
    db: AsyncSession = Depends(deps.get_db),
    vine_id: int,
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Delete a vine.
    """
    vine = await crud_vine.vine.get(db, id=vine_id)
    if not vine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vine not found",
        )
    vine = await crud_vine.vine.remove(db, id=vine_id)
    return vine


# Vine Location endpoints
@router.post("/locations/", response_model=VineLocation)
async def create_vine_location(
    *,
    db: AsyncSession = Depends(deps.get_db),
    location_in: VineLocationCreate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create new vine location.
    """
    location = await crud_vine.vine_location.create(db, obj_in=location_in)
    return location


@router.put("/locations/sync", response_model=VineLocation)
async def sync_vine_location(
    *,
    db: AsyncSession = Depends(deps.get_db),
    location_in: VineLocationCreate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create or update a vine location (for mobile app syncing vines without tags).
    """
    location = await crud_vine.vine_location.create_or_update_by_location(db, obj_in=location_in)
    return location


@router.get("/locations/{location_id}", response_model=VineLocation)
async def read_vine_location_by_id(
    *,
    db: AsyncSession = Depends(deps.get_db),
    location_id: int,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get vine location by ID.
    """
    location = await crud_vine.vine_location.get(db, id=location_id)
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vine location not found",
        )
    return location


@router.put("/locations/{location_id}", response_model=VineLocation)
async def update_vine_location(
    *,
    db: AsyncSession = Depends(deps.get_db),
    location_id: int,
    location_in: VineLocationUpdate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update a vine location.
    """
    location = await crud_vine.vine_location.get(db, id=location_id)
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vine location not found",
        )
    location = await crud_vine.vine_location.update(db, db_obj=location, obj_in=location_in)
    return location


@router.delete("/locations/{location_id}", response_model=VineLocation)
async def delete_vine_location(
    *,
    db: AsyncSession = Depends(deps.get_db),
    location_id: int,
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Delete a vine location.
    """
    location = await crud_vine.vine_location.get(db, id=location_id)
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vine location not found",
        )
    location = await crud_vine.vine_location.remove(db, id=location_id)
    return location