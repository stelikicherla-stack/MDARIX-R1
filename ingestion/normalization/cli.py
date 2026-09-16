import argparse
import json

from ingestion.normalization.service import NormalizationService


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = NormalizationService().normalize_all()
    if args.json:
        print(json.dumps(result, indent=2, default=str, sort_keys=True))
    else:
        print("DAY 5 NORMALIZATION = PASS")
        print(json.dumps(result, default=str, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
