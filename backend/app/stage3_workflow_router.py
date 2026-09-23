import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Header, HTTPException, Request, UploadFile, File
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from backend.app.db.session import get_db
from backend.app.db.models.stage3 import AIInteraction, AIInteractionFeedback, AIInteractionSession, ContextSnapshot, InboundEmailEvent, SupplierEvidenceRequest, EvidenceAttachment
from backend.app.db.models.foundation import AuditEvent
from object_storage.service import ObjectStorageService
from communication.email.service import EmailService
from communication.email.provider import EmailMessage
from backend.app.request_context import AuthenticatedRequestContext, get_request_context
from communication.email.inbound import classify_inbound_event, verify_webhook

router = APIRouter(prefix="/api/v1/stage3", tags=["Stage 3 Workflow"])
NOW = lambda: datetime.now(timezone.utc)

class InteractionRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=12000); page_context: str = "ASK_MDARIX"; product_id: uuid.UUID | None = None; product_version_id: uuid.UUID | None = None; investigation_id: uuid.UUID | None = None; temporal_mode: str = "CURRENT"; temporal_cutoff: datetime | None = None
class FeedbackRequest(BaseModel):
    rating: str = Field(min_length=1, max_length=40); comment: str | None = Field(default=None, max_length=4000)
class SupplierEvidenceRequestPayload(BaseModel):
    recipient: str = Field(min_length=3, max_length=254); title: str = Field(min_length=1, max_length=240); requested_items: list[str] = Field(min_length=1, max_length=50); investigation_id: uuid.UUID | None = None; supplier_id: uuid.UUID | None = None

@router.post("/interactions")
def create_interaction(payload: InteractionRequest, db: Session = Depends(get_db), ctx: AuthenticatedRequestContext = Depends(get_request_context)):
    now = NOW(); session = AIInteractionSession(id=uuid.uuid4(), tenant_id=ctx.tenant_id, user_id=ctx.user_id, page_context=payload.page_context, correlation_id=ctx.correlation_id, created_at=now, updated_at=now); db.add(session); db.flush()
    response = {"what_is_known": [], "relevant_evidence": [], "what_may_be_related": [], "contradictions": [], "unknowns": [], "missing_evidence": [], "limitations": ["No live model execution was requested by this endpoint."], "suggested_next_questions": [], "suggested_next_actions": [], "sources_provenance": [], "human_review_required": True}
    row = AIInteraction(id=uuid.uuid4(), tenant_id=ctx.tenant_id, session_id=session.id, user_id=ctx.user_id, product_id=payload.product_id, product_version_id=payload.product_version_id, investigation_id=payload.investigation_id, user_prompt=payload.prompt, normalized_intent="STRUCTURED_ASK", temporal_mode=payload.temporal_mode, temporal_cutoff=payload.temporal_cutoff, response=response, provenance={"provider":"controlled-foundation"}, correlation_id=ctx.correlation_id, created_at=now); db.add(row); db.commit()
    return {"interaction_id": str(row.id), "session_id": str(session.id), "status": "READY_FOR_REVIEW", "response": response}

@router.post("/interactions/{interaction_id}/feedback")
def interaction_feedback(interaction_id: uuid.UUID, payload: FeedbackRequest, db: Session = Depends(get_db), ctx: AuthenticatedRequestContext = Depends(get_request_context)):
    row = db.query(AIInteraction).filter(AIInteraction.id == interaction_id, AIInteraction.tenant_id == ctx.tenant_id).first()
    if not row: raise HTTPException(404, detail={"code":"INTERACTION_NOT_FOUND","message":"Interaction is not available for this tenant"})
    feedback = AIInteractionFeedback(id=uuid.uuid4(), tenant_id=ctx.tenant_id, interaction_id=row.id, user_id=ctx.user_id, feedback=payload.model_dump(), created_at=NOW()); db.add(feedback); db.commit(); return {"status":"RECORDED","feedback_id":str(feedback.id)}

@router.get("/interactions")
def list_interactions(db: Session = Depends(get_db), ctx: AuthenticatedRequestContext = Depends(get_request_context)):
    rows = db.query(AIInteraction).filter(AIInteraction.tenant_id == ctx.tenant_id, AIInteraction.user_id == ctx.user_id).order_by(AIInteraction.created_at.desc()).limit(100).all()
    return [{"id":str(r.id),"prompt":r.user_prompt,"response":r.response,"created_at":r.created_at,"investigation_id":r.investigation_id} for r in rows]

