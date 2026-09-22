"""Add retry and dead-letter state to the transactional outbox."""
from alembic import op
import sqlalchemy as sa
revision='s35outbox'; down_revision='r34durableauth'; branch_labels=None; depends_on=None
def upgrade():
    op.add_column('event_outbox', sa.Column('next_attempt_at', sa.DateTime(timezone=True)))
    op.add_column('event_outbox', sa.Column('dead_lettered_at', sa.DateTime(timezone=True)))
    op.add_column('event_outbox', sa.Column('last_error', sa.Text()))
def downgrade():
    op.drop_column('event_outbox','last_error'); op.drop_column('event_outbox','dead_lettered_at'); op.drop_column('event_outbox','next_attempt_at')
