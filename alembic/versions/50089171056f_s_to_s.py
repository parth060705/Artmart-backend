"""S to s

Revision ID: 50089171056f
Revises: 8a746a24f9bb
Create Date: 2025-10-19 23:44:54.109257
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = '50089171056f'
down_revision: Union[str, Sequence[str], None] = '8a746a24f9bb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create the lowercase 'saved' table
    op.create_table(
        'saved',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('userId', sa.String(length=36), nullable=False),
        sa.Column('artworkId', sa.String(length=36), nullable=False),
        sa.Column('createdAt', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['userId'], ['users.id'], name='fk_saved_user'),
        sa.ForeignKeyConstraint(['artworkId'], ['artworks.id'], name='fk_saved_artwork'),
        sa.PrimaryKeyConstraint('id')
    )

    # Remove the drop table command, it's not needed
    # op.drop_table('Saved')


def downgrade() -> None:
    """Downgrade schema."""
    # Recreate old 'Saved' table if needed
    op.create_table(
        'Saved',
        sa.Column('id', mysql.VARCHAR(length=36), nullable=False),
        sa.Column('userId', mysql.VARCHAR(length=36), nullable=False),
        sa.Column('artworkId', mysql.VARCHAR(length=36), nullable=False),
        sa.Column('createdAt', mysql.DATETIME(), nullable=False),
        sa.ForeignKeyConstraint(['userId'], ['users.id'], name='Saved_ibfk_1'),
        sa.ForeignKeyConstraint(['artworkId'], ['artworks.id'], name='Saved_ibfk_2'),
        sa.PrimaryKeyConstraint('id')
    )

    # Drop the lowercase table on downgrade
    op.drop_table('saved')
