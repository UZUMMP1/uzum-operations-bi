from __future__ import annotations

import hashlib
import io
import re
from datetime import date, datetime

import pandas as pd
from fastapi import HTTPException, UploadFile
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .models import InventoryHistory, SalesRecord, TrafficHistory, UploadBatch


ALIASES = {
    "created_date": ["дата создана", "дата создания", "created date", "创建日期", "日期"],
    "received_date": ["дата получения", "received date", "收货日期"],
    "order_no": ["№ заказа", "номер заказа", "order no", "订单号"],
    "sku": ["штрихкод", "sku", "barcode", "条形码"],
    "category": ["категория", "category", "分类", "品类"],
    "quantity": ["количество", "quantity", "订单量", "销量"],
    "returns": ["возвраты", "return", "returns", "取消退款", "退货"],
    "gmv": ["выручка (сумы)", "gmv", "сумма продажи", "сумма продаж", "сумма", "sales amount", "销售金额", "金额"],
    "product": ["название товара", "товар", "продукт", "product", "产品", "商品名称"],
    "color": ["цвет", "color", "颜色"],
    "memory": ["память", "memory", "内存"],
    "region": ["регион", "region", "地区", "仓库"],
    "inventory": ["в продаже, шт", "на стороне маркетплейса (всего в продаже, в пути, на складах и фотостудии), шт", "остаток", "inventory", "stock", "库存", "库存量"],
    "record_date": ["дата", "date", "日期"],
    "uv": ["открыли карточку, раз", "打开 商品详情页，次数", "uv", "посетители", "访客", "访客数"],
    "clicks": ["открыли карточку, раз", "打开 商品详情页，次数", "клики", "clicks", "点击", "点击量"],
    "impressions": ["показы, раз", "展示次数", "показы", "impressions", "曝光", "曝光量"],
    "seller_sku": ["sku"],
}

PARSER_HASH_SALT = {"inventory": b":inventory-in-sale-v1"}

DATASET_FIELDS = {
    "sales": ["created_date", "received_date", "order_no", "sku", "category", "quantity", "returns", "gmv"],
    "inventory": ["record_date", "sku", "seller_sku", "product", "color", "memory", "region", "inventory"],
    "traffic": ["record_date", "sku", "uv", "clicks", "impressions"],
}

DISPLAY_FIELDS = {
    "created_date": "Дата создания（创建日期）", "order_no": "№ заказа（订单号）",
    "sku": "Штрихкод（条形码）", "quantity": "Количество（数量）",
    "returns": "Возвраты（退货/取消）", "gmv": "Выручка (сумы)（销售额）",
    "inventory": "在售库存（В продаже, шт）", "record_date": "日期", "uv": "打开商品详情页次数",
}

COLOR_NAMES = {
    "ЧЕРН": "黑色", "БЕЛ": "白色", "БЕЛЫЙ": "白色", "ЗЕЛЕН": "绿色",
    "ФИОЛЕТ": "紫色", "СИНИЙ": "蓝色", "СИН": "蓝色", "ГОЛУБ": "浅蓝色", "ЗОЛОТ": "金色",
    "ОРАНЖ": "橙色", "РОЗОВ": "粉色", "СВЕТСИН": "浅蓝色", "СЕРЕБР": "银色",
    "СЕРЫЙ": "灰色", "КРАСН": "红色", "БЕЖ": "米色", "КОРИЧ": "棕色",
    "БИРЮЗ": "青绿色", "СЕРЕБРН": "银色", "ГРАФИТ": "石墨色",
}

COLOR_PATTERN = re.compile(r"-(" + "|".join(sorted(COLOR_NAMES, key=len, reverse=True)) + r")[^-]*(?:-|$)")


def parse_seller_sku_color(seller_sku: str) -> str | None:
    normalized = (seller_sku or "").upper()
    match = COLOR_PATTERN.search(normalized)
    if match:
        return COLOR_NAMES.get(match.group(1))
    for segment in re.split(r"[-_/\s]+", normalized):
        for token in sorted(COLOR_NAMES, key=len, reverse=True):
            if segment.startswith(token):
                return COLOR_NAMES[token]
    return None


def _normalize(value: object) -> str:
    return re.sub(r"\s+", " ", str(value).strip().lower().replace("ё", "е"))


def _columns(frame: pd.DataFrame, fields: list[str], required: set[str]) -> dict[str, str]:
    normalized = {_normalize(column): str(column) for column in frame.columns}
    result: dict[str, str] = {}
    for field in fields:
        for alias in ALIASES[field]:
            if _normalize(alias) in normalized:
                result[field] = normalized[_normalize(alias)]
                break
    missing = sorted(required - result.keys())
    if missing:
        available = "、".join(map(str, frame.columns[:20]))
        labels = "、".join(DISPLAY_FIELDS.get(field, field) for field in missing)
        raise ValueError(f"缺少必要字段：{labels}。检测到的字段：{available}")
    return result


def _row_alias_score(values: list[object], data_type: str) -> int:
    cells = {_normalize(value) for value in values if not pd.isna(value)}
    return sum(any(_normalize(alias) in cells for alias in ALIASES[field]) for field in DATASET_FIELDS[data_type])


def _read_excel(content: bytes, filename: str, data_type: str) -> pd.DataFrame:
    if not filename.lower().endswith((".xlsx", ".xlsm")):
        raise ValueError("目前支持 .xlsx 或 .xlsm 文件，请将旧版 .xls 另存为 .xlsx")
    raw = pd.read_excel(io.BytesIO(content), engine="openpyxl", header=None)
    raw = raw.dropna(how="all")
    if raw.empty:
        raise ValueError("Excel 中没有可导入的数据")
    candidates = [(_row_alias_score(raw.iloc[index].tolist(), data_type), index) for index in range(min(12, len(raw)))]
    score, header_index = max(candidates, key=lambda item: item[0])
    if score < 2:
        preview = "、".join(_text(value) for value in raw.iloc[0].tolist()[:20] if not pd.isna(value))
        raise ValueError(f"前 12 行未找到可识别的{data_type}表头。首行内容：{preview}")
    header = [_text(value, f"Unnamed: {index}") for index, value in enumerate(raw.iloc[header_index].tolist())]
    frame = raw.iloc[header_index + 1:].copy()
    frame.columns = header
    while len(frame) and _row_alias_score(frame.iloc[0].tolist(), data_type) >= 2:
        frame = frame.iloc[1:]
    frame = frame.dropna(how="all").reset_index(drop=True)
    if frame.empty:
        raise ValueError("Excel 表头下方没有可导入的数据")
    return frame


def _text(value: object, default: str = "") -> str:
    if pd.isna(value):
        return default
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def _number(value: object) -> float:
    if pd.isna(value) or value == "":
        return 0.0
    if isinstance(value, str):
        value = value.replace(" ", "").replace("\u00a0", "").replace(",", ".")
    return float(value)


def _date(value: object, field: str, optional: bool = False) -> date | None:
    if pd.isna(value) or value == "":
        if optional:
            return None
        raise ValueError(f"{field} 存在空日期")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        parsed = pd.to_datetime(value, unit="D", origin="1899-12-30", errors="coerce")
    else:
        parsed = pd.to_datetime(value, errors="coerce", dayfirst=True)
    if pd.isna(parsed):
        raise ValueError(f"{field} 包含无法识别的日期：{value}")
    return parsed.date()


async def import_file(db: Session, data_type: str, upload: UploadFile, snapshot_date: date | None = None, skip_duplicate: bool = False) -> dict:
    content = await upload.read()
    digest = hashlib.sha256(content + PARSER_HASH_SALT.get(data_type, b"")).hexdigest()
    duplicate = db.scalar(select(UploadBatch).where(UploadBatch.file_hash == digest))
    if duplicate:
        if skip_duplicate:
            return {"type": data_type, "filename": duplicate.filename, "rows": duplicate.row_count, "status": "skipped", "message": "文件已导入，已跳过"}
        raise HTTPException(status_code=409, detail=f"文件已于 {duplicate.uploaded_at:%Y-%m-%d %H:%M} 导入，请勿重复上传")

    batch = UploadBatch(data_type=data_type, filename=upload.filename or "unknown.xlsx", file_hash=digest)
    db.add(batch)
    db.flush()
    try:
        frame = _read_excel(content, batch.filename, data_type)
        if data_type == "sales":
            count = _import_sales(db, batch.id, frame)
        elif data_type == "inventory":
            count = _import_inventory(db, batch.id, frame, snapshot_date)
        else:
            count = _import_traffic(db, batch.id, frame)
        batch.row_count = count
        batch.status = "success"
        db.commit()
        return {"type": data_type, "filename": batch.filename, "rows": count, "status": "success"}
    except HTTPException:
        db.rollback()
        raise
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=422,
            detail=f"{batch.filename} 导入失败：同一日期存在重复的 SKU 数据，请重新上传；系统不会重复保存。",
        ) from exc
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=422, detail=f"{batch.filename} 导入失败：{exc}") from exc
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=422,
            detail=f"{batch.filename} 导入失败：程序未能处理这个文件，请确认文件格式后重试。",
        ) from exc


def _import_sales(db: Session, batch_id: int, frame: pd.DataFrame) -> int:
    fields = ["created_date", "received_date", "order_no", "sku", "category", "quantity", "returns", "gmv"]
    cols = _columns(frame, fields, {"created_date", "order_no", "sku", "quantity", "returns", "gmv"})
    records = []
    for index, row in frame.iterrows():
        try:
            records.append(SalesRecord(
                batch_id=batch_id,
                created_date=_date(row[cols["created_date"]], "创建日期"),
                received_date=_date(row[cols["received_date"]], "收货日期", True) if "received_date" in cols else None,
                order_no=_text(row[cols["order_no"]]), sku=_text(row[cols["sku"]]),
                category=_text(row[cols["category"]]) if "category" in cols else None,
                quantity=_number(row[cols["quantity"]]), returns=_number(row[cols["returns"]]), gmv=_number(row[cols["gmv"]]),
            ))
        except Exception as exc:
            raise ValueError(f"第 {index + 2} 行：{exc}") from exc
    # Sales exports are cumulative and overlap earlier uploads. Replace every
    # date carried by the new export so orders are never counted twice.
    record_dates = {record.created_date for record in records}
    if record_dates:
        db.execute(delete(SalesRecord).where(SalesRecord.created_date.in_(record_dates)))
    db.add_all(records)
    return len(records)


def _import_inventory(db: Session, batch_id: int, frame: pd.DataFrame, snapshot_date: date | None) -> int:
    fields = ["record_date", "sku", "seller_sku", "product", "color", "memory", "region", "inventory"]
    cols = _columns(frame, fields, {"sku", "inventory"})
    records: dict[tuple[date, str, str], InventoryHistory] = {}
    for index, row in frame.iterrows():
        seller_sku = _text(row[cols["seller_sku"]]) if "seller_sku" in cols else ""
        memory_match = re.search(r"(\d{1,2}\s*[+/]\s*\d{2,4})", seller_sku)
        region_match = re.search(r"(?:^|-)(EU|RU)(?:-|$)", seller_sku.upper())
        record_date = _date(row[cols["record_date"]], "库存日期") if "record_date" in cols else snapshot_date
        if record_date is None:
            raise ValueError("库存表没有 DATE 列，请选择库存快照日期")
        sku = _text(row[cols["sku"]])
        if not sku or sku == "0":
            continue
        region = _text(row[cols["region"]], "ALL") if "region" in cols else (region_match.group(1) if region_match else "ALL")
        key = (record_date, sku, region)
        parsed_color = parse_seller_sku_color(seller_sku)
        records[key] = InventoryHistory(
            batch_id=batch_id, download_date=record_date, sku=sku, seller_sku=seller_sku or None,
            product=_text(row[cols["product"]]) if "product" in cols else None,
            color=_text(row[cols["color"]]) if "color" in cols else parsed_color,
            memory=_text(row[cols["memory"]]) if "memory" in cols else (memory_match.group(1).replace(" ", "") if memory_match else None),
            region=region,
            inventory=_number(row[cols["inventory"]]),
        )
    # A cumulative export contains complete snapshots for several dates. Replace
    # every included date so tomorrow's 7/27-to-date file updates history safely.
    record_dates = {item.download_date for item in records.values()}
    if record_dates:
        db.execute(delete(InventoryHistory).where(InventoryHistory.download_date.in_(record_dates)))
    db.add_all(list(records.values()))
    return len(records)


def _import_traffic(db: Session, batch_id: int, frame: pd.DataFrame) -> int:
    fields = ["record_date", "sku", "uv", "clicks", "impressions"]
    cols = _columns(frame, fields, {"record_date", "sku", "uv"})
    records = []
    seen: dict[tuple[date, str], TrafficHistory] = {}
    for index, row in frame.iterrows():
        sku = _text(row[cols["sku"]])
        if not sku or sku == "0":
            continue
        try:
            record_date = _date(row[cols["record_date"]], "日期")
            key = (record_date, sku)
            uv = _number(row[cols["uv"]])
            clicks = _number(row[cols["clicks"]]) if "clicks" in cols else None
            impressions = _number(row[cols["impressions"]]) if "impressions" in cols else None
            if key in seen:
                seen[key].uv = (seen[key].uv or 0) + uv
                seen[key].clicks = (seen[key].clicks or 0) + (clicks or 0)
                seen[key].impressions = (seen[key].impressions or 0) + (impressions or 0)
            else:
                seen[key] = TrafficHistory(batch_id=batch_id, record_date=record_date, sku=sku, uv=uv, clicks=clicks, impressions=impressions)
        except Exception as exc:
            raise ValueError(f"第 {index + 2} 行：{exc}") from exc
    records = list(seen.values())
    # UZUM traffic exports can overlap previously imported dates. Treat every
    # date present in this file as a replacement so renamed/updated exports are
    # idempotent and cannot violate (record_date, sku).
    record_dates = {record.record_date for record in records}
    if record_dates:
        db.execute(delete(TrafficHistory).where(TrafficHistory.record_date.in_(record_dates)))
    db.add_all(records)
    return len(records)
