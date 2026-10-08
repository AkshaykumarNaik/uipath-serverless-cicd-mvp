import pytest

from src.order_processor import FulfillmentInput, fulfill_order, main


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
    assert first.retryable is False

@pytest.mark.asyncio
async def test_processor_returns_stable_failure_when_queue_completion_fails(monkeypatch):
    class BrokenQueues:
        async def complete_transaction_item_async(self, *args, **kwargs):
            raise RuntimeError("queue service unavailable")
    class FakeSdk:
        queues = BrokenQueues()
    monkeypatch.setattr("uipath.platform.UiPath", lambda: FakeSdk())
    result = await main({"transaction_key": "tx-2", "reference": "ORD-2002", "specific_content": {"amount": 100}, "complete_queue_item": True})
    assert result.status == "Failed"
    assert result.transaction_key == "tx-2"
    assert result.fulfillment_id == "FULFILL-ORD-2002"
    assert result.queue_completed is False
    assert "queue service unavailable" in result.error
    assert result.retryable is False

@pytest.mark.asyncio
async def test_processor_rejects_overlong_reference():
    result = await main({"transaction_key": "tx-3", "reference": "x" * 129, "specific_content": {}})
    assert result.status == "Invalid"
    assert result.queue_completed is False
