from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .logging_config import setup_logging
from .neo4j_client import init_driver, close_driver
from .api.routes_root import router as root_router
from .api.routes_ingest import router as ingest_router


setup_logging()

app = FastAPI(
  title="InsightGuard Backend",
  version="1.0.0",
  description="Backend API for InsightGuard demo (FastAPI + Neo4j).",
)

app.add_middleware(
  CORSMiddleware,
  allow_origins=settings.cors_origins,
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup() -> None:
  init_driver()


@app.on_event("shutdown")
async def on_shutdown() -> None:
  await close_driver()


app.include_router(root_router)
app.include_router(ingest_router)
