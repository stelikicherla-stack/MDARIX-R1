from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from integration.gateway import ConnectionConfig, MappingDefinition, preview
from backend.app.request_context import AuthenticatedRequestContext, get_request_context
router=APIRouter(prefix="/api/v1/integrations",tags=["Integration Gateway"])
class PreviewRequest(BaseModel): connection_id:str; connector_type:str="FILE"; source_system_type:str="SIMULATED"; records:list[dict]; target_entity:str; mapping_version:str; rules:dict
@router.post("/preview")
def mapping_preview(request:PreviewRequest, ctx: AuthenticatedRequestContext = Depends(get_request_context)):
    config=ConnectionConfig(ctx.tenant_id,request.connection_id,"preview",request.connector_type,request.source_system_type)
    return {"connection":config.safe_dict(),"preview":preview(request.records,MappingDefinition(request.source_system_type,request.target_entity,request.mapping_version,request.rules))}

@router.get('/health/{connector_type}')
def connector_health(connector_type: str, ctx: AuthenticatedRequestContext = Depends(get_request_context)):
    if connector_type not in {'FILE','REST','DATABASE'}:
        raise HTTPException(400, detail={'code':'UNSUPPORTED_CONNECTOR','message':'Connector type is not supported'})
    return {'tenant_id':ctx.tenant_id,'connector_type':connector_type,'status':'HEALTHY','configuration_valid':True}
