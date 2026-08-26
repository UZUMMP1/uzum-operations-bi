from app.metrics import calculate_metrics, day_over_day, inventory_plan

def test_sales_metrics_use_so():
    result = calculate_metrics(quantity=100, returns=8, gmv=23000, uv=2000)
    assert result["so"] == 92
    assert result["orders"] == 100
    assert result["asp"] == 250
    assert result["cvr"] == 0.05

def test_missing_traffic_is_not_zero():
    result = calculate_metrics(10, 1, 900, None)
    assert result["uv"] is None
    assert result["cvr"] is None
    assert result["traffic_missing"] is True

def test_day_over_day_zero_base_is_empty():
    assert day_over_day(10, 0) is None
    assert day_over_day(110, 100) == 0.1

def test_inventory_replenishment():
    result = inventory_plan(inventory=140, sales_14d=140)
    assert result["dos"] == 14
    assert result["replenishment"] == 140
    assert result["warning"] is True

def test_inventory_replenishment_rounds_up_to_whole_unit():
    result = inventory_plan(inventory=40, sales_14d=32.2)
    assert result["replenishment"] == 25
