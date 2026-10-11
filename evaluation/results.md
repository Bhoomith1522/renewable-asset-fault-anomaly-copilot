# Evaluation Results and Limitations

## Dataset inspection

The bundled `data/asset_telemetry.csv` contains 240 rows, 8 columns, and 2 assets (`SOLAR_INV_01` and `WTG_07`) with 120 rows each. A local inspection found no missing values in the supplied columns. The dataset is synthetic, uses `timestamp_id` and hour-of-day rather than a full datetime, and contains no verified ground-truth fault labels.

## Automated tests

Command executed from the repository root: `python -m pytest -q`

Observed result in the available execution environment: **5 passed in 2.59 seconds**. These tests cover the health endpoint, dataset counts, anomaly output/explanations, asset filtering, unknown-asset handling, and detector output columns. Passing software tests validate expected behavior and API contracts only; they are not model-accuracy metrics. The runtime dependency versions in this test environment may differ from the exact pins in `requirements.txt`, so also run the tests in a clean environment installed from that file before submission.

## Detection metrics

No precision, recall, F1, ROC-AUC, or operational false-alarm rate is claimed because the dataset does not include verified anomaly labels. In the current run, the combined pipeline flagged **10 of 240 rows (4.17%)**: 5 rows for `SOLAR_INV_01` and 5 for `WTG_07`. This is a descriptive flag rate, not an accuracy score. The model also flagged some points without a specific thermal/vibration rule hit, demonstrating that IsolationForest can flag unusual-but-valid readings in a small dataset.

## Validation limitations

- Synthetic data may encode obvious anomalies and does not represent full real-world variability.
- Thresholds (45 °C, 2.5 mm/s, and the simple solar power baseline) are illustrative assumptions, not Greenko or manufacturer-approved limits.
- IsolationForest's anomaly scores are relative to the small dataset and should not be interpreted as fault probabilities.
- Explanations map measured signals to plausible checks; they do not identify a confirmed root cause.
- There is no time-based holdout, labeled benchmark, comparison to a naive baseline, or domain-expert review.

## Next validation steps

1. Obtain labeled historical telemetry and maintenance/event records with permission.
2. Define anomaly windows with energy-domain reviewers and split evaluation by time and asset to avoid leakage.
3. Compare rule-only, IsolationForest-only, and combined methods at an agreed alert budget.
4. Report precision/recall/F1, false alarms per asset-day, detection delay, and results by asset class.
5. Have operators review explanation faithfulness and recommended checks before any operational pilot.
