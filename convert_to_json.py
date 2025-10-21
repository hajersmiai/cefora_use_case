import pandas as pd
import json
import hashlib
from datetime import datetime
from langdetect import detect, DetectorFactory
DetectorFactory.seed = 0

# --- CONFIG ---
EXCEL_FILE = "CP200 en ordre de cotisations 20251014.xlsx"
OUTPUT_JSON = "offers.json"
SOURCE = "vdab"  # change to actiris, stepstone, etc.

# --- HELPER FUNCTIONS ---
def clean_text(text):
    if not isinstance(text, str):
        return ""
    return " ".join(text.strip().split())

def detect_languages(text):
    try:
        return [detect(text)]
    except:
        return ["unknown"]

def compute_hash(data):
    """Stable SHA1 hash to deduplicate records."""
    base = json.dumps(data, sort_keys=True).encode("utf-8")
    return hashlib.sha1(base).hexdigest()

# --- LOAD DATA ---
df = pd.read_excel(EXCEL_FILE)

# --- MAIN CONVERSION ---
records = []
for _, row in df.iterrows():
    title = clean_text(row.get("title") or row.get("Titre") or "")
    company = clean_text(row.get("company") or row.get("Entreprise") or "")
    description = clean_text(row.get("description") or row.get("Description") or "")
    location_city = clean_text(row.get("city") or row.get("Ville") or "")
    region = clean_text(row.get("region") or row.get("Région") or "")
    posted_at = row.get("posted_at") or row.get("Date publication") or None
    if pd.notna(posted_at):
        try:
            posted_at = pd.to_datetime(posted_at).strftime("%Y-%m-%d")
        except:
            posted_at = None

    data = {
        "source": SOURCE,
        "source_id": str(row.get("id") or row.get("source_id") or f"{SOURCE}-{_}"),
        "title": title,
        "company": company,
        "location": {
            "country": "BE",
            "region": region or "unknown",
            "city": location_city or "unknown",
        },
        "contract_type": "unknown",
        "work_model": "unknown",
        "posted_at": posted_at or datetime.utcnow().strftime("%Y-%m-%d"),
        "description": description,
        "languages_detected": detect_languages(description),
        "skills": [],  # can be filled later with NLP
        "skills_meta": [],
        "salary": {
            "min": None,
            "max": None,
            "currency": "EUR",
            "period": "unknown",
        },
        "hash": None,  # computed below
        "ingested_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    data["hash"] = compute_hash(data)
    records.append(data)

# --- SAVE TO JSON ---
with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(records, f, ensure_ascii=False, indent=2)

print(f"✅ Converted {len(records)} rows to {OUTPUT_JSON}")
