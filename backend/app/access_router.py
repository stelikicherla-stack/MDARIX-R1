from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from access_control.policy import PermissionSet, Role, User, effective_permissions, switch_role
router=APIRouter(prefix="/api/v1",tags=["Access Control"])
demo=User("ACME_CARE_SYNTHETIC","demo-user","Authenticated User",[Role("ACME_CARE_SYNTHETIC","Viewer",[PermissionSet("viewer",{"Investigation":"READ_ONLY","Evidence":"READ_ONLY"})])],"Viewer")
class RoleSwitch(BaseModel): role: str
@router.get("/me/context")
def context():
    return {"user_id":demo.user_id,"display_name":demo.display_name,"tenant_id":demo.tenant_id,"active_role":demo.active_role_id,"permissions":effective_permissions(demo)}
@router.post("/me/active-role")
def active_role(request:RoleSwitch):
    result=switch_role(demo,request.role)
    if result["status"]=="DENIED": raise HTTPException(403,detail={"code":"ROLE_NOT_ASSIGNED","message":"Requested role is not assigned to the authenticated user"})
    return {"user_id":demo.user_id,"display_name":demo.display_name,"active_role":demo.active_role_id,"permissions":result["permissions"]}