@router.post("/supplier-evidence-requests")
def request_supplier_evidence(payload: SupplierEvidenceRequestPayload, db: Session = Depends(get_db), ctx: AuthenticatedRequestContext = Depends(get_request_context)):
    now = NOW(); row = SupplierEvidenceRequest(id=uuid.uuid4(), tenant_id=ctx.tenant_id, investigation_id=payload.investigation_id, supplier_id=payload.supplier_id, requested_by=ctx.user_id, recipient=payload.recipient, title=payload.title, requested_items={"items": payload.requested_items}, status="PENDING_DELIVERY", created_at=now, updated_at=now); db.add(row); db.flush()
    delivery = "NOT_CONFIGURED"
    try:
        delivery = EmailService().send_template(payload.recipient, "evidence_request", {"intro": payload.title, "link": "Use the authorized supplier evidence channel."})
        row.status = "SENT"
    except Exception:
        row.status = "DELIVERY_PENDING"
    db.add(AuditEvent(id=uuid.uuid4(), tenant_id=ctx.tenant_id, actor_ref=ctx.user_id, action="SUPPLIER_EVIDENCE_REQUEST_CREATED", entity_type="SupplierEvidenceRequest", entity_id=row.id, details={"status":row.status,"email_delivery":delivery,"item_count":len(payload.requested_items)}, created_at=now)); db.commit()
    return {"id":str(row.id),"tenant_id":ctx.tenant_id,"status":row.status,"email_delivery":delivery}

@router.get("/supplier-evidence-requests")
def list_supplier_evidence_requests(db: Session = Depends(get_db), ctx: AuthenticatedRequestContext = Depends(get_request_context)):
    rows = db.query(SupplierEvidenceRequest).filter(SupplierEvidenceRequest.tenant_id == ctx.tenant_id).order_by(SupplierEvidenceRequest.created_at.desc()).limit(100).all()
    return [{"id":str(r.id),"recipient":r.recipient,"title":r.title,"status":r.status,"requested_items":r.requested_items} for r in rows]

@router.post("/supplier-evidence-requests/{request_id}/attachments")
async def upload_supplier_attachment(request_id: uuid.UUID, file: UploadFile = File(...), db: Session = Depends(get_db), ctx: AuthenticatedRequestContext = Depends(get_request_context)):
    row = db.query(SupplierEvidenceRequest).filter(SupplierEvidenceRequest.id == request_id, SupplierEvidenceRequest.tenant_id == ctx.tenant_id).first()
    if not row: raise HTTPException(404, detail={"code":"EVIDENCE_REQUEST_NOT_FOUND","message":"Evidence request is not available"})
    content = await file.read(); metadata = ObjectStorageService().put(ctx.tenant_id, f"{request_id}-{file.filename or 'attachment'}", content); now = NOW(); attachment = EvidenceAttachment(id=uuid.uuid4(), tenant_id=ctx.tenant_id, request_id=row.id, uploaded_by=ctx.user_id, filename=file.filename or "attachment", content_type=file.content_type or "application/octet-stream", object_key=metadata["object_key"], size=metadata["size"], checksum=metadata["checksum"], created_at=now); db.add(attachment); db.add(AuditEvent(id=uuid.uuid4(), tenant_id=ctx.tenant_id, actor_ref=ctx.user_id, action="SUPPLIER_EVIDENCE_ATTACHMENT_UPLOADED", entity_type="EvidenceAttachment", entity_id=attachment.id, details={"filename":attachment.filename,"size":attachment.size,"checksum":attachment.checksum}, created_at=now)); db.commit(); return {"id":str(attachment.id),**metadata,"filename":attachment.filename}

@router.post("/resend/webhook")
async def persisted_resend_webhook(request: Request, x_resend_signature: str | None = Header(default=None), db: Session = Depends(get_db)):
    body = await request.body()
    if not verify_webhook(body, x_resend_signature): raise HTTPException(401, detail={"code":"INVALID_WEBHOOK_SIGNATURE","message":"Webhook authentication failed"})
    try: event = await request.json()
    except Exception: raise HTTPException(400, detail={"code":"INVALID_WEBHOOK_PAYLOAD","message":"Webhook payload is invalid"})
    event_id = str(event.get("id", "")); event_type = str(event.get("type", ""))
    if not event_id: raise HTTPException(400, detail={"code":"MISSING_PROVIDER_EVENT_ID","message":"Provider event id is required"})
    existing = db.query(InboundEmailEvent).filter(InboundEmailEvent.provider_event_id == event_id).first()
    if existing: return {"status":"DUPLICATE_IGNORED","event_id":event_id}
    classified = classify_inbound_event(event); row = InboundEmailEvent(id=uuid.uuid4(), tenant_id=None, provider_event_id=event_id, event_type=event_type, status=classified["status"], event_metadata={"processing_state":classified.get("processing_state"),"evidence_acceptance":"NEVER_AUTOMATIC"}, created_at=NOW())
    # Tenant resolution is intentionally pending; the event is not authorized by email content.
    db.add(row); db.commit(); return {**classified, "event_id": event_id}

@router.get("/provider-health")
def stage3_provider_health(ctx: AuthenticatedRequestContext = Depends(get_request_context)):
    from communication.email.resend_provider import ResendProvider
    return {"tenant_id":ctx.tenant_id, **ResendProvider().health()}

@router.post("/reports/{report_code}")
def generate_report(report_code: str, output_format: str = "JSON", ctx: AuthenticatedRequestContext = Depends(get_request_context)):
    from reports.service import generate_report as build_report
    try: return build_report(report_code.upper(), ctx.tenant_id, output_format=output_format, context={"correlation_id":ctx.correlation_id})
    except ValueError as exc: raise HTTPException(400, detail={"code":str(exc),"message":"Report type is not supported"})
