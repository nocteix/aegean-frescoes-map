import csv
import os
import re
import random
from urllib.parse import quote, unquote
import requests
from bs4 import BeautifulSoup

USER_PAGE = "https://commons.wikimedia.org/wiki/User:ArchaiOptix/ancient_painting"
HEADERS = {"User-Agent": "FrescoSchemaExporter/1.0 (contact@example.com)"}

CSV_FIELDNAMES = [
    "id", "title", "culture", "theme", "period", "dateStart", "dateEnd",
    "site", "region", "currentMuseum", "lat", "lng", "locationPrecision",
    "imageUrl", "image_photographer", "image_license", "image_licenseUrl",
    "image_sourceUrl", "sourceCitation", "description"
]

SITE_LOOKUP = {
    "akrotiri": {"lat": 36.3514, "lng": 25.4037, "region": "Santorini (Thera)", "museum": "Museum of Prehistoric Thera", "site": "Akrotiri"},
    "thera": {"lat": 36.3514, "lng": 25.4037, "region": "Santorini (Thera)", "museum": "Museum of Prehistoric Thera", "site": "Akrotiri"},
    "santorini": {"lat": 36.3514, "lng": 25.4037, "region": "Santorini (Thera)", "museum": "Museum of Prehistoric Thera", "site": "Akrotiri"},
    "phylakopi": {"lat": 36.7428, "lng": 24.4267, "region": "Cyclades", "museum": "National Archaeological Museum, Athens", "site": "Phylakopi"},
    "milos": {"lat": 36.7428, "lng": 24.4267, "region": "Cyclades", "museum": "Archaeological Museum of Milos", "site": "Phylakopi"},
    "kea": {"lat": 37.6631, "lng": 24.3314, "region": "Cyclades", "museum": "Archaeological Museum of Kea", "site": "Ayia Irini"},
    "delos": {"lat": 37.3978, "lng": 25.2675, "region": "Cyclades", "museum": "Archaeological Museum of Delos", "site": "Delos"},

    "knossos": {"lat": 35.2980, "lng": 25.1632, "region": "Crete", "museum": "Heraklion Archaeological Museum", "site": "Knossos"},
    "phaistos": {"lat": 35.0513, "lng": 24.8142, "region": "Crete", "museum": "Heraklion Archaeological Museum", "site": "Phaistos"},
    "triada": {"lat": 35.0594, "lng": 24.7933, "region": "Crete", "museum": "Heraklion Archaeological Museum", "site": "Ayia Triada"},
    "malia": {"lat": 35.2931, "lng": 25.4925, "region": "Crete", "museum": "Heraklion Archaeological Museum", "site": "Malia"},
    "zakros": {"lat": 35.0978, "lng": 26.2611, "region": "Crete", "museum": "Heraklion Archaeological Museum", "site": "Zakros"},
    "tylissos": {"lat": 35.2975, "lng": 25.0133, "region": "Crete", "museum": "Heraklion Archaeological Museum", "site": "Tylissos"},
    "amnisos": {"lat": 35.3308, "lng": 25.2056, "region": "Crete", "museum": "Heraklion Archaeological Museum", "site": "Amnisos"},

    "mycenae": {"lat": 37.7308, "lng": 22.7561, "region": "Peloponnese", "museum": "Archaeological Museum of Mycenae", "site": "Mycenae"},
    "tiryns": {"lat": 37.5994, "lng": 22.8169, "region": "Peloponnese", "museum": "National Archaeological Museum, Athens", "site": "Tiryns"},
    "pylos": {"lat": 37.0278, "lng": 21.6967, "region": "Peloponnese", "museum": "Archaeological Museum of Chora", "site": "Pylos"},
    "thebes": {"lat": 38.3225, "lng": 23.3175, "region": "Boeotia", "museum": "Archaeological Museum of Thebes", "site": "Thebes"},
    "orchomenos": {"lat": 38.4922, "lng": 22.9753, "region": "Boeotia", "museum": "Archaeological Museum of Thebes", "site": "Orchomenos"},
    "pella": {"lat": 40.7594, "lng": 22.5222, "region": "Macedonia", "museum": "Archaeological Museum of Pella", "site": "Pella"},
    "vergina": {"lat": 40.4853, "lng": 22.3197, "region": "Macedonia", "museum": "Museum of the Royal Tombs of Aigai", "site": "Aigai"},
    "athens": {"lat": 37.9891, "lng": 23.7326, "region": "Attica", "museum": "National Archaeological Museum, Athens", "site": "Athens"},

    "pompeii": {"lat": 40.7508, "lng": 14.4866, "region": "Campania", "museum": "Naples National Archaeological Museum", "site": "Pompeii"},
    "herculaneum": {"lat": 40.8061, "lng": 14.3475, "region": "Campania", "museum": "Naples National Archaeological Museum", "site": "Herculaneum"},
    "stabiae": {"lat": 40.6978, "lng": 14.4989, "region": "Campania", "museum": "Naples National Archaeological Museum", "site": "Stabiae"},
    "naples": {"lat": 40.8534, "lng": 14.2505, "region": "Campania", "museum": "Naples National Archaeological Museum", "site": "Naples"},
    "tarquinia": {"lat": 42.2536, "lng": 11.7583, "region": "Lazio", "museum": "Tarquinia National Museum", "site": "Tarquinia"},
    "cerveteri": {"lat": 41.9986, "lng": 12.0983, "region": "Lazio", "museum": "National Etruscan Museum", "site": "Cerveteri"},
    "rome": {"lat": 41.8902, "lng": 12.4922, "region": "Lazio", "museum": "National Roman Museum", "site": "Rome"},

    "egypt": {"lat": 25.7280, "lng": 32.6053, "region": "Egypt", "museum": "Egyptian Museum, Cairo", "site": "Luxor"},
    "fayum": {"lat": 29.3084, "lng": 30.8428, "region": "Egypt", "museum": "Egyptian Museum, Cairo", "site": "Faiyum"},
    "saqqara": {"lat": 29.8713, "lng": 31.2163, "region": "Egypt", "museum": "Imhotep Museum", "site": "Saqqara"}
}

