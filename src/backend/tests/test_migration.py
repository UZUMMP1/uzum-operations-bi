from datetime import date
from pathlib import Path

import pytest
from sqlalchemy import create_engine, func, select

from app.database import Base
from app.models import InventoryHistory, SalesRecord, TrafficHistory, UploadBatch
from scripts.migrate_sqlite_to_postgres import migrate


def make_source(path: Path) -> None:
    engine = create_engine(f"sqlite:///{path}")
    Base.metadata.create_all(engine)
    with engine.begin() as connection:
        connection.execute(
            UploadBatch.__table__.insert(),
            {"id": 1, "data_type": "sales", "filename": "sales.xlsx", "file_hash": "abc", "row_count": 1, "status": "success"},
        )
        connection.execute(
            SalesRecord.__table__.insert(),
            {"id": 1, "batch_id": 1, "created_date": date(2026, 8, 9), "order_no": "A1", "sku": "10001", "quantity": 2, "returns": 1, "gmv": 1000},
        )


def test_migration_copies_all_tables_and_refuses_overwrite(tmp_path):
    source = tmp_path / "source.db"
    target = tmp_path / "target.db"
    make_source(source)

    counts = migrate(source, f"sqlite:///{target}")
    assert counts == {
        "upload_batches": 1,
        "inventory_history": 0,
        "sales_records": 1,
        "traffic_history": 0,
        "product_mappings": 0,
    }

    with pytest.raises(RuntimeError, match="已经有数据"):
        migrate(source, f"sqlite:///{target}")

    target_engine = create_engine(f"sqlite:///{target}")
    with target_engine.connect() as connection:
        assert connection.scalar(select(func.count()).select_from(SalesRecord)) == 1
