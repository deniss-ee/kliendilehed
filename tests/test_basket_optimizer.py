import pytest
from decimal import Decimal
from app.consumer_api.basket_optimizer import SingleStoreSummary, SplitStoreRoute
from app.schemas.common import StoreCode

class TestBasketStructures:
    def test_single_store_summary_calculation(self):
        summary = SingleStoreSummary(
            store_code=StoreCode.SELVER,
            store_name="Selver",
            available_items_count=4,
            missing_items_count=0,
            total_cost=Decimal("12.50"),
            regular_total_cost=Decimal("15.00"),
            total_savings=Decimal("2.50"),
            missing_item_names=[],
        )
        assert summary.total_savings == Decimal("2.50")
        assert summary.missing_items_count == 0

    def test_split_store_route_calculation(self):
        split = SplitStoreRoute(
            total_cost=Decimal("10.80"),
            savings_vs_best_single=Decimal("1.70"),
            store_breakdown={"SELVER": [], "PRISMA": []},
        )
        assert split.total_cost == Decimal("10.80")
        assert split.savings_vs_best_single == Decimal("1.70")
