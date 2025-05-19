from datetime import datetime
from typing import Any, List, Optional
import base64
import os
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import JSONResponse, Response

from app.api import deps
from app.crud import crud_issue, crud_user, crud_vine
from app.models.user import User
from app.schemas.issue import Issue, IssueCreate, IssueUpdate, IssueWithDetails, IssueWithPhoto
from app.utils.image_utils import decode_base64_image, save_uploaded_image, process_uploaded_file, get_full_image_path

router = APIRouter()


@router.get("/", response_model=List[Issue])
async def read_issues(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve issues.
    """
    issues = await crud_issue.issue.get_multi(db, skip=skip, limit=limit)
    return issues


@router.get("/with-details", response_model=List[IssueWithDetails])
async def read_issues_with_details(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve issues with detailed information (user names, vine IDs).
    """
    issues_with_details = await crud_issue.issue.get_multi_with_details(
        db, skip=skip, limit=limit
    )
    
    # Format the data for response
    result = []
    for issue, reporter, resolver, vine in issues_with_details:
        issue_data = Issue.model_validate(issue)
        issue_data_dict = issue_data.model_dump()
        issue_data_dict["reporter_name"] = reporter.full_name or reporter.email
        issue_data_dict["resolver_name"] = resolver.full_name or resolver.email if resolver else None
        issue_data_dict["vine_alpha_numeric_id"] = vine.alpha_numeric_id
        result.append(issue_data_dict)
    
    return result


@router.post("/", response_model=Issue)
async def create_issue(
    *,
    db: AsyncSession = Depends(deps.get_db),
    issue_in: IssueCreate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create new issue.
    """
    try:
        # Debug output
        print(f"DEBUG: Got issue create request with data: {issue_in.model_dump()}")
        print(f"DEBUG: Current user: {current_user.id}, {current_user.email}")
        print(f"DEBUG: reported_by: {getattr(issue_in, 'reported_by', None)}")
        print(f"DEBUG: reported_by_id: {getattr(issue_in, 'reported_by_id', None)}")
        print(f"DEBUG: Photo data provided: {getattr(issue_in, 'photo_data_base64', None) is not None}")
        
        # Check if vine exists
        vine = await crud_vine.vine.get(db, id=issue_in.vine_id)
        if not vine:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vine not found",
            )
        
        # Check if reporter exists - handle both field names
        reporter_id = getattr(issue_in, "reported_by", None)
        if reporter_id is None:
            reporter_id = getattr(issue_in, "reported_by_id", None)
        
        if reporter_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing required field reported_by or reported_by_id",
            )
        
        reporter = await crud_user.user.get(db, id=reporter_id)
        if not reporter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Reporting user with ID {reporter_id} not found",
            )
        
        # Check if resolver exists if provided - handle both field names
        resolver_id = getattr(issue_in, "resolved_by", None)
        if resolver_id is None:
            resolver_id = getattr(issue_in, "resolved_by_id", None)
        
        if resolver_id is not None:
            resolver = await crud_user.user.get(db, id=resolver_id)
            if not resolver:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Resolving user with ID {resolver_id} not found",
                )
        
        # Try to process the photo data if provided
        photo_data_base64 = getattr(issue_in, "photo_data_base64", None)
        if photo_data_base64:
            try:
                # Just try to decode it to check if it's valid
                if isinstance(photo_data_base64, str):
                    # Clean the string and ensure proper padding
                    photo_data_base64 = photo_data_base64.strip()
                    while len(photo_data_base64) % 4 != 0:
                        photo_data_base64 += "="
                        
                    # Test decode to validate
                    base64.b64decode(photo_data_base64)
                    print(f"DEBUG: Successfully validated base64 photo data of length {len(photo_data_base64)}")
                else:
                    print(f"DEBUG: Warning: photo_data_base64 is not a string, it's a {type(photo_data_base64)}")
            except Exception as e:
                print(f"ERROR: Invalid base64 photo data: {e}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid photo data: {str(e)}",
                )
        
        issue = await crud_issue.issue.create(db, obj_in=issue_in)
        return issue
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Handle any other exceptions
        print(f"ERROR creating issue: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating issue: {str(e)}",
        )


@router.get("/{issue_id}", response_model=Issue)
async def read_issue(
    *,
    db: AsyncSession = Depends(deps.get_db),
    issue_id: int,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get issue by ID.
    """
    issue = await crud_issue.issue.get(db, id=issue_id)
    if not issue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Issue not found",
        )
    return issue


@router.get("/{issue_id}/with-details", response_model=IssueWithDetails)
async def read_issue_with_details(
    *,
    db: AsyncSession = Depends(deps.get_db),
    issue_id: int,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get issue with detailed information (user names, vine ID).
    """
    issue_with_details = await crud_issue.issue.get_with_details(db, issue_id=issue_id)
    if not issue_with_details:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Issue not found",
        )
    
    issue, reporter, resolver, vine = issue_with_details
    
    # Format the data for response
    issue_data = Issue.model_validate(issue)
    issue_data_dict = issue_data.model_dump()
    issue_data_dict["reporter_name"] = reporter.full_name or reporter.email
    issue_data_dict["resolver_name"] = resolver.full_name or resolver.email if resolver else None
    issue_data_dict["vine_alpha_numeric_id"] = vine.alpha_numeric_id
    
    return issue_data_dict


@router.get("/vine/{vine_id}", response_model=List[Issue])
async def read_vine_issues(
    *,
    db: AsyncSession = Depends(deps.get_db),
    vine_id: int,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get issues for a specific vine.
    """
    # Check if vine exists
    vine = await crud_vine.vine.get(db, id=vine_id)
    if not vine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vine not found",
        )
    
    issues = await crud_issue.issue.get_by_vine_id(db, vine_id=vine_id, skip=skip, limit=limit)
    return issues


@router.get("/status/{is_resolved}", response_model=List[Issue])
async def read_issues_by_status(
    *,
    db: AsyncSession = Depends(deps.get_db),
    is_resolved: bool,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get issues filtered by resolution status.
    """
    issues = await crud_issue.issue.get_by_status(
        db, is_resolved=is_resolved, skip=skip, limit=limit
    )
    return issues


@router.put("/{issue_id}", response_model=Issue)
async def update_issue(
    *,
    db: AsyncSession = Depends(deps.get_db),
    issue_id: int,
    issue_in: IssueUpdate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update an issue.
    """
    try:
        # Debug output
        print(f"DEBUG: Got issue update request for ID {issue_id} with data: {issue_in.model_dump()}")
        print(f"DEBUG: Current user: {current_user.id}, {current_user.email}")
        print(f"DEBUG: Photo data provided: {getattr(issue_in, 'photo_data_base64', None) is not None}")
        
        issue = await crud_issue.issue.get(db, id=issue_id)
        if not issue:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Issue not found",
            )
        
        # Handle resolver_id if provided
        resolver_id = getattr(issue_in, "resolved_by", None)
        if resolver_id is None:
            resolver_id = getattr(issue_in, "resolved_by_id", None)
        
        if resolver_id is not None:
            resolver = await crud_user.user.get(db, id=resolver_id)
            if not resolver:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Resolving user with ID {resolver_id} not found",
                )
        
        # Try to process the photo data if provided
        photo_data_base64 = getattr(issue_in, "photo_data_base64", None)
        if photo_data_base64:
            try:
                # Just try to decode it to check if it's valid
                if isinstance(photo_data_base64, str):
                    # Clean the string and ensure proper padding
                    photo_data_base64 = photo_data_base64.strip()
                    while len(photo_data_base64) % 4 != 0:
                        photo_data_base64 += "="
                        
                    # Test decode to validate
                    base64.b64decode(photo_data_base64)
                    print(f"DEBUG: Successfully validated base64 photo data of length {len(photo_data_base64)}")
                else:
                    print(f"DEBUG: Warning: photo_data_base64 is not a string, it's a {type(photo_data_base64)}")
            except Exception as e:
                print(f"ERROR: Invalid base64 photo data: {e}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid photo data: {str(e)}",
                )
        
        # Convert to dictionary
        issue_in_dict = issue_in.model_dump(exclude_unset=True)
        
        # If both fields exist, ensure they're consistent
        if "resolved_by" in issue_in_dict and "resolved_by_id" in issue_in_dict:
            if issue_in_dict["resolved_by"] != issue_in_dict["resolved_by_id"]:
                issue_in_dict["resolved_by"] = issue_in_dict["resolved_by_id"]  # Use resolved_by_id as primary
        elif "resolved_by_id" in issue_in_dict and "resolved_by" not in issue_in_dict:
            issue_in_dict["resolved_by"] = issue_in_dict.pop("resolved_by_id")
            
        # If marking as resolved but no date_resolved provided, set it to now
        if issue_in.is_resolved and not issue_in.date_resolved:
            issue_in_dict["date_resolved"] = datetime.utcnow()
            
        # Update the issue
        issue = await crud_issue.issue.update(db, db_obj=issue, obj_in=issue_in_dict)
        
        return issue
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Handle any other exceptions
        print(f"ERROR updating issue: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating issue: {str(e)}",
        )


