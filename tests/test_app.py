from fastapi.testclient import TestClient
from backend.app import app
from backend.anomaly_detector import load_telemetry, detect_anomalies

client = TestClient(app)

def test_health_endpoint():
    response = client.get('/api/health')
    assert response.status_code == 200
    assert response.json()['status'] == 'ok'
    assert response.json()['dataset_available'] is True

def test_demo_summary_has_expected_dataset_size():
    response = client.get('/api/demo')
    assert response.status_code == 200
    body = response.json()
    assert body['rows_scanned'] == 240
    assert body['assets_scanned'] == 2
    assert body['anomalies_flagged'] > 0

def test_run_returns_anomalies_with_explanations():
    response = client.post('/api/run', json={'mode': 'anomalies', 'limit': 500})
    assert response.status_code == 200
    body = response.json()
    assert body['returned_rows'] > 0
    assert all(row['is_anomaly'] for row in body['rows'])
    assert all(row['evidence'] for row in body['rows'])
    assert all(isinstance(row['recommended_checks'], list) for row in body['rows'])

def test_asset_filter_and_unknown_asset():
    response = client.post('/api/run', json={'asset_id': 'SOLAR_INV_01', 'mode': 'anomalies'})
    assert response.status_code == 200
    assert all(row['asset_id'] == 'SOLAR_INV_01' for row in response.json()['rows'])
    missing = client.post('/api/run', json={'asset_id': 'NOT_AN_ASSET'})
    assert missing.status_code == 404

def test_detector_output_columns_and_no_missing_values():
    result = detect_anomalies(load_telemetry())
    assert len(result) == 240
    assert {'is_anomaly', 'model_score', 'rule_reasons', 'recommended_checks', 'severity'} <= set(result.columns)
    assert result['is_anomaly'].notna().all()
