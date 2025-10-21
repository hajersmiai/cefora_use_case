import pandas as pd
import json
import hashlib
from datetime import datetime
from langdetect import detect, DetectorFactory
DetectorFactory.seed = 0
import pandas as pd
import json
import hashlib
from datetime import datetime
from pathlib import Path

INPUT_FILE = "SkillsFramework.xlsx"

def sha1_hash(text: str) -> str:
    """Generate a stable SHA1 hash for deduplication."""
    return hashlib.sha1(text.encode("utf-8")).hexdigest()

def build_json_records(df: pd.DataFrame, lang: str) -> list[dict]:
    """Convert DataFrame to a list of JSON records for the given language."""
    title_col = f"Title {lang}"
    desc_col = f"Description {lang}"
    context_col = f"Working Context {lang}" if f"Working Context {lang}" in df.columns else None

    records = []
    for _, row in df.iterrows():
        title = str(row.get(title_col, "") or "").strip()
        description = str(row.get(desc_col, "") or "").strip()
        context = str(row.get(context_col, "") or "").strip() if context_col else ""

        # Skip rows with no text
        if not title and not description:
            continue

        full_text = " ".join(filter(None, [title, description, context]))
        record = {
            "source": "CEFORA",
            "source_id": str(row.get("UUID", "")).strip(),
            "title": title,
            "company": None,
            "location": {
                "country": "BE",
                "region": None,
                "city": None,
            },
            "contract_type": "unknown",
            "work_model": "unknown",
            "posted_at": str(row.get("LAST_PUBLISHED_DATE", ""))[:10] or None,
            "description": full_text,
            "languages_detected": [lang.lower()],
            "skills": [],
            "skills_meta": [],
            "salary": {
                "min": None,
                "max": None,
                "currency": "EUR",
                "period": "unknown",
            },
            "hash": sha1_hash(full_text),
            "ingested_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        records.append(record)

    return records

def main():
    df = pd.read_excel(INPUT_FILE)
    langs = ["FR", "NL", "EN"]

    for lang in langs:
        data = build_json_records(df, lang)
        output_path = Path(f"offers_{lang}.json")
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ {len(data)} offers saved to {output_path.name}")

    print("🏁 Done! Files generated: offers_FR.json, offers_NL.json, offers_EN.json")

if __name__ == "__main__":
    main()
