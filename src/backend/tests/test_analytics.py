from datetime import date
from app.main import _bucket, _business_category, _category_breakdown, _daily_diagnosis, _data_quality_overview, _inventory_plan_data, _period_diagnosis, _period_metrics, returns_monitor, sales_products

def test_week_bucket_starts_on_monday():
    assert _bucket(date(2026, 8, 7), "week") == date(2026, 8, 3)

def test_month_bucket_starts_on_first_day():
    assert _bucket(date(2026, 8, 7), "month") == date(2026, 8, 1)

def test_business_categories_split_phones_and_tablets():
    assert _business_category({"category": "Смартфоны Android"}) == "手机"
    assert _business_category({"category": "Планшеты"}) == "平板"
    assert _business_category({"category": "Умные часы"}) == "可穿戴及其他"
    assert _business_category({"seller_sku": "REDMIHEADPHONESNEO"}) == "可穿戴及其他"

def test_returns_monitor_splits_cancellations_and_refunds_by_received_date():
    from app.database import Base
    from app.models import InventoryHistory, SalesRecord, UploadBatch
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        batch = UploadBatch(data_type="sales", filename="returns.xlsx", file_hash="returns-monitor")
        db.add(batch)
        db.flush()
        db.add_all([
            SalesRecord(batch_id=batch.id, created_date=date(2026, 8, 8), received_date=None, order_no="C1", sku="CANCEL", quantity=2, returns=2, gmv=0),
            SalesRecord(batch_id=batch.id, created_date=date(2026, 8, 8), received_date=date(2026, 8, 10), order_no="R1", sku="REFUND", quantity=3, returns=3, gmv=0),
            SalesRecord(batch_id=batch.id, created_date=date(2026, 8, 8), received_date=None, order_no="N1", sku="IGNORED", quantity=1, returns=0, gmv=100),
            InventoryHistory(batch_id=batch.id, download_date=date(2026, 8, 9), sku="CANCEL", product="取消商品", region="EU", inventory=5),
            InventoryHistory(batch_id=batch.id, download_date=date(2026, 8, 9), sku="REFUND", product="退款商品", region="RU", inventory=4),
        ])
        db.commit()

        result = returns_monitor(date(2026, 8, 8), date(2026, 8, 8), db)

        assert result["trend"] == [{"date": date(2026, 8, 8), "cancellations": 2.0, "refunds": 3.0}]
        assert result["top_cancellations"][0]["sku"] == "CANCEL"
        assert result["top_cancellations"][0]["cancellations"] == 2.0
        assert result["top_refunds"][0]["sku"] == "REFUND"
        assert result["top_refunds"][0]["refunds"] == 3.0

def test_inventory_plan_uses_14_days_and_separates_zero_movement():
    from app.database import Base
    from app.models import InventoryHistory, SalesRecord, UploadBatch
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        batch = UploadBatch(data_type="inventory", filename="test.xlsx", file_hash="plan-test")
        db.add(batch)
        db.flush()
        db.add_all([
                # Inventory DATE is shifted back one day: 8/8 stock is used
                # for the 8/7 sales-day PSI calculation.
                InventoryHistory(batch_id=batch.id, download_date=date(2026, 8, 8), sku="PHONE", product="手机", region="EU", inventory=20),
                InventoryHistory(batch_id=batch.id, download_date=date(2026, 8, 8), sku="SLOW", product="手机", region="EU", inventory=50),
            SalesRecord(batch_id=batch.id, created_date=date(2026, 8, 7), order_no="A1", sku="PHONE", quantity=14, returns=0, gmv=140),
        ])
        db.commit()
        result = _inventory_plan_data(db, date(2026, 8, 7))
        by_sku = {item["sku"]: item for item in result["items"]}
        assert by_sku["PHONE"]["average_sales_14d"] == 1
        assert by_sku["PHONE"]["dos"] == 20
        assert by_sku["PHONE"]["replenishment"] == 8
        assert by_sku["PHONE"]["lifetime_sales"] == 14
        assert by_sku["SLOW"]["dos"] is None
        assert by_sku["SLOW"]["status"] == "slow"

def test_category_breakdown_includes_orders_uv_asp_and_cvr():
    rows = _category_breakdown([
        {"category": "smartphone", "so": 8, "orders": 10, "gmv": 800, "uv": 100},
        {"category": "smartphone", "so": 4, "orders": 5, "gmv": 600, "uv": 50},
    ])
    phone = next(item for item in rows if item["category"] == "手机")
    assert phone["orders"] == 15
    assert phone["uv"] == 150
    assert phone["asp"] == 1400 / 12
    assert phone["cvr"] == 0.1

