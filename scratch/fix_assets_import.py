with open(r'C:\sistematicosV4\backend\app\api\routes\assets.py', 'r', encoding='utf-8') as f:
    code = f.read()

code = code.replace(
    'from app.modules.organization.domain.models import Department',
    'from app.modules.organization.domain.models import Department, Organization'
)

with open(r'C:\sistematicosV4\backend\app\api\routes\assets.py', 'w', encoding='utf-8') as f:
    f.write(code)
