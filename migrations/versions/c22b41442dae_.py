"""empty message

Revision ID: c22b41442dae
Revises: 13b784a4a8cf
Create Date: 2020-02-23 06:47:16.318978

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'c22b41442dae'
down_revision = '13b784a4a8cf'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('user', 'email',
               existing_type=mysql.VARCHAR(length=50),
               nullable=True)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('user', 'email',
               existing_type=mysql.VARCHAR(length=50),
               nullable=False)
    # ### end Alembic commands ###