"""msg91 otp — make firebaseUid columns nullable

Auth moved from Firebase phone-OTP to MSG91 OTP. New users are no longer
created with a Firebase UID, so the NOT NULL constraint on `users.firebaseUid`
and `otp_logs.firebaseUid` is dropped. The columns are kept (nullable) so older
rows / accounts remain intact.

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-06-29 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("users", "firebaseUid", nullable=True)
    op.alter_column("otp_logs", "firebaseUid", nullable=True)


def downgrade() -> None:
    # Backfill placeholders so the NOT NULL can be re-applied without error.
    op.execute("UPDATE users SET \"firebaseUid\" = 'legacy-' || id WHERE \"firebaseUid\" IS NULL")
    op.execute("UPDATE otp_logs SET \"firebaseUid\" = '' WHERE \"firebaseUid\" IS NULL")
    op.alter_column("otp_logs", "firebaseUid", nullable=False)
    op.alter_column("users", "firebaseUid", nullable=False)
