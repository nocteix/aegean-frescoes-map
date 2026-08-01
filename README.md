## Aegean Frescoes Atlas

An interactive Leaflet map of Bronze Age Aegean frescoes (Minoan, Mycenaean, Cycladic), with culture-based filtering, a date-range timeline slider, search, and an image lightbox.

## Project structure

index.html              Entry point
assets/
  css/
    style.css
  js/
    data.js             Generated dataset (do not hand-edit — see Data pipeline)
    app.js              App logic
frescoes.csv            Source-of-truth data, one row per fresco
csv_to_data.py          frescoes.csv -> data.geojson + data.js
validate_dataset.py     Sanity-checks the generated data.geojson

Leaflet, Leaflet.markercluster, and Leaflet.fullscreen are loaded from a CDN. Everything else is local and static.

## Data pipeline

frescoes.csv
    │
    │  python3 csv_to_data.py frescoes.csv <output_dir>
    ▼
<output_dir>/data.geojson + <output_dir>/data.js
    │
    │  python3 validate_dataset.py <output_dir>/data.geojson
    ▼
copy data.js into assets/js/data.js

To add or edit a fresco, edit frescoes.csv, re-run both scripts, then copy the freshly generated data.js into assets/js/.

Required CSV columns: id, title, culture, lat, lng, imageUrl. Columns prefixed image_ (e.g. image_license, image_sourceUrl) are collected into an imageAttribution object on each feature. dateStart/dateEnd are parsed as numbers (negative = BCE) and drive the timeline slider, rows without both are excluded from timeline filtering.

validate_dataset.py checks for duplicate ids, missing required fields, out-of-range coordinates (catches a swapped lat/lng), malformed image URLs, and missing image attribution.


## Credits / license

Fresco images are sourced from Wikimedia Commons under CC BY-SA 4.0. Attribution for each image (photographer, license, source) is stored per entry and surfaced in the map popup.
