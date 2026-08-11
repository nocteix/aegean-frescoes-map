import json
import re
import sys
from pathlib import Path

MIN_LAT, MAX_LAT = 20.0, 48.0
MIN_LNG, MAX_LNG = -10.0, 40.0

REQUIRED_PROPERTIES = ["title", "culture", "imageUrl"]
ID_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def validate_feature(feature: dict, index: int, seen_ids: set) -> list[str]:
    errors = []
    feat_id = feature.get("id") or feature.get("properties", {}).get("id")

    if not feat_id:
        errors.append(f"Feature index {index}: Missing required field 'id'")
        feat_id = f"index-{index}"
    else:
        if feat_id in seen_ids:
            errors.append(f"[{feat_id}] Duplicate ID found in dataset")
        seen_ids.add(feat_id)

        if not ID_PATTERN.match(str(feat_id)):
            errors.append(
                f"[{feat_id}] ID must be lowercase letters, numbers, and hyphens only"
            )

    geometry = feature.get("geometry")
    if not geometry or geometry.get("type") != "Point":
        errors.append(f"[{feat_id}] Invalid or missing geometry (expected Point)")
    else:
        coords = geometry.get("coordinates")
        if not isinstance(coords, list) or len(coords) != 2:
            errors.append(f"[{feat_id}] Invalid coordinates structure")
        else:
            lng, lat = coords
            try:
                lat, lng = float(lat), float(lng)

                if not (MIN_LAT <= lat <= MAX_LAT):
                    errors.append(
                        f"[{feat_id}] latitude {lat} is outside expected range ({MIN_LAT}-{MAX_LAT})"
                    )

                if not (MIN_LNG <= lng <= MAX_LNG):
                    errors.append(
                        f"[{feat_id}] longitude {lng} is outside expected range ({MIN_LNG}-{MAX_LNG})"
                    )

            except (ValueError, TypeError):
                errors.append(f"[{feat_id}] Non-numeric coordinates: lat={lat}, lng={lng}")

    props = feature.get("properties", {})
    if not isinstance(props, dict):
        errors.append(f"[{feat_id}] 'properties' must be an object")
    else:
        for prop in REQUIRED_PROPERTIES:
            val = props.get(prop)
            if val is None or str(val).strip() == "":
                errors.append(f"[{feat_id}] Missing required property '{prop}'")

    return errors


def main():
    if len(sys.argv) > 1:
        geojson_path = Path(sys.argv[1])
    else:
        geojson_path = Path("assets/js/data.geojson")

    if not geojson_path.exists():
        print(f"Error: File not found at '{geojson_path}'")
        sys.exit(1)

    try:
        with geojson_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error reading JSON from '{geojson_path}': {e}")
        sys.exit(1)

    if data.get("type") != "FeatureCollection":
        print("Error: Root GeoJSON object must be of type 'FeatureCollection'")
        sys.exit(1)

    features = data.get("features", [])
    if not isinstance(features, list):
        print("Error: 'features' must be an array")
        sys.exit(1)

    print(f"Validating {len(features)} features in '{geojson_path}'...\n")

    seen_ids = set()
    all_errors = []

    for idx, feature in enumerate(features):
        feature_errors = validate_feature(feature, idx, seen_ids)
        all_errors.extend(feature_errors)

    if all_errors:
        print(f"{len(all_errors)} issue(s) found:\n")
        for err in all_errors:
            print(f"  - {err}")
        sys.exit(1)

    print("Validation successful! Dataset is valid and ready to use.")


if __name__ == "__main__":
    main()
