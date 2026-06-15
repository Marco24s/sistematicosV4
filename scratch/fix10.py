with open(r'C:\sistematicosV4\scratch\e2e_test_final.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Fix step 10 auth token
code = code.replace(
'''        print("\\n[PASO 10] Instalación en Aeronave")
        res = client.post("/api/v1/squadron/install-component", headers=auth_h(token_jefe), json={''',
'''        print("\\n[PASO 10] Instalación en Aeronave")
        res = client.post("/api/v1/squadron/install-component", headers=auth_h(token_tech), json={'''
)

with open(r'C:\sistematicosV4\scratch\e2e_test_final.py', 'w', encoding='utf-8') as f:
    f.write(code)
