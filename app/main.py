import os
from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.data_loader import init_db, get_db
from app.models import QueryRequest, QueryResponse
from app.query_engine import process_query


def load_env():
    if os.path.exists(".env"):
        with open(".env", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ[k.strip()] = v.strip().strip("'\"")


load_env()

@asynccontextmanager
async def lifespan(app: FastAPI):
    load_env()
    init_db()
    yield


app = FastAPI(title="Intelligent Analytics Query Engine", lifespan=lifespan)


@app.get("/health")
def health():
    db = get_db()
    tables = [r[0] for r in db.execute("SHOW TABLES;").fetchall()]
    return {"status": "ok", "tables_loaded": tables}


@app.post("/query", response_model=QueryResponse)
def query(payload: QueryRequest):
    load_env()
    return process_query(payload.query)
