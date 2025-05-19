from typing import List, Optional, Tuple, Any, Dict, Union
import base64
import os
import logging

from fastapi.encoders import jsonable_encoder
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased, joinedload
from app.utils.image_utils import (
    decode_base64_image, 
    save_uploaded_image, 
    get_image_url
)

from app.crud.base import CRUDBase
from app.models.issue import VineIssue
from app.models.user import User
from app.models.vine import Vine
from app.schemas.issue import IssueCreate, IssueUpdate


class CRUDIssue(CRUDBase[VineIssue, IssueCreate, IssueUpdate]):
    # Override create method to handle photo data
    async def create(self, db: AsyncSession, *, obj_in: Union[IssueCreate, Dict[str, Any]]) -> VineIssue:
        # Process the issue data
        if isinstance(obj_in, dict):
            obj_in_data = obj_in.copy()
        else:
            # If it's a Pydantic model, use model_dump (new in v2) or fall back to dict (v1)
            if hasattr(obj_in, "model_dump"):
                obj_in_data = obj_in.model_dump(exclude_unset=True)
            else:
                obj_in_data = obj_in.dict(exclude_unset=True)
        
        # Handle field name compatibility for reported_by_id
        if "reported_by_id" in obj_in_data:
            if obj_in_data.get("reported_by") is None:
                obj_in_data["reported_by"] = obj_in_data.pop("reported_by_id")
            else:
                # If both fields exist, make sure they're consistent
                if obj_in_data["reported_by"] != obj_in_data["reported_by_id"]:
                    obj_in_data["reported_by"] = obj_in_data.pop("reported_by_id")
                else:
                    # If they're the same, just remove the redundant field
                    obj_in_data.pop("reported_by_id")
        
        # Handle photo data if provided
        photo_data_base64 = obj_in_data.pop("photo_data_base64", None)
        if photo_data_base64:
            try:
                # Decode base64 to binary
                image_data = await decode_base64_image(photo_data_base64)
                
                # Save the file to disk
                full_path, relative_path, content_type = await save_uploaded_image(
                    image_data, obj_in_data.get('photo_content_type')
                )
                
                # Update issue with file information
                obj_in_data["photo_path"] = relative_path
                obj_in_data["photo_content_type"] = content_type
                
                # We no longer store the full image data in the database
                obj_in_data["photo_data"] = None
                
                print(f"DEBUG: Successfully saved image to {full_path}")
                print(f"DEBUG: Relative path saved to DB: {relative_path}")
            except Exception as e:
                print(f"Error processing photo data: {e}")
                # If there's an error, we won't set any photo fields
        
        # Create the issue using the parent class method with the dictionary
        # We need to pass the dictionary directly instead of through obj_in
        # to avoid the parent class trying to call .dict() on it again
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    # Override update method to handle photo data
    async def update(
        self, db: AsyncSession, *, db_obj: VineIssue, obj_in: Union[IssueUpdate, Dict[str, Any]]
    ) -> VineIssue:
        if isinstance(obj_in, dict):
            update_data = obj_in.copy()
        else:
            # If it's a Pydantic model, use model_dump (new in v2) or fall back to dict (v1)
            if hasattr(obj_in, "model_dump"):
                update_data = obj_in.model_dump(exclude_unset=True)
            else:
                update_data = obj_in.dict(exclude_unset=True)
        
        # Handle field name compatibility for resolved_by_id
        if "resolved_by_id" in update_data:
            if update_data.get("resolved_by") is None:
                update_data["resolved_by"] = update_data.pop("resolved_by_id")
            else:
                # If both fields exist, make sure they're consistent
                if update_data["resolved_by"] != update_data["resolved_by_id"]:
                    update_data["resolved_by"] = update_data.pop("resolved_by_id")
                else:
                    # If they're the same, just remove the redundant field
                    update_data.pop("resolved_by_id")
        
        # Handle photo data if provided
        photo_data_base64 = update_data.pop("photo_data_base64", None)
        if photo_data_base64:
            try:
                # Decode base64 to binary
                image_data = await decode_base64_image(photo_data_base64)
                
                # Save the file to disk
                full_path, relative_path, content_type = await save_uploaded_image(
                    image_data, update_data.get('photo_content_type')
                )
                
                # Update issue with file information
                update_data["photo_path"] = relative_path
                update_data["photo_content_type"] = content_type
                
                # We no longer store the full image data in the database
                update_data["photo_data"] = None
                
                print(f"DEBUG: Successfully saved image to {full_path}")
                print(f"DEBUG: Relative path saved to DB: {relative_path}")
            except Exception as e:
                print(f"Error processing photo data: {e}")
                # If there's an error, we won't set any photo fields
        
        # Update the issue using direct attribute setting instead of parent method
        # to avoid the parent class trying to call .dict() on the dictionary again
        obj_data = jsonable_encoder(db_obj)
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def get_by_vine_id(
        self, db: AsyncSession, *, vine_id: int, skip: int = 0, limit: int = 100
    ) -> List[VineIssue]:
        result = await db.execute(
            select(VineIssue)
            .filter(VineIssue.vine_id == vine_id)
            .order_by(VineIssue.date_reported.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_by_status(
        self, db: AsyncSession, *, is_resolved: bool, skip: int = 0, limit: int = 100
    ) -> List[VineIssue]:
        result = await db.execute(
            select(VineIssue)
            .filter(VineIssue.is_resolved == is_resolved)
            .order_by(VineIssue.date_reported.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_with_details(
        self, db: AsyncSession, *, issue_id: int
    ) -> Optional[Tuple[VineIssue, User, Optional[User], Vine]]:
        """Get issue with reporter, resolver, and vine details"""
        reporter = aliased(User)
        resolver = aliased(User)
        
        result = await db.execute(
            select(VineIssue, reporter, resolver, Vine)
            .join(reporter, VineIssue.reported_by == reporter.id)
            .outerjoin(resolver, VineIssue.resolved_by == resolver.id)
            .join(Vine, VineIssue.vine_id == Vine.id)
            .filter(VineIssue.id == issue_id)
        )
        
        row = result.first()
        if not row:
            return None
        
        return row
    
    async def get_multi_with_details(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> List[Tuple[VineIssue, User, Optional[User], Vine]]:
        """Get multiple issues with reporter, resolver, and vine details"""
        reporter = aliased(User)
        resolver = aliased(User)
        
        result = await db.execute(
            select(VineIssue, reporter, resolver, Vine)
            .join(reporter, VineIssue.reported_by == reporter.id)
            .outerjoin(resolver, VineIssue.resolved_by == resolver.id)
            .join(Vine, VineIssue.vine_id == Vine.id)
            .order_by(VineIssue.date_reported.desc())
            .offset(skip)
            .limit(limit)
        )
        
        return result.all()


issue = CRUDIssue(VineIssue)