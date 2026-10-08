"""Typed order validation and optional UiPath Queue dispatch."""

from typing import Any, Protocol

from pydantic import Field, ValidationError
from pydantic.dataclasses import dataclass
from uipath.platform.orchestrator import CommitType


@dataclass
class Order:
    order_id: str = Field(min_length=1, max_length=64)
    customer_id: str = Field(min_length=1, max_length=64)
    amount: float = Field(gt=0)
    currency: str = Field(min_length=3, max_length=3)


@dataclass
class OrderBatchInput:
    orders: list[Order]
    max_order_amount: float = Field(default=5000, gt=0)
    queue_name: str = Field(default="ValidatedOrders", min_length=1, max_length=128)
    dispatch_to_queue: bool = False


@dataclass
class OrderResult:
    order_id: str
    status: str
    reason: str = ""


@dataclass
class OrderBatchOutput:
    accepted: list[OrderResult]
    rejected: list[OrderResult]
    duplicates: list[str]
    dispatched_count: int


class QueueClient(Protocol):
    async def create_items_async(self, items: list[dict[str, Any]], queue_name: str, **kwargs: Any) -> Any:
        ...


def classify_orders(batch: OrderBatchInput) -> tuple[list[OrderResult], list[OrderResult], list[str]]:
    accepted: list[OrderResult] = []
    rejected: list[OrderResult] = []
    duplicates: list[str] = []
    seen: set[str] = set()

    for order in batch.orders:
        if order.order_id in seen:
            duplicates.append(order.order_id)
            continue
        seen.add(order.order_id)

        if order.amount > batch.max_order_amount:
            rejected.append(OrderResult(order.order_id, "Rejected", "amount exceeds configured limit"))
        elif order.currency.upper() != "INR":
            rejected.append(OrderResult(order.order_id, "Rejected", "unsupported currency"))
        else:
            accepted.append(OrderResult(order.order_id, "Accepted"))

    return accepted, rejected, duplicates


async def _dispatch(client: QueueClient, batch: OrderBatchInput, accepted: list[OrderResult]) -> int:
    order_by_id = {order.order_id: order for order in batch.orders}
    items = [
        {"SpecificContent": order_by_id[result.order_id].__dict__, "Reference": result.order_id}
        for result in accepted
    ]
    if not items:
        return 0
    await client.create_items_async(
        items,
        batch.queue_name,
        CommitType.PROCESS_ALL_INDEPENDENTLY,
    )
    return len(items)


async def validate_orders(batch: OrderBatchInput) -> OrderBatchOutput:
    """Validate orders and optionally dispatch accepted orders to a UiPath Queue."""
    accepted, rejected, duplicates = classify_orders(batch)
    dispatched_count = 0

    if batch.dispatch_to_queue and accepted:
        from uipath.platform import UiPath

        sdk = UiPath()
        dispatched_count = await _dispatch(sdk.queues, batch, accepted)

    return OrderBatchOutput(accepted, rejected, duplicates, dispatched_count)


async def main(input_data: dict[str, Any]) -> OrderBatchOutput:
    """Function entry point with a stable error contract for runtime callers."""
    try:
        batch = OrderBatchInput(**input_data)
        return await validate_orders(batch)
    except ValidationError as exc:
        return OrderBatchOutput([], [OrderResult("", "Invalid", str(exc))], [], 0)
