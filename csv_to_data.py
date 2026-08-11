import csv
import json
import os
import sys

def parse_number(val):
    if val is None or val == '':
        return None
    try:
        return int(val)
    except ValueError:
        try:
            return float(val)
        except ValueError:
            return None

def get_field(row, *possible_keys):
    for key in possible_keys:
        for csv_key in row.keys():
            if csv_key and csv_key.strip().lower() == key.lower():
                val = row[csv_key]
                if val is not None and str(val).strip() != '':
                    return str(val).strip()
    return ""

def clean_url(val):
    if not val:
        return ""
    v = val.strip()
    if v.startswith(('http://', 'https://')):
        return v
    if v.startswith(('www.', '//')):
        return 'https://' + v.lstrip('/')
    if '.org' in v or '.com' in v or '.edu' in v or '.gov' in v:
        return 'https://' + v
    return ""

def convert_csv_to_js(csv_path='frescoes_cleaned.csv', output_dir='assets/js'):
    if not os.path.exists(csv_path):
        print(f"Error: File '{csv_path}' not found.")
        sys.exit(1)

    features = []

    with open(csv_path, mode='r', encoding='utf-8-sig') as infile:
        reader = csv.DictReader(infile)
        
        for index, row in enumerate(reader, start=1):
            raw_lat = get_field(row, 'lat', 'latitude', 'site_latitude', 'y')
            raw_lng = get_field(row, 'lng', 'longitude', 'site_longitude', 'x')
            
            lat = parse_number(raw_lat)
            lng = parse_number(raw_lng)
            
            if lat is None or lng is None:
                continue

            photographer = get_field(row, 'image_photographer', 'photographer', 'imageAttographer', 'author')
            license_name = get_field(row, 'image_license', 'license', 'imageLicense')
            license_url = clean_url(get_field(row, 'image_licenseUrl', 'licenseUrl', 'license_url'))
            source_url = clean_url(get_field(row, 'image_sourceUrl', 'sourceUrl', 'source_url', 'source', 'url'))

            citation = get_field(row, 'sourceCitation', 'citation', 'bibliography', 'reference')

            attribution = {}
            if photographer: attribution['photographer'] = photographer
            if license_name: attribution['license'] = license_name
            if license_url: attribution['licenseUrl'] = license_url
            if source_url: attribution['sourceUrl'] = source_url

            properties = {
                "id": get_field(row, 'id') or f"fresco-{index}",
                "title": get_field(row, 'title', 'name') or "Untitled Fresco",
                "culture": get_field(row, 'culture') or "Unknown",
                "theme": get_field(row, 'theme') or "",
                "period": get_field(row, 'period') or "",
                "dateStart": parse_number(get_field(row, 'dateStart', 'date_start')),
                "dateEnd": parse_number(get_field(row, 'dateEnd', 'date_end')),
                "site": get_field(row, 'site', 'findspot', 'location') or "",
                "region": get_field(row, 'region') or "",
                "currentMuseum": get_field(row, 'currentMuseum', 'museum') or "",
                "locationPrecision": get_field(row, 'locationPrecision') or "",
                "imageUrl": clean_url(get_field(row, 'imageUrl', 'image_url', 'image')),
                "description": get_field(row, 'description') or "",
                "sourceCitation": citation,
                "imageAttribution": attribution if len(attribution) > 0 else None
            }

            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [lng, lat]
                },
                "properties": properties
            })

    geojson = {
        "type": "FeatureCollection",
        "features": features
    }

    os.makedirs(output_dir, exist_ok=True)
    js_output_path = os.path.join(output_dir, 'data.js')

    with open(js_output_path, mode='w', encoding='utf-8') as outfile:
        outfile.write("const frescoesData = ")
        json.dump(geojson, outfile, indent=2, ensure_ascii=False)
        outfile.write(";\n")

    print(f"Successfully exported {len(features)} frescoes to '{js_output_path}'")

if __name__ == '__main__':
    csv_file = sys.argv[1] if len(sys.argv) > 1 else 'frescoes_cleaned.csv'
    output_directory = sys.argv[2] if len(sys.argv) > 2 else 'assets/js'
    convert_csv_to_js(csv_file, output_directory)