@router.put("/{issue_id}/upload", response_model=Issue)
async def update_issue_with_file(
    *,
    db: AsyncSession = Depends(deps.get_db),
    issue_id: int,
    description: Optional[str] = Form(None),
    is_resolved: Optional[bool] = Form(None),
    photo: Optional[UploadFile] = None,
    resolved_by: Optional[int] = Form(None),
    resolved_by_id: Optional[int] = Form(None),  # Support both field names
    date_resolved: Optional[datetime] = Form(None),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update an issue with file upload.
    """
    # Process the photo outside of database transaction if provided
    photo_info = None
    if photo:
        try:
            # Import the utilities for processing uploaded files
            from app.utils.image_utils import process_uploaded_file
            
            # Process the photo - this doesn't use the database
            photo_info = await process_uploaded_file(photo)
            print(f"DEBUG: Successfully prepared photo for upload to {photo_info[0]}")
        except Exception as e:
            print(f"ERROR processing photo: {e}")
            import traceback
            traceback.print_exc()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error processing photo: {str(e)}",
            )
    
    try:
        # Debug output
        print(f"DEBUG: Got issue update request with file upload for ID {issue_id}")
        print(f"DEBUG: description: {description}, is_resolved: {is_resolved}")
        print(f"DEBUG: resolved_by: {resolved_by}, resolved_by_id: {resolved_by_id}")
        print(f"DEBUG: photo provided: {photo is not None}")
        
        # Resolve the resolver ID field
        effective_resolver_id = resolved_by if resolved_by is not None else resolved_by_id
        print(f"DEBUG: Using effective resolver ID: {effective_resolver_id}")
        
        # Get the issue
        issue = await crud_issue.issue.get(db, id=issue_id)
        if not issue:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Issue not found",
            )
        
        # Create the update data with non-null values
        update_data = {}
        if description is not None:
            update_data["description"] = description
        if is_resolved is not None:
            update_data["is_resolved"] = is_resolved
        if effective_resolver_id is not None:
            update_data["resolved_by"] = effective_resolver_id
        if date_resolved is not None:
            update_data["date_resolved"] = date_resolved
            
        # If marking as resolved but no date_resolved provided, set it to now
        if is_resolved and not date_resolved and not issue.date_resolved:
            update_data["date_resolved"] = datetime.utcnow()
        
        # Add the photo information to the update data if we processed a photo
        if photo_info:
            full_path, relative_path, content_type = photo_info
            update_data["photo_path"] = relative_path
            update_data["photo_content_type"] = content_type
            update_data["photo_data"] = None  # Clear any existing photo data
            print(f"DEBUG: Photo metadata added to update: {relative_path}, {content_type}")
        
        # Update the issue
        issue = await crud_issue.issue.update(db, db_obj=issue, obj_in=update_data)
        return issue
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Handle any other exceptions
        print(f"ERROR updating issue with file upload: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating issue: {str(e)}",
        )


@router.delete("/{issue_id}", response_model=Issue)
async def delete_issue(
    *,
    db: AsyncSession = Depends(deps.get_db),
    issue_id: int,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Delete an issue.
    """
    issue = await crud_issue.issue.get(db, id=issue_id)
    if not issue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Issue not found",
        )
    
    # Only allow superusers or the reporter to delete
    if not crud_user.user.is_superuser(current_user) and issue.reported_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to delete this issue",
        )
    
    issue = await crud_issue.issue.remove(db, id=issue_id)
    return issue


