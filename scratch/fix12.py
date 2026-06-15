with open(r'C:\sistematicosV4\scratch\e2e_test_final.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Fix Document import
code = code.replace(
'''from app.modules.document_management.domain.models import Document''',
'''from app.modules.document_management.domain.models import TechnicalDocument as Document'''
)

with open(r'C:\sistematicosV4\scratch\e2e_test_final.py', 'w', encoding='utf-8') as f:
    f.write(code)
