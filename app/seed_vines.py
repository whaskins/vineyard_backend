import asyncio
import datetime
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.db.session import get_db
from app.models.vine import Vine

# Sample vines to add
SAMPLE_VINES = [
    {
        "alpha_numeric_id": "ID2023-02210",
        "year_of_planting": 2020,
        "nursery": "Vineyard Supply Co.",
        "variety": "Merlot",
        "rootstock": "1103P",
        "vineyard_name": "Main Vineyard",
        "field_name": "south",
        "row_number": 1,
        "spot_number": 1,
        "is_dead": False,
        "date_died": None,
        "record_created": datetime.datetime.now(),
    },
    {
        "alpha_numeric_id": "ID2023-02097",
        "year_of_planting": 2020,
        "nursery": "Vineyard Supply Co.",
        "variety": "Cabernet Sauvignon",
        "rootstock": "101-14",
        "vineyard_name": "Main Vineyard",
        "field_name": "south",
        "row_number": 9,
        "spot_number": 1,
        "is_dead": False,
        "date_died": None,
        "record_created": datetime.datetime.now(),
    },
    {
        "alpha_numeric_id": "ID2023-02098",
        "year_of_planting": 2020,
        "nursery": "Vineyard Supply Co.",
        "variety": "Cabernet Sauvignon",
        "rootstock": "101-14",
        "vineyard_name": "Main Vineyard",
        "field_name": "south",
        "row_number": 9,
        "spot_number": 2,
        "is_dead": False,
        "date_died": None,
        "record_created": datetime.datetime.now(),
    },
    {
        "alpha_numeric_id": "ID2023-02099",
        "year_of_planting": 2020,
        "nursery": "Vineyard Supply Co.",
        "variety": "Cabernet Sauvignon",
        "rootstock": "101-14",
        "vineyard_name": "Main Vineyard",
        "field_name": "south",
        "row_number": 9,
        "spot_number": 3,
        "is_dead": False,
        "date_died": None,
        "record_created": datetime.datetime.now(),
    },
    {
        "alpha_numeric_id": "ID2023-02100",
        "year_of_planting": 2020,
        "nursery": "Vineyard Supply Co.",
        "variety": "Cabernet Sauvignon",
        "rootstock": "101-14",
        "vineyard_name": "Main Vineyard",
        "field_name": "south",
        "row_number": 9,
        "spot_number": 4,
        "is_dead": False,
        "date_died": None,
        "record_created": datetime.datetime.now(),
    },
]

async def seed_vines():
    """Add sample vines to the database."""
    # Create engine with proper connection parameters
    engine = create_async_engine(
        "postgresql+asyncpg://postgres:postgres@db/postgres",
        pool_pre_ping=True,
        pool_recycle=1800,
        pool_size=3,
        max_overflow=5,
        pool_timeout=10,
        pool_reset_on_return=None,  # Critical for avoiding event loop issues
        connect_args={
            "command_timeout": 5,
            "server_settings": {
                "application_name": "vineyard_seeder",
                "idle_in_transaction_session_timeout": "5000",
            }
        }
    )
    
    # Create session maker
    db = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    # Create session
    async_session = db()
    
    try:
        print("Seeding vines...")
        
        # Insert each sample vine
        for vine_data in SAMPLE_VINES:
            vine = Vine(**vine_data)
            async_session.add(vine)
        
        # Commit the changes
        await async_session.commit()
        
        print(f"Added {len(SAMPLE_VINES)} sample vines to the database")
        
    except Exception as e:
        print(f"Error seeding vines: {e}")
        await async_session.rollback()
        raise
    finally:
        # Always close the session
        await async_session.close()
        # Dispose the engine to close all connections
        await engine.dispose()
        print("Database connections closed")

# Run the seeding function
if __name__ == "__main__":
    try:
        asyncio.run(seed_vines())
    except Exception as e:
        print(f"Fatal error during seeding: {e}")
        # Exit with error status
        import sys
        sys.exit(1)