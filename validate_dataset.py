#!/usr/bin/env python3
"""
Validates a converted data.geojson file for common data-entry problems
before it gets wired into the Leaflet map.

Checks:
  - Duplicate `id` values
  - Missing required fields (id, title, culture, imageUrl)
  - Coordinates outside a sane Aegean/Mediterranean bounding box
    (catches a swapped lat/lng, or a stray digit, before it ships)
  - Image URLs that don't look like valid http(s) URLs
    (does NOT check that the URL is actually reachable -- that would
    require network access; run a link-checker separately if needed)
  - Missing imageAttribution (required per the CC BY-SA 4.0 sourcing plan)

Usage:
    python3 validate_dataset.py assets/js/data.geojson
"""

import json
import sys
from pathlib import Path

REQUIRED_PROPS = ["id", "title", "culture", "imageUrl"]

# Loose Mediterranean/Aegean bounding box -- covers Greece, Crete, the
# Cyclades, western Turkey, and Italy (for Pompeii/Herculaneum pieces).
# Adjust if your dataset extends further.
BBOX = {"lat_min": 33.0, "lat_max": 46.0, "lng_min": 9.0, "lng_max": 30.0}


def check_feature(feature: dict, index: int) -> list:
    issues = []
    props = feature.get("properties", {})
    fid = props.get("id", f"<no id, feature #{index}>")

    for field in REQUIRED_PROPS:
        if not props.get(field):
            issues.append(f"[{fid}] missing required field '{field}'")

    coords = feature.get("geometry", {}).get("coordinates")
    if not coords or len(coords) != 2:
        issues.append(f"[{fid}] missing or malformed coordinates")
    else:
        lng, lat = coords
        if not (BBOX["lat_min"] <= lat <= BBOX["lat_max"]):
            issues.append(f"[{fid}] latitude {lat} is outside the expected range "
                           f"({BBOX['lat_min']}-{BBOX['lat_max']}) -- check for a swapped lat/lng")
        if not (BBOX["lng_min"] <= lng <= BBOX["lng_max"]):
            issues.append(f"[{fid}] longitude {lng} is outside the expected range "
                           f"({BBOX['lng_min']}-{BBOX['lng_max']}) -- check for a swapped lat/lng")

    image_url = props.get("imageUrl", "")
    if image_url and not (image_url.startswith("http://") or image_url.startswith("https://")):
        issues.append(f"[{fid}] imageUrl doesn't look like a valid URL: {image_url!r}")

    if "imageAttribution" not in props:
        issues.append(f"[{fid}] missing imageAttribution (required for CC BY-SA 4.0 sourcing)")

    return issues


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 validate_dataset.py <data.geojson>")
        sys.exit(1)

    path = Path(sys.argv[1])
    data = json.loads(path.read_text(encoding="utf-8"))
    features = data.get("features", [])

    all_issues = []
    seen_ids = {}

    for i, feature in enumerate(features):
        all_issues.extend(check_feature(feature, i))
        fid = feature.get("properties", {}).get("id")
        if fid:
            seen_ids.setdefault(fid, []).append(i)

    for fid, indices in seen_ids.items():
        if len(indices) > 1:
            all_issues.append(f"[{fid}] duplicate id used in {len(indices)} entries")

    print(f"Checked {len(features)} fresco(es).\n")

    if not all_issues:
        print("No issues found.")
        sys.exit(0)

    print(f"{len(all_issues)} issue(s) found:\n")
    for issue in all_issues:
        print(f"  - {issue}")

    sys.exit(1)


if __name__ == "__main__":
    main()