def test_sales_products_compares_with_previous_equal_length_period():
    from app.database import Base
    from app.models import SalesRecord, UploadBatch
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        batch = UploadBatch(data_type="sales", filename="comparison.xlsx", file_hash="product-comparison")
        db.add(batch); db.flush()
        db.add_all([
            SalesRecord(batch_id=batch.id, created_date=date(2026, 8, 1), order_no="P1", sku="PHONE", category="smartphone", quantity=5, returns=1, gmv=400),
            SalesRecord(batch_id=batch.id, created_date=date(2026, 8, 2), order_no="P2", sku="PHONE", category="smartphone", quantity=10, returns=2, gmv=800),
            SalesRecord(batch_id=batch.id, created_date=date(2026, 8, 3), order_no="C1", sku="PHONE", category="smartphone", quantity=15, returns=3, gmv=1200),
            SalesRecord(batch_id=batch.id, created_date=date(2026, 8, 4), order_no="C2", sku="PHONE", category="smartphone", quantity=15, returns=3, gmv=1200),
        ])
        db.commit()
        result = sales_products(date(2026, 8, 3), date(2026, 8, 4), category="all", db=db)
        assert result[0]["comparisons"]["so"] == 1.0
        assert result[0]["comparisons"]["orders"] == 1.0
        assert result[0]["comparisons"]["gmv"] == 1.0

def test_daily_diagnosis_compares_eight_business_signals():
    from app.database import Base
    from app.models import InventoryHistory, SalesRecord, TrafficHistory, UploadBatch
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        batch = UploadBatch(data_type="sales", filename="test.xlsx", file_hash="daily-diagnosis")
        db.add(batch)
        db.flush()
        db.add_all([
            SalesRecord(batch_id=batch.id, created_date=date(2026, 8, 6), order_no="P1", sku="PHONE", category="smartphone", quantity=100, returns=0, gmv=10000),
            SalesRecord(batch_id=batch.id, created_date=date(2026, 8, 7), order_no="C1", sku="PHONE", category="smartphone", quantity=80, returns=10, gmv=7000),
            TrafficHistory(batch_id=batch.id, record_date=date(2026, 8, 6), sku="PHONE", uv=1000),
            TrafficHistory(batch_id=batch.id, record_date=date(2026, 8, 7), sku="PHONE", uv=800),
            InventoryHistory(batch_id=batch.id, download_date=date(2026, 8, 7), sku="PHONE", product="POCO Test", region="EU", inventory=10),
            InventoryHistory(batch_id=batch.id, download_date=date(2026, 8, 8), sku="PHONE", product="POCO Test", region="EU", inventory=0),
        ])
        db.commit()

        result = _daily_diagnosis(db, date(2026, 8, 7))

        assert result["direction"] == "decline"
        assert result["changes"]["so"] == -0.3
        assert result["changes"]["uv"] == -0.2
        assert result["changes"]["return_rate"] is None  # previous rate is zero
        assert result["stockouts"][0]["product"] == "POCO Test"
        assert result["sku_drivers"][0]["delta_so"] == -30
        assert result["category_drivers"][0]["delta_so"] == -30
        assert result["data_quality"]["complete"] is True
        assert [item["key"] for item in result["checks"]] == ["uv", "cvr", "asp", "stockout", "return_rate", "sku", "category", "quality"]

def test_daily_diagnosis_uses_positive_sku_drivers_when_sales_grow():
    from app.database import Base
    from app.models import SalesRecord, UploadBatch
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        batch = UploadBatch(data_type="sales", filename="growth.xlsx", file_hash="growth-diagnosis")
        db.add(batch); db.flush()
        db.add_all([
            SalesRecord(batch_id=batch.id, created_date=date(2026, 8, 8), order_no="A1", sku="PHONE-A", category="smartphone", quantity=5, returns=0, gmv=500),
            SalesRecord(batch_id=batch.id, created_date=date(2026, 8, 9), order_no="A2", sku="PHONE-A", category="smartphone", quantity=12, returns=0, gmv=1200),
            SalesRecord(batch_id=batch.id, created_date=date(2026, 8, 8), order_no="B1", sku="PHONE-B", category="smartphone", quantity=4, returns=0, gmv=400),
            SalesRecord(batch_id=batch.id, created_date=date(2026, 8, 9), order_no="B2", sku="PHONE-B", category="smartphone", quantity=6, returns=0, gmv=600),
        ])
        db.commit()
        result = _daily_diagnosis(db, date(2026, 8, 9))
        assert result["direction"] == "growth"
        assert result["sku_drivers"][0]["sku"] == "PHONE-A"
        assert result["sku_drivers"][0]["delta_so"] == 7
        assert next(item for item in result["checks"] if item["key"] == "sku")["label"] == "哪些SKU对上升贡献最大"

