import pytest

from src.order_processor import FulfillmentInput, fulfill_order


@pytest.mark.asyncio
async def test_processor_is_deterministic_and_idempotent_by_reference():
    data = FulfillmentInput(
        transaction_key="tx-1",
        reference="ORD-2001",
        specific_content={"amount": 250},
    )
    first = await fulfill_order(data)
    second = await fulfill_order(data)
    assert first.fulfillment_id == "FULFILL-ORD-2001"
    assert second.fulfillment_id == first.fulfillment_id
    assert first.queue_completed is False
