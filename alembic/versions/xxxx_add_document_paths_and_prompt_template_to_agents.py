from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'xxxx'
down_revision = 'yyyy'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('agents', sa.Column('document_paths', sa.Text(), nullable=True))
    op.add_column('agents', sa.Column('prompt_template', sa.Text(), nullable=True))

def downgrade():
    op.drop_column('agents', 'document_paths')
    op.drop_column('agents', 'prompt_template')