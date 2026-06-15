with open(r'C:\sistematicosV4\scratch\e2e_test_final.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Replace review_id extraction
code = code.replace(
'''        review_id = res.json()["engineering_review_id"]

        print("\\n[PASO 5B] Dictamen Técnico de Ingeniería")
        res = client.post("/api/v1/engineering/technical-decision", headers=auth_h(token_jefe), json={
            "maintenance_request_id": maint_req_id,
            "engineer_id": str(tech_user.id),
            "decision": "REPAIR",
            "instruction_code": "ENG-INST-HP-99",
            "technical_directive": "Reemplazar sello",
            "required_repair_procedure": "Proc 42"
        })
        assert res.status_code == 200, f"Error: {res.text}"
        print(f"-> Engineering Decision emitida: REPAIR")''',
'''        instruction_id = res.json()["instruction_id"]
        review_id = res.json()["review_id"]
'''
)

# Replace instruction_id: review_id with instruction_id: instruction_id
code = code.replace(
'''        res = client.post("/api/v1/technical-section/start-repair", headers=auth_h(token_jefe), json={
            "maintenance_request_id": maint_req_id,
            "assigned_section_id": str(dep.id),
            "assigned_technician_id": str(tech_user.id),
            "assigned_by": "Jefe",
            "instruction_id": review_id
        })''',
'''        res = client.post("/api/v1/technical-section/start-repair", headers=auth_h(token_jefe), json={
            "maintenance_request_id": maint_req_id,
            "assigned_section_id": str(dep.id),
            "assigned_technician_id": str(tech_user.id),
            "assigned_by": "Jefe",
            "instruction_id": instruction_id
        })'''
)

# In release component, quality_inspection_id uses inspection_id, which is already fixed in the script. Wait, let me check the script.
with open(r'C:\sistematicosV4\scratch\fix5.py', 'w', encoding='utf-8') as f:
    f.write(code)
