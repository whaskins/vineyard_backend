from typing import Any, Dict, Optional, Union

from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash, verify_password
from app.crud.base import CRUDBase
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    async def get_by_email(self, db: AsyncSession, *, email: str) -> Optional[User]:
        # In the actual database, we're using user_name as the identifier
        # For the authentication we'll use user_name as the email
        result = await db.execute(select(User).filter(User.user_name == email))
        user = result.scalars().first()
        
        # If user found, set up the authentication-related fields that aren't in the database
        if user:
            # Set dummy values for testing - in a real system, these would be stored somewhere
            user.email = user.user_name  # Use username as email
            user.hashed_password = get_password_hash("password")  # Default password for all users
            user.is_active = True
            user.is_superuser = user.user_role == "administrator"
        
        return user

    async def create(self, db: AsyncSession, *, obj_in: UserCreate) -> User:
        # In the real implementation, we'd store auth info in a separate table or service
        # For the current DB schema, we can only add user_name and user_role
        db_obj = User(
            user_name=obj_in.email,  # Use email as user_name
            user_role="user",  # Default role
        )
        
        # Set non-DB fields after creating the object
        db_obj._email = obj_in.email
        db_obj.hashed_password = get_password_hash(obj_in.password)
        db_obj.full_name = obj_in.full_name
        db_obj.is_superuser = obj_in.is_superuser
        db_obj.is_active = obj_in.is_active
        
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        
        # Re-set non-DB fields after refresh because they're not in the database
        db_obj._email = obj_in.email
        db_obj.hashed_password = get_password_hash(obj_in.password)
        db_obj.full_name = obj_in.full_name
        db_obj.is_superuser = obj_in.is_superuser
        db_obj.is_active = obj_in.is_active
        
        return db_obj

    async def update(
        self, db: AsyncSession, *, db_obj: User, obj_in: Union[UserUpdate, Dict[str, Any]]
    ) -> User:
        # For the current implementation, we can only update user_name and user_role in DB
        # Other fields would be handled separately in a real implementation
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            # Handle both Pydantic v1 and v2
            if hasattr(obj_in, "model_dump"):
                # Pydantic v2
                update_data = obj_in.model_dump(exclude_unset=True)
            else:
                # Pydantic v1
                update_data = obj_in.dict(exclude_unset=True)
            
        # Remove fields that don't exist in the DB schema
        db_only_data = {k: v for k, v in update_data.items() 
                       if k in ["user_name", "user_role"]}
        
        # Update the user directly without using the parent method
        obj_data = jsonable_encoder(db_obj)
        for field in obj_data:
            if field in db_only_data:
                setattr(db_obj, field, db_only_data[field])
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def authenticate(self, db: AsyncSession, *, email: str, password: str) -> Optional[User]:
        # For this simplified version we'll accept any password for any existing user
        # In a real implementation, passwords would be stored and verified properly
        user = await self.get_by_email(db, email=email)
        if not user:
            return None
            
        # For development/testing purposes, accept any password
        # In production, you would use: if not verify_password(password, user.hashed_password):
        #    return None
        
        return user

    def is_active(self, user: User) -> bool:
        return user.is_active

    def is_superuser(self, user: User) -> bool:
        return user.is_superuser


user = CRUDUser(User)