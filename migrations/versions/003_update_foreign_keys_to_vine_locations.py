"""Update foreign keys to use vine_locations

Revision ID: 003
Revises: 002
Create Date: 2025-01-24 11:20:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade():
    """Update foreign keys to point to vine_locations instead of vines"""
    
    # First, we need to populate vine_location_id in existing records
    # For maintenance_activities, find the corresponding vine_location for each vine
    op.execute("""
        ALTER TABLE maintenance_activities 
        ADD COLUMN vine_location_id INTEGER;
    """)
    
    op.execute("""
        UPDATE maintenance_activities 
        SET vine_location_id = (
            SELECT vl.location_id 
            FROM vine_locations vl 
            WHERE vl.vine_id = maintenance_activities.vine_id
            LIMIT 1
        );
    """)
    
    # For vine_issues, do the same
    op.execute("""
        ALTER TABLE vine_issues 
        ADD COLUMN vine_location_id INTEGER;
    """)
    
    op.execute("""
        UPDATE vine_issues 
        SET vine_location_id = (
            SELECT vl.location_id 
            FROM vine_locations vl 
            WHERE vl.vine_id = vine_issues.vine_id
            LIMIT 1
        );
    """)
    
    # Now create the foreign key constraints
    op.create_foreign_key(
        'fk_maintenance_activities_vine_location_id',
        'maintenance_activities', 
        'vine_locations',
        ['vine_location_id'], 
        ['location_id'],
        ondelete='CASCADE'
    )
    
    op.create_foreign_key(
        'fk_vine_issues_vine_location_id',
        'vine_issues', 
        'vine_locations',
        ['vine_location_id'], 
        ['location_id'],
        ondelete='CASCADE'
    )
    
    # Drop the old foreign key constraints and columns
    # Note: SQLite doesn't support dropping foreign keys directly, 
    # so we'll keep the old vine_id columns for now but they won't be used


def downgrade():
    """Revert foreign keys back to vines table"""
    
    # Drop the new foreign key constraints
    op.drop_constraint('fk_maintenance_activities_vine_location_id', 'maintenance_activities', type_='foreignkey')
    op.drop_constraint('fk_vine_issues_vine_location_id', 'vine_issues', type_='foreignkey')
    
    # Drop the new columns
    op.drop_column('maintenance_activities', 'vine_location_id')
    op.drop_column('vine_issues', 'vine_location_id')