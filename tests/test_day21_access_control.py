from access_control.policy import PermissionSet, Role, User, allowed, effective_permissions, filter_fields, switch_role

def users():
    a=User("A","a1","Customer A User",[Role("A","Complaint Analyst",[PermissionSet("A-set",{"Complaint":"EDIT"},{"Complaint.Description":"EDITABLE","Complaint.SourceSystem":"READ_ONLY","Complaint.InternalNote":"HIDDEN"},{"EXPORT":False})])],"Complaint Analyst")
    b=User("B","b1","Customer B User",[Role("B","Post Market Specialist",[PermissionSet("B-set",{"Complaint":"READ_ONLY"},{"Complaint.Description":"READ_ONLY","Complaint.SourceSystem":"READ_ONLY"})])],"Post Market Specialist")
    c=User("C","c1","Customer C User",[Role("C","Regulatory Reviewer",[PermissionSet("C-set",{"Investigation":"READ_ONLY"},{"Investigation.FinalDecision":"READ_ONLY","Investigation.InternalNote":"HIDDEN"},{"EXPORT":False})])],"Regulatory Reviewer")
    return a,b,c

def test_customer_a_b_c_use_same_configurable_engine():
    a,b,c=users(); assert allowed(a,"Complaint","EDIT", "Description"); assert not allowed(b,"Complaint","EDIT","Description"); assert not allowed(c,"AIConfiguration","READ"); assert filter_fields(a,"Complaint",{"Description":"ok","SourceSystem":"QMS","InternalNote":"secret"})=={"Description":"ok","SourceSystem":"QMS"}

def test_deny_default_read_only_and_export():
    _,b,_=users(); assert not allowed(b,"UnknownObject","READ"); assert allowed(b,"Complaint","READ","Description"); assert not allowed(b,"Complaint","UPDATE","Description"); assert not allowed(b,"Complaint","EXPORT")

def test_role_switch_is_assigned_and_recalculates():
    a,_,_=users(); a.roles.append(Role("A","Auditor",[PermissionSet("audit",{"AuditEvent":"READ_ONLY"})])); assert switch_role(a,"Auditor")["status"]=="SWITCHED"; assert allowed(a,"AuditEvent","READ"); assert switch_role(a,"Administrator")["status"]=="DENIED"

def test_cross_tenant_and_inactive_denied():
    a,_,_=users(); assert not allowed(a,"Complaint","READ",tenant_id="B"); a.status="INACTIVE"; assert effective_permissions(a)["objects"]=={}; assert not allowed(a,"Complaint","READ")