CULTURE_RULES = {
    "Minoan": ["minoan", "knossos", "phaistos", "malia", "zakros", "triada"],
    "Cycladic": ["cycladic", "akrotiri", "thera", "phylakopi", "milos", "kea"],
    "Mycenaean": ["mycenaean", "mycenae", "tiryns", "pylos", "thebes"],
    "Etruscan": ["etruscan", "tarquinia", "cerveteri"],
    "Roman": ["roman", "pompeii", "herculaneum", "stabiae", "fayum"],
    "Greek / Classical": ["classical", "hellenistic", "pella", "delos"],
    "Egyptian": ["egyptian", "egypt", "saqqara", "fayum"]
}

THEME_RULES = {
    "Animal": ["monkey", "bull", "dolphin", "bird", "swallow", "cat", "lion", "fish", "squid", "octopus"],
    "Floral & Landscape": ["landscape", "lily", "crocus", "papyrus", "garden", "flower", "reeds", "nature", "tree"],
    "Ritual & Religion": ["procession", "priest", "priestess", "goddess", "altar", "offering", "bull-leaping", "shrine"],
    "Human & Daily Life": ["boxer", "fisherman", "musician", "dancer", "hunting", "warrior", "banquet", "portrait"],
    "Architecture & Pattern": ["marbling", "architectural", "frieze", "rosette", "spiral", "border", "pattern"]
}

def classify_text(text: str, rules: dict, default: str = "Unclassified") -> str:
    text_lower = text.lower()
    for category, keywords in rules.items():
        if any(keyword in text_lower for keyword in keywords):
            return category
    return default

def match_site_info(text: str):
    text_lower = text.lower()
    for key, data in SITE_LOOKUP.items():
        if key in text_lower:
            jitter_lat = round(data["lat"] + random.uniform(-0.0015, 0.0015), 5)
            jitter_lng = round(data["lng"] + random.uniform(-0.0015, 0.0015), 5)
            return {
                "lat": str(jitter_lat),
                "lng": str(jitter_lng),
                "region": data["region"],
                "museum": data["museum"],
                "site": data["site"]
            }
    return {
        "lat": str(round(35.2980 + random.uniform(-0.002, 0.002), 5)),
        "lng": str(round(25.1632 + random.uniform(-0.002, 0.002), 5)),
        "region": "Crete",
        "museum": "Heraklion Archaeological Museum",
        "site": "Aegean Prehistoric"
    }

def slugify(text: str) -> str:
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')

def generate_unique_id(site: str, title: str, file_title: str, index: int, seen_ids: set) -> str:
    candidate = slugify(f"{site}-{title}")
    if not candidate or candidate == "aegean-prehistoric":
        candidate = slugify(file_title)
    if not candidate:
        candidate = f"fresco-{index + 1}"
    
    final_id = candidate
    counter = 1
    while final_id in seen_ids or not final_id:
        final_id = f"{candidate}-{counter}"
        counter += 1
    
    seen_ids.add(final_id)
    return final_id

def sanitize_fresco(item: dict, index: int, seen_ids: set) -> dict:
    raw_id = item.get("id")
    if not raw_id or not str(raw_id).strip() or str(raw_id).strip() == "?":
        new_id = f"fresco-{index + 1}"
        counter = 1
        while new_id in seen_ids:
            new_id = f"fresco-{index + 1}-{counter}"
            counter += 1
        item["id"] = new_id
        seen_ids.add(new_id)

    if not item.get("title") or not str(item["title"]).strip():
        item["title"] = f"Ancient Fresco #{index + 1}"

    for field in CSV_FIELDNAMES:
        if field not in item or item[field] is None:
            item[field] = ""

    return item

