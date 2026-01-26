"""add notified in Appointment

Revision ID: a9f8678cc8a4
Revises: 001_initial
Create Date: 2026-01-26 15:56:33.967436

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a9f8678cc8a4'
down_revision: Union[str, Sequence[str], None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column(
        'appointments',
        sa.Column(
            'notified',
            sa.Boolean(),
            nullable=False,
            server_default=sa.false()
        )
    )

def downgrade():
    op.drop_column('appointments', 'notified')

