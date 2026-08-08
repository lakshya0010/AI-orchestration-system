"""add created_at default

Revision ID: 9ee85e6b3d94
Revises: e5745774558a
Create Date: 2026-08-09 00:42:19.033106

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9ee85e6b3d94'
down_revision: Union[str, Sequence[str], None] = 'e5745774558a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "agent_steps",
        "created_at",
        server_default=sa.text("now()"),
    )


def downgrade() -> None:
    op.alter_column(
        "agent_steps",
        "created_at",
        server_default=None,
    )
