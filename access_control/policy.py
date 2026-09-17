from dataclasses import dataclass, field
from typing import Any

STATES={"EDITABLE","READ_ONLY","HIDDEN"}; ACTIONS={"READ","EDIT","CREATE","UPDATE","DELETE","EXPORT","REVIEW","APPROVE","SIGN","CONFIGURE","ACTIVATE"}
@dataclass
class PermissionSet:
    name: str; object_permissions: dict[str,str]=field(default_factory=dict); field_permissions: dict[str,str]=field(default_factory=dict); action_permissions: dict[str,bool]=field(default_factory=dict); version: str="v1"; status: str="DRAFT"
@dataclass
class Role:
    tenant_id: str; name: str; permission_sets: list[PermissionSet]=field(default_factory=list); version: str="v1"; status: str="DRAFT"
@dataclass
class User:
    tenant_id: str; user_id: str; display_name: str; roles: list[Role]=field(default_factory=list); active_role_id: str|None=None; status: str="ACTIVE"
    def active_role(self):
        if self.status != "ACTIVE": return None
        return next((r for r in self.roles if r.name == self.active_role_id), None) or (self.roles[0] if self.roles else None)

def effective_permissions(user: User) -> dict[str,Any]:
    role=user.active_role(); result={"objects":{},"fields":{},"actions":{},"tenant_id":user.tenant_id,"user_id":user.user_id,"active_role":role.name if role else None}
    if not role: return result
    for permission_set in role.permission_sets:
        result["objects"].update(permission_set.object_permissions); result["fields"].update(permission_set.field_permissions); result["actions"].update(permission_set.action_permissions)
    return result

def allowed(user: User, object_name: str, action: str="READ", field: str|None=None, tenant_id: str|None=None):
    if user.status != "ACTIVE" or tenant_id is not None and tenant_id != user.tenant_id: return False
    permissions=effective_permissions(user)
    if field and permissions["fields"].get(f"{object_name}.{field}","HIDDEN") == "HIDDEN": return False
    if field and action in {"EDIT","UPDATE"} and permissions["fields"].get(f"{object_name}.{field}","HIDDEN") != "EDITABLE": return False
    if action in ACTIONS and action in permissions["actions"]: return bool(permissions["actions"][action])
    if action in {"READ","EDIT"}: return permissions["objects"].get(object_name,"NO_ACCESS") in ({"READ_ONLY","EDIT"} if action=="READ" else {"EDIT"})
    return False

def filter_fields(user: User, object_name: str, record: dict[str,Any]):
    return {key:value for key,value in record.items() if allowed(user,object_name,"READ",key)}

def switch_role(user: User, requested_role: str):
    if user.status != "ACTIVE" or not any(role.name==requested_role for role in user.roles): return {"status":"DENIED","active_role":user.active_role_id}
    user.active_role_id=requested_role; return {"status":"SWITCHED","active_role":requested_role,"permissions":effective_permissions(user)}
