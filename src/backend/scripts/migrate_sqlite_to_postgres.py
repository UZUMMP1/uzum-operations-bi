"""Copy the complete UZUM BI history from SQLite to a cloud database."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

from sqlalchemy import create_engine, delete, func, select, text

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.database import Base  # noqa: E402
from app import models  # noqa: F401,E402


def normalize_database_url(url: str) -> str:
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


def row_counts(engine) -> dict[str, int]:
    with engine.connect() as connection:
        return {
            table.name: connection.scalar(select(func.count()).select_from(table)) or 0
            for table in Base.metadata.sorted_tables
        }


def migrate(source_path: Path, target_url: str, replace: bool = False) -> dict[str, int]:
    if not source_path.is_file():
        raise FileNotFoundError(f"找不到本地数据库：{source_path}")

    source_engine = create_engine(
        f"sqlite:///{source_path.resolve()}", connect_args={"check_same_thread": False}
    )
    target_engine = create_engine(normalize_database_url(target_url), pool_pre_ping=True)

    Base.metadata.create_all(target_engine)
    existing = row_counts(target_engine)
    if any(existing.values()) and not replace:
        raise RuntimeError(
            "目标数据库中已经有数据。为避免覆盖，请使用一个空数据库；"
            "确认需要完全替换时再添加 --replace。"
        )

    with source_engine.connect() as source, target_engine.begin() as target:
        if replace:
            for table in reversed(Base.metadata.sorted_tables):
                target.execute(delete(table))

        for table in Base.metadata.sorted_tables:
            rows = source.execute(select(table)).mappings()
            while chunk := rows.fetchmany(1000):
                target.execute(table.insert(), [dict(row) for row in chunk])

        if target_engine.dialect.name == "postgresql":
            for table in Base.metadata.sorted_tables:
                if "id" not in table.c:
                    continue
                target.execute(
                    text(
                        "SELECT setval(pg_get_serial_sequence(:table_name, 'id'), "
                        "COALESCE(MAX(id), 1), MAX(id) IS NOT NULL) FROM "
                        f'"{table.name}"'
                    ),
                    {"table_name": table.name},
                )

    source_counts = row_counts(source_engine)
    target_counts = row_counts(target_engine)
    if source_counts != target_counts:
        raise RuntimeError(
            f"迁移校验失败。源数据库：{source_counts}；目标数据库：{target_counts}"
        )
    return target_counts


def main() -> None:
    parser = argparse.ArgumentParser(description="迁移 UZUM BI 历史数据")
    parser.add_argument(
        "--source",
        type=Path,
        default=BACKEND_DIR / "uzum_bi.db",
        help="本地 SQLite 数据库路径",
    )
    parser.add_argument(
        "--target",
        default=os.getenv("DATABASE_URL"),
        help="目标数据库连接地址，默认读取 DATABASE_URL",
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        help="清空目标数据库并用本地历史完整替换",
    )
    args = parser.parse_args()
    if not args.target:
        parser.error("请通过 --target 或 DATABASE_URL 提供目标数据库连接地址")

    counts = migrate(args.source, args.target, args.replace)
    print("迁移成功，源数据库与目标数据库行数完全一致：")
    for table_name, count in counts.items():
        print(f"  {table_name}: {count:,} 行")


if __name__ == "__main__":
    main()
