"""Validate and export a clean copy of the bundled telemetry CSV."""
import argparse
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.anomaly_detector import DATA_PATH, load_telemetry


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', default=str(DATA_PATH), help='Input telemetry CSV')
    parser.add_argument('--output', default='data/processed_telemetry.csv', help='Output CSV path')
    args = parser.parse_args()
    df = load_telemetry(Path(args.input))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output, index=False)
    print(f'Validated {len(df)} rows across {df["asset_id"].nunique()} assets; wrote {output}')

if __name__ == '__main__':
    main()
