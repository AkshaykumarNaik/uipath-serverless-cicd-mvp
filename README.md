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
- `deploy.yml` is manually triggered and documents the UiPath deployment boundary. It should only be enabled after configuring the required UiPath credentials and deployment target.

## Source attribution

The calculator implementation is adapted from the official UiPath Python SDK repository:
https://github.com/UiPath/uipath-python/tree/main/packages/uipath/samples/calculator

The sample code remains under the original repository's license. This MVP's workflow and test additions are provided for demonstration.
