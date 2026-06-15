from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from app.core.database import Base

# Import all models
import app.modules.organization.domain.models
import app.modules.assets.domain.models
import app.modules.maintenance.domain.models
import app.modules.flight_operations.domain.models
import app.modules.arsenal_workflow.domain.models
import app.modules.squadron_operations.domain.models
import app.modules.personnel_certification.domain.models
import app.modules.document_management.domain.models
import app.modules.supply_chain.domain.models
import app.shared.infrastructure.event_store
import app.modules.workflow_orchestration.domain.models

engine = create_engine("sqlite:///:memory:")
Base.metadata.create_all(bind=engine)

inspector = inspect(engine)
tables = inspector.get_table_names()
print("Created tables in SQLite:")
print(tables)
print("Is 'assets' in tables?", "assets" in tables)
