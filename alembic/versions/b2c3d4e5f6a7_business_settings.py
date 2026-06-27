"""business_settings (SRS Module 4 — Business Configuration)

Adds the `business_settings` table: one row per business with the four
Module-4 toggles (inventory / GST / multi-branch / manufacturing).

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-06-27 15:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "business_settings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("createdAt", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updatedAt", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("businessId", sa.Integer(), nullable=False),
        sa.Column("inventoryEnabled", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("gstRegistered", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("multiBranch", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("manufacturing", sa.Boolean(), nullable=False, server_default="false"),
        sa.ForeignKeyConstraint(["businessId"], ["businesses.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("businessId"),
    )
    op.create_index(
        op.f("ix_business_settings_businessId"),
        "business_settings",
        ["businessId"],
        unique=True,
    )

    # Backfill: give every existing business a default config row. GST defaults
    # ON when the business already has a GSTIN.
    op.execute(
        """
        INSERT INTO business_settings
            ("businessId", "inventoryEnabled", "gstRegistered", "multiBranch", "manufacturing")
        SELECT b.id,
               false,
               (b.gstin IS NOT NULL AND btrim(b.gstin) <> ''),
               false,
               false
        FROM businesses b
        WHERE NOT EXISTS (
            SELECT 1 FROM business_settings s WHERE s."businessId" = b.id
        )
        """
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_business_settings_businessId"), table_name="business_settings")
    op.drop_table("business_settings")
