"""merge multiple heads

Revision ID: 91f516a4d8e3
Revises: 6f5bb7e39937, b1f9461d4ec0
Create Date: 2025-07-31 08:05:58.975180

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '91f516a4d8e3'
down_revision: Union[str, Sequence[str], None] = ('6f5bb7e39937', 'b1f9461d4ec0')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
