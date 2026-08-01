import csv
import json
import re
import sys
from pathlib import Path

REQUIRED_FIELDS = ["id", "title", "culture", "lat", "lng", "imageUrl"]

ID_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

NUMERIC_FIELDS = {"lat", "lng", "dateStart", "dateEnd"}


def row_to_feature(row: dict, line_no: int) -> dict:
    missing = [f for f in REQUIRED_FIELDS if not row.get(f, "").strip()]
    if missing:
        raise ValueError(f"Row {line_no} (id={row.get('id', '?')!r}) missing required field(s): {missing}")

    raw_id = row["id"].strip()
    if not ID_PATTERN.match(raw_id):
        raise ValueError(
            f"Row {line_no}: id {raw_id!r} must be lowercase letters/numbers/hyphens only "
            f"(e.g. 'knossos-bull-leaping') so it can't collide with a same-name id in different case"
        )

    if None in row:
        raise ValueError(
            f"Row {line_no} (id={raw_id!r}) has more columns than the header defines -- "
            f"check for a stray comma in this row"
        )

    props = {}
    image_attribution = {}

    for key, value in row.items():
        value = (value or "").strip()
        if value == "":
            continue 

        if key in ("lat", "lng"):
            continue  

        if key.startswith("image_"):
            sub_key = key[len("image_"):]
            image_attribution[sub_key] = value
            continue

        if key in NUMERIC_FIELDS:
            try:
                props[key] = int(value)
            except ValueError:
                props[key] = float(value)
            continue

        props[key] = value

    if image_attribution:
        props["imageAttribution"] = image_attribution

    try:
        lat = float(row["lat"])
        lng = float(row["lng"])
    except ValueError as e:
        raise ValueError(f"Row {line_no} (id={row.get('id')!r}) has a non-numeric lat/lng") from e

    return {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [lng, lat]},
        "properties": props,
    }


def main():
    if len(sys.argv) != 3:
        print("Usage: python3 csv_to_data.py <input.csv> <output_dir>")
        sys.exit(1)

    csv_path = Path(sys.argv[1])
    out_dir = Path(sys.argv[2])
    out_dir.mkdir(parents=True, exist_ok=True)

    features = []
    errors = []

    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, start=2):
            try:
                features.append(row_to_feature(row, i))
            except ValueError as e:
                errors.append(str(e))

    if errors:
        print(f"Stopped: {len(errors)} row(s) failed to convert:\n")
        for e in errors:
            print(f"  - {e}")
        print("\nFix these rows in the CSV and re-run. No output files were written.")
        sys.exit(1)

    feature_collection = {"type": "FeatureCollection", "features": features}

    geojson_path = out_dir / "data.geojson"
    geojson_path.write_text(json.dumps(feature_collection, indent=2, ensure_ascii=False), encoding="utf-8")

    js_path = out_dir / "data.js"
    js_content = "const frescoesData = " + json.dumps(feature_collection, indent=2, ensure_ascii=False) + ";\n"
    js_path.write_text(js_content, encoding="utf-8")

    print(f"Converted {len(features)} fresco(es).")
    print(f"  Wrote {geojson_path}")
    print(f"  Wrote {js_path}")
    print("\nRun validate_dataset.py next before wiring this into the map.")


if __name__ == "__main__":
    main()
