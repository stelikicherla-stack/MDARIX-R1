"""Persist sessions, invitations, and password reset tokens."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'r34durableauth'
down_revision = 'q33stage2'
branch_labels = None
depends_on = None

def _id(): return sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()'))
def _ts(name, nullable=True): return sa.Column(name, sa.DateTime(timezone=True), nullable=nullable)
def _table(name):
    op.create_table(name, _id(), sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False), sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False), sa.Column('token_hash', sa.String(128), nullable=False, unique=True), _ts('expires_at', False), _ts('used_at'), _ts('created_at', False), sa.Column('created_by', postgresql.UUID(as_uuid=True)))
def upgrade():
    _table('user_invitations')
    _table('password_reset_requests')
    op.create_index('ix_user_invitations_user','user_invitations',['tenant_id','user_id'])
    op.create_index('ix_password_reset_user','password_reset_requests',['tenant_id','user_id'])
def downgrade():
    op.drop_index('ix_password_reset_user', table_name='password_reset_requests'); op.drop_index('ix_user_invitations_user', table_name='user_invitations')
    op.drop_table('password_reset_requests'); op.drop_table('user_invitations')
