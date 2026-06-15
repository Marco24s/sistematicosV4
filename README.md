# SISTEMATICOS V4

Sistema web modular para gestion integral de mantenimiento aeronautico militar, logistica tecnica, trazabilidad documental y control de aeronavegabilidad.

El objetivo operativo principal es impedir que una aeronave sea liberada si tiene componentes vencidos, sin certificacion tecnica, fuera de condicion aeronavegable o con trazabilidad documental incompleta.

## Stack

- Backend: Python, FastAPI, SQLAlchemy, Pydantic
- Frontend: Next.js, React, TypeScript
- Base de datos: PostgreSQL
- Arquitectura: DDD, Event Driven Architecture, REST API

## Principios

- No hay modelos de aeronaves, motores o componentes hardcodeados.
- Los tipos, modelos, fabricantes, ciclos de vida y reglas se administran desde catalogos en base de datos.
- El dominio decide la aeronavegabilidad; la UI solo muestra el resultado.
- Cada componente tiene identidad e historial propio.
- Los eventos de dominio registran hechos tecnicos relevantes.

## Ejecutar en desarrollo

```powershell
docker compose up -d postgres
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

PostgreSQL del proyecto queda publicado en `localhost:55432` para evitar conflictos con instalaciones locales en `5432`.

```powershell
cd frontend
npm install
npm run dev
```
