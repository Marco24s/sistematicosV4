with open(r'C:\sistematicosV4\scratch\e2e_test_v2.py', 'r', encoding='utf-8') as f:
    code = f.read()
code = code.replace('datetime.now(datetime.UTC)', 'datetime.utcnow()')
with open(r'C:\sistematicosV4\scratch\e2e_test_v2.py', 'w', encoding='utf-8') as f:
    f.write(code)
