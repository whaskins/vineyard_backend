# Import all the models here so that Alembic can detect them
from app.db.base_class import Base  # noqa
# Reorder imports to fix circular dependency issues
from app.models.user import User  # noqa
from app.models.maintenance import MaintenanceType, MaintenanceActivity  # noqa
from app.models.vine import Vine, VineLocation  # noqa
from app.models.issue import VineIssue  # noqa