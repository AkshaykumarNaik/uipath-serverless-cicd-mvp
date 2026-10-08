# UiPath Serverless CI/CD MVP

This repository is a minimal GitHub Actions example based on the official `UiPath/uipath-python` calculator sample.

The sample is intentionally cloud-independent for CI: it performs typed Python calculations and does not require UiPath credentials to run tests. The deployment workflow is included as a disabled-by-default template because publishing to UiPath requires tenant-specific configuration and GitHub Secrets.

## Local setup

Prerequisites: Python 3.11+ and `uv`.

```powershell
uv sync
uv run pytest -q
uv run uipath run main '{"a": 2, "b": 3, "operator": "+"}'
```

## GitHub Actions

- `ci.yml` runs on pull requests and pushes to `main`: dependency setup, compile check, tests, and project-contract checks.
- `deploy.yml` is manually triggered. It authenticates with a UiPath confidential External Application, regenerates function metadata, packs the project, and publishes the package to the configured Orchestrator Processes feed.

The workflow publishes to the tenant Processes feed. The current tenant Processes feed is `cbf16dfa-a275-426a-a67b-fc87326b082a`. The workflow uses the existing environment secrets `UIPATH_URL`, `UIPATH_CLIENT_ID`, `UIPATH_CLIENT_SECRET`, and `UIPATH_SCOPES`.

Publishing the package is the CI/CD deployment boundary. A UiPath Function Release or process binding may still need to be created or updated in Orchestrator before a Serverless job can be started.

## Verified Serverless deployment

The package was bound to the `RPA_Automation` folder as process `calculator-agent` and executed with runtime type `Serverless`.

Smoke-test input:

```json
{"a": 2, "b": 3, "operator": "+"}
```

Verified output:

```json
{"result": 5.0}
```

The successful job was a UiPath `Function` process with `TargetFramework: Portable`, `TargetRuntime: python`, and `ServerlessJobType: PythonCodedFunction`.

## Complex automation: order validation and queue dispatch

The `validate_orders` entry point accepts a batch of orders, rejects amounts above the configured limit or unsupported currencies, detects duplicate order references, and can dispatch accepted orders to the `ValidatedOrders` UiPath Queue. Queue dispatch uses unique references and `ProcessAllIndependently` bulk semantics.

Verified Serverless smoke test for package `calculator-agent:0.1.1`:

- Process: `order-validator-v2`
- Input order: `ORD-2001`, INR 250
- Result: one accepted order, `dispatched_count: 1`
- Queue item: `ORD-2001`, status `New`
- Queue: `ValidatedOrders`

## Performer stage

The `process_order` entry point is the second stage. It accepts a queue transaction payload, produces a deterministic fulfillment ID from the queue reference, and can complete the transaction through the UiPath SDK when `complete_queue_item` is enabled. The default adapter is safe and local; replace it with an authenticated fulfillment API adapter when that integration is ready.

Verified Serverless smoke test for package `calculator-agent:0.2.0`:

- Process: `order-processor`
- Entry point: `process_order`
- Result: `FULFILL-ORD-2001`
- Status: `Fulfilled`

## Fulfillment adapter hardening

`process_order` supports `fulfillment_mode=stub` for deterministic smoke tests and `fulfillment_mode=http` for production integration. HTTP mode reads `FULFILLMENT_API_URL` and `FULFILLMENT_API_TOKEN`, sends the queue reference as the `Idempotency-Key`, applies a 10-second timeout, retries transient 429/5xx/network failures up to three times, and returns a `retryable` failure flag without exposing the token.

## Source attribution

The calculator implementation is adapted from the official UiPath Python SDK repository:
https://github.com/UiPath/uipath-python/tree/main/packages/uipath/samples/calculator

The sample code remains under the original repository's license. This MVP's workflow and test additions are provided for demonstration.
