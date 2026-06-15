with open(r'C:\sistematicosV4\scratch\e2e_test_final.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Replace the engineering_review_id with review_id
code = code.replace(
'''        review_id = res.json()["engineering_review_id"]''',
'''        review_id = res.json()["review_id"]
        instruction_id = res.json()["instruction_id"]'''
)

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

with open(r'C:\sistematicosV4\scratch\e2e_test_final.py', 'w', encoding='utf-8') as f:
    f.write(code)
