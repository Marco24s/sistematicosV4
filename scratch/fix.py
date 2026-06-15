with open(r'C:\sistematicosV4\scratch\e2e_test.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
with open(r'C:\sistematicosV4\scratch\e2e_test.py', 'w', encoding='utf-8') as f:
    for line in lines:
        if 'installed_at' not in line:
            f.write(line)