def test_period_diagnosis_compares_equal_length_stages_in_eight_steps():
    from app.database import Base
    from app.models import SalesRecord, TrafficHistory, UploadBatch
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        batch = UploadBatch(data_type="sales", filename="period.xlsx", file_hash="period-diagnosis")
        db.add(batch); db.flush()
        for index, day in enumerate((date(2026, 8, 1), date(2026, 8, 2), date(2026, 8, 3), date(2026, 8, 4))):
            quantity = 10 if index < 2 else 6
            db.add(SalesRecord(batch_id=batch.id, created_date=day, order_no=f"O{index}", sku="PHONE", category="smartphone", quantity=quantity, returns=0, gmv=quantity*100))
            db.add(TrafficHistory(batch_id=batch.id, record_date=day, sku="PHONE", uv=quantity*10))
        db.commit()
        result = _period_diagnosis(db, date(2026, 8, 3), date(2026, 8, 4), date(2026, 8, 1), date(2026, 8, 2))
        assert result["direction"] == "decline"
        assert result["changes"]["so"] == -0.4
        assert result["sku_drivers"][0]["delta_so"] == -8
        assert [item["key"] for item in result["checks"]] == ["uv", "cvr", "asp", "stockout", "return_rate", "sku", "category", "quality"]

def test_period_metrics_respects_global_business_category():
    from app.database import Base
    from app.models import SalesRecord, UploadBatch
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        batch = UploadBatch(data_type="sales", filename="category.xlsx", file_hash="category-filter")
        db.add(batch); db.flush()
        db.add_all([
            SalesRecord(batch_id=batch.id, created_date=date(2026, 8, 9), order_no="P1", sku="PHONE", category="smartphone", quantity=10, returns=1, gmv=900),
            SalesRecord(batch_id=batch.id, created_date=date(2026, 8, 9), order_no="A1", sku="BUDS", category="headphones", quantity=20, returns=0, gmv=400),
        ])
        db.commit()
        phone = _period_metrics(db, date(2026, 8, 9), date(2026, 8, 9), "phone")
        aiot = _period_metrics(db, date(2026, 8, 9), date(2026, 8, 9), "aiot")
        assert phone["so"] == 9
        assert phone["gmv"] == 900
        assert aiot["so"] == 20
        assert aiot["gmv"] == 400

def test_data_quality_overview_reports_gaps_and_upload_history():
    from app.database import Base
    from app.models import InventoryHistory, SalesRecord, TrafficHistory, UploadBatch
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        batch = UploadBatch(data_type="sales", filename="sales.xlsx", file_hash="quality-overview", row_count=2, status="success")
        db.add(batch); db.flush()
        db.add_all([
            SalesRecord(batch_id=batch.id, created_date=date(2026, 8, 1), order_no="A1", sku="PHONE", quantity=1, returns=0, gmv=100),
            SalesRecord(batch_id=batch.id, created_date=date(2026, 8, 2), order_no="A2", sku="PHONE", quantity=1, returns=0, gmv=100),
            TrafficHistory(batch_id=batch.id, record_date=date(2026, 8, 1), sku="PHONE", uv=10),
            InventoryHistory(batch_id=batch.id, download_date=date(2026, 8, 2), sku="PHONE", inventory=10),
            InventoryHistory(batch_id=batch.id, download_date=date(2026, 8, 3), sku="PHONE", inventory=9),
        ])
        db.commit()

        result = _data_quality_overview(db, date(2026, 8, 1), date(2026, 8, 2))

        assert result["complete"] is False
        assert result["sources"]["sales"]["covered_days"] == 2
        assert result["sources"]["traffic"]["missing_dates"] == [date(2026, 8, 2)]
        assert result["sources"]["inventory"]["covered_days"] == 2
        assert result["issues"][0]["code"] == "traffic_gap"
        assert result["uploads"][0]["filename"] == "sales.xlsx"
