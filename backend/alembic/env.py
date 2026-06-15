from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.database import Base
from app.modules.arsenal_workflow.domain import models as arsenal_workflow_models
from app.modules.assets.domain import models as asset_models
from app.modules.document_management.domain import models as document_management_models
from app.modules.flight_operations.domain import models as flight_operations_models
from app.modules.maintenance.domain import models as maintenance_models
from app.modules.organization.domain import models as organization_models
from app.modules.personnel_certification.domain import models as personnel_certification_models
from app.modules.squadron_operations.domain import models as squadron_operations_models
from app.modules.supply_chain.domain import models as supply_chain_models
from app.shared.infrastructure import event_store as event_store_models
from app.modules.workflow_orchestration.domain import models as workflow_models
from app.modules.tool_calibration.domain import models as tool_calibration_models
from app.modules.authorization.domain import models as authorization_models
from app.modules.engine_management.domain import models as engine_management_models
from app.modules.reporting_analytics.domain import models as reporting_analytics_models
from app.modules.flight_release_control.domain import models as flight_release_control_models
from app.modules.airworthiness_engine.domain import models as airworthiness_engine_models
from app.modules.disposal_management.domain import models as disposal_management_models
from app.modules.asset_reallocation.domain import models as asset_reallocation_models
from app.modules.auditing.domain import models as auditing_models
from app.modules.configuration_baseline.domain import models as configuration_baseline_models
from app.modules.structural_fatigue.domain import models as structural_fatigue_models
from app.modules.maintenance_human_factors.domain import models as maintenance_human_factors_models
from app.modules.reliability_engine.domain import models as reliability_engine_models
from app.modules.fod_management.domain import models as fod_management_models






config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
