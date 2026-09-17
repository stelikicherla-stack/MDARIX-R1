from fastapi import APIRouter
from pydantic import BaseModel
from integration.gateway import ConnectionConfig, MappingDefinition, preview
router=APIRouter(prefix="/api/v1/integrations",tags=["Integration Gateway"])
class PreviewRequest(BaseModel): tenant_id:str; connection_id:str; connector_type:str="FILE"; source_system_type:str="SIMULATED"; records:list[dict]; target_entity:str; mapping_version:str; rules:dict
@router.post("/preview")
def mapping_preview(request:PreviewRequest):
    config=ConnectionConfig(request.tenant_id,request.connection_id,"preview",request.connector_type,request.source_system_type)
    return {"connection":config.safe_dict(),"preview":preview(request.records,MappingDefinition(request.source_system_type,request.target_entity,request.mapping_version,request.rules))}
