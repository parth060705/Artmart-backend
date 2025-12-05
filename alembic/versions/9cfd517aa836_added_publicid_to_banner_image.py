"""added publicid to banner image 

Revision ID: 9cfd517aa836
Revises: 8bb589d27040
Create Date: 2025-12-05 08:37:59.669582
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = '9cfd517aa836'
down_revision: Union[str, Sequence[str], None] = '8bb589d27040'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema safely."""
    # Drop table if exists to avoid errors
    op.execute("DROP TABLE IF EXISTS community_banner_images")
    
    # Add new column to communities
    op.add_column(
        'communities',
        sa.Column('bannerImagePublicId', sa.String(length=255), nullable=True)
    )
    
    # Alter bannerImage column length
    op.alter_column(
        'communities',
        'bannerImage',
        existing_type=mysql.VARCHAR(length=255),
        type_=sa.String(length=500),
        existing_nullable=True
    )


def downgrade() -> None:
    """Downgrade schema safely."""
    # Revert bannerImage column length
    op.alter_column(
        'communities',
        'bannerImage',
        existing_type=sa.String(length=500),
        type_=mysql.VARCHAR(length=255),
        existing_nullable=True
    )
    
    # Drop the added column
    op.drop_column('communities', 'bannerImagePublicId')
    
    # Recreate community_banner_images table
    op.create_table(
        'community_banner_images',
        sa.Column('id', mysql.VARCHAR(length=36), nullable=False),
        sa.Column('community_id', mysql.VARCHAR(length=36), nullable=False),
        sa.Column('url', mysql.VARCHAR(length=500), nullable=False),
        sa.Column('public_id', mysql.VARCHAR(length=255), nullable=False),
        sa.Column('created_at', mysql.DATETIME(), nullable=True),
        sa.ForeignKeyConstraint(
            ['community_id'],
            ['communities.id'],
            name=op.f('community_banner_images_ibfk_1')
        ),
        sa.PrimaryKeyConstraint('id')
    )
