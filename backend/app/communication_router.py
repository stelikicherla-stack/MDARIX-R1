import json
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from communication.email.inbound import classify_inbound_event, verify_webhook
from communication.email.resend_provider import ResendProvider
from backend.app.request_context import AuthenticatedRequestContext, get_request_context

router = APIRouter(prefix="/api/v1/communication", tags=["Communication"])


@router.get("/provider-health")
def provider_health(ctx: AuthenticatedRequestContext = Depends(get_request_context)):
    return {"tenant_id": ctx.tenant_id, **ResendProvider().health(), "smtp_is_fallback_only": True}


@router.post("/resend/webhook")
async def resend_webhook(request: Request, x_resend_signature: str | None = Header(default=None)):
    body = await request.body()
    if not verify_webhook(body, x_resend_signature):
        raise HTTPException(401, detail={"code": "INVALID_WEBHOOK_SIGNATURE", "message": "Webhook authentication failed"})
    try:
        event = json.loads(body.decode())
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise HTTPException(400, detail={"code": "INVALID_WEBHOOK_PAYLOAD", "message": "Webhook payload is invalid"})
    return classify_inbound_event(event)
