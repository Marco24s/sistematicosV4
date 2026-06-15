from fastapi import APIRouter

from app.modules.assets.api.routes import router as assets_router
from app.modules.maintenance.api.routes import router as maintenance_router
from app.modules.organization.api.routes import router as organization_router

api_router = APIRouter()
api_router.include_router(organization_router)
api_router.include_router(assets_router)
api_router.include_router(maintenance_router)
