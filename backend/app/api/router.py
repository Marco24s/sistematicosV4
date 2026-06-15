from fastapi import APIRouter
from app.modules.document_management.api import routes as document_management
from app.api.routes import (
    assets,
    flight,
    maintenance,
    squadron,
    arsenal,
    supply_chain,
    engine_management,
    flight_release,
    airworthiness,
    llp,
    maintenance_signoff,
    personnel,
    tools,
    procurement,
    reporting,
    security_audit,
    command_console,
    auth,
)

api_router = APIRouter()
api_router.include_router(assets.router)
api_router.include_router(flight.router)
api_router.include_router(maintenance.router)
api_router.include_router(squadron.router)
api_router.include_router(arsenal.router)
api_router.include_router(supply_chain.router)
api_router.include_router(engine_management.router)
api_router.include_router(flight_release.router)
api_router.include_router(airworthiness.router)
api_router.include_router(llp.router)
api_router.include_router(maintenance_signoff.router)
api_router.include_router(personnel.router)
api_router.include_router(tools.router)
api_router.include_router(procurement.router)
api_router.include_router(reporting.router)
api_router.include_router(security_audit.router)
api_router.include_router(command_console.router)
api_router.include_router(auth.router)
api_router.include_router(document_management.router)

