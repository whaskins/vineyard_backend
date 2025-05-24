"""Allow vines without QR tags

Revision ID: 001
Revises: 
Create Date: 2025-01-22 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Make alpha_numeric_id nullable and add unique constraint for position-based identification"""
    
    # Make alpha_numeric_id nullable
    op.alter_column('vine_inventory', 'alpha_numeric_id',
                   existing_type=sa.VARCHAR(length=50),
                   nullable=True)
    
    # Make other fields nullable to match the application models
    op.alter_column('vine_inventory', 'year_of_planting',
                   existing_type=sa.INTEGER(),
                   nullable=True)
    
    op.alter_column('vine_inventory', 'nursery',
                   existing_type=sa.VARCHAR(length=255),
                   nullable=True)
    
    op.alter_column('vine_inventory', 'variety',
                   existing_type=sa.VARCHAR(length=255),
                   nullable=True)
    
    op.alter_column('vine_inventory', 'rootstock',
                   existing_type=sa.VARCHAR(length=255),
                   nullable=True)
    
    op.alter_column('vine_inventory', 'vineyard_name',
                   existing_type=sa.VARCHAR(length=255),
                   nullable=True)
    
    op.alter_column('vine_inventory', 'field_name',
                   existing_type=sa.VARCHAR(length=255),
                   nullable=True)
    
    op.alter_column('vine_inventory', 'row_number',
                   existing_type=sa.INTEGER(),
                   nullable=True)
    
    op.alter_column('vine_inventory', 'spot_number',
                   existing_type=sa.INTEGER(),
                   nullable=True)
    
    # Add unique constraint for position-based identification (for vines without tags)
    # This allows multiple NULL alpha_numeric_ids but ensures unique positions
    op.create_index('idx_unique_position', 'vine_inventory', 
                   ['vineyard_name', 'field_name', 'row_number', 'spot_number'],
                   unique=True, 
                   postgresql_where="alpha_numeric_id IS NULL")
    
    # Add updated_at column if it doesn't exist
    # Check if column exists before adding it
    from sqlalchemy import text
    connection = op.get_bind()
    result = connection.execute(text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='vine_inventory' AND column_name='updated_at'
    """))
    
    if not result.fetchone():
        op.add_column('vine_inventory', sa.Column('updated_at', sa.DateTime(), 
                                                 server_default=sa.text('CURRENT_TIMESTAMP'), 
                                                 nullable=False))


def downgrade() -> None:
    """Revert changes - make alpha_numeric_id not nullable again"""
    
    # Remove the updated_at column if it exists
    from sqlalchemy import text
    connection = op.get_bind()
    result = connection.execute(text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='vine_inventory' AND column_name='updated_at'
    """))
    
    if result.fetchone():
        op.drop_column('vine_inventory', 'updated_at')
    
    # Remove the unique constraint for position-based identification
    op.drop_index('idx_unique_position', table_name='vine_inventory')
    
    # Make alpha_numeric_id not nullable again
    op.alter_column('vine_inventory', 'alpha_numeric_id',
                   existing_type=sa.VARCHAR(length=50),
                   nullable=False)
    
    # Make other fields not nullable to match original schema
    op.alter_column('vine_inventory', 'year_of_planting',
                   existing_type=sa.INTEGER(),
                   nullable=False)
    
    op.alter_column('vine_inventory', 'nursery',
                   existing_type=sa.VARCHAR(length=255),
                   nullable=False)
    
    op.alter_column('vine_inventory', 'variety',
                   existing_type=sa.VARCHAR(length=255),
                   nullable=False)
    
    op.alter_column('vine_inventory', 'rootstock',
                   existing_type=sa.VARCHAR(length=255),
                   nullable=False)
    
    op.alter_column('vine_inventory', 'vineyard_name',
                   existing_type=sa.VARCHAR(length=255),
                   nullable=False)
    
    op.alter_column('vine_inventory', 'field_name',
                   existing_type=sa.VARCHAR(length=255),
                   nullable=False)
    
    op.alter_column('vine_inventory', 'row_number',
                   existing_type=sa.INTEGER(),
                   nullable=False)
    
    op.alter_column('vine_inventory', 'spot_number',
                   existing_type=sa.INTEGER(),
                   nullable=False)