@router.get("/{issue_id}/photo", response_class=Response)
async def get_issue_photo(
    *,
    db: AsyncSession = Depends(deps.get_db),
    issue_id: int,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get issue photo as image.
    """
    # First get the issue metadata only
    issue = None
    photo_path = None
    photo_content_type = None
    photo_data = None
    
    try:
        # Get the issue with required fields only to minimize DB interaction time
        issue = await crud_issue.issue.get(db, id=issue_id)
        if not issue:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Issue not found",
            )
        
        # Store the photo information and close the database connection as soon as possible
        photo_path = issue.photo_path
        photo_content_type = issue.photo_content_type or "image/jpeg"
        photo_data = issue.photo_data
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        print(f"ERROR retrieving issue metadata: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving issue metadata: {str(e)}",
        )
    
    # Now process the file outside the database transaction
    try:
        from pathlib import Path
        from app.utils.image_utils import get_full_image_path
        import os
        
        # Try to serve the file from disk first
        if photo_path:
            try:
                # Construct the full path to the image file
                file_path = get_full_image_path(photo_path)
                
                print(f"DEBUG: Attempting to read image file from: {file_path}")
                
                # Check if the file exists
                if os.path.exists(file_path):
                    with open(file_path, "rb") as f:
                        file_content = f.read()
                    
                    print(f"DEBUG: Successfully read image file from disk: {len(file_content)} bytes")
                    return Response(content=file_content, media_type=photo_content_type)
            except Exception as e:
                print(f"ERROR reading image file from disk: {str(e)}")
                # If file read fails, we'll fall back to the database blob if available
        
        # Fall back to the database blob if available
        if photo_data:
            # Validate photo data
            if len(photo_data) < 10:  # Arbitrary small size that's unlikely for a real image
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Photo data appears to be corrupt or incomplete",
                )
            
            return Response(content=photo_data, media_type=photo_content_type)
        
        # If we get here, no photo is available
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No photo available for this issue",
        )
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Handle any other exceptions
        print(f"ERROR retrieving photo: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving photo: {str(e)}",
        )


@router.post("/upload", response_model=Issue)
async def create_issue_with_file(
    *,
    db: AsyncSession = Depends(deps.get_db),
    vine_id: int = Form(...),
    description: str = Form(...),
    reported_by: Optional[int] = Form(None),
    reported_by_id: Optional[int] = Form(None),  # Support both field names
    is_resolved: bool = Form(False),
    photo: Optional[UploadFile] = None,
    resolved_by: Optional[int] = Form(None),
    resolved_by_id: Optional[int] = Form(None),  # Support both field names
    date_reported: Optional[str] = Form(None),  # Added for Flutter app compatibility
    date_resolved: Optional[datetime] = Form(None),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create a new issue with file upload.
    """
    # Enhanced debugging for form data
    print(f"DEBUG: Form data received:")
    print(f"DEBUG: vine_id: {vine_id}, type: {type(vine_id)}")
    print(f"DEBUG: description: {description}, type: {type(description)}")
    print(f"DEBUG: reported_by: {reported_by}, type: {type(reported_by)}")
    print(f"DEBUG: reported_by_id: {reported_by_id}, type: {type(reported_by_id)}")
    print(f"DEBUG: is_resolved: {is_resolved}, type: {type(is_resolved)}")
    print(f"DEBUG: resolved_by: {resolved_by}, type: {type(resolved_by)}")
    print(f"DEBUG: resolved_by_id: {resolved_by_id}, type: {type(resolved_by_id)}")
    print(f"DEBUG: date_reported: {date_reported}, type: {type(date_reported)}")
    print(f"DEBUG: date_resolved: {date_resolved}, type: {type(date_resolved)}")
    
    # Resolve the reporter ID using either field
    effective_reporter_id = reported_by if reported_by is not None else reported_by_id
    
    # If reporter ID is still None, use the current user's ID as a fallback
    if effective_reporter_id is None:
        effective_reporter_id = current_user.id
        print(f"DEBUG: Using current user ID as reporter: {effective_reporter_id}")
    
    print(f"DEBUG: Using effective reporter ID: {effective_reporter_id}")
    
    # Resolve the resolver ID using either field
    effective_resolver_id = resolved_by if resolved_by is not None else resolved_by_id
    print(f"DEBUG: Using effective resolver ID: {effective_resolver_id}")
    
    # Enhanced photo debugging
    if photo:
        print(f"DEBUG: Photo details:")
        print(f"DEBUG: filename: {photo.filename}")
        print(f"DEBUG: content_type: {photo.content_type}")
        try:
            size = 0
            chunk = await photo.read(1024)
            while chunk:
                size += len(chunk)
                chunk = await photo.read(1024)
            await photo.seek(0)  # Reset file pointer to beginning
            print(f"DEBUG: file size: {size} bytes")
        except Exception as e:
            print(f"DEBUG: Error reading photo size: {e}")
    else:
        print(f"DEBUG: No photo provided")
    
    # Process the photo outside of database transaction if provided
    photo_info = None
    if photo:
        try:
            # Import the utilities for processing uploaded files
            from app.utils.image_utils import process_uploaded_file
            
            # Process the photo - this doesn't use the database
            photo_info = await process_uploaded_file(photo)
            print(f"DEBUG: Successfully prepared photo for upload to {photo_info[0]}")
        except Exception as e:
            print(f"ERROR processing photo: {e}")
            import traceback
            traceback.print_exc()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error processing photo: {str(e)}",
            )
    
    try:
        # Check if vine exists
        vine = await crud_vine.vine.get(db, id=vine_id)
        if not vine:
            print(f"DEBUG: Vine with ID {vine_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vine not found",
            )
        print(f"DEBUG: Vine found: {vine.alpha_numeric_id}")
        
        # Check if reporter exists
        reporter = await crud_user.user.get(db, id=effective_reporter_id)
        if not reporter:
            print(f"DEBUG: User with ID {effective_reporter_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Reporting user with ID {effective_reporter_id} not found",
            )
        print(f"DEBUG: Reporter found: {reporter.email}")
        
        # Create the issue data
        issue_data = {
            "vine_id": vine_id,
            "description": description,
            "reported_by": effective_reporter_id,
            "is_resolved": is_resolved,
            "resolved_by": effective_resolver_id,
            "date_resolved": date_resolved,
        }
        
        # Add the photo information to the issue data if we processed a photo
        if photo_info:
            full_path, relative_path, content_type = photo_info
            issue_data["photo_path"] = relative_path
            issue_data["photo_content_type"] = content_type
            print(f"DEBUG: Photo metadata added to issue: {relative_path}, {content_type}")
        
        # Create the issue
        print(f"DEBUG: Creating issue with data: {issue_data}")
        issue = await crud_issue.issue.create(db, obj_in=issue_data)
        print(f"DEBUG: Issue created successfully with ID: {issue.id}")
        return issue
        
    except HTTPException as e:
        # Enhanced HTTP exception logging
        print(f"DEBUG: HTTP Exception: {e.status_code} - {e.detail}")
        raise
    except Exception as e:
        # Handle any other exceptions
        print(f"ERROR creating issue with file upload: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating issue: {str(e)}",
        )


@router.get("/{issue_id}/with-photo", response_model=IssueWithPhoto)
async def read_issue_with_photo(
    *,
    db: AsyncSession = Depends(deps.get_db),
    issue_id: int,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get issue with photo data in base64 format.
    """
    try:
        issue = await crud_issue.issue.get(db, id=issue_id)
        if not issue:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Issue not found",
            )
        
        issue_data = Issue.model_validate(issue).model_dump()
        
        # Add base64 encoded photo data if available
        if issue.photo_data:
            try:
                # Encode photo data to base64
                base64_data = base64.b64encode(issue.photo_data).decode("utf-8")
                issue_data["photo_data_base64"] = base64_data
                print(f"DEBUG: Successfully encoded photo data to base64 string of length {len(base64_data)}")
            except Exception as e:
                print(f"ERROR encoding photo data to base64: {str(e)}")
                # Don't fail the request, just don't include the photo data
                issue_data["photo_data_base64"] = None
        
        return issue_data
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Handle any other exceptions
        print(f"ERROR retrieving issue with photo: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving issue with photo: {str(e)}",
        )