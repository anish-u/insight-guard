from fastapi import APIRouter, Depends
from neo4j import Driver
from ..neo4j_client import driver_dependency

router = APIRouter()


@router.get("/hello")
async def hello():
  return {"message": "Hello from FastAPI + Neo4j 👋"}


@router.get("/health")
async def health(driver: Driver = Depends(driver_dependency)):
  """
  Health check that also verifies connectivity to Neo4j.
  """
  try:
    with driver.session() as session:
      result = session.run("RETURN 1 AS ok")
      record = result.single()
      if record and record["ok"] == 1:
        return {"status": "ok", "neo4j": "connected"}
      return {"status": "degraded", "neo4j": "unexpected_response"}
  except Exception as exc:
    return {"status": "error", "neo4j": f"connection_failed: {exc}"}
