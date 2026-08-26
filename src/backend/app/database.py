import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import NullPool

DB_PATH = Path(__file__).resolve().parents[1] / "uzum_bi.db"


def normalize_database_url(url: str) -> str:
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


DATABASE_URL = normalize_database_url(os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH}"))


def build_engine_options(database_url: str, serverless: bool = False) -> dict:
    options: dict = {"pool_pre_ping": True}
    if database_url.startswith("sqlite"):
        options["connect_args"] = {"check_same_thread": False}
    elif serverless:
        options["poolclass"] = NullPool
    return options


# Railway can put an idle service to sleep only when it stops producing
# outbound traffic, so serverless deployments must not retain DB connections.
SERVERLESS = os.getenv("UZUM_SERVERLESS") == "1" or bool(os.getenv("RAILWAY_ENVIRONMENT"))
engine_options = build_engine_options(DATABASE_URL, SERVERLESS)

engine = create_engine(DATABASE_URL, **engine_options)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

class Base(DeclarativeBase):
    pass
