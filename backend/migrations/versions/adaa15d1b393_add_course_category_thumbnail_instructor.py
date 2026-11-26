"""add_course_category_thumbnail_instructor

Revision ID: adaa15d1b393
Revises: daa7965436ff
Create Date: 2026-11-25 12:45:51.589848

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'adaa15d1b393'
down_revision: Union[str, Sequence[str], None] = 'daa7965436ff'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('courses', schema=None) as batch_op:
        batch_op.add_column(sa.Column('category', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('thumbnail_url', sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column('instructor_id', sa.Integer(), nullable=True))
        batch_op.create_index(op.f('ix_courses_category'), ['category'], unique=False)
        batch_op.create_index(op.f('ix_courses_instructor_id'), ['instructor_id'], unique=False)
        batch_op.create_foreign_key(
            'fk_courses_instructor_id',
            'instructors',
            ['instructor_id'],
            ['id'],
            ondelete='RESTRICT',
        )


def downgrade() -> None:
    with op.batch_alter_table('courses', schema=None) as batch_op:
        batch_op.drop_constraint('fk_courses_instructor_id', type_='foreignkey')
        batch_op.drop_index(op.f('ix_courses_instructor_id'))
        batch_op.drop_index(op.f('ix_courses_category'))
        batch_op.drop_column('instructor_id')
        batch_op.drop_column('thumbnail_url')
        batch_op.drop_column('category')
