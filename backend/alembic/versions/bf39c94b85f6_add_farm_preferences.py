"""add farm preferences

Revision ID: bf39c94b85f6
Revises: 0001
Create Date: 2025-10-12 18:11:53.398986

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.sqlite import JSON as SQLITE_JSON


# revision identifiers, used by Alembic.
revision: str = 'bf39c94b85f6'
down_revision: Union[str, None] = '0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # SQLite: store JSON as TEXT if JSON not available; SQLAlchemy will handle.
    op.add_column("farms", sa.Column("preferred_commodities", sa.JSON().with_variant(sa.Text(), "sqlite"), nullable=False, server_default="[]"))
    op.add_column("farms", sa.Column("preferred_mandi", sa.String(), nullable=True))
    # drop server_default after backfilling
    with op.batch_alter_table("farms") as batch:
        batch.alter_column("preferred_commodities", server_default=None)

def downgrade():
    with op.batch_alter_table("farms") as batch:
        batch.drop_column("preferred_mandi")
        batch.drop_column("preferred_commodities")
