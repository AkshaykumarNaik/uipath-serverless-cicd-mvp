"""Small dependency-free HTTP adapter for the fulfillment service."""

import asyncio
import json
import os
from dataclasses import dataclass
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class FulfillmentApiError(RuntimeError):
    def __init__(self, message: str, *, retryable: bool):
        super().__init__(message)
        self.retryable = retryable


@dataclass(frozen=True)
class FulfillmentApiConfig:
    url: str
    token: str
    timeout_seconds: float = 10.0
    max_attempts: int = 3

    @classmethod
    def from_environment(cls) -> "FulfillmentApiConfig":
        url = os.environ.get("FULFILLMENT_API_URL", "").strip()
        token = os.environ.get("FULFILLMENT_API_TOKEN", "").strip()
        if not url or not token:
            raise FulfillmentApiError("FULFILLMENT_API_URL and FULFILLMENT_API_TOKEN are required for http mode", retryable=False)
        return cls(url=url, token=token)


def _request(config: FulfillmentApiConfig, reference: str, content: dict[str, Any], opener: Callable[..., Any] = urlopen) -> str:
    request = Request(
        config.url,
        data=json.dumps({"reference": reference, "content": content}).encode("utf-8"),
        headers={"Authorization": f"Bearer {config.token}", "Content-Type": "application/json", "Idempotency-Key": reference},
        method="POST",
    )
    try:
        with opener(request, timeout=config.timeout_seconds) as response:
            payload = json.loads(response.read().decode("utf-8"))
        fulfillment_id = payload.get("fulfillment_id")
        if not isinstance(fulfillment_id, str) or not fulfillment_id:
            raise FulfillmentApiError("fulfillment API returned no fulfillment_id", retryable=False)
        return fulfillment_id
    except HTTPError as exc:
        raise FulfillmentApiError(f"fulfillment API HTTP {exc.code}", retryable=exc.code == 429 or exc.code >= 500) from exc
    except (TimeoutError, URLError) as exc:
        raise FulfillmentApiError(f"fulfillment API connection error: {exc}", retryable=True) from exc
    except json.JSONDecodeError as exc:
        raise FulfillmentApiError("fulfillment API returned invalid JSON", retryable=False) from exc


async def fulfill_via_http(reference: str, content: dict[str, Any], config: FulfillmentApiConfig | None = None) -> str:
    config = config or FulfillmentApiConfig.from_environment()
    for attempt in range(config.max_attempts):
        try:
            return await asyncio.to_thread(_request, config, reference, content)
        except FulfillmentApiError as exc:
            if not exc.retryable or attempt == config.max_attempts - 1:
                raise
            await asyncio.sleep(0.25 * (2**attempt))
    raise AssertionError("unreachable")
