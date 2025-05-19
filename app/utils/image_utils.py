import base64
import os
import uuid
from datetime import datetime
from typing import Optional, Tuple, Dict, List
import magic
from PIL import Image, UnidentifiedImageError
from fastapi import HTTPException, UploadFile
import logging
from pathlib import Path

# Configure logger
logger = logging.getLogger(__name__)

# Define base directory for uploads
UPLOAD_DIR = Path("/app/app/static/uploads/images")

# Ensure the upload directory exists
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Define allowed mime types for images
ALLOWED_IMAGE_TYPES = {
    'image/jpeg': ['.jpg', '.jpeg'],
    'image/png': ['.png'],
    'image/gif': ['.gif'],
    'image/heic': ['.heic'],
    'image/heif': ['.heif'],
    'image/webp': ['.webp'],
    'image/tiff': ['.tiff', '.tif'],
}

# Define a max file size (5MB)
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB in bytes


def validate_image_file(file_content: bytes, content_type: Optional[str] = None) -> Tuple[str, str]:
    """
    Validate that the given file content is a valid image.
    Returns the detected mime type and appropriate file extension.
    Raises HTTPException if the file is not a valid image.
    """
    if not file_content:
        logger.error("Empty file content provided")
        raise HTTPException(status_code=400, detail="Empty file content")

    file_size = len(file_content)
    logger.info(f"Validating image file of size: {file_size} bytes")
    
    if file_size > MAX_FILE_SIZE:
        logger.error(f"File size {file_size} exceeds maximum size of {MAX_FILE_SIZE}")
        raise HTTPException(
            status_code=400, 
            detail=f"File size exceeds the maximum allowed size of {MAX_FILE_SIZE // (1024 * 1024)}MB"
        )

    # Use python-magic to detect the file type
    try:
        detected_type = magic.from_buffer(file_content, mime=True)
        logger.info(f"Detected file type using magic: {detected_type}")
    except Exception as e:
        logger.error(f"Error detecting file type with magic: {e}")
        # Check if content_type is provided and use that as a fallback
        if content_type:
            logger.info(f"Using provided content_type as fallback: {content_type}")
            # Strip away any parameters
            simple_content_type = content_type.split(';')[0].strip()
            # Check if it's in our allowed list
            if simple_content_type in ALLOWED_IMAGE_TYPES:
                logger.info(f"Content type {simple_content_type} is in allowed list")
                detected_type = simple_content_type
            else:
                logger.error(f"Provided content type {simple_content_type} not in allowed list")
                raise HTTPException(status_code=400, detail=f"Unsupported content type: {simple_content_type}")
        else:
            raise HTTPException(status_code=400, detail="Could not detect file type and no content type provided")

    logger.info(f"Detected file type: {detected_type}, provided content type: {content_type}")

    # Check if the detected type is allowed
    if detected_type not in ALLOWED_IMAGE_TYPES:
        valid_types = ", ".join(ALLOWED_IMAGE_TYPES.keys())
        logger.error(f"Unsupported file type: {detected_type}. Allowed types: {valid_types}")
        
        # Dump the first few bytes for debugging
        try:
            hex_dump = ' '.join([f'{b:02x}' for b in file_content[:50]])
            logger.info(f"File starts with bytes: {hex_dump}")
        except Exception as e:
            logger.error(f"Error creating hex dump: {e}")
            
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file type: {detected_type}. Allowed types: {valid_types}"
        )

    # Get the appropriate extension for the file type
    extension = ALLOWED_IMAGE_TYPES[detected_type][0]
    logger.info(f"Using file extension: {extension}")

    # Try to open the image with Pillow to verify it's a valid image
    try:
        from io import BytesIO
        img = Image.open(BytesIO(file_content))
        img.verify()  # Verify it's a valid image
        logger.info(f"Image verified successfully with Pillow")
    except UnidentifiedImageError:
        logger.error("Image could not be identified by Pillow")
        raise HTTPException(status_code=400, detail="Invalid image format")
    except Exception as e:
        logger.error(f"Error validating image with Pillow: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid image: {str(e)}")

    return detected_type, extension


async def save_uploaded_image(file_content: bytes, content_type: Optional[str] = None) -> Tuple[str, str, str]:
    """
    Save uploaded image to the filesystem.
    Returns the saved file path, filename, and detected content type.
    """
    # Validate the image
    mime_type, extension = validate_image_file(file_content, content_type)

    # Generate a unique filename
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    filename = f"issue_{timestamp}_{unique_id}{extension}"
    
    # Create a directory structure based on year/month
    year_month = datetime.utcnow().strftime("%Y/%m")
    relative_directory = Path(year_month)
    absolute_directory = UPLOAD_DIR / relative_directory
    absolute_directory.mkdir(parents=True, exist_ok=True)
    
    # Full path to the file
    file_path = absolute_directory / filename
    relative_path = relative_directory / filename
    
    # Save the file
    try:
        with open(file_path, "wb") as f:
            f.write(file_content)
        logger.info(f"Saved image to {file_path}")
    except Exception as e:
        logger.error(f"Error saving file: {e}")
        raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")
    
    return str(file_path), str(relative_path), mime_type


async def decode_base64_image(base64_string: str) -> bytes:
    """
    Decode a base64 encoded image.
    Returns the decoded image as bytes.
    """
    if not base64_string:
        raise HTTPException(status_code=400, detail="Empty base64 string")
    
    try:
        # Clean the string
        base64_string = base64_string.strip()
        
        # Remove data URL prefix if present
        if base64_string.startswith('data:'):
            # Format: data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEA...
            header, base64_string = base64_string.split(',', 1)
        
        # Add padding if needed
        padding = len(base64_string) % 4
        if padding > 0:
            base64_string += '=' * (4 - padding)
        
        # Decode the base64 string
        image_data = base64.b64decode(base64_string)
        return image_data
    
    except Exception as e:
        logger.error(f"Error decoding base64 image: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid base64 encoded image: {str(e)}")


async def process_uploaded_file(upload_file: UploadFile) -> Tuple[str, str, str]:
    """
    Process an uploaded file from FastAPI's UploadFile.
    """
    try:
        # Enhanced logging
        logger.info(f"Processing file: {upload_file.filename}, content_type: {upload_file.content_type}")
        
        # Read the file content
        contents = await upload_file.read()
        logger.info(f"Read {len(contents)} bytes from uploaded file")
        
        if len(contents) == 0:
            logger.error("File content is empty")
            raise ValueError("Empty file content")
            
        # Add more debugging about the file contents
        if len(contents) > 100:
            logger.info(f"File content starts with: {contents[:100]}")
            
        # Verify content type
        if not upload_file.content_type:
            try:
                import magic
                detected_type = magic.from_buffer(contents, mime=True)
                logger.info(f"Detected content type: {detected_type}")
            except Exception as e:
                logger.warning(f"Error detecting content type with magic: {e}")
                
        # Save the file
        result = await save_uploaded_image(contents, upload_file.content_type)
        logger.info(f"File saved successfully: {result[1]}")
        return result
    
    except Exception as e:
        logger.error(f"Error processing uploaded file: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=400, detail=f"Error processing uploaded file: {str(e)}")


def get_image_url(issue_id: int) -> str:
    """
    Generate a URL for retrieving an issue's image.
    """
    return f"/api/v1/issues/{issue_id}/photo"


def get_full_image_path(relative_path: str) -> str:
    """
    Get the full filesystem path from a relative path.
    """
    return str(UPLOAD_DIR / relative_path)