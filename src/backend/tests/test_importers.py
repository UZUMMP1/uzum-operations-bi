import io
from datetime import date
import pandas as pd
from app.importers import _columns, _read_excel, parse_seller_sku_color

def test_wearable_sku_colors_are_recognized():
    assert parse_seller_sku_color("XIAOMI0-ФИТНЕСБРАСЛЕТЫXIAOMISMARTBAND10PRO-ЧЕРН") == "黑色"
    assert parse_seller_sku_color("XIAOMI0-НАУШНИКИREDMIBUDS8ACTIVE-БЕЛЫЙ") == "白色"
    assert parse_seller_sku_color("XIAOMI0-REDMIPAD2-БИРЮЗОВЫЙ-8/256-EU") == "青绿色"

def test_russian_sales_columns_are_recognized():
    frame = pd.DataFrame(columns=["дата создана", "№ заказа", "Штрихкод", "количество", "возвраты", "GMV"])
    result = _columns(frame, ["created_date", "order_no", "sku", "quantity", "returns", "gmv"], {"created_date", "order_no", "sku", "quantity", "returns", "gmv"})
    assert result["created_date"] == "дата создана"
    assert result["sku"] == "Штрихкод"

def test_excel_reader_rejects_empty_file():
    output = io.BytesIO()
    pd.DataFrame().to_excel(output, index=False)
    try:
        _read_excel(output.getvalue(), "empty.xlsx", "sales")
        assert False
    except ValueError as exc:
        assert "没有可导入的数据" in str(exc)

def test_sales_template_detects_second_row_header():
    output = io.BytesIO()
    pd.DataFrame([
        ["Данные отображаются по часовому поясу Узбекистана, GMT+5", None, None, None, None, None],
        ["Дата создания", "№ заказа", "Штрихкод", "Количество", "Возвраты", "Выручка (сумы)"],
        ["06.08.2026 06:31", 120850477, "1000104504830", 1, 0, 139000],
    ]).to_excel(output, index=False, header=False)
    frame = _read_excel(output.getvalue(), "sales.xlsx", "sales")
    assert list(frame.columns)[:2] == ["Дата создания", "№ заказа"]
    assert frame.iloc[0]["Выручка (сумы)"] == 139000

def test_traffic_template_skips_bilingual_second_header():
    output = io.BytesIO()
    pd.DataFrame([
        ["日期", "条形码", "展示次数", "打开\n商品详情页，次数"],
        ["Дата", "Штрихкод", "Показы, раз", "Открыли\nкарточку, раз"],
        [46185, "1000104478209", 175, 5],
    ]).to_excel(output, index=False, header=False)
    frame = _read_excel(output.getvalue(), "traffic.xlsx", "traffic")
    assert len(frame) == 1
    assert frame.iloc[0]["条形码"] == "1000104478209"

def test_excel_serial_date_is_supported():
    from app.importers import _date
    assert _date(46185, "日期") == date(2026, 6, 12)

def test_zero_sku_is_not_a_real_traffic_record():
    from app.importers import _import_traffic
    from app.database import Base
    from app.models import TrafficHistory, UploadBatch
    from sqlalchemy import create_engine, func, select
    from sqlalchemy.orm import Session
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        batch = UploadBatch(data_type="traffic", filename="traffic.xlsx", file_hash="test-zero")
        db.add(batch); db.flush()
        frame = pd.DataFrame({"日期": [46185, 46185], "条形码": [0, "1000104478209"], "打开 商品详情页，次数": [14, 5], "展示次数": [356, 175]})
        assert _import_traffic(db, batch.id, frame) == 1

def test_inventory_reupload_replaces_same_day_snapshot():
    from app.importers import _import_inventory
    from app.database import Base
    from app.models import InventoryHistory, UploadBatch
    from sqlalchemy import create_engine, select
    from sqlalchemy.orm import Session
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        first = UploadBatch(data_type="inventory", filename="first.xlsx", file_hash="inventory-first")
        second = UploadBatch(data_type="inventory", filename="second.xlsx", file_hash="inventory-second")
        db.add_all([first, second]); db.flush()
        frame1 = pd.DataFrame({"SKU": ["1001"], "库存": [5]})
        frame2 = pd.DataFrame({"SKU": ["1001"], "库存": [9]})
        _import_inventory(db, first.id, frame1, date(2026, 8, 7)); db.commit()
        _import_inventory(db, second.id, frame2, date(2026, 8, 7)); db.commit()
        rows = list(db.scalars(select(InventoryHistory)))
        assert len(rows) == 1
        assert rows[0].inventory == 9
        assert rows[0].batch_id == second.id

