import re

with open(r'C:\sistematicosV4\scratch\e2e_test_final.py', 'r', encoding='utf-8') as f:
    code = f.read()

def replacer(match):
    prefix = match.group(1)
    return f'"{prefix}-" + str(uuid4())[:8]'

# Reemplazar códigos hardcodeados por dinámicos
code = re.sub(r'"(FR-[A-Z0-9]+)"', replacer, code)
code = re.sub(r'"(MAF-[A-Z0-9]+)"', replacer, code)
code = re.sub(r'"(ING-[A-Z0-9\-]+)"', replacer, code)
code = re.sub(r'"(ENG-[A-Z0-9\-]+)"', replacer, code)
code = re.sub(r'"(RCR-[A-Z0-9]+)"', replacer, code)
code = re.sub(r'"(QI-[A-Z0-9\-]+)"', replacer, code)
code = re.sub(r'"(SRC-[A-Z0-9\-]+)"', replacer, code)
code = re.sub(r'"(HRB-[A-Z0-9\-]+)"', replacer, code)

with open(r'C:\sistematicosV4\scratch\e2e_test_final.py', 'w', encoding='utf-8') as f:
    f.write(code)