def scrape_frescoes():
    response = requests.get(USER_PAGE, headers=HEADERS)
    soup = BeautifulSoup(response.text, "html.parser")
    
    tables = soup.find_all("table")
    gallery_boxes = soup.find_all("li", class_="gallerybox")
    frescoes = []
    seen_files = set()
    seen_ids = set()

    # Strategy 1: Table parsing
    for table in tables:
        for row in table.find_all("tr"):
            cells = row.find_all(["td", "th"])
            if not cells:
                continue
            
            img_link = row.find("a", href=re.compile(r'File:'))
            if not img_link:
                continue
            
            href = img_link.get("href", "")
            file_title = unquote(href.split("File:")[-1]) if "File:" in href else ""
            if not file_title or file_title in seen_files:
                continue
            seen_files.add(file_title)
            
            raw_text = [c.get_text(strip=True) for c in cells if c.get_text(strip=True)]
            full_line = " ".join(raw_text) + " " + file_title
            
            title = raw_text[0] if len(raw_text) > 0 else file_title.replace("_", " ")
            site_museum_str = raw_text[1] if len(raw_text) > 1 else ""
            period_str = raw_text[2] if len(raw_text) > 2 else ""
            description = " ".join(raw_text[3:]) if len(raw_text) > 3 else full_line
            
            site_data = match_site_info(full_line)
            culture = classify_text(full_line, CULTURE_RULES, default="Minoan")
            theme = classify_text(full_line, THEME_RULES, default="General / Decorative")
            row_id = generate_unique_id(site_data["site"], title, file_title, len(frescoes), seen_ids)

            frescoes.append({
                "id": row_id,
                "title": title or f"Fresco #{len(frescoes) + 1}",
                "culture": culture,
                "theme": theme,
                "period": period_str,
                "dateStart": "",
                "dateEnd": "",
                "site": site_museum_str or site_data["site"],
                "region": site_data["region"],
                "currentMuseum": site_data["museum"],
                "lat": site_data["lat"],
                "lng": site_data["lng"],
                "locationPrecision": "approximate",
                "imageUrl": f"https://commons.wikimedia.org/wiki/Special:FilePath/{quote(file_title)}?width=400",
                "image_photographer": "ArchaiOptix",
                "image_license": "CC BY-SA 4.0",
                "image_licenseUrl": "https://creativecommons.org/licenses/by-sa/4.0",
                "image_sourceUrl": f"https://commons.wikimedia.org/wiki/File:{quote(file_title)}",
                "sourceCitation": "",
                "description": description
            })

    for box in gallery_boxes:
        img_link = box.find("a", href=re.compile(r'File:'))
        if not img_link:
            continue
        
        file_title = unquote(img_link["href"].split("File:")[-1])
        if not file_title or file_title in seen_files:
            continue
        seen_files.add(file_title)

        caption = box.find("div", class_="gallerytext")
        caption_text = caption.get_text(strip=True) if caption else file_title
        full_line = file_title + " " + caption_text
        
        site_data = match_site_info(full_line)
        image_url = f"https://commons.wikimedia.org/wiki/Special:FilePath/{quote(file_title)}?width=400"
        culture = classify_text(full_line, CULTURE_RULES, default="Minoan")
        theme = classify_text(full_line, THEME_RULES, default="General / Decorative")
        row_id = generate_unique_id(site_data["site"], caption_text, file_title, len(frescoes), seen_ids)
        
        frescoes.append({
            "id": row_id,
            "title": caption_text.split(".")[0] or f"Fresco #{len(frescoes) + 1}",
            "culture": culture,
            "theme": theme,
            "period": "",
            "dateStart": "",
            "dateEnd": "",
            "site": site_data["site"],
            "region": site_data["region"],
            "currentMuseum": site_data["museum"],
            "lat": site_data["lat"],
            "lng": site_data["lng"],
            "locationPrecision": "approximate",
            "imageUrl": image_url,
            "image_photographer": "ArchaiOptix",
            "image_license": "CC BY-SA 4.0",
            "image_licenseUrl": "https://creativecommons.org/licenses/by-sa/4.0",
            "image_sourceUrl": f"https://commons.wikimedia.org/wiki/File:{quote(file_title)}",
            "sourceCitation": "",
            "description": caption_text
        })

    final_seen_ids = set()
    sanitized_frescoes = [sanitize_fresco(item, idx, final_seen_ids) for idx, item in enumerate(frescoes)]

    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, "frescoes_custom_schema.csv")

    with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES)
        writer.writeheader()
        writer.writerows(sanitized_frescoes)

    print(f"Done! Scraped and sanitized {len(sanitized_frescoes)} entries.")

if __name__ == "__main__":
    scrape_frescoes()
