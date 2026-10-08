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

## Source attribution

The calculator implementation is adapted from the official UiPath Python SDK repository:
https://github.com/UiPath/uipath-python/tree/main/packages/uipath/samples/calculator

The sample code remains under the original repository's license. This MVP's workflow and test additions are provided for demonstration.
