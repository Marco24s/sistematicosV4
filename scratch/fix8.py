with open(r'C:\sistematicosV4\scratch\e2e_test_final.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Fix PASO 5B payload
code = code.replace(
'''        res = client.post("/api/v1/engineering/technical-decision", headers=auth_h(token_jefe), json={
            "maintenance_request_id": maint_req_id,
            "engineer_id": str(tech_user.id),
            "decision": "REPAIR",
            "instruction_code": "ENG-INST-HP-99-" + str(uuid4())[:8],
            "technical_directive": "Reemplazar sello",
            "required_repair_procedure": "Proc 42"
        })''',
'''        res = client.post("/api/v1/engineering/technical-decision", headers=auth_h(token_jefe), json={
            "maintenance_request_id": maint_req_id,
            "engineer_id": str(tech_user.id),
            "decision": "REPAIR",
            "instruction_code": "ENG-INST-HP-99-" + str(uuid4())[:8],
            "technical_directive": "Reemplazar sello",
            "required_repair_procedure": "Proc 42",
            "authorized_engineer": "Jefe",
            "decision_date": datetime.utcnow().isoformat()
        })'''
)

with open(r'C:\sistematicosV4\scratch\e2e_test_final.py', 'w', encoding='utf-8') as f:
    f.write(code)
