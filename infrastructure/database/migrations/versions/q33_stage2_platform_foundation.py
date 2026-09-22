"""Stage 2 durable context, auth session, and transactional outbox foundation."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision='q33stage2'; down_revision='p32reusableoffboardedemails'; branch_labels=None; depends_on=None
def _id(): return sa.Column('id',postgresql.UUID(as_uuid=True),primary_key=True,server_default=sa.text('gen_random_uuid()'))
def _ts(name, nullable=True): return sa.Column(name,sa.DateTime(timezone=True),nullable=nullable)
def upgrade():
    op.create_table('auth_sessions',_id(),sa.Column('session_hash',sa.String(128),nullable=False,unique=True),sa.Column('user_id',postgresql.UUID(as_uuid=True),nullable=False),sa.Column('tenant_id',postgresql.UUID(as_uuid=True),sa.ForeignKey('tenants.id'),nullable=False),_ts('expires_at',False),_ts('revoked_at'),_ts('created_at',False),_ts('last_seen_at',False),sa.UniqueConstraint('tenant_id','id',name='uq_auth_sessions_tenant_id'))
    op.create_table('authentication_events',_id(),sa.Column('tenant_id',postgresql.UUID(as_uuid=True),sa.ForeignKey('tenants.id')),sa.Column('user_id',postgresql.UUID(as_uuid=True)),sa.Column('event_type',sa.String(80),nullable=False),sa.Column('outcome',sa.String(40),nullable=False),sa.Column('correlation_id',sa.String(120)),sa.Column('metadata',postgresql.JSONB),_ts('created_at',False))
    op.create_table('case_contexts',_id(),sa.Column('tenant_id',postgresql.UUID(as_uuid=True),sa.ForeignKey('tenants.id'),nullable=False),sa.Column('user_id',postgresql.UUID(as_uuid=True),nullable=False),sa.Column('membership_id',postgresql.UUID(as_uuid=True)),*[sa.Column(n,postgresql.UUID(as_uuid=True)) for n in ('product_id','product_version_id','signal_id','complaint_cluster_id','investigation_id','decision_brief_id','decision_id')],sa.Column('temporal_mode',sa.String(30),nullable=False,server_default='CURRENT'),_ts('temporal_cutoff'),sa.Column('context_version',sa.Integer,nullable=False,server_default='1'),sa.Column('last_page',sa.String(160)),_ts('created_at',False),_ts('updated_at',False),sa.UniqueConstraint('tenant_id','user_id',name='uq_case_context_tenant_user'))
    op.create_table('event_outbox',_id(),sa.Column('tenant_id',postgresql.UUID(as_uuid=True),sa.ForeignKey('tenants.id'),nullable=False),sa.Column('event_name',sa.String(120),nullable=False),sa.Column('aggregate_type',sa.String(120),nullable=False),sa.Column('aggregate_id',postgresql.UUID(as_uuid=True)),sa.Column('payload',postgresql.JSONB,nullable=False),_ts('occurred_at',False),_ts('published_at'),sa.Column('attempts',sa.Integer,nullable=False,server_default='0'))
    op.create_index('ix_event_outbox_pending','event_outbox',['published_at','occurred_at'])
def downgrade():
    op.drop_index('ix_event_outbox_pending',table_name='event_outbox'); op.drop_table('event_outbox'); op.drop_table('case_contexts'); op.drop_table('authentication_events'); op.drop_table('auth_sessions')
