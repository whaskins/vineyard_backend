from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.crud import crud_maintenance, crud_vine
from app.models.user import User
from app.schemas.maintenance import (
    MaintenanceActivity,
    MaintenanceActivityCreate,
    MaintenanceActivityUpdate,
    MaintenanceActivityWithType,
    MaintenanceType,
    MaintenanceTypeCreate,
    MaintenanceTypeUpdate,
)

router = APIRouter()


# Maintenance Type endpoints
@router.get("/types", response_model=List[MaintenanceType])
async def read_maintenance_types(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve maintenance types.
    """
    types = await crud_maintenance.maintenance_type.get_multi(db, skip=skip, limit=limit)
    return types


@router.post("/types", response_model=MaintenanceType)
async def create_maintenance_type(
    *,
    db: AsyncSession = Depends(deps.get_db),
    type_in: MaintenanceTypeCreate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create new maintenance type.
    """
    # Check if type with this name already exists
    existing_type = await crud_maintenance.maintenance_type.get_by_name(db, name=type_in.name)
    if existing_type:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Maintenance type '{type_in.name}' already exists",
        )
    
    maintenance_type = await crud_maintenance.maintenance_type.create(db, obj_in=type_in)
    return maintenance_type


@router.get("/types/{type_id}", response_model=MaintenanceType)
async def read_maintenance_type(
    *,
    db: AsyncSession = Depends(deps.get_db),
    type_id: int,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get maintenance type by ID.
    """
    maintenance_type = await crud_maintenance.maintenance_type.get(db, id=type_id)
    if not maintenance_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Maintenance type not found",
        )
    return maintenance_type


@router.put("/types/{type_id}", response_model=MaintenanceType)
async def update_maintenance_type(
    *,
    db: AsyncSession = Depends(deps.get_db),
    type_id: int,
    type_in: MaintenanceTypeUpdate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update a maintenance type.
    """
    maintenance_type = await crud_maintenance.maintenance_type.get(db, id=type_id)
    if not maintenance_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Maintenance type not found",
        )
    
    # Check if name is being changed and if new name already exists
    if type_in.name and type_in.name != maintenance_type.name:
        existing_type = await crud_maintenance.maintenance_type.get_by_name(db, name=type_in.name)
        if existing_type:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Maintenance type '{type_in.name}' already exists",
            )
    
    maintenance_type = await crud_maintenance.maintenance_type.update(
        db, db_obj=maintenance_type, obj_in=type_in
    )
    return maintenance_type


@router.delete("/types/{type_id}", response_model=MaintenanceType)
async def delete_maintenance_type(
    *,
    db: AsyncSession = Depends(deps.get_db),
    type_id: int,
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Delete a maintenance type.
    """
    maintenance_type = await crud_maintenance.maintenance_type.get(db, id=type_id)
    if not maintenance_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Maintenance type not found",
        )
    maintenance_type = await crud_maintenance.maintenance_type.remove(db, id=type_id)
    return maintenance_type


# Maintenance Activity endpoints
@router.get("/activities", response_model=List[MaintenanceActivity])
async def read_maintenance_activities(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve maintenance activities.
    """
    activities = await crud_maintenance.maintenance_activity.get_multi(db, skip=skip, limit=limit)
    return activities


@router.post("/activities", response_model=MaintenanceActivity)
async def create_maintenance_activity(
    *,
    db: AsyncSession = Depends(deps.get_db),
    activity_in: MaintenanceActivityCreate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create new maintenance activity.
    """
    # Check if vine exists
    vine = await crud_vine.vine.get(db, id=activity_in.vine_id)
    if not vine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vine not found",
        )
    
    # Check if maintenance type exists
    maintenance_type = await crud_maintenance.maintenance_type.get(db, id=activity_in.type_id)
    if not maintenance_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Maintenance type not found",
        )
    
    activity = await crud_maintenance.maintenance_activity.create(db, obj_in=activity_in)
    return activity


@router.get("/activities/{activity_id}", response_model=MaintenanceActivity)
async def read_maintenance_activity(
    *,
    db: AsyncSession = Depends(deps.get_db),
    activity_id: int,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get maintenance activity by ID.
    """
    activity = await crud_maintenance.maintenance_activity.get(db, id=activity_id)
    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Maintenance activity not found",
        )
    return activity


@router.get("/activities/vine/{vine_id}", response_model=List[MaintenanceActivityWithType])
async def read_vine_maintenance_activities(
    *,
    db: AsyncSession = Depends(deps.get_db),
    vine_id: int,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get maintenance activities for a specific vine.
    """
    # Check if vine exists
    vine = await crud_vine.vine.get(db, id=vine_id)
    if not vine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vine not found",
        )
    
    activities = await crud_maintenance.maintenance_activity.get_by_vine_id(
        db, vine_id=vine_id, skip=skip, limit=limit
    )
    return activities


@router.put("/activities/{activity_id}", response_model=MaintenanceActivity)
async def update_maintenance_activity(
    *,
    db: AsyncSession = Depends(deps.get_db),
    activity_id: int,
    activity_in: MaintenanceActivityUpdate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update a maintenance activity.
    """
    activity = await crud_maintenance.maintenance_activity.get(db, id=activity_id)
    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Maintenance activity not found",
        )
    
    # Check if maintenance type exists if being updated
    if activity_in.type_id:
        maintenance_type = await crud_maintenance.maintenance_type.get(db, id=activity_in.type_id)
        if not maintenance_type:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Maintenance type not found",
            )
    
    activity = await crud_maintenance.maintenance_activity.update(
        db, db_obj=activity, obj_in=activity_in
    )
    return activity


@router.delete("/activities/{activity_id}", response_model=MaintenanceActivity)
async def delete_maintenance_activity(
    *,
    db: AsyncSession = Depends(deps.get_db),
    activity_id: int,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Delete a maintenance activity.
    """
    activity = await crud_maintenance.maintenance_activity.get(db, id=activity_id)
    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Maintenance activity not found",
        )
    activity = await crud_maintenance.maintenance_activity.remove(db, id=activity_id)
    return activity