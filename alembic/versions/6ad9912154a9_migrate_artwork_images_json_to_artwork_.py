"""migrate artwork.images JSON to artwork_images

Revision ID: 6ad9912154a9
Revises: 335908776d30
Create Date: 2025-09-01 07:49:37.135615
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import Session
import uuid
import json

# revision identifiers, used by Alembic.
revision: str = '6ad9912154a9'
down_revision: Union[str, Sequence[str], None] = '335908776d30'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Migrate old artwork.images JSON into artwork_images table."""
    bind = op.get_bind()
    session = Session(bind=bind)

    # Reflect artworks table
    artworks = sa.Table(
        "artworks",
        sa.MetaData(),
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("images", sa.JSON),
    )

    artwork_images = sa.Table(
        "artwork_images",
        sa.MetaData(),
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("artwork_id", sa.String(36)),
        sa.Column("url", sa.String(500)),
        sa.Column("public_id", sa.String(255)),
    )

    results = session.execute(sa.select(artworks.c.id, artworks.c.images)).fetchall()

    for artwork_id, images_json in results:
        if not images_json:
            continue

        try:
            if isinstance(images_json, str):
                images = json.loads(images_json)
            else:
                images = images_json
        except Exception:
            images = []

        if not isinstance(images, list):
            continue

        for img in images:
            if isinstance(img, dict):
                url = img.get("url")
                public_id = img.get("public_id", f"legacy_{uuid.uuid4()}")
            else:  # just a URL string
                url = str(img)
                public_id = f"legacy_{uuid.uuid4()}"

            if url:
                session.execute(
                    artwork_images.insert().values(
                        id=str(uuid.uuid4()),
                        artwork_id=artwork_id,
                        url=url,
                        public_id=public_id,
                    )
                )

    session.commit()


def downgrade() -> None:
    """Optional: push images back into artworks.images JSON."""
    pass
