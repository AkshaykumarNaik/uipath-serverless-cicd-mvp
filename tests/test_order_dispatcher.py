import pytest

from src.order_dispatcher import OrderBatchInput, classify_orders, validate_orders


def make_batch():
    return OrderBatchInput(
        orders=[
            {"order_id": "ORD-1", "customer_id": "C-1", "amount": 100, "currency": "INR"},
            {"order_id": "ORD-2", "customer_id": "C-2", "amount": 6000, "currency": "INR"},
            {"order_id": "ORD-3", "customer_id": "C-3", "amount": 100, "currency": "USD"},
            {"order_id": "ORD-1", "customer_id": "C-1", "amount": 100, "currency": "INR"},
        ]
    )


def test_classification_separates_accept_reject_and_duplicate():
    accepted, rejected, duplicates = classify_orders(make_batch())
    assert [item.order_id for item in accepted] == ["ORD-1"]
    assert [item.order_id for item in rejected] == ["ORD-2", "ORD-3"]
    assert duplicates == ["ORD-1"]


@pytest.mark.asyncio
async def test_validation_does_not_dispatch_by_default():
    result = await validate_orders(make_batch())
    assert result.dispatched_count == 0
    assert len(result.accepted) == 1
