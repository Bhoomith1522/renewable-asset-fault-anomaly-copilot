from pathlib import Path
from typing import Literal
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from backend.anomaly_detector import detect_anomalies, load_telemetry, summarize_results, json_safe_row

BASE = Path(__file__).resolve().parents[1]
FRONTEND = BASE / "frontend"
app = FastAPI(
    title="Renewable Asset Fault & Anomaly Detection Copilot",
    description="Offline-capable baseline anomaly screening for synthetic solar/wind telemetry. Flags are screening signals, not confirmed faults.",
    version="1.0.0",
)

class RunRequest(BaseModel):
    asset_id: str | None = Field(default=None, description="Optional asset filter")
    limit: int = Field(default=100, ge=1, le=500, description="Maximum anomaly rows to return")
    mode: Literal["all", "anomalies"] = "all"

@app.get("/", include_in_schema=False)
def home():
    return FileResponse(FRONTEND / "index.html")

@app.get("/api/health")
def health():
    return {"status": "ok", "dataset_available": (BASE / "data" / "asset_telemetry.csv").exists()}

@app.get("/api/demo")
def demo():
    try:
        df = load_telemetry()
        return {"case_study": "Renewable Asset Fault & Anomaly Detection Copilot", "status": "ready", **summarize_results(detect_anomalies(df))}
    except (ValueError, OSError) as exc:
        raise HTTPException(status_code=500, detail=f"Could not load or analyze bundled telemetry: {exc}") from exc

@app.post("/api/run")
def run_case(request: RunRequest):
    try:
        summary_source = detect_anomalies(load_telemetry())
        if request.asset_id:
            summary_source = summary_source[summary_source["asset_id"].str.casefold() == request.asset_id.casefold()]
            if summary_source.empty:
                raise HTTPException(status_code=404, detail=f"No telemetry found for asset '{request.asset_id}'")
        results = summary_source
        if request.mode == "anomalies":
            results = results[results["is_anomaly"]]
        rows = [json_safe_row(row) for _, row in results.head(request.limit).iterrows()]
        return {"summary": summarize_results(summary_source), "returned_rows": len(rows), "mode": request.mode, "rows": rows,
                "method": "IsolationForest per asset + transparent screening rules", 
                "interpretation_note": "An anomaly is a review signal, not a confirmed fault. Suggested causes and checks are hypotheses based on telemetry only."}
    except HTTPException:
        raise
    except (ValueError, OSError) as exc:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {exc}") from exc

app.mount("/static", StaticFiles(directory=FRONTEND), name="static")
