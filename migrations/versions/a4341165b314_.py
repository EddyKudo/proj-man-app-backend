"""empty message

Revision ID: a4341165b314
Revises: 9b5bd6ad4236
Create Date: 2020-03-26 19:54:58.465085

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a4341165b314'
down_revision = '9b5bd6ad4236'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('todo', sa.Column('createdDate', sa.String(length=12), nullable=True))
    op.add_column('todo', sa.Column('dueDate', sa.String(length=12), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('todo', 'dueDate')
    op.drop_column('todo', 'createdDate')
    # ### end Alembic commands ###
