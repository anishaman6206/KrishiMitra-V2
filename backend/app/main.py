# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.config import get_settings
from backend.app.routers.users import router as users_router
from backend.app.routers.farms import router as farms_router
from backend.app.routers.market import router as market_router
from backend.app.routers.weather import router as weather_router
from backend.app.routers.soil import router as soil_router
from backend.app.routers.crop_recommendation import router as reco_router  # NEW
from backend.app.routers.crop_disease import router as crop_disease_router  # NEW
from backend.app.routers.market_forecast import router as market_forecast_router  # NEW
from backend.app.routers.ai import router as ai_router
from backend.app.routers.ai_graph import router as ai_graph_router
from backend.app.routers.ai_agentic import router as ai_agent_router
from backend.app.routers.rag import router as rag_router
from backend.app.routers.market_meta import router as market_meta_router



from dotenv import load_dotenv
load_dotenv()

from backend.app.db import Base  # wherever your declarative_base() lives
from backend.app.db import engine  # your SQLAlchemy engine factory

APP_NAME = "KrishiMitra API"
APP_VERSION = "0.0.1"

def create_app() -> FastAPI:
    s = get_settings()
    app = FastAPI(title=APP_NAME, version=APP_VERSION, debug=s.debug)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=s.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

        # NEW: dev convenience — create tables automatically for SQLite
    @app.on_event("startup")
    def _ensure_sqlite_tables():
        db_url = s.database_url.lower()
        if db_url.startswith("sqlite:///"):
            Base.metadata.create_all(bind=engine)

    @app.get("/", tags=["system"])
    def root():
        return {"name": APP_NAME, "version": APP_VERSION, "status": "ok"}

    @app.get("/health", tags=["system"])
    def health():
        return {"status": "healthy"}

    @app.get("/version", tags=["system"])
    def version():
        return {"version": APP_VERSION}

    app.include_router(users_router)
    app.include_router(farms_router)
    app.include_router(market_router)
    app.include_router(weather_router)
    app.include_router(soil_router)
    app.include_router(reco_router)  # NEW
    app.include_router(crop_disease_router)
    app.include_router(market_forecast_router) 
    app.include_router(ai_router)
    app.include_router(ai_graph_router)
    app.include_router(ai_agent_router)
    app.include_router(rag_router)
    app.include_router(market_meta_router)

    return app

app = create_app()



# Run (PowerShell/cmd):
# uvicorn backend.app.main:app --reload --port 8000
