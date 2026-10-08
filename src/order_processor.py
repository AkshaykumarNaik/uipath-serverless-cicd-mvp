"""Queue transaction performer with a deterministic fulfillment adapter."""

from typing import Any

from pydantic import BaseModel, Field, ValidationError


class FulfillmentInput(BaseModel):
    transaction_key: str = Field(min_length=1)
    reference: str = Field(min_length=1)
    specific_content: dict[str, Any]
    queue_name: str = "ValidatedOrders"
    complete_queue_item: bool = False


class FulfillmentOutput(BaseModel):
    transaction_key: str
    reference: str
    status: str
    fulfillment_id: str
    queue_completed: bool
    error: str = ""


async def fulfill_order(data: FulfillmentInput) -> FulfillmentOutput:
    """Perform an idempotent, deterministic fulfillment operation.

    The default adapter is local and deterministic. A production implementation
    can replace this block with an authenticated HTTP/API call while preserving
    the input/output contract and idempotency key.
    """
    fulfillment_id = f"FULFILL-{data.reference}"
    queue_completed = False

    if data.complete_queue_item:
        from uipath.platform import UiPath

        sdk = UiPath()
        await sdk.queues.complete_transaction_item_async(
            data.transaction_key,
            {"IsSuccessful": True, "Output": {"fulfillment_id": fulfillment_id}},
            queue_name=data.queue_name,
        )
        queue_completed = True

    return FulfillmentOutput(
        transaction_key=data.transaction_key,
        reference=data.reference,
        status="Fulfilled",
        fulfillment_id=fulfillment_id,
        queue_completed=queue_completed,
    )


async def main(input_data: dict[str, Any]) -> FulfillmentOutput:
    try:
        return await fulfill_order(FulfillmentInput(**input_data))
    except ValidationError as exc:
        return FulfillmentOutput("", "", "Invalid", "", False, str(exc))
