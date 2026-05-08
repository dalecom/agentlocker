"""add open source fields

Revision ID: 20240320123456
Revises: d4782df1b631
Create Date: 2024-03-20 12:34:56.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20240320123456'
down_revision = 'd4782df1b631'
branch_labels = None
depends_on = None

def upgrade():
    with op.batch_alter_table('agent') as batch_op:
        batch_op.add_column(sa.Column('is_open_source', sa.Boolean(), nullable=False, server_default='false'))
        batch_op.add_column(sa.Column('source_repository', sa.String(length=255), nullable=True))

def downgrade():
    with op.batch_alter_table('agent') as batch_op:
        batch_op.drop_column('source_repository')
        batch_op.drop_column('is_open_source') 