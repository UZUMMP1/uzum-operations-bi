from math import ceil


def safe_divide(numerator: float, denominator: float) -> float | None:
    return numerator / denominator if denominator else None

def calculate_metrics(quantity: float, returns: float, gmv: float, uv: float | None) -> dict:
    so = quantity - returns
    return {
        "so": so,
        "orders": quantity,
        "returns": returns,
        "gmv": gmv,
        "asp": safe_divide(gmv, so),
        "uv": uv,
        "cvr": safe_divide(quantity, uv) if uv is not None else None,
        "traffic_missing": uv is None,
    }

def day_over_day(today: float, yesterday: float) -> float | None:
    return safe_divide(today - yesterday, yesterday)

def inventory_plan(inventory: float, sales_14d: float) -> dict:
    average = sales_14d / 14
    dos = safe_divide(inventory, average)
    replenishment = max(0, ceil(average * 28 - inventory)) if dos is not None else 0
    return {"average_sales_14d": average, "dos": dos, "replenishment": replenishment, "warning": dos is not None and dos < 28}
