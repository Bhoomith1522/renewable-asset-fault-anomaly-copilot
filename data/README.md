# Bundled dataset

`asset_telemetry.csv` is the self-contained synthetic dataset supplied with the assignment package. It contains 240 observations and two asset identifiers: `SOLAR_INV_01` and `WTG_07`.

Columns: `timestamp_id`, `asset_id`, `hour`, `irradiance_wm2`, `wind_speed_ms`, `temperature_c`, `vibration_mm_s`, `power_mw`.

The dataset has no verified fault labels and should not be treated as real operational telemetry. `timestamp_id` is a row-like identifier, not a calendar timestamp. The app runs from this CSV without downloading any external data.
