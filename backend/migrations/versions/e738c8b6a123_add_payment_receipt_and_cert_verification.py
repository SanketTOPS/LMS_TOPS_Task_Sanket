"""add_payment_receipt_and_cert_verification

Revision ID: e738c8b6a123
Revises: 9008ff4cc9e1
Create Date: 2026-11-25 15:43:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e738c8b6a123'
down_revision: Union[str, Sequence[str], None] = '9008ff4cc9e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('certificates') as batch_op:
        batch_op.add_column(sa.Column('verification_code', sa.String(length=100), nullable=True))
        batch_op.create_index(batch_op.f('ix_certificates_verification_code'), ['verification_code'], unique=True)

    with op.batch_alter_table('payments') as batch_op:
        batch_op.add_column(sa.Column('receipt_number', sa.String(length=100), nullable=True))
        batch_op.create_index(batch_op.f('ix_payments_receipt_number'), ['receipt_number'], unique=True)


def downgrade() -> None:
    with op.batch_alter_table('payments') as batch_op:
        batch_op.drop_index(batch_op.f('ix_payments_receipt_number'))
        batch_op.drop_column('receipt_number')

    with op.batch_alter_table('certificates') as batch_op:
        batch_op.drop_index(batch_op.f('ix_certificates_verification_code'))
        batch_op.drop_column('verification_code')
