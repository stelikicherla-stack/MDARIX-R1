"""Stage 2 durable platform primitives."""
import uuid
from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, Boolean
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.db.base import Base

def _id(): return mapped_column(UUID(as_uuid=True), primary_key=True, server_default=__import__('sqlalchemy').text('gen_random_uuid()'))
def _tenant(): return mapped_column(UUID(as_uuid=True), ForeignKey('tenants.id'), nullable=False)
def _ts(nullable=True): return mapped_column(DateTime(timezone=True), nullable=nullable)

class AuthSession(Base):
    __tablename__ = 'auth_sessions'
    id = _id(); session_hash: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False); tenant_id = _tenant()
    expires_at = _ts(False); revoked_at = _ts(); created_at = _ts(False); last_seen_at = _ts(False)
    __table_args__ = (UniqueConstraint('tenant_id','id',name='uq_auth_sessions_tenant_id'),)

class LoginThrottle(Base):
    """Durable per-identifier lockout state shared by all app instances."""
    __tablename__ = 'login_throttles'
    identifier: Mapped[str] = mapped_column(String(254), primary_key=True)
    failure_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default='0')
    locked_until = _ts()
    last_failure_at = _ts()
    updated_at = _ts(False)

class UserInvitation(Base):
    __tablename__ = 'user_invitations'
    id = _id(); user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False); tenant_id = _tenant()
    token_hash: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    expires_at = _ts(False); used_at = _ts(); created_at = _ts(False); created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    __table_args__ = (Index('ix_user_invitations_user','tenant_id','user_id'),)

class PasswordResetRequest(Base):
    __tablename__ = 'password_reset_requests'
    id = _id(); user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False); tenant_id = _tenant()
    token_hash: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    expires_at = _ts(False); used_at = _ts(); created_at = _ts(False); created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    __table_args__ = (Index('ix_password_reset_user','tenant_id','user_id'),)

class OnboardingRequest(Base):
    """Public signup intent; it never creates a tenant or active identity."""
    __tablename__ = 'onboarding_requests'
    id = _id(); email: Mapped[str] = mapped_column(String(254), nullable=False, unique=True)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    organization: Mapped[str] = mapped_column(String(160), nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False, server_default='PENDING_REVIEW')
    created_at = _ts(False); updated_at = _ts(False)

class AuthenticationEvent(Base):
    __tablename__ = 'authentication_events'
    id = _id(); tenant_id = mapped_column(UUID(as_uuid=True), ForeignKey('tenants.id'))
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True)); event_type: Mapped[str] = mapped_column(String(80), nullable=False)
    outcome: Mapped[str] = mapped_column(String(40), nullable=False); correlation_id: Mapped[str | None] = mapped_column(String(120)); metadata_json: Mapped[dict | None] = mapped_column('metadata', JSONB); created_at = _ts(False)

class MDARIXCaseContext(Base):
    __tablename__ = 'case_contexts'
    id = _id(); tenant_id = _tenant(); user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False); membership_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    product_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True)); product_version_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True)); signal_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True)); complaint_cluster_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True)); investigation_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    temporal_mode: Mapped[str] = mapped_column(String(30), nullable=False, server_default='CURRENT'); temporal_cutoff = _ts(); decision_brief_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True)); decision_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True)); context_version: Mapped[int] = mapped_column(Integer, nullable=False, server_default='1'); last_page: Mapped[str | None] = mapped_column(String(160)); created_at = _ts(False); updated_at = _ts(False)
    __table_args__ = (UniqueConstraint('tenant_id','user_id',name='uq_case_context_tenant_user'),)

class OutboxEvent(Base):
    __tablename__ = 'event_outbox'
    id = _id(); tenant_id = _tenant(); event_name: Mapped[str] = mapped_column(String(120), nullable=False); aggregate_type: Mapped[str] = mapped_column(String(120), nullable=False); aggregate_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True)); payload: Mapped[dict] = mapped_column(JSONB, nullable=False); occurred_at = _ts(False); published_at = _ts(); attempts: Mapped[int] = mapped_column(Integer, nullable=False, server_default='0'); next_attempt_at = _ts(); dead_lettered_at = _ts(); last_error: Mapped[str | None] = mapped_column(Text)
    __table_args__ = (Index('ix_event_outbox_pending','published_at','occurred_at'),)

class SubscriptionLifecycle(Base):
    __tablename__ = 'subscription_lifecycles'
    id = _id(); tenant_id = _tenant(); plan_id = mapped_column(UUID(as_uuid=True), ForeignKey('plan_definitions.id'), nullable=False)
    plan_version: Mapped[str] = mapped_column(String(40), nullable=False); starts_at = _ts(False); expires_at = _ts(False); grace_ends_at = _ts()
    expiry_version: Mapped[int] = mapped_column(Integer, nullable=False, server_default='1'); status: Mapped[str] = mapped_column(String(40), nullable=False, server_default='ACTIVE')
    renewal_state: Mapped[str] = mapped_column(String(40), nullable=False, server_default='NOT_REQUESTED'); exception_expires_at = _ts(); created_at = _ts(False); updated_at = _ts(False)
    __table_args__ = (UniqueConstraint('tenant_id','id',name='uq_subscription_lifecycle_tenant_id'),)

class ReminderPolicy(Base):
    __tablename__ = 'subscription_reminder_policies'
    id = _id(); tenant_id = _tenant(); name: Mapped[str] = mapped_column(String(120), nullable=False); thresholds = mapped_column(JSONB, nullable=False, server_default='[60,30,7]'); timezone: Mapped[str] = mapped_column(String(80), nullable=False, server_default='UTC'); recipient_types = mapped_column(JSONB, nullable=False, server_default='["CUSTOMER_ADMIN"]'); version: Mapped[str] = mapped_column(String(40), nullable=False, server_default='v1'); status: Mapped[str] = mapped_column(String(30), nullable=False, server_default='ACTIVE'); created_at = _ts(False); updated_at = _ts(False)

class EmailTemplate(Base):
    __tablename__ = 'subscription_email_templates'
    id = _id(); tenant_id = _tenant(); stage: Mapped[str] = mapped_column(String(40), nullable=False); version: Mapped[str] = mapped_column(String(40), nullable=False); subject: Mapped[str] = mapped_column(String(255), nullable=False); body = mapped_column(Text, nullable=False); allowed_variables = mapped_column(JSONB, nullable=False, server_default='[]'); status: Mapped[str] = mapped_column(String(30), nullable=False, server_default='DRAFT'); created_at = _ts(False); updated_at = _ts(False)
    __table_args__ = (UniqueConstraint('tenant_id','stage','version',name='uq_subscription_email_template'),)
