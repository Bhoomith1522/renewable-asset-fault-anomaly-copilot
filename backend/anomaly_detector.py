"""Transparent baseline anomaly detection for the bundled synthetic telemetry."""
from pathlib import Path
import pandas as pd
from sklearn.ensemble import IsolationForest

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = BASE_DIR / "data" / "asset_telemetry.csv"
REQUIRED_COLUMNS = {
    "timestamp_id", "asset_id", "hour", "irradiance_wm2", "wind_speed_ms",
    "temperature_c", "vibration_mm_s", "power_mw"
}
NUMERIC_COLUMNS = ["hour", "irradiance_wm2", "wind_speed_ms", "temperature_c", "vibration_mm_s", "power_mw"]


def load_telemetry(path: Path | str = DATA_PATH) -> pd.DataFrame:
    """Load and validate telemetry. Does not require network access."""
    df = pd.read_csv(path)
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Dataset is missing required columns: {', '.join(sorted(missing))}")
    if df.empty:
        raise ValueError("Dataset contains no telemetry rows")
    for col in NUMERIC_COLUMNS + ["timestamp_id"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    if df[NUMERIC_COLUMNS].isna().any().any():
        raise ValueError("Numeric telemetry contains missing or non-numeric values")
    if (df["hour"] < 0).any() or (df["hour"] > 23).any():
        raise ValueError("hour must be between 0 and 23")
    return df


def _explain(row: pd.Series) -> tuple[list[str], list[str], str]:
    """Return observable evidence and checks; these are hypotheses, not diagnoses."""
    evidence, checks = [], []
    asset = str(row["asset_id"]).upper()
    if row["temperature_c"] >= 45:
        evidence.append(f"temperature is elevated at {row['temperature_c']:.1f} °C")
        checks.extend(["Verify the temperature sensor and recent thermal trend", "Inspect cooling/ventilation and review the asset alarm log"])
    if row["vibration_mm_s"] >= 2.5:
        evidence.append(f"vibration is elevated at {row['vibration_mm_s']:.2f} mm/s")
        checks.extend(["Check vibration sensor mounting and compare with the asset's normal baseline", "Inspect for looseness, imbalance or bearing-related alarms using site procedures"])
    if asset.startswith("SOLAR") and row["irradiance_wm2"] >= 200:
        expected = row["irradiance_wm2"] * 0.0019
        if row["power_mw"] < expected * 0.65:
            evidence.append(f"power ({row['power_mw']:.3f} MW) is low relative to a simple irradiance baseline ({expected:.3f} MW)")
            checks.extend(["Verify irradiance and power meter readings", "Check inverter status, curtailment and recent fault/alarm records"])
    if not evidence:
        evidence.append("the multivariate telemetry pattern is unusual relative to this small dataset")
        checks.extend(["Compare adjacent readings and similar operating conditions", "Verify sensor quality and check the asset event/alarm log"])
    severity = "high" if row["temperature_c"] >= 45 or row["vibration_mm_s"] >= 3.5 else "medium"
    return evidence, list(dict.fromkeys(checks)), severity


def detect_anomalies(df: pd.DataFrame | None = None, contamination: float = 0.04) -> pd.DataFrame:
    """Apply IsolationForest plus transparent high-signal operational rules."""
    source = load_telemetry() if df is None else df.copy()
    missing = REQUIRED_COLUMNS - set(source.columns)
    if missing:
        raise ValueError(f"Telemetry is missing required columns: {', '.join(sorted(missing))}")
    out = source.copy()
    numeric = out[NUMERIC_COLUMNS].apply(pd.to_numeric, errors="coerce")
    if numeric.isna().any().any():
        raise ValueError("Numeric telemetry contains missing or non-numeric values")

    # Per-asset fit reduces the risk of confusing normal solar and wind operating modes.
    out["model_flag"] = 0
    out["model_score"] = 0.0
    model_features = ["hour", "irradiance_wm2", "wind_speed_ms", "temperature_c", "vibration_mm_s", "power_mw"]
    for _, indices in out.groupby("asset_id").groups.items():
        subset = out.loc[indices, model_features]
        model = IsolationForest(n_estimators=200, contamination=contamination, random_state=42)
        model.fit(subset)
        out.loc[indices, "model_flag"] = (model.predict(subset) == -1).astype(int)
        out.loc[indices, "model_score"] = -model.decision_function(subset)

    out["rule_reasons"] = ""
    out["recommended_checks"] = ""
    out["severity"] = "none"
    out["is_anomaly"] = out["model_flag"].astype(bool)
    for idx, row in out.iterrows():
        # Explicit rules are designed as conservative screening signals, not fault labels.
        rule_hit = row["temperature_c"] >= 45 or row["vibration_mm_s"] >= 2.5
        if str(row["asset_id"]).upper().startswith("SOLAR") and row["irradiance_wm2"] >= 200:
            rule_hit = rule_hit or row["power_mw"] < row["irradiance_wm2"] * 0.0019 * 0.65
        out.at[idx, "is_anomaly"] = bool(out.at[idx, "is_anomaly"] or rule_hit)
        if out.at[idx, "is_anomaly"]:
            evidence, checks, severity = _explain(row)
            out.at[idx, "rule_reasons"] = "; ".join(evidence)
            out.at[idx, "recommended_checks"] = checks
            out.at[idx, "severity"] = severity
    out["is_anomaly"] = out["is_anomaly"].astype(bool)
    return out


def summarize_results(results: pd.DataFrame) -> dict:
    flagged = results[results["is_anomaly"]]
    return {
        "rows_scanned": int(len(results)),
        "assets_scanned": int(results["asset_id"].nunique()),
        "anomalies_flagged": int(len(flagged)),
        "anomaly_rate_pct": round(float(len(flagged) / len(results) * 100), 2) if len(results) else 0.0,
        "asset_summary": [
            {"asset_id": str(asset), "rows_scanned": int(len(group)), "anomalies_flagged": int(group["is_anomaly"].sum())}
            for asset, group in results.groupby("asset_id", sort=True)
        ],
    }


def json_safe_row(row: pd.Series) -> dict:
    return {
        "timestamp_id": int(row["timestamp_id"]), "asset_id": str(row["asset_id"]), "hour": int(row["hour"]),
        "irradiance_wm2": float(row["irradiance_wm2"]), "wind_speed_ms": float(row["wind_speed_ms"]),
        "temperature_c": float(row["temperature_c"]), "vibration_mm_s": float(row["vibration_mm_s"]),
        "power_mw": float(row["power_mw"]), "model_score": round(float(row["model_score"]), 5),
        "model_flag": bool(row["model_flag"]), "is_anomaly": bool(row["is_anomaly"]),
        "severity": str(row["severity"]), "evidence": str(row["rule_reasons"]),
        "recommended_checks": row["recommended_checks"] if isinstance(row["recommended_checks"], list) else [],
    }
