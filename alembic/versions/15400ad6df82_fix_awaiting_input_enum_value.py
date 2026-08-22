"""fix awaiting input enum value

Revision ID: 15400ad6df82
Revises: f91cf7b2ef5e
Create Date: 2026-08-22 18:34:32.459329

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '15400ad6df82'
down_revision: Union[str, Sequence[str], None] = 'f91cf7b2ef5e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TYPE session_status_new AS ENUM (
            'planning',
            'executing',
            'critiquing',
            'replanning',
            'done',
            'failed',
            'awaiting_input'
        )
    """)

    # Change the column to use the new enum
    op.execute("""
        ALTER TABLE sessions
        ALTER COLUMN status
        TYPE session_status_new
        USING (
            CASE
                WHEN status::text = 'AWAITING_INPUT'
                THEN 'awaiting_input'
                ELSE status::text
            END
        )::session_status_new
    """)

    # Remove old enum
    op.execute("DROP TYPE session_status")

    # Rename new enum
    op.execute(
        "ALTER TYPE session_status_new RENAME TO session_status"
    )


def downgrade() -> None:
    op.execute("""
        CREATE TYPE session_status_old AS ENUM (
            'planning',
            'executing',
            'critiquing',
            'replanning',
            'done',
            'failed',
            'AWAITING_INPUT'
        )
    """)

    op.execute("""
        ALTER TABLE sessions
        ALTER COLUMN status
        TYPE session_status_old
        USING (
            CASE
                WHEN status::text = 'awaiting_input'
                THEN 'AWAITING_INPUT'
                ELSE status::text
            END
        )::session_status_old
    """)

    op.execute("DROP TYPE session_status")

    op.execute(
        "ALTER TYPE session_status_old RENAME TO session_status"
    )
