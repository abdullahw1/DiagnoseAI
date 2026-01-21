"""add_cascade_delete_to_foreign_keys

Revision ID: 00f61415c527
Revises: 562b70d02351
Create Date: 2026-01-18 12:13:15.627970

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '00f61415c527'
down_revision = '562b70d02351'
branch_labels = None
depends_on = None


def upgrade():
    # SQLite doesn't support ALTER COLUMN, so we need to recreate tables
    # For now, we'll handle this at the application level with explicit deletes
    # In production with PostgreSQL, you would use:
    # op.drop_constraint('fk_name', 'table_name', type_='foreignkey')
    # op.create_foreign_key('fk_name', 'table_name', 'referenced_table', ['column'], ['id'], ondelete='CASCADE')
    pass


def downgrade():
    pass
