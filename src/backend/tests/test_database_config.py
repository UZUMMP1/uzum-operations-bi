def test_default_database_is_sqlite():
    import app.database as database
    assert database.engine.dialect.name == "sqlite"


def test_postgres_url_is_normalized():
    from app.database import normalize_database_url
    assert normalize_database_url("postgresql://user:pass@example.com/db").startswith("postgresql+psycopg://")
    assert normalize_database_url("postgres://user:pass@example.com/db").startswith("postgresql+psycopg://")


def test_serverless_postgres_uses_no_persistent_pool():
    from app.database import build_engine_options
    from sqlalchemy.pool import NullPool

    options = build_engine_options("postgresql+psycopg://user:pass@example.com/db", True)
    assert options["poolclass"] is NullPool
