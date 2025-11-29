import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from neo4j import GraphDatabase, basic_auth

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "NEO4J_PASS")

app = FastAPI(title="Neo4j Test API")

# Allow frontend (React) to call the API
origins = [
    "http://localhost:3000",
    "http://localhost:5173",   # Vite default dev port
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

driver = GraphDatabase.driver(
    NEO4J_URI,
    auth=basic_auth(NEO4J_USER, NEO4J_PASSWORD)
)


@app.get("/hello")
async def hello():
    return {"message": "Hello from FastAPI + Neo4j setup 👋"}


@app.get("/health")
async def health():
    """
    Simple health check that also verifies we can talk to Neo4j.
    """
    try:
        with driver.session() as session:
            result = session.run("RETURN 1 AS ok")
            record = result.single()
            if record and record["ok"] == 1:
                return {"status": "ok", "neo4j": "connected"}
            else:
                return {"status": "degraded", "neo4j": "unexpected_response"}
    except Exception as e:
        return {"status": "error", "neo4j": f"connection_failed: {e}"}


@app.on_event("shutdown")
def close_driver():
    driver.close()
