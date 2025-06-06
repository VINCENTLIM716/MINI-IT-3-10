"""upgrade

Revision ID: d540fefd54e1
Revises: 4f27d83b87f8
Create Date: 2025-05-29 00:53:58.866108

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd540fefd54e1'
down_revision = '4f27d83b87f8'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('habit_completion', schema=None) as batch_op:
        batch_op.add_column(sa.Column('completed_at', sa.DateTime(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('habit_completion', schema=None) as batch_op:
        batch_op.drop_column('completed_at')

    # ### end Alembic commands ###
