import re

with open(r'C:\sistematicosV4\frontend\src\app\page.tsx', 'r', encoding='utf-8') as f:
    code = f.read()

# Map all simulated users to real seeded ones based on their roles
code = re.sub(r"username:\s*'jefe_supervision',\s*password:\s*'pin_supervision'", "username: 'comando', password: 'comando123'", code)
code = re.sub(r"username:\s*'jefe_operaciones',\s*password:\s*'pin_operaciones'", "username: 'jefe', password: 'jefe123'", code)
code = re.sub(r"username:\s*'mecanico_hangar',\s*password:\s*'pin_mecanico'", "username: 'tech', password: 'tech123'", code)
code = re.sub(r"username:\s*'panolero_escuadron',\s*password:\s*'pin_panol_escuadron'", "username: 'tech', password: 'tech123'", code)
code = re.sub(r"username:\s*'panolero_arsenal',\s*password:\s*'pin_panol_arsenal'", "username: 'jefe', password: 'jefe123'", code)
code = re.sub(r"username:\s*'mecanico_taller',\s*password:\s*'pin_taller'", "username: 'tech', password: 'tech123'", code)
code = re.sub(r"username:\s*'inspector_calidad',\s*password:\s*'pin_inspector'", "username: 'inspector', password: 'inspector123'", code)
code = re.sub(r"username:\s*'analista_estadisticas',\s*password:\s*'pin_estadisticas'", "username: 'jefe', password: 'jefe123'", code)
code = re.sub(r"username:\s*'jefe_pcp',\s*password:\s*'pin_pcp'", "username: 'jefe', password: 'jefe123'", code)
code = re.sub(r"username:\s*'ingeniero_aero',\s*password:\s*'pin_ingenieria'", "username: 'jefe', password: 'jefe123'", code)
code = re.sub(r"username:\s*'comprador',\s*password:\s*'pin_compras'", "username: 'jefe', password: 'jefe123'", code)
code = re.sub(r"username:\s*'comandante',\s*password:\s*'pin_comando'", "username: 'comando', password: 'comando123'", code)

with open(r'C:\sistematicosV4\frontend\src\app\page.tsx', 'w', encoding='utf-8') as f:
    f.write(code)
