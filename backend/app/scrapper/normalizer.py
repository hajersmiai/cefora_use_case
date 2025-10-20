from __future__ import annotations
import re
import hashlib

BELGIUM_REGION_MAP = {
    "Brussels": "Brussels",
    "Bruxelles": "Brussels",
    "Brussel": "Brussels",
    "Wallonia": "Wallonia",
    "Wallonie": "Wallonia",
    "Flanders": "Flanders",
    "Vlaanderen": "Flanders",
    # fallback: province keywords
    "Hainaut": "Wallonia", "Liège":"Wallonia", "Namur":"Wallonia", "Luxembourg":"Wallonia", "Brabant Wallon":"Wallonia",
    "Antwerp":"Flanders","Antwerpen":"Flanders","Limburg":"Flanders","Oost-Vlaanderen":"Flanders","West-Vlaanderen":"Flanders","Vlaams-Brabant":"Flanders"
}

SKILL_KEYWORDS = [
    "python","sql","excel","power bi","pandas","etl","fastapi","react","docker",
    "nl","fr","en","azure","aws","spark","ml","nltk","gis","sap","salesforce"
]

def url_hash(url: str) -> str:
    return hashlib.sha256(url.strip().encode("utf-8")).hexdigest()

def normalize_region(location_text: str) -> str:
    for k, v in BELGIUM_REGION_MAP.items():
        if re.search(rf"\b{k}\b", location_text, flags=re.I):
            return v
    return ""

def extract_skills(text: str) -> dict:
    found = sorted({kw for kw in SKILL_KEYWORDS if re.search(rf"\b{re.escape(kw)}\b", text, flags=re.I)})
    return {"keywords": found}
