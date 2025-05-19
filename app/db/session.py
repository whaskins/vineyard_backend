from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_scoped_session
from sqlalchemy.orm import sessionmaker
import logging
import asyncio
from asyncio import current_task

from app.core.config import settings

logger = logging.getLogger(__name__)

# Configure more aggressive connection recycling
engine = create_async_engine(
    str(settings.DATABASE_URL), 
    echo=settings.DEBUG,
    future=True,
    pool_pre_ping=True,         # Check if connection is still alive
    pool_recycle=1800,          # Recycle connections after 30 minutes
    pool_size=5,                # Reduce pool size to avoid leaks
    max_overflow=10,            # Allow some overflow
    pool_timeout=10,            # Timeout for getting a connection from pool - reduced from 20s
    pool_use_lifo=True,         # Use LIFO (last in, first out) for better performance
    # Critical fix for "Event loop is closed" errors during garbage collection
    pool_reset_on_return=None,  # Don't reset connections on return to avoid event loop issues
    connect_args={
        "command_timeout": 5,   # Command timeout in seconds
        # Handle connection termination during shutdown
        "server_settings": {
            "application_name": "vineyard_backend",
            "idle_in_transaction_session_timeout": "5000",  # 5 seconds - reduced from 10s
            "statement_timeout": "15000",  # Statement timeout in milliseconds (15 sec)
        }
    }
)

# Create a factory for scoped sessions
async_session_factory = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine, 
    class_=AsyncSession,
    expire_on_commit=False,
)

# Use async_scoped_session to create scoped sessions tied to the current task
AsyncSessionLocal = async_scoped_session(
    async_session_factory,
    scopefunc=current_task
)


async def get_db() -> AsyncSession:
    """
    Dependency function that yields db sessions
    """
    session = AsyncSessionLocal()
    try:
        yield session
    except Exception as e:
        logger.error(f"Session error: {str(e)}")
        await session.rollback()  # Roll back transaction on error
        raise
    finally:
        try:
            await session.close()
            logger.debug("Database session closed successfully")
        except Exception as e:
            logger.error(f"Error closing database session: {str(e)}")
        finally:
            # Explicitly remove it from the registry
            AsyncSessionLocal.remove()


# Define a function to close the SQLAlchemy connection pool on shutdown
async def close_db_connection():
    """Close all connections in the pool on application shutdown."""
    logger.info("Closing database connections...")
    try:
        # First remove all sessions from the registry
        AsyncSessionLocal.remove()
        
        # Set a short timeout for connection closure
        await asyncio.wait_for(engine.dispose(), timeout=5.0)
        logger.info("Database connections closed successfully.")
    except asyncio.TimeoutError:
        logger.warning("Timeout while closing database connections")
    except RuntimeError as e:
        if "Event loop is closed" in str(e):
            # This is expected during shutdown, just log it
            logger.info("Event loop closed during connection disposal")
        else:
            logger.error(f"RuntimeError closing connections: {str(e)}")
    except Exception as e:
        logger.error(f"Error closing database connections: {str(e)}")
        
# Create a sync version for use during garbage collection or sync contexts
def sync_close_db_connection():
    """Synchronous version of close_db_connection for use in sync contexts."""
    logger.info("Synchronously closing database connections...")
    try:
        # Just remove all sessions from the registry
        AsyncSessionLocal.remove()
        logger.info("Session registry cleared.")
    except Exception as e:
        logger.error(f"Error clearing session registry: {str(e)}")