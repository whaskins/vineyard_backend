from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.crud import crud_vine
from app.models.user import User
from app.schemas.vine import Vine, VineCreate, VineSearchParams, VineUpdate

router = APIRouter()


@router.get("/", response_model=List[Vine])
async def read_vines(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve all vines.
    """
    vines = await crud_vine.vine.get_multi(db, skip=skip, limit=limit)
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
    # Check if vine with this ID already exists
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


@router.get("/by-location/{field_name}/{row_number}/{spot_number}", response_model=List[Vine])
async def read_vine_by_location(
    *,
    db: AsyncSession = Depends(deps.get_db),
    field_name: str,
    row_number: int,
    spot_number: int,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get vines by location (field, row, spot).
    """
    vines = await crud_vine.vine.get_by_location(
        db, field_name=field_name, row_number=row_number, spot_number=spot_number
    )
    return vines


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