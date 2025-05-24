"""Split vine_inventory into vines and vine_locations tables

Revision ID: 002
Revises: 001
Create Date: 2025-01-24 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Split vine_inventory into vines and vine_locations tables"""
    
    # Create vines table with vine characteristics
    op.create_table('vines',
        sa.Column('vine_id', sa.Integer(), nullable=False),
        sa.Column('alpha_numeric_id', sa.String(length=50), nullable=True),
        sa.Column('year_of_planting', sa.Integer(), nullable=True),
        sa.Column('nursery', sa.String(length=255), nullable=True),
        sa.Column('variety', sa.String(length=255), nullable=True),
        sa.Column('rootstock', sa.String(length=255), nullable=True),
        sa.Column('is_dead', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('date_died', sa.DateTime(), nullable=True),
        sa.Column('record_created', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('vine_id')
    )
    
    # Add unique constraint for alpha_numeric_id only when it's not null
    op.create_index('idx_vines_alpha_numeric_id', 'vines', 
                   ['alpha_numeric_id'],
                   unique=True, 
                   postgresql_where="alpha_numeric_id IS NOT NULL")
    
    # Create vine_locations table with location information
    op.create_table('vine_locations',
        sa.Column('location_id', sa.Integer(), nullable=False),
        sa.Column('alpha_numeric_id', sa.String(length=50), nullable=True),
        sa.Column('vineyard_name', sa.String(length=255), nullable=True),
        sa.Column('field_name', sa.String(length=255), nullable=True),
        sa.Column('row_number', sa.Integer(), nullable=True),
        sa.Column('spot_number', sa.Integer(), nullable=True),
        sa.Column('year_of_planting', sa.Integer(), nullable=True),
        sa.Column('vine_id', sa.Integer(), nullable=True),
        sa.Column('record_created', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('location_id'),
        sa.ForeignKeyConstraint(['vine_id'], ['vines.vine_id'], ondelete='SET NULL')
    )
    
    # Add unique constraint for alpha_numeric_id only when it's not null
    op.create_index('idx_vine_locations_alpha_numeric_id', 'vine_locations', 
                   ['alpha_numeric_id'],
                   unique=True, 
                   postgresql_where="alpha_numeric_id IS NOT NULL")
    
    # Create unique constraint for position-based identification
    op.create_index('idx_unique_location_position', 'vine_locations', 
                   ['vineyard_name', 'field_name', 'row_number', 'spot_number'],
                   unique=True, 
                   postgresql_where="alpha_numeric_id IS NULL")
    
    # Migrate data from vine_inventory to new tables
    # First, insert vine data
    op.execute("""
        INSERT INTO vines (vine_id, alpha_numeric_id, year_of_planting, nursery, variety, rootstock, is_dead, date_died, record_created, updated_at)
        SELECT vine_id, alpha_numeric_id, year_of_planting, nursery, variety, rootstock, is_dead, date_died, record_created, updated_at
        FROM vine_inventory
    """)
    
    # Then, insert location data
    op.execute("""
        INSERT INTO vine_locations (alpha_numeric_id, vineyard_name, field_name, row_number, spot_number, year_of_planting, vine_id, record_created, updated_at)
        SELECT alpha_numeric_id, vineyard_name, field_name, row_number, spot_number, year_of_planting, vine_id, record_created, updated_at
        FROM vine_inventory
    """)
    
    # Drop foreign key constraints that reference vine_inventory before dropping the table
    op.drop_constraint('maintenance_activities_vine_id_fkey', 'maintenance_activities', type_='foreignkey')
    op.drop_constraint('vine_issues_vine_id_fkey', 'vine_issues', type_='foreignkey')
    
    # Check if inventory_checks table exists and has the constraint
    from sqlalchemy import text
    connection = op.get_bind()
    result = connection.execute(text("""
        SELECT constraint_name 
        FROM information_schema.table_constraints 
        WHERE table_name='inventory_checks' AND constraint_name='inventory_checks_vine_id_fkey'
    """))
    
    if result.fetchone():
        op.drop_constraint('inventory_checks_vine_id_fkey', 'inventory_checks', type_='foreignkey')
    
    # Drop the original vine_inventory table
    op.drop_table('vine_inventory')


def downgrade() -> None:
    """Recreate vine_inventory table from vines and vine_locations"""
    
    # Recreate the original vine_inventory table
    op.create_table('vine_inventory',
        sa.Column('vine_id', sa.Integer(), nullable=False),
        sa.Column('alpha_numeric_id', sa.String(length=50), nullable=True),
        sa.Column('year_of_planting', sa.Integer(), nullable=True),
        sa.Column('nursery', sa.String(length=255), nullable=True),
        sa.Column('variety', sa.String(length=255), nullable=True),
        sa.Column('rootstock', sa.String(length=255), nullable=True),
        sa.Column('vineyard_name', sa.String(length=255), nullable=True),
        sa.Column('field_name', sa.String(length=255), nullable=True),
        sa.Column('row_number', sa.Integer(), nullable=True),
        sa.Column('spot_number', sa.Integer(), nullable=True),
        sa.Column('is_dead', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('date_died', sa.DateTime(), nullable=True),
        sa.Column('record_created', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('vine_id')
    )
    
    # Recreate the unique constraint for alpha_numeric_id only when it's not null
    op.create_index('uq_vine_inventory_alpha_numeric_id', 'vine_inventory', 
                   ['alpha_numeric_id'],
                   unique=True, 
                   postgresql_where="alpha_numeric_id IS NOT NULL")
    
    # Recreate the unique constraint for position-based identification
    op.create_index('idx_unique_position', 'vine_inventory', 
                   ['vineyard_name', 'field_name', 'row_number', 'spot_number'],
                   unique=True, 
                   postgresql_where="alpha_numeric_id IS NULL")
    
    # Migrate data back from new tables to vine_inventory
    op.execute("""
        INSERT INTO vine_inventory (vine_id, alpha_numeric_id, year_of_planting, nursery, variety, rootstock, 
                                   vineyard_name, field_name, row_number, spot_number, is_dead, date_died, record_created, updated_at)
        SELECT v.vine_id, COALESCE(v.alpha_numeric_id, vl.alpha_numeric_id), COALESCE(v.year_of_planting, vl.year_of_planting), v.nursery, v.variety, v.rootstock,
               vl.vineyard_name, vl.field_name, vl.row_number, vl.spot_number, v.is_dead, v.date_died, v.record_created, v.updated_at
        FROM vines v
        LEFT JOIN vine_locations vl ON v.vine_id = vl.vine_id
    """)
    
    # Recreate the foreign key constraints
    op.create_foreign_key('maintenance_activities_vine_id_fkey', 'maintenance_activities', 'vine_inventory', ['vine_id'], ['vine_id'], ondelete='CASCADE')
    op.create_foreign_key('vine_issues_vine_id_fkey', 'vine_issues', 'vine_inventory', ['vine_id'], ['vine_id'], ondelete='CASCADE')
    
    # Check if inventory_checks table exists before creating constraint
    from sqlalchemy import text
    connection = op.get_bind()
    result = connection.execute(text("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_name='inventory_checks'
    """))
    
    if result.fetchone():
        op.create_foreign_key('inventory_checks_vine_id_fkey', 'inventory_checks', 'vine_inventory', ['vine_id'], ['vine_id'], ondelete='CASCADE')
    
    # Drop the new tables and their indexes
    op.drop_index('idx_unique_location_position', table_name='vine_locations')
    op.drop_index('idx_vine_locations_alpha_numeric_id', table_name='vine_locations')
    op.drop_index('idx_vines_alpha_numeric_id', table_name='vines')
    op.drop_table('vine_locations')
    op.drop_table('vines')