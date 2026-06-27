"""initial migration

Full Phase-1 schema in one migration:
  auth   -> users, user_sessions, otp_logs
  module -> businesses, financial_years (SRS Module 3 + 5)

Revision ID: a1b2c3d4e5f6
Revises:
Create Date: 2026-06-27 12:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Define the enums ONCE with create_type=False so create_table does NOT try to
# auto-create them again. We create them explicitly below with checkfirst=True.
gender_enum = postgresql.ENUM(
    "male", "female", "other", name="usergender", create_type=False
)
type_enum = postgresql.ENUM(
    "normal", "agent", "admin", "superadmin", name="usertype", create_type=False
)
status_enum = postgresql.ENUM(
    "draft", "active", name="businessstatus", create_type=False
)


def upgrade() -> None:
    bind = op.get_bind()
    gender_enum.create(bind, checkfirst=True)
    type_enum.create(bind, checkfirst=True)
    status_enum.create(bind, checkfirst=True)

    # ── users ──────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("createdAt", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updatedAt", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("firebaseUid", sa.String(), nullable=False),
        sa.Column("phone", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column("fullName", sa.String(), nullable=False),
        sa.Column("profilePhoto", sa.String(), nullable=True),
        sa.Column("timeZone", sa.String(), nullable=False, server_default="Asia/Kolkata"),
        sa.Column("language", sa.String(), nullable=False, server_default="en"),
        sa.Column("gender", gender_enum, nullable=True),
        sa.Column("verified", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("userType", type_enum, nullable=False, server_default="normal"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("firebaseUid"),
        sa.UniqueConstraint("phone"),
        sa.UniqueConstraint("email"),
    )
    op.create_index(op.f("ix_users_firebaseUid"), "users", ["firebaseUid"], unique=True)

    # ── user_sessions ──────────────────────────────────────────────────
    op.create_table(
        "user_sessions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("createdAt", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("userId", sa.Integer(), nullable=False),
        sa.Column("refreshTokenHash", sa.String(), nullable=False),
        sa.Column("deviceInfo", sa.String(), nullable=True),
        sa.Column("ipAddress", sa.String(), nullable=True),
        sa.Column("expiresAt", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False, server_default="false"),
        sa.ForeignKeyConstraint(["userId"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("refreshTokenHash"),
    )
    op.create_index(op.f("ix_user_sessions_userId"), "user_sessions", ["userId"], unique=False)

    # ── otp_logs (audit trail of Firebase verifications) ───────────────
    op.create_table(
        "otp_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("createdAt", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("userId", sa.Integer(), nullable=True),
        sa.Column("phone", sa.String(), nullable=False),
        sa.Column("firebaseUid", sa.String(), nullable=False),
        sa.Column("ipAddress", sa.String(), nullable=True),
        sa.Column("purpose", sa.String(), nullable=False, server_default="login"),
        sa.ForeignKeyConstraint(["userId"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_otp_logs_userId"), "otp_logs", ["userId"], unique=False)

    # ── businesses (SRS Module 3) ──────────────────────────────────────
    op.create_table(
        "businesses",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("createdAt", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updatedAt", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("userId", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("tradeName", sa.String(), nullable=True),
        sa.Column("pan", sa.String(), nullable=True),
        sa.Column("gstin", sa.String(), nullable=True),
        sa.Column("stateCode", sa.String(), nullable=True),
        sa.Column("country", sa.String(), nullable=False, server_default="India"),
        sa.Column("currency", sa.String(), nullable=False, server_default="INR"),
        sa.Column("fyStartMonth", sa.Integer(), nullable=False, server_default="4"),
        sa.Column("status", status_enum, nullable=False, server_default="draft"),
        sa.ForeignKeyConstraint(["userId"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_businesses_userId"), "businesses", ["userId"], unique=False)

    # ── financial_years (SRS Module 5 storage) ─────────────────────────
    op.create_table(
        "financial_years",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("createdAt", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("businessId", sa.Integer(), nullable=False),
        sa.Column("label", sa.String(), nullable=False),
        sa.Column("startDate", sa.String(), nullable=False),
        sa.Column("endDate", sa.String(), nullable=False),
        sa.Column("isClosed", sa.Boolean(), nullable=False, server_default="false"),
        sa.ForeignKeyConstraint(["businessId"], ["businesses.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_financial_years_businessId"), "financial_years", ["businessId"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_financial_years_businessId"), table_name="financial_years")
    op.drop_table("financial_years")

    op.drop_index(op.f("ix_businesses_userId"), table_name="businesses")
    op.drop_table("businesses")

    op.drop_index(op.f("ix_otp_logs_userId"), table_name="otp_logs")
    op.drop_table("otp_logs")

    op.drop_index(op.f("ix_user_sessions_userId"), table_name="user_sessions")
    op.drop_table("user_sessions")

    op.drop_index(op.f("ix_users_firebaseUid"), table_name="users")
    op.drop_table("users")

    bind = op.get_bind()
    status_enum.drop(bind, checkfirst=True)
    type_enum.drop(bind, checkfirst=True)
    gender_enum.drop(bind, checkfirst=True)
