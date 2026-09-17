from integration.gateway import ConnectionConfig, FileConnector, MappingDefinition, preview, reconcile, resolve_identity, validate_mapping

def config(customer, fields):
    return ConnectionConfig(customer, f"conn-{customer}", customer, "FILE", "QMS")

def mapping(fields):
    return MappingDefinition("complaints", "Complaint", "v1", {source:{"target_field":target,"required":True,"transform":"trim"} for source,target in fields.items()})

def test_customer_a_b_c_use_same_connector_and_normalize_semantically():
    connectors=[FileConnector(config("A",[]), [{"complaint_number":"C-1","device_code":"NV200","revision":"B","event_date":"2026-08-14"}]),FileConnector(config("B",[]), [{"case_id":"C-1","device_model":"NV200","version_label":"B","incident_timestamp":"2026-08-14"}]),FileConnector(config("C",[]), [{"ticket":"C-1","model":"NV200","rev":"B","occurred":"2026-08-14"}])]
    mappings=[mapping({"complaint_number":"Complaint.identifier","device_code":"Complaint.product_external_key","revision":"Complaint.product_version_external","event_date":"Complaint.event_time"}),mapping({"case_id":"Complaint.identifier","device_model":"Complaint.product_external_key","version_label":"Complaint.product_version_external","incident_timestamp":"Complaint.event_time"}),mapping({"ticket":"Complaint.identifier","model":"Complaint.product_external_key","rev":"Complaint.product_version_external","occurred":"Complaint.event_time"})]
    outputs=[preview(c.read_records(),m)["records"][0] for c,m in zip(connectors,mappings)]
    assert all(type(c) is FileConnector for c in connectors); assert [o["Complaint.identifier"] for o in outputs]==["C-1"]*3; assert [o["Complaint.product_version_external"] for o in outputs]==["B"]*3

def test_mapping_drift_transform_failure_ambiguity_and_reconciliation():
    m=MappingDefinition("qms","Complaint","v1",{"supplier_code":{"target_field":"ProductVersion.id","required":True,"transform":"identity"}})
    assert validate_mapping(m)["status"]=="INVALID"; bad=preview([{}],m); assert bad["status"]=="BLOCKED"; assert reconcile(100,90,5,3,2,90,5)["status"]=="COMPLETE"; assert resolve_identity("B",[{"key":"B"},{"key":"B"}])["status"]=="AMBIGUOUS"
