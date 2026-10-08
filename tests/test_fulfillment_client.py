import json

import pytest

from src.fulfillment_client import FulfillmentApiConfig, FulfillmentApiError, _request


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


def test_http_adapter_sends_auth_and_idempotency_headers():
    captured = {}

    def opener(request, timeout):
        captured["headers"] = dict(request.header_items())
        captured["timeout"] = timeout
        captured["body"] = json.loads(request.data)
        return FakeResponse({"fulfillment_id": "FULFILL-ORD-9"})

    result = _request(FulfillmentApiConfig("https://example.test/fulfill", "token"), "ORD-9", {"amount": 4}, opener)
    assert result == "FULFILL-ORD-9"
    assert captured["headers"]["Authorization"] == "Bearer token"
    assert captured["headers"]["Idempotency-key"] == "ORD-9"
    assert captured["body"] == {"reference": "ORD-9", "content": {"amount": 4}}


def test_missing_fulfillment_id_is_non_retryable():
    with pytest.raises(FulfillmentApiError, match="no fulfillment_id") as error:
        _request(FulfillmentApiConfig("https://example.test/fulfill", "token"), "ORD-9", {}, lambda *args, **kwargs: FakeResponse({}))
    assert error.value.retryable is False
