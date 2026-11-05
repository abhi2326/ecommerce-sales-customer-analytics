from pathlib import Path
import sys
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from build_warehouse import read_tables, build, quality_checks


def test_demo_pipeline_grain_and_quality():
    tables = read_tables(ROOT / "data" / "demo")
    mart = build(tables)
    checks = quality_checks(mart)
    fact = mart["fact_order_items"]
    assert len(checks) >= 4
    assert not fact.duplicated(["order_id", "order_item_id"]).any()
    assert fact.order_id.nunique() == tables["olist_orders"].order_id.nunique()
    assert fact.gmv.sum() > 0


def test_payment_is_not_join_fanned_out():
    tables = read_tables(ROOT / "data" / "demo")
    mart = build(tables)
    fact = mart["fact_order_items"]
    # The order-level payment total should be identical across lines for an order.
    counts = fact.groupby("order_id").payment_value.nunique(dropna=True)
    assert (counts <= 1).all()
