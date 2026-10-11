# Renewable Asset Fault & Anomaly Detection Copilot

A lightweight, offline-capable demonstration that screens synthetic solar-inverter and wind-turbine telemetry, flags unusual observations, and presents operator-oriented evidence and recommended checks.

> **Safety and scope:** this is a candidate-assignment prototype using dummy data. An anomaly flag is not a confirmed fault, root-cause diagnosis, or instruction to operate equipment. Do not use it for autonomous control or real maintenance decisions without domain validation.

## Features

- Bundled CSV dataset; no external data download is required.
- FastAPI endpoints for health, summary, and anomaly analysis.
- Per-asset IsolationForest baseline plus explicit high-signal screening rules.
- Explanation text tied to observed values, with next checks framed as hypotheses.
- Single-page HTML/CSS/JavaScript dashboard served by FastAPI.
- Tests for endpoints, filters, and detector outputs.

## Repository layout

```text
backend/app.py              FastAPI application
backend/anomaly_detector.py Data validation, features/model, explanations
frontend/index.html         Dashboard
 data/asset_telemetry.csv   Bundled synthetic telemetry
tests/test_app.py           Automated API and detector tests
evaluation/results.md       Reproducible evaluation notes
requirements.txt            Python dependencies
Procfile                    Railway start command
```

## Requirements

- Python 3.11 or 3.12 (the pinned scientific Python dependencies are intended for this range; Railway is configured for Python 3.12.8)
- pip

The app uses the bundled CSV and does not require an LLM key, embedding API, or network access to analyze data.

## Run locally (Windows PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/`. API docs are available at `http://127.0.0.1:8000/docs`.

## Run locally (macOS/Linux)

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000
```

## API examples

Health check:

```bash
curl http://127.0.0.1:8000/api/health
```

Summary:

```bash
curl http://127.0.0.1:8000/api/demo
```

Analyze and return anomaly rows only:

```bash
curl -X POST http://127.0.0.1:8000/api/run \
  -H "Content-Type: application/json" \
  -d '{"mode":"anomalies","limit":100}'
```

Filter to one asset:

```bash
curl -X POST http://127.0.0.1:8000/api/run \
  -H "Content-Type: application/json" \
  -d '{"asset_id":"SOLAR_INV_01","mode":"anomalies","limit":100}'
```

Request body fields: `asset_id` (optional), `mode` (`all` or `anomalies`), and `limit` (1–500). Unknown assets return HTTP 404.

## Model and feature logic

1. Validate required columns and numeric telemetry.
2. Fit a separate `IsolationForest` for each asset to reduce confusion between solar and wind operating modes. The model uses hour, irradiance, wind speed, temperature, vibration, and power. The random seed is fixed for repeatability; the contamination setting is a heuristic, not a measured fault prevalence.
3. Combine the model's outlier flag with transparent screening rules: temperature at or above 45 °C, vibration at or above 2.5 mm/s, and solar power below 65% of a simple irradiance-based expectation when irradiance is at least 200 W/m².
4. Produce an explanation from observable values and suggest checks that an operator can verify.

The solar expectation uses `irradiance_wm2 * 0.0019` as a deliberately simple baseline. It is not a validated performance model. Thresholds are illustrative and must be adapted to equipment specifications and site procedures.

## Evaluation

Run tests:

```bash
python -m pip install pytest httpx
python -m pytest -q
```

The current observed run passed 5 tests (`5 passed in 2.59s`) in the available execution environment. The tests check API health, dataset row/asset counts, anomaly output shape, explanations, asset filtering, and unknown-asset handling. Re-run in a clean environment installed from `requirements.txt` before submission. They do **not** establish operational fault-detection accuracy. The bundled dataset is synthetic and does not provide verified ground-truth labels, so precision, recall, F1, and real-world false-alarm rates are not reported. See [`evaluation/results.md`](evaluation/results.md) for measured results and limitations.

## Railway deployment

1. Push this repository to GitHub.
2. In Railway, create a project and deploy from the GitHub repository.
3. Ensure the service root is the repository root (the directory containing `Procfile`, `requirements.txt`, `backend/`, `frontend/`, and `data/`).
4. Railway should select Python from `runtime.txt`, install dependencies from `requirements.txt`, and use the `Procfile` command. The app binds to `0.0.0.0` and uses the provided `PORT` environment variable, with 8000 as a local fallback.
5. Once deployed, verify `/api/health`, `/api/demo`, `/docs`, and `/` using the assigned public domain.
6. Add the actual public URL and a real deployment screenshot/log excerpt to your submission. Do not claim deployment success before it works.

No secrets are needed for the current baseline. If an external LLM is added later, load its key from an environment variable and never commit `.env` files or credentials.

## Production-readiness gaps

- Synthetic, small dataset with no verified labels or real site context.
- Static thresholds and simplified irradiance-to-power relationship.
- IsolationForest may flag valid operating transitions and does not explain causal mechanisms.
- No timestamp cadence, asset metadata, rated capacity, maintenance logs, curtailment status, or environmental context beyond the supplied columns.
- No authentication, authorization, audit logging, model monitoring, drift detection, or role-based workflows.
- Operator recommendations require review against manufacturer guidance and site safety procedures.
