"""business address — add address, city, pincode columns

SRS Module 3: businesses can now store a postal address (street/building),
city/town and PIN code. All three are optional (nullable) so existing rows
remain valid.

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-06-30 12:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, None] = "c3d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("businesses", sa.Column("address", sa.String(), nullable=True))
    op.add_column("businesses", sa.Column("city", sa.String(), nullable=True))
    op.add_column("businesses", sa.Column("pincode", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("businesses", "pincode")
    op.drop_column("businesses", "city")
    op.drop_column("businesses", "address")
