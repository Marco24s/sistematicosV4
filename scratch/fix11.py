with open(r'C:\sistematicosV4\scratch\e2e_test_final.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Fix event store import
code = code.replace(
'''from app.shared.infrastructure.event_store import DomainEventModel''',
'''from app.shared.infrastructure.event_store import StoredDomainEvent'''
)

code = code.replace(
'''events = db.query(DomainEventModel).filter(DomainEventModel.aggregate_id == pump.id).order_by(DomainEventModel.occurred_on).all()''',
'''events = db.query(StoredDomainEvent).filter(StoredDomainEvent.aggregate_id == pump.id).order_by(StoredDomainEvent.occurred_on).all()'''
)

with open(r'C:\sistematicosV4\scratch\e2e_test_final.py', 'w', encoding='utf-8') as f:
    f.write(code)
