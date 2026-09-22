from datetime import datetime, timezone
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session
from backend.app.db.models.stage2 import MDARIXCaseContext
from backend.app.db.models.foundation import Product, ProductVersion, Investigation
from backend.app.db.session import get_db
from backend.app.request_context import AuthenticatedRequestContext, get_request_context
router = APIRouter(prefix='/api/v1/workspace/context', tags=['Workspace Context'])
class ContextUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    product_id: UUID | None = None; product_version_id: UUID | None = None; signal_id: UUID | None = None; complaint_cluster_id: UUID | None = None; investigation_id: UUID | None = None; temporal_mode: str = 'CURRENT'; temporal_cutoff: datetime | None = None; decision_brief_id: UUID | None = None; decision_id: UUID | None = None; last_page: str | None = None
def _row(db, ctx):
    row = db.query(MDARIXCaseContext).filter(MDARIXCaseContext.tenant_id == ctx.tenant_id, MDARIXCaseContext.user_id == ctx.user_id).first()
    if row is None:
        now=datetime.now(timezone.utc); row=MDARIXCaseContext(tenant_id=ctx.tenant_id,user_id=ctx.user_id,membership_id=ctx.membership_id,created_at=now,updated_at=now); db.add(row); db.flush()
    return row
def _validate(db, ctx, data):
    if data.product_id and not db.query(Product.id).filter(Product.id==data.product_id,Product.tenant_id==ctx.tenant_id).first(): raise HTTPException(404,detail={'code':'PRODUCT_NOT_FOUND','message':'Product is not available for this tenant'})
    if data.product_version_id and not db.query(ProductVersion.id).filter(ProductVersion.id==data.product_version_id,ProductVersion.tenant_id==ctx.tenant_id,ProductVersion.product_id==data.product_id).first(): raise HTTPException(404,detail={'code':'PRODUCT_VERSION_NOT_FOUND','message':'ProductVersion is not available for this tenant'})
    if data.investigation_id and not db.query(Investigation.id).filter(Investigation.id==data.investigation_id,Investigation.tenant_id==ctx.tenant_id).first(): raise HTTPException(404,detail={'code':'INVESTIGATION_NOT_FOUND','message':'Investigation is not available for this tenant'})
    if data.temporal_mode not in {'CURRENT','EVENT_AS_OF','KNOWN_AS_OF'}: raise HTTPException(422,detail={'code':'INVALID_TEMPORAL_MODE','message':'Unsupported temporal mode'})
def _out(row): return {k:(str(v) if v is not None and k.endswith('_id') else v) for k in ('id','tenant_id','user_id','membership_id','product_id','product_version_id','signal_id','complaint_cluster_id','investigation_id','temporal_mode','temporal_cutoff','decision_brief_id','decision_id','context_version','last_page','updated_at') for v in [getattr(row,k)]}
@router.get('')
def get_context(db:Session=Depends(get_db),ctx:AuthenticatedRequestContext=Depends(get_request_context)): return _out(_row(db,ctx))
@router.put('')
def put_context(data:ContextUpdate,db:Session=Depends(get_db),ctx:AuthenticatedRequestContext=Depends(get_request_context)):
    _validate(db,ctx,data); row=_row(db,ctx)
    if data.product_id != row.product_id: row.product_version_id=row.signal_id=row.investigation_id=None
    if data.product_version_id != row.product_version_id: row.signal_id=row.investigation_id=None
    for k,v in data.model_dump(exclude_unset=True).items(): setattr(row,k,v)
    row.context_version+=1; row.updated_at=datetime.now(timezone.utc); db.commit(); db.refresh(row); return _out(row)
@router.post('/reset')
def reset_context(db:Session=Depends(get_db),ctx:AuthenticatedRequestContext=Depends(get_request_context)):
    row=_row(db,ctx)
    for k in ('product_id','product_version_id','signal_id','complaint_cluster_id','investigation_id','temporal_cutoff','decision_brief_id','decision_id','last_page'): setattr(row,k,None)
    row.temporal_mode='CURRENT'; row.context_version+=1; row.updated_at=datetime.now(timezone.utc); db.commit(); return _out(row)
