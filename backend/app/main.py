from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.api.html_router import html_router
from app.core.database import Base, engine
from app.core.settings import get_settings
# Inicializar cableado de eventos y comandos
import app.modules.workflow_orchestration
import app.modules.authorization


# Early development bootstrap. Replace with Alembic migrations before production.
Base.metadata.create_all(bind=engine)

settings = get_settings()
app = FastAPI(title=settings.app_name)

# Habilitar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permitir todos los orígenes en desarrollo
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.shared.events.worker import outbox_worker

app.include_router(api_router, prefix=settings.api_v1_prefix)

@app.on_event("startup")
def startup_event():
    outbox_worker.start()

@app.on_event("shutdown")
def shutdown_event():
    outbox_worker.stop()
# app.include_router(html_router)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok", "system": settings.app_name}


# Servir Frontend compilado de Next.js
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

out_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "out"))

if os.path.exists(out_dir):
    # Servir archivos estáticos del compilado
    app.mount("/_next", StaticFiles(directory=os.path.join(out_dir, "_next")), name="next-assets")
    
    # Manejar enrutado del cliente (SPA)
    @app.get("/{catchall:path}")
    async def serve_frontend(catchall: str):
        # Si la petición apunta a la API, no interferir
        if catchall.startswith("api/") or catchall.startswith("health") or catchall.startswith("docs") or catchall.startswith("openapi.json"):
            return
            
        file_path = os.path.join(out_dir, catchall)
        # Si el archivo exacto existe físicamente (ej. favicon.ico, etc.), devolverlo
        if os.path.isfile(file_path):
            return FileResponse(file_path)
            
        # Si hay una ruta de Next.js como operaciones.html, la devolvemos
        html_route_path = file_path + ".html"
        if os.path.isfile(html_route_path):
            return FileResponse(html_route_path)

        # De lo contrario, devolver index.html para enrutado del lado del cliente
        return FileResponse(os.path.join(out_dir, "index.html"))



