with open(r'C:\sistematicosV4\scratch\e2e_test_v2.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Fix Step 3 payload
code = code.replace('"component_id": str(pump.id),', '"component_asset_id": str(pump.id),\n            "source_squadron_id": str(db.query(Department).first().id),')

with open(r'C:\sistematicosV4\scratch\e2e_test_v2.py', 'w', encoding='utf-8') as f:
    f.write(code)
