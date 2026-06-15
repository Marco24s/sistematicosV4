with open(r'C:\sistematicosV4\backend\scripts\seed.py', 'r', encoding='utf-8') as f:
    code = f.read()

code = code.replace(
    'current_custodian_id=escuadron.id,',
    'current_custodian_id=escuadron.id,\n                    organization_owner_id=comando.id,\n                    airworthiness_status="AIRWORTHY",\n                    current_location="Base Aeronaval Comandante Espora",'
)

with open(r'C:\sistematicosV4\backend\scripts\seed.py', 'w', encoding='utf-8') as f:
    f.write(code)
