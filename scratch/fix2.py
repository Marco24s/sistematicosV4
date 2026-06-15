with open(r'C:\sistematicosV4\scratch\e2e_test_v2.py', 'r', encoding='utf-8') as f:
    code = f.read()
code = code.replace('installed_by="tech",\n                status=MountedComponentStatus.ACTIVE', 'installation_date=datetime.now(datetime.UTC),\n                installed_by="tech",\n                status=MountedComponentStatus.ACTIVE')
with open(r'C:\sistematicosV4\scratch\e2e_test_v2.py', 'w', encoding='utf-8') as f:
    f.write(code)
