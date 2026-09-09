#!/usr/bin/env python3
import argparse, json, sys
from pathlib import Path
from jsonschema import Draft202012Validator


def load_schema(path: Path):
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def validate_file(data_path: Path, schema_path: Path) -> int:
    validator = Draft202012Validator(load_schema(schema_path))
    seen = set()
    rows = 0
    errors = 0
    verified = 0
    with data_path.open(encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            if not line.strip():
                continue
            rows += 1
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as e:
                print(f"{data_path}:{lineno}: invalid JSON: {e}", file=sys.stderr)
                errors += 1
                continue
            for err in sorted(validator.iter_errors(obj), key=lambda e: list(e.path)):
                loc = ".".join(map(str, err.path)) or "<record>"
                print(f"{data_path}:{lineno}:{loc}: {err.message}", file=sys.stderr)
                errors += 1
            rid = obj.get("id")
            if rid in seen:
                print(f"{data_path}:{lineno}: duplicate id: {rid}", file=sys.stderr)
                errors += 1
            seen.add(rid)
            verified += bool(obj.get("verified"))

    print(f"rows={rows} verified={verified} unverified={rows-verified} errors={errors}")
    return 1 if errors else 0


def main():
    p = argparse.ArgumentParser()
    p.add_argument("data", type=Path)
    p.add_argument("--schema", type=Path, default=Path(__file__).parents[1] / "schema" / "record.schema.json")
    args = p.parse_args()
    raise SystemExit(validate_file(args.data, args.schema))

if __name__ == "__main__":
    main()
