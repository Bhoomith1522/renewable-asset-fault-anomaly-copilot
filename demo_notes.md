# Demo Notes

1. Start the app using the README instructions and open `/` in a browser.
2. The dashboard runs analysis on the bundled telemetry when it loads.
3. Review the summary cards and the per-asset counts.
4. Select `Anomalies only` to inspect flagged rows, or `All telemetry` to browse the full dataset.
5. Choose an asset to filter the results.
6. Select a row to view measured evidence and recommended checks.
7. Show `/docs` to demonstrate the FastAPI endpoints and `/api/health` to show service health.

Current local smoke-test evidence: `/`, `/api/health`, `/api/demo`, `/docs`, and `POST /api/run` all returned HTTP 200 in the available test environment. This is local evidence only, not Railway deployment evidence. Capture fresh screenshots from the actual running app before submission.