def test_traffic_reupload_replaces_overlapping_dates():
    from app.importers import _import_traffic
    from app.database import Base
    from app.models import TrafficHistory, UploadBatch
    from sqlalchemy import create_engine, select
    from sqlalchemy.orm import Session
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        first = UploadBatch(data_type="traffic", filename="first.xlsx", file_hash="traffic-first")
        second = UploadBatch(data_type="traffic", filename="second.xlsx", file_hash="traffic-second")
        db.add_all([first, second]); db.flush()
        frame1 = pd.DataFrame({"日期": [46185], "条形码": ["1001"], "打开 商品详情页，次数": [5]})
        frame2 = pd.DataFrame({"日期": [46185], "条形码": ["1001"], "打开 商品详情页，次数": [8]})
        _import_traffic(db, first.id, frame1); db.commit()
        _import_traffic(db, second.id, frame2); db.commit()
        rows = list(db.scalars(select(TrafficHistory)))
        assert len(rows) == 1
        assert rows[0].uv == 8
        assert rows[0].batch_id == second.id

def test_sales_reupload_replaces_overlapping_dates():
    from app.importers import _import_sales
    from app.database import Base
    from app.models import SalesRecord, UploadBatch
    from sqlalchemy import create_engine, select
    from sqlalchemy.orm import Session
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        first = UploadBatch(data_type="sales", filename="first.xlsx", file_hash="sales-first")
        second = UploadBatch(data_type="sales", filename="second.xlsx", file_hash="sales-second")
        db.add_all([first, second]); db.flush()
        frame1 = pd.DataFrame({"创建日期": ["2026-08-07"], "订单号": ["A1"], "SKU": ["1001"], "订单量": [1], "取消退款": [0], "GMV": [100]})
        frame2 = pd.DataFrame({"创建日期": ["2026-08-07"], "订单号": ["A2"], "SKU": ["1001"], "订单量": [2], "取消退款": [0], "GMV": [180]})
        _import_sales(db, first.id, frame1); db.commit()
        _import_sales(db, second.id, frame2); db.commit()
        rows = list(db.scalars(select(SalesRecord)))
        assert len(rows) == 1
        assert rows[0].order_no == "A2"
        assert rows[0].quantity == 2
        assert rows[0].batch_id == second.id

def test_cumulative_inventory_uses_row_dates_and_parses_variant():
    from app.importers import _import_inventory
    from app.database import Base
    from app.models import InventoryHistory, UploadBatch
    from sqlalchemy import create_engine, select
    from sqlalchemy.orm import Session
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        batch = UploadBatch(data_type="inventory", filename="history.xlsx", file_hash="inventory-history")
        db.add(batch); db.flush()
        frame = pd.DataFrame({
            "DATE": [46230, 46231],
            "SKU": ["XIAOMI0-СМАРТФОНPOCOC81PRO-ЧЕРН-4/128-EU"] * 2,
            "Штрихкод": ["1001", "1001"],
            "Название товара": ["POCO C81 Pro", "POCO C81 Pro"],
            "На стороне маркетплейса (всего в продаже, в пути, на складах и фотостудии), шт": [65, 41],
            "В продаже, шт": [60, 37],
        })
        assert _import_inventory(db, batch.id, frame, None) == 2
        db.commit()
        rows = list(db.scalars(select(InventoryHistory).order_by(InventoryHistory.download_date)))
        assert [row.download_date for row in rows] == [date(2026, 7, 27), date(2026, 7, 28)]
        assert rows[0].seller_sku.endswith("4/128-EU")
        assert rows[0].memory == "4/128"
        assert rows[0].color == "黑色"
        assert rows[0].region == "EU"
        assert [row.inventory for row in rows] == [60, 37]
