import asyncio
import nest_asyncio
from playwright.async_api import async_playwright
import pandas as pd
import re
import json
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from urllib.parse import urlparse
import spacy
import logging
import random
from tenacity import retry, stop_after_attempt, wait_exponential
import os
import argparse
from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime
import subprocess
import sys
import math

# --- AIOHTTP FAST SCRAPER ---
try:
    import aiohttp
except Exception:
    aiohttp = None

async def aiohttp_fast_scrape(domains, limit=0, concurrency=32, save_path="vdab_jobs_aiohttp_fast.csv"):
    if aiohttp is None:
        raise RuntimeError("aiohttp not installed")
    results = []
    timeout = aiohttp.ClientTimeout(total=30)
    headers = {'User-Agent': config.USER_AGENT, 'Accept-Language': 'nl-BE,nl;q=0.9,en;q=0.8'}
    sem = asyncio.Semaphore(concurrency)
    page_size = 50
    # Print found domains at the start
    tqdm.write(f"Found {len(domains)} domains: {', '.join(domains)}")
    async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
        async def fetch(url):
            async with sem:
                try:
                    async with session.get(url) as r:
                        if r.status == 200:
                            return await r.text()
                        return None
                except Exception:
                    return None
        async def process_job(url, domain, idx):
            html = await fetch(url)
            if not html:
                return None
            # Use selectolax if available, else BeautifulSoup
            if SELECTOLAX_AVAILABLE and config.USE_SELECTOLAX:
                try:
                    doc = SelectolaxParser(html)
                    title_node = doc.css_first('h1') or doc.css_first('.job-title')
                    title = title_node.text(deep=False).strip() if title_node else ''
                    desc = doc.text(separator=' ').strip()
                except Exception:
                    soup = BeautifulSoup(html, 'lxml')
                    title = soup.find('h1').get_text(strip=True) if soup.find('h1') else ''
                    desc = soup.get_text(' ', strip=True)
            else:
                soup = BeautifulSoup(html, 'lxml')
                title = soup.find('h1').get_text(strip=True) if soup.find('h1') else ''
                desc = soup.get_text(' ', strip=True)
            # Suppress per-job info logs (JSON-LD and extracted fields)
            # Minimal job dict (expand as needed)
            job = {
                'job_id': f'vdab-{domain[:2].title()}{idx:05d}',
                'title': title,
                'company': '',
                'city': '',
                'contract_type': '',
                'posted_on': '',
                'detail_url': url,
                'original_url': url,
                'domain': domain,
                'scraped_at': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
                'functieomschrijving': desc[:3000],
                'profiel': '',
                'professionele_vaardigheden': '',
                'anbod': '',
                'full_description': desc,
                'academic_level': 'Not specified',
                'years_experience': 0,
                'salary': 'Not specified',
            }
            return job
        for domain in domains:
            offset = 0
            idx = 0
            domain_total = 0
            # First, get the total number of jobs for this domain (estimate by fetching the first page and counting tiles)
            list_url = f"{SITE_ROOT}/vindeenjob/jobs/{domain}?limit={page_size}&offset=0"
            html = await fetch(list_url)
            if not html:
                continue
            soup = BeautifulSoup(html, 'lxml')
            tiles = soup.select('div.product-tile')
            domain_total = len(tiles) if tiles else 0
            # tqdm progress bar for this domain
            if TQDM_AVAILABLE:
                bar = tqdm(total=0, desc=f"{domain} jobs", unit="jobs")
            else:
                bar = None
            while True:
                if offset > 0:
                    list_url = f"{SITE_ROOT}/vindeenjob/jobs/{domain}?limit={page_size}&offset={offset}"
                    html = await fetch(list_url)
                    if not html:
                        break
                    soup = BeautifulSoup(html, 'lxml')
                    tiles = soup.select('div.product-tile')
                links = []
                for tile in tiles:
                    a = tile.select_one('a.product-link') or tile.select_one('a')
                    if not a:
                        continue
                    href = a.get('href')
                    if not href:
                        continue
                    u = href.split('#')[0]
                    if u.startswith('/'):
                        u = urljoin(SITE_ROOT, u)
                    if u not in links:
                        links.append(u)
                if not links:
                    break
                tasks = [asyncio.create_task(process_job(u, domain, idx+i+1)) for i, u in enumerate(links)]
                jobs = await asyncio.gather(*tasks)
                for job in jobs:
                    if job:
                        results.append(job)
                        idx += 1
                        if bar:
                            bar.update(1)
                        if limit and len(results) >= limit:
                            break
                if limit and len(results) >= limit:
                    break
                offset += page_size
            if bar:
                bar.close()
    if results:
        df = pd.DataFrame(results)
        df.to_csv(save_path, index=False)
        tqdm.write(f"[AIOHTTP FAST] Saved {len(results)} jobs to {save_path}")
    else:
        tqdm.write("[AIOHTTP FAST] No jobs scraped.")
    return results

# Optional fast parser (selectolax) for high-throughput HTML parsing
try:
    from selectolax.parser import HTMLParser as SelectolaxParser
    SELECTOLAX_AVAILABLE = True
except Exception:
    SelectolaxParser = None
    SELECTOLAX_AVAILABLE = False

# Optional progress bar (tqdm). If not available, provide a no-op fallback.
try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except Exception:
    TQDM_AVAILABLE = False
    def tqdm(x=None, **kwargs):
        # simple fallback that returns the iterable unchanged
        return x if x is not None else []

def pwrite(msg: str):
    """Print a message using tqdm.write when available (keeps bars intact), else logger.info."""
    try:
        if TQDM_AVAILABLE:
            tqdm.write(msg)
        else:
            logger.info(msg)
    except Exception:
        logger.info(msg)

# Apply nest_asyncio for Jupyter compatibility
nest_asyncio.apply()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('vdab_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class Config:
    SAVE_PATH: str = os.getenv("SAVE_PATH", "vdab_jobs_datafull3.csv")
    LIMIT: int = int(os.getenv("LIMIT", "2000"))
    BASE_URL: str = "https://www.vdab.be/vindeenjob/jobs"
    REQUEST_DELAY: tuple = (1, 3)  # min, max delay in seconds
    TIMEOUT: int = 60000
    PAGE_TIMEOUT_MS: int = 20000
    USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
    MAX_RETRIES: int = 3
    # Concurrency and pagination tuning
    CONCURRENCY: int = int(os.getenv("CONCURRENCY", "12"))
    MAX_PAGES: int = int(os.getenv("MAX_PAGES", "200"))
    SAVE_EVERY: int = int(os.getenv("SAVE_EVERY", "20"))
    # Fast-mode tuning: when enabled the scraper will throttle less, increase concurrency
    FAST_MODE: bool = os.getenv("FAST_MODE", "0") in ("1", "true", "True")
    FAST_CONCURRENCY: int = int(os.getenv("FAST_CONCURRENCY", "24"))
    # When True, use Playwright's request API (context.request) to fetch job detail HTML
    # which is significantly faster than creating a full new Page for each job.
    # Default to False to ensure JS-rendered content (JSON-LD/title) is available when parsing.
    USE_REQUESTS_FOR_DETAILS: bool = os.getenv("USE_REQUESTS_FOR_DETAILS", "0") in ("1", "true", "True")
    # Use aiohttp for both listing and detail fetching (bypasses Playwright entirely).
    # Disable by default to reduce complexity; enable only if you know aiohttp is required.
    USE_AIOHTTP_FOR_FETCH: bool = os.getenv("USE_AIOHTTP_FOR_FETCH", "0") in ("1", "true", "True")
    # Prefer selectolax parser when available for speed; fallback to BeautifulSoup
    USE_SELECTOLAX: bool = os.getenv("USE_SELECTOLAX", "1") in ("1", "true", "True") and SELECTOLAX_AVAILABLE
    # Number of parallel OS worker processes to spawn for large scrapes
    WORKERS: int = int(os.getenv("WORKERS", "1"))
    # QUICK_MODE: force more aggressive speedup for local/testing runs
    QUICK_MODE: bool = os.getenv("QUICK_MODE", "0") in ("1", "true", "True")
    # Restart browser context every N domains to avoid long-lived pipe issues
    RESTART_CONTEXT_EVERY_DOMAINS: int = int(os.getenv("RESTART_CONTEXT_EVERY_DOMAINS", "6"))
    # When True, ignore per-domain LIMIT and fetch until pagination ends (or MAX_PAGES reached)
    FETCH_ALL: bool = os.getenv("FETCH_ALL", "0") in ("1", "true", "True")

config = Config()

# Site root used for normalizing absolute-path hrefs
SITE_ROOT = "https://www.vdab.be"

# Mapping of domain key -> two-letter code (copied from vdab_scapper.py)
DOMAIN_CODE_MAP = {
    "aankoop": "Aa", "administratie": "Ad", "bouw": "Bo", "communicatie": "Co",
    "creatief": "Cr", "dienstverlening": "Di", "financieel": "Fi", "gezondheid": "Ge",
    "horeca-en-toerisme": "Ho", "human-resources": "Hu", "ict": "Ic", "juridisch": "Ju",
    "land-en-tuinbouw": "La", "logistiek-en-transport": "Lo", "management": "Ma",
    "marketing": "Mk", "onderhoud": "On", "onderwijs": "Od", "onderzoek-en-ontwikkeling": "Oo",
    "overheid": "Ov", "productie": "Pr", "techniek": "Te", "verkoop": "Ve", "andere": "An"
}

# Load spaCy model
try:
    nlp = spacy.load("nl_core_news_lg")
    logger.info("Loaded large Dutch spaCy model")
except OSError:
    try:
        nlp = spacy.load("nl_core_news_sm")
        logger.info("Loaded small Dutch spaCy model")
    except OSError:
        logger.warning("No Dutch spaCy model found. Please install with: python -m spacy download nl_core_news_sm")
        nlp = None

def extract_salary_structured(text: str) -> Optional[Dict]:
    """Return a structured salary dict extracted from text.

    Dict shape (any of):
      - {raw: str, value: int, currency: 'EUR', unit: str}
      - {raw: str, min: int, max: int, currency: 'EUR', unit: str}

    Returns None when no plausible salary found.
    """
    if not text:
        return None

    t = re.sub(r"\s+", " ", text)

    def _looks_like_address(fragment: str) -> bool:
        if not fragment:
            return False
        groups = re.findall(r"\d{1,4}", fragment)
        if not groups:
            return False
        for g in groups:
            if len(g) == 4:
                try:
                    v = int(g)
                    if 1000 <= v <= 9999:
                        return True
                except Exception:
                    pass
        if len(groups) >= 3:
            return True
        return False

    # Normalize euro amounts like '€18.191' -> '18191'
    def _normalize_number_fragment(s: str) -> Optional[int]:
        if not s:
            return None
        # remove spaces and thousands separators like '.' and ',' when used as grouping
        # Keep only digits
        num = re.sub(r"[^\d]", "", s)
        if not num:
            return None
        try:
            return int(num)
        except Exception:
            return None

    # Unit detection (heuristics)
    unit = None
    unit_patterns = {
        'year': [r'per jaar', r'jaarlijks', r'per jaar', r'p\.j\.', r'jaarloon', r'jaar'],
        'month': [r'per maand', r'maandelijks', r'maandloon', r'maand'],
        'hour': [r'per uur', r'uurloon', r'per uur', r'/uur', r'uur']
    }
    low = t.lower()
    for u, pats in unit_patterns.items():
        for p in pats:
            if re.search(p, low):
                unit = u
                break
        if unit:
            break

    # Range patterns like '€ 3.000 - € 4.500' or 'tussen €3.000 en €4.500'
    range_match = re.search(r"€\s*([\d\.\s,]+)\s*(?:-|tot|en|à)\s*€?\s*([\d\.\s,]+)", t, flags=re.IGNORECASE)
    if range_match:
        a_raw = range_match.group(1)
        b_raw = range_match.group(2)
        if _looks_like_address(a_raw) or _looks_like_address(b_raw):
            pass
        else:
            a_n = _normalize_number_fragment(a_raw)
            b_n = _normalize_number_fragment(b_raw)
            if a_n and b_n:
                mn, mx = min(a_n, b_n), max(a_n, b_n)
                if 800 <= mx <= 200000:
                    return {"raw": range_match.group(0).strip(), "min": mn, "max": mx, "currency": "EUR", "unit": unit}

    # Single euro amounts
    amounts = re.findall(r"€\s*([\d\.\s,]+)", t)
    cleaned = []
    for amt in amounts:
        if _looks_like_address(amt):
            continue
        n = _normalize_number_fragment(amt)
        if n:
            cleaned.append((amt.strip(), n))

    if cleaned:
        # take plausible values
        plausible = [pair for pair in cleaned if 800 <= pair[1] <= 200000]
        if plausible:
            vals = [p[1] for p in plausible]
            if len(vals) == 1:
                return {"raw": plausible[0][0], "value": vals[0], "currency": "EUR", "unit": unit}
            else:
                return {"raw": ", ".join([p[0] for p in plausible]), "min": min(vals), "max": max(vals), "currency": "EUR", "unit": unit}

    # words like '2000 euro' or '2000 eur'
    eur_word_match = re.findall(r"(\d[\d\.\s,]+)\s*(?:eur|euro)\b", t, flags=re.IGNORECASE)
    eur_clean = []
    for amt in eur_word_match:
        n = _normalize_number_fragment(amt)
        if n:
            eur_clean.append((amt.strip(), n))
    if eur_clean:
        plausible = [pair for pair in eur_clean if 800 <= pair[1] <= 200000]
        if plausible:
            vals = [p[1] for p in plausible]
            if len(vals) == 1:
                return {"raw": plausible[0][0] + ' euro', "value": vals[0], "currency": "EUR", "unit": unit}
            else:
                return {"raw": ", ".join([p[0] for p in plausible]) + ' euro', "min": min(vals), "max": max(vals), "currency": "EUR", "unit": unit}

    # fallback: look for 'salaris' or 'bruto' followed by a number
    m = re.search(r"(?:salaris|bruto)[^\d€%]*(?:€)?\s*([\d\.\s,]+)", t, flags=re.IGNORECASE)
    if m:
        n = _normalize_number_fragment(m.group(1))
        if n and 800 <= n <= 200000:
            return {"raw": m.group(0).strip(), "value": n, "currency": "EUR", "unit": unit}

    return None

    

# --- Feature extraction ---
def extract_features(text: str) -> Dict:
    """Extract features from job description text."""
    if not text:
        return create_default_features()
    
    text = text.lower()
    feats = create_default_features()

    # Academic level extraction
    academic_patterns = {
        "PhD": r'\b(phd|doctoraat|promotie)\b',
        "Master": r'\b(master|universitair|licentiaat)\b', 
        "Bachelor": r'\b(bachelor|hogeschool)\b',
        "Secondary": r'\b(middelbaar|secundair)\b'
    }
    
    for level, pattern in academic_patterns.items():
        if re.search(pattern, text):
            feats["academic_level"] = level
            break  # Stop at highest level found

    # Years of experience
    experience_match = extract_experience(text)
    if experience_match:
        feats["years_experience"] = experience_match

    # Salary extraction: produce a structured salary object and keep a
    # backwards-compatible `salary` field (int or range string or 'Not specified')
    salary_struct = extract_salary_structured(text)
    if salary_struct:
        feats["salary_structured"] = salary_struct
        # keep old 'salary' simple string/int for compatibility
        if salary_struct.get("value") is not None:
            feats["salary"] = salary_struct["value"]
        elif salary_struct.get("min") is not None and salary_struct.get("max") is not None:
            feats["salary"] = f"{salary_struct['min']}-{salary_struct['max']}"
        else:
            feats["salary"] = "Not specified"

    # Skill extraction
    feats.update(extract_skills(text))
    
    return feats

def create_default_features() -> Dict:
    """Create a dictionary with default feature values."""
    return {
        "academic_level": "Not specified",
        "years_experience": 0,
        "salary": "Not specified",
        **{f"{skill}_skill": "No" for skill in [
            "computer", "ai", "data_analysis", "communication", "leadership",
            "project_management", "customer_service", "sales", "technical",
            "creative", "finance", "hr", "administrative", "dutch_language",
            "french_language", "english_language", "spanish_language", "italian_language"
        ]}
    }

def extract_experience(text: str) -> int:
    """Extract years of experience from text."""
    match = re.search(r"(\d{1,2})(?:\s*(?:-|à|tot)\s*(\d{1,2}))?\s*(jaar|years)", text)
    if match:
        try:
            start = int(match.group(1))
            end = int(match.group(2)) if match.group(2) else start
            return (start + end) // 2
        except (ValueError, TypeError):
            pass
    return 0

def extract_salary(text: str) -> str:
    """Extract salary information from text."""
    if not text:
        return "Not specified"

    # Normalize whitespace
    t = re.sub(r"\s+", " ", text)
    # helper: detect address/postcode-like numeric fragments such as '49 3 2630' which
    # would otherwise become '4932630' when non-digits are stripped. If a fragment
    # contains multiple small numeric groups and a 4-digit group in Belgian postal-code
    # range, treat it as an address and ignore.
    def _looks_like_address(fragment: str) -> bool:
        if not fragment:
            return False
        groups = re.findall(r"\d{1,4}", fragment)
        if not groups:
            return False
        # If any 4-digit group falls in typical postal code range, consider address-like
        for g in groups:
            if len(g) == 4:
                try:
                    v = int(g)
                    if 1000 <= v <= 9999:
                        return True
                except Exception:
                    pass
        # Multiple small numeric groups (house no., box, postal) likely indicate address
        if len(groups) >= 3:
            return True
        return False

    # Look for explicit range patterns like 'tussen €3.000 en €4.500' or '€3.000 - €4.500'
    range_match = re.search(r"€\s*([\d\.\s]+)\s*(?:-|tot|en|à)\s*€?\s*([\d\.\s]+)", t, flags=re.IGNORECASE)
    if range_match:
        raw_a = range_match.group(1) or ''
        raw_b = range_match.group(2) or ''
        # if either side looks like an address/postcode fragment, ignore this match
        if _looks_like_address(raw_a) or _looks_like_address(raw_b):
            pass
        else:
            a = re.sub(r"[^\d]", "", raw_a)
            b = re.sub(r"[^\d]", "", raw_b)
            if a and b:
                try:
                    a_i = int(a)
                    b_i = int(b)
                    # prefer realistic salary ranges (monthly or yearly bounds)
                    if max(a_i, b_i) > 200000 or (a_i < 100 and b_i < 100):
                        pass
                    else:
                        return f"{min(a_i,b_i)}-{max(a_i,b_i)}"
                except Exception:
                    pass

    # Fall back: find all euro amounts and if multiple are present, return the min-max
    amounts = re.findall(r"€\s*([\d\.\s]+)", t)
    cleaned = []
    for amt in amounts:
        # skip fragments that look like addresses (e.g., '49 3 2630')
        if _looks_like_address(amt):
            continue
        num = re.sub(r"[^\d]", "", amt)
        if num:
            try:
                cleaned.append(int(num))
            except Exception:
                continue

    if len(cleaned) >= 1:
        # prefer amounts that are within reasonable salary bounds
        filtered = [c for c in cleaned if 800 <= c <= 200000]
        if filtered:
            return f"{min(filtered)}-{max(filtered)}" if len(filtered) > 1 else str(filtered[0])
        else:
            # no plausible euro amounts found; avoid returning tiny numbers or concatenated addresses
            return "Not specified"

    # Last-resort: look for words 'salaris' followed by numbers
    # Also accept amounts expressed with 'eur' or 'euro' words (e.g., '2000 euro')
    eur_word_match = re.findall(r"(\d[\d\.\s]+)\s*(?:eur|euro)\b", t, flags=re.IGNORECASE)
    eur_cleaned = []
    for amt in eur_word_match:
        num = re.sub(r"[^\d]", "", amt)
        if num:
            try:
                eur_cleaned.append(int(num))
            except Exception:
                continue
    if eur_cleaned:
        filtered = [c for c in eur_cleaned if 800 <= c <= 200000]
        if filtered:
            return f"{min(filtered)}-{max(filtered)}" if len(filtered) > 1 else str(filtered[0])

    # Last-resort: look for words 'salaris' or 'bruto' followed by numbers, but ignore percentages and reimbursement contexts
    # Ignore patterns like '100% terugbetaling' or numbers followed by '%'
    if re.search(r"\d+%", t):
        # If there's a % in the text, it's likely not a salary unless accompanied by a euro amount
        if not re.search(r"€", t) and not re.search(r"eur|euro", t, flags=re.IGNORECASE) and not re.search(r"salaris|bruto", t, flags=re.IGNORECASE):
            return "Not specified"

    match = re.search(r"(?:salaris|bruto)[^\d€\%]*(?:€)?\s*([\d\.\s]+)", t, flags=re.IGNORECASE)
    if match:
        num = re.sub(r"[^\d]", "", match.group(1))
        if num:
            try:
                val = int(num)
                if 800 <= val <= 200000:
                    return str(val)
            except Exception:
                pass

    return "Not specified"

def extract_skills(text: str) -> Dict:
    """Extract various skills from text."""
    # Use regex-based patterns for more robust detection (captures punctuation and separators)
    t = (text or "").lower()
    skill_patterns = {
        "computer_skill": [r"\bexcel\b", r"\boffice\b", r"\berp\b", r"\bsoftware\b", r"\bict\b", r"\bpython\b", r"\bjava\b", r"\bsql\b"],
        "ai_skill": [r"machine learning", r"\bai\b", r"kunstmatige intelligentie", r"artificial intelligence"],
        "data_analysis_skill": [r"\bdata\b", r"analyse", r"statistiek", r"analytics", r"\bbi\b"],
        "communication_skill": [r"communicatie", r"communicatief", r"presentatie", r"overleg"],
        "leadership_skill": [r"leiding", r"\bmanager\b", r"coach", r"teamleider", r"leiderschap"],
        "project_management": [r"project", r"planning", r"scrum", r"agile", r"waterfall"],
        "customer_service_skill": [r"klantgericht", r"\bklant\b", r"service", r"customer"],
        "sales_skill": [r"verkoop", r"sales", r"commercieel", r"accountmanager"],
        "technical_skill": [r"technisch", r"engineering", r"installatie", r"technologie"],
        "creative_skill": [r"creatief", r"ontwerp", r"design", r"grafisch"],
        "finance_skill": [r"boekhouding", r"finance", r"budget", r"accounting"],
        "hr_skill": [r"\bhr\b", r"rekrutering", r"personeel", r"human resources"],
        "administrative_skill": [r"administratie", r"secretariaat", r"kantoor"],
        # Languages: use word-boundary and common variants
        "dutch_language": [r"\bnederlands\b", r"nederlandstalig", r"beheersing van het nederlands", r"beheersing van nederlands"],
        "french_language": [r"\bfrans\b", r"fran[cç]ais", r"franstalig"],
        "english_language": [r"\bengels\b", r"\benglish\b", r"engelstalig"],
    }

    skills = {}
    for skill_key, patterns in skill_patterns.items():
        found = False
        for pat in patterns:
            try:
                if re.search(pat, t, flags=re.IGNORECASE):
                    found = True
                    break
            except re.error:
                # fallback to substring check when regex invalid
                if pat.lower() in t:
                    found = True
                    break
        skills[skill_key] = "Yes" if found else "No"

    return skills


def extract_contract_type(text: str) -> str:
    """Determine whether the job contract is permanent or time-specific.

    Returns one of: 'permanent', 'time-specific', or 'Not specified'.
    Uses common Dutch phrases found on Belgian job ads.
    """
    if not text:
        return "Not specified"

    t = text.lower()

    # Patterns indicating permanent / indefinite contract
    permanent_patterns = [
        r"vast contract",
        r"onbepaalde tijd",
        r"contract van onbepaalde duur",
        r"vast dienstverband",
        r"permanent",
    ]

    # Patterns indicating fixed-term / temporary / other time-specific contracts
    temporary_patterns = [
        r"tijdelijk",
        r"bepaalde tijd",
        r"contract van bepaalde duur",
        r"uitzend",
        r"interim",
        r"stage",
        r"mvv?",
    ]

    for pat in permanent_patterns:
        if re.search(pat, t):
            return "permanent"

    for pat in temporary_patterns:
        if re.search(pat, t):
            return "time-specific"

    return "Not specified"


def extract_posted_on(soup: BeautifulSoup, text: str) -> str:
    """Try to find a posted/publish date on the job page and return as dd-mm-yyyy.

    The function looks for common labels like 'geplaatst op', 'geplaatst', 'published', or time elements.
    If no date is found, returns empty string.
    """
    # look for time elements
    try:
        # common date selectors
        candidates = []
        for sel in ['time', '.posted', '.date', '[data-published]']:
            for el in soup.select(sel):
                txt = (el.get('datetime') or el.get_text() or '').strip()
                if txt:
                    candidates.append(txt)

        # also try phrase-based search in visible text
        m = re.search(r'(?:geplaatst op|geplaatst|published on|published|datum|online sinds|gewijzigd sinds)[:\s]+([0-9]{1,2}[-/.][0-9]{1,2}[-/.][0-9]{2,4})', text, flags=re.IGNORECASE)
        if m:
            d = m.group(1)
            try:
                dt = datetime.strptime(d.replace('.', '-').replace('/', '-'), '%d-%m-%Y')
            except Exception:
                try:
                    dt = datetime.strptime(d.replace('.', '-').replace('/', '-'), '%d-%m-%y')
                except Exception:
                    dt = None
            if dt:
                return dt.strftime('%d-%m-%Y')

        # try parse candidates with dateutil-like heuristics (basic)
        for c in candidates:
            try:
                # normalize
                val = c.strip()
                # some datetimes include time; try ISO parse
                try:
                    dt = datetime.fromisoformat(val)
                except Exception:
                    # fallback: extract date-like pattern
                    mm = re.search(r'([0-9]{4}-[0-9]{2}-[0-9]{2})', val)
                    if mm:
                        dt = datetime.fromisoformat(mm.group(1))
                    else:
                        # try dd-mm-yyyy
                        mm2 = re.search(r'([0-9]{1,2}[-/.][0-9]{1,2}[-/.][0-9]{2,4})', val)
                        if mm2:
                            try:
                                dt = datetime.strptime(mm2.group(1).replace('.', '-').replace('/', '-'), '%d-%m-%Y')
                            except Exception:
                                try:
                                    dt = datetime.strptime(mm2.group(1).replace('.', '-').replace('/', '-'), '%d-%m-%y')
                                except Exception:
                                    dt = None
                        else:
                            dt = None

                if dt:
                    return dt.strftime('%d-%m-%Y')
            except Exception:
                continue
    except Exception:
        pass
    return ""


def extract_sections(soup: BeautifulSoup, text: str) -> Dict[str, str]:
    """Try to split the job page into sections: functieomschrijving, profiel, professionele_vaardigheden, aanbod.

    Heuristic: look for headings with keywords and gather following sibling text until next heading.
    Returns a dict with empty string defaults.
    """
    keys = {
        'functieomschrijving': ['functieomschrijving', 'beschrijving', 'taakomschrijving', 'job description', 'functie'],
        'profiel': ['profiel', 'jouw profiel', 'jouw vaardigheden', 'wie ben jij'],
        'professionele_vaardigheden': ['vaardigheden', 'competenties', 'skills'],
        'anbod': ['aanbod', 'wat wij aanbieden', 'wij bieden', 'aanbieding', 'wat we bieden']
    }
    out = {k: '' for k in keys}

    try:
        # convert soup to a list of block elements
        for header in soup.find_all(re.compile('^h[1-6]$')):
            hdr = header.get_text(strip=True).lower()
            for k, kws in keys.items():
                if any(kw in hdr for kw in kws):
                    # gather siblings until next header
                    parts = []
                    for sib in header.find_next_siblings():
                        if sib.name and re.match('^h[1-6]$', sib.name, flags=re.IGNORECASE):
                            break
                        txt = sib.get_text(' ', strip=True)
                        if txt:
                            parts.append(txt)
                    if parts:
                        out[k] = ' '.join(parts)

        # fallback: simple phrase splitting from the full text using markers
        if not out['functieomschrijving']:
            m = re.split(r'(?:profiel:|functie:|beschrijving:)', text, flags=re.IGNORECASE)
            if m:
                out['functieomschrijving'] = m[0][:2000].strip()
        return out
    except Exception:
        return out


def extract_jsonld_job(soup: BeautifulSoup) -> Dict[str, str]:
    """Return fields extracted from JobPosting JSON-LD when present.

    Returns dict possibly containing: title, description, hiringOrganization, addressLocality, datePosted
    """
    out = {}
    try:
        for script in soup.select('script[type="application/ld+json"]'):
            raw = script.string or script.get_text() or ''
            try:
                data = json.loads(raw)
            except Exception:
                # some pages put multiple JSON objects without array; attempt to fix
                try:
                    data = json.loads('[' + raw.replace('}\n{', '},{') + ']')
                except Exception:
                    continue

            items = data if isinstance(data, list) else [data]
            for it in items:
                if not isinstance(it, dict):
                    continue
                # JobPosting at top-level or under mainEntity
                typ = it.get('@type') or it.get('type') or ''
                if isinstance(typ, list):
                    typ = typ[0] if typ else ''
                if typ and 'JobPosting' in str(typ):
                    # title
                    title = it.get('title') or it.get('name')
                    if title:
                        out['title'] = str(title).strip()
                    # description (may contain html)
                    desc = it.get('description')
                    if desc:
                        # strip simple html tags
                        out['description'] = re.sub(r'<[^>]+>', ' ', str(desc)).strip()
                    # hiringOrganization
                    ho = it.get('hiringOrganization') or it.get('hiring_org')
                    if isinstance(ho, dict):
                        out['company'] = ho.get('name')
                    elif isinstance(ho, str):
                        out['company'] = ho
                    # jobLocation
                    jl = it.get('jobLocation') or it.get('jobLocationType')
                    if isinstance(jl, list):
                        jl = jl[0]
                    if isinstance(jl, dict):
                        addr = jl.get('address') or {}
                        if isinstance(addr, dict):
                            out['city'] = addr.get('addressLocality') or addr.get('addressRegion')
                    # datePosted
                    dp = it.get('datePosted') or it.get('date')
                    if dp:
                        out['posted_on'] = str(dp).strip()
                    return out
    except Exception:
        pass
    return out


def extract_personal_skills(text: str, soup: BeautifulSoup) -> List[str]:
    """Extract 'persoonlijke vaardigheden' from page using heading heuristics and fallbacks.

    Returns a list of skills (strings)."""
    skills: List[str] = []
    try:
        heading_phrases = [
            'persoonlijke vaardigheden', 'persoonlijk profiel', 'persoonlijke competenties',
            'vaardigheden', 'competenties', 'soft skills', 'persoonlijke skills'
        ]
        if soup is not None:
            for h in soup.find_all(re.compile(r'^h[1-6]$')):
                hdr = (h.get_text(separator=' ', strip=True) or '').lower()
                if any(phrase in hdr for phrase in heading_phrases):
                    # gather following siblings until next header
                    collected: List[str] = []
                    nxt = h.find_next_sibling()
                    while nxt and (not re.match(r'^h[1-6]$', getattr(nxt, 'name', ''), re.I)):
                        if nxt.name in ('ul', 'ol'):
                            for li in nxt.find_all('li'):
                                t = li.get_text(' ', strip=True)
                                if t:
                                    collected.append(t)
                        elif nxt.name == 'p':
                            t = nxt.get_text('\n', strip=True)
                            if t:
                                for line in re.split(r'[\n\u2022\-–—]+', t):
                                    line = line.strip()
                                    if line:
                                        collected.append(line)
                        else:
                            t = nxt.get_text(' ', strip=True)
                            if t:
                                collected.append(t)
                        nxt = nxt.find_next_sibling()
                    # clean collected
                    for chunk in collected:
                        for part in re.split(r'[;,\n]+', chunk):
                            s = part.strip()
                            if not s:
                                continue
                            s = re.sub(r'^[\d\)\.\-\s]+', '', s)
                            if len(s) > 1 and s not in skills:
                                skills.append(s)
                    if skills:
                        return skills

        # fallback: scan text for common tokens
        if text:
            lower = text.lower()
            tokens = [
                'communiceren', 'zorgvuldigheid', 'digitaal denken', 'verantwoordelijkheid',
                'resultaatgerichtheid', 'initiatief', 'analyseren', 'zelfontwikkeling',
                'klantgerichtheid', 'zelfstandigheid', 'stressbestendigheid', 'betrouwbaarheid',
                'inleving', 'flexibiliteit', 'creativiteit', 'samenwerken', 'kritisch denken',
                'plannen en organiseren'
            ]
            for tok in tokens:
                if tok in lower and tok not in skills:
                    skills.append(tok)
    except Exception:
        pass
    return skills


def find_content_container(soup: BeautifulSoup) -> Optional[BeautifulSoup]:
    """Attempt to find the most likely job-description container element.

    Heuristics:
    - element with itemprop=description
    - article tag
    - main tag
    - nearest ancestor of h1 that contains multiple <p> children
    - a div with many <p> children
    Returns None when not found.
    """
    # prefer explicit description itemprop
    sel = soup.select_one('[itemprop="description"], [itemprop="jobDescription"]')
    if sel:
        return sel

    sel = soup.select_one('article')
    if sel:
        return sel

    sel = soup.select_one('main')
    if sel:
        return sel

    # nearest ancestor of the first h1 that contains paragraphs
    h1 = soup.find('h1')
    if h1:
        parent = h1.parent
        depth = 0
        while parent and depth < 6:
            p_count = len(parent.find_all('p'))
            if p_count >= 2:
                return parent
            parent = parent.parent
            depth += 1

    # fallback: div with many paragraphs
    candidates = sorted(soup.find_all('div'), key=lambda d: len(d.find_all('p')), reverse=True)
    if candidates and len(candidates[0].find_all('p')) >= 2:
        return candidates[0]

    return None


def clean_text_field(txt: Optional[str]) -> str:
    """Clean common site-chrome and placeholders from short text fields (title/company/city)."""
    if not txt:
        return ""
    s = re.sub(r"\s+", " ", txt).strip()
    # Remove obvious placeholders
    blacklist_tokens = ['ingelogd', 'ingelogd als', 'gebruikersnaam', 'opleidingen', 'vind een job', 'inloggen', 'inschrijven']
    low = s.lower()
    for tok in blacklist_tokens:
        if tok in low:
            return ""
    # trim site name suffixes like ' - VDAB' or '| VDAB'
    s = re.sub(r"\s+[-|]\s*vdab.*$", '', s, flags=re.IGNORECASE)
    # remove leading UI words
    s = re.sub(r'^(menu:|menu\s+-)\s*', '', s, flags=re.IGNORECASE)
    return s.strip()


def title_from_url(url: str) -> str:
    """Create a human-friendly title from the URL slug as a last-resort fallback."""
    try:
        path = urlparse(url).path or ''
        parts = [p for p in path.split('/') if p]
        if not parts:
            return ''
        slug = parts[-1]
        # remove numeric ids
        slug = re.sub(r"\d+", '', slug)
        # replace separators and clean
        t = re.sub(r'[-_]+', ' ', slug).strip()
        # remove common tokens like 'vacatures' or 'vacature'
        t = re.sub(r"\b(vacatures|vacature|vindeenjob)\b", '', t, flags=re.IGNORECASE).strip()
        # Title-case the result
        if t:
            return ' '.join([w.capitalize() for w in t.split()])
    except Exception:
        pass
    return ''


# Small list of Belgian cities/municipalities for heuristic matching (not exhaustive)
def extract_city_from_text(text: str, soup: Optional[BeautifulSoup] = None) -> str:
    """Extract a likely city/locality from page text or HTML.

    Strategy (in order):
    1. If a BeautifulSoup `soup` is provided, look for elements/classes that often
       contain location/locality info (class names containing 'location', 'localit', 'gemeente', 'stad').
    2. Look for explicit phrases in the raw text like 'in Brussel', 'te Gent', 'voor een job in <City>'.
    3. Use spaCy NER (if available) and pick the first GPE/LOC entity.
    4. Return empty string if nothing found.
    """
    # 1) HTML-based selectors and structured data
    if soup is not None:
        # 1a) Look for JSON-LD structured data (JobPosting.jobLocation.address.addressLocality)
        try:
            for script in soup.select('script[type="application/ld+json"]'):
                try:
                    data = json.loads(script.string or script.get_text())
                except Exception:
                    continue
                # data may be a list or dict
                items = data if isinstance(data, list) else [data]
                for it in items:
                    # Navigate common JobPosting shapes
                    jobloc = None
                    if isinstance(it, dict):
                        # direct jobLocation
                        jobloc = it.get('jobLocation') or it.get('jobLocationType') or None
                        # some pages nest under 'mainEntity'
                        if not jobloc and it.get('mainEntity') and isinstance(it.get('mainEntity'), dict):
                            jobloc = it['mainEntity'].get('jobLocation')
                    if jobloc:
                        # jobloc could be dict or list
                        jl = jobloc[0] if isinstance(jobloc, list) else jobloc
                        # address may be present
                        addr = jl.get('address') if isinstance(jl, dict) else None
                        if isinstance(addr, dict):
                            locality = addr.get('addressLocality') or addr.get('address_region') or addr.get('addressLocality')
                            if locality:
                                return str(locality).strip()

        except Exception:
            # ignore JSON-LD parsing issues
            pass

        # 1b) Fallback: look for common selectors / data attributes
        selectors = ['.job-location', '.location', '[class*="location"]', '.vdab-localities', '[class*="localit"]', '[class*="gemeente"]', '[class*="stad"]', '[data-locality]', '[data-city]']
        for sel in selectors:
            el = soup.select_one(sel)
            if el:
                txt = el.get_text(strip=True)
                if txt and 'vdab' not in txt.lower():
                    return txt
        # also check data attributes on other elements
        for attr in ('data-locality', 'data-city', 'data-location'):
            el = soup.select_one(f'[{attr}]')
            if el:
                val = el.get(attr)
                if val:
                    return val.strip()

    if not text:
        return ""

    # 2) Phrase-based patterns (Dutch/Belgian style)
    # Examples: 'in Brussel', 'te Gent', 'voor een job in Brussel', 'locatie: Brussel'
    phrase_patterns = [r"\b(?:in|te)\s+([A-ZÅÄÖÁÉÍÓÚËÊÈ][\w'\-\s]{1,60}?)\b",
                       r"voor een job in\s+([A-Z][\w'\-\s]{1,60}?)\b",
                       r"locatie[:\s]+([A-Z][\w'\-\s]{1,60}?)\b",
                       r"gemeente[:\s]+([A-Z][\w'\-\s]{1,60}?)\b"]
    for pat in phrase_patterns:
        m = re.search(pat, text)
        if m:
            candidate = m.group(1).strip().rstrip('.,')
            if candidate:
                return candidate

    # 3) spaCy NER fallback
    if nlp is not None:
        try:
            doc = nlp(text)
            for ent in doc.ents:
                if ent.label_ in ("LOC", "GPE"):
                    cand = ent.text.strip()
                    # simple filter: avoid very short tokens like 'EU' and avoid company-like tokens
                    if len(cand) >= 3 and not any(ch.isdigit() for ch in cand):
                        return cand
        except Exception:
            # If spaCy fails for any reason, just continue
            pass

    return ""

def validate_job_data(job: Dict) -> bool:
    """Validate that job data has required fields.

    Relaxed rules: title is required. If company is missing we assign a default.
    Domain may be filled later by the caller (scrape_domain) so we allow 'unknown'.
    """
    # Title is essential
    if not job.get('title'):
        logger.warning("Missing required field 'title' in job data")
        return False

    # Provide sensible defaults instead of rejecting the job
    if not job.get('company'):
        job['company'] = 'Unknown'

    # Allow domain to be unknown here; caller (scrape_domain) will fill it when possible
    return True

# --- Async Scraper ---
class VdabScraper:
    def __init__(self, config: Config):
        self.config = config
        self.results = []
    
    async def random_delay(self):
        """Add random delay between requests."""
        # In FAST_MODE we minimize artificial delays
        if getattr(self.config, 'FAST_MODE', False):
            # minimal jitter in FAST_MODE
            await asyncio.sleep(0.005)
            return
        # QUICK_MODE reduces delays for local/testing runs
        if getattr(self.config, 'QUICK_MODE', False):
            # pick a tiny random delay up to half the configured max, but no smaller than 20ms
            delay = max(0.02, random.uniform(0, max(0.5, self.config.REQUEST_DELAY[1] / 2)))
        else:
            delay = random.uniform(*self.config.REQUEST_DELAY)
        logger.debug(f"Waiting {delay:.2f} seconds...")
        await asyncio.sleep(delay)
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def scrape_job_page(self, page, url: str, job_id: str) -> Optional[Dict]:
        """Scrape individual job page with retry logic."""
        try:
            # Use domcontentloaded to avoid waiting for all network activity (more robust)
            await page.goto(url, wait_until="domcontentloaded", timeout=self.config.PAGE_TIMEOUT_MS)
            # Set default navigation timeout on the page/context to ensure subsequent waits use the same timeout
            try:
                page.set_default_navigation_timeout(self.config.PAGE_TIMEOUT_MS)
            except Exception:
                pass

            # Wait for a likely selector (title or job description) instead of full networkidle
            # In fast-mode we use a shorter selector timeout to avoid waiting too long
            selector_timeout = int(self.config.PAGE_TIMEOUT_MS if not getattr(self.config, 'FAST_MODE', False) else min(self.config.PAGE_TIMEOUT_MS, 3000))
            try:
                await page.wait_for_selector('h1, .job-title, .vdab-company', timeout=selector_timeout)
            except Exception:
                # selector not found within timeout; continue and attempt to extract whatever is available
                logger.debug(f"Selector wait timed out for {url}; continuing with available content")

            await self.random_delay()
            
            job_html = await page.content()
            job_soup = BeautifulSoup(job_html, 'lxml')

            # Prefer structured data when available
            jsonld = extract_jsonld_job(job_soup)
            raw_title = jsonld.get('title') or self.extract_title(job_soup, url) or title_from_url(url)
            logger.info(f"Raw title candidate for {url}: '{raw_title}'")
            logger.info(f"JSON-LD extracted for {url}: {jsonld}")
            title = clean_text_field(raw_title)
            company = clean_text_field(jsonld.get('company') or self.extract_text(job_soup, ['.vdab-company', '.job-company', '[class*="company"]', 'strong']))
            city = clean_text_field(jsonld.get('city') or self.extract_text(job_soup, ['.job-location', '.location', '[class*="location"]']))

            logger.info(f"Extracted fields for {url}: title='{title}' company='{company}' city='{city}'")

            # description: prefer JSON-LD description, else try to find a content container
            if jsonld.get('description'):
                desc_text = jsonld.get('description')
            else:
                cont = find_content_container(job_soup)
                if cont is not None:
                    desc_text = cont.get_text(' ', strip=True)
                else:
                    # last-resort: limited-length full-text to avoid menu/footer noise
                    desc_text = ' '.join(job_soup.get_text(' ', strip=True).split()[:3000])

            # Quick validation: skip pages that don't look like real vacancy pages
            if not self.is_likely_vacancy(job_soup, job_html, url, title):
                logger.debug(f"Rejected non-vacancy page: {url} (title='{title}')")
                return None

            # parse posted date and sections
            posted_on = extract_posted_on(job_soup, desc_text)
            sections = extract_sections(job_soup, desc_text)

            # Compute features from combined text (full description + obvious sections)
            combined_text = ' '.join(filter(None, [desc_text, sections.get('profiel', ''), sections.get('anbod', ''), sections.get('functieomschrijving', '')]))
            feats = extract_features(combined_text)
            try:
                aanbod_text = sections.get('anbod', '') if isinstance(sections, dict) else ''
                if aanbod_text:
                    salary_from_anbod = extract_salary(aanbod_text)
                    if salary_from_anbod and salary_from_anbod != 'Not specified':
                        feats['salary'] = salary_from_anbod
            except Exception:
                # keep original feats if anything goes wrong
                pass

            job = {
                "job_id": job_id,
                "title": title,
                "company": company,
                "city": city,
                "contract_type": extract_contract_type(desc_text),
                "posted_on": posted_on,
                "detail_url": url,
                "domain": url.split("/jobs/")[-1].split("/")[0] if "/jobs/" in url else "unknown",
                "scraped_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "functieomschrijving": sections.get('functieomschrijving', ''),
                "profiel": sections.get('profiel', ''),
                "professionele_vaardigheden": sections.get('professionele_vaardigheden', ''),
                "persoonlijke_vaardigheden": extract_personal_skills(combined_text, job_soup),
                "anbod": sections.get('anbod', ''),
                "full_description": desc_text,
                **feats,
            }

            # Heuristic: try to extract a Belgian city from the full job text when the
            # explicit city selector is empty or contains a placeholder like 'VDAB-localities'
            if (not job.get('city')) or (job.get('city') and 'vdab' in job.get('city').lower()):
                found_city = extract_city_from_text(desc_text, soup=job_soup)
                if found_city:
                    job['city'] = found_city
            
            if validate_job_data(job):
                return job
            else:
                logger.warning(f"Invalid job data for {url}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to scrape job page {url}: {e}")
            raise  # Re-raise for retry mechanism

    async def scrape_job_html(self, html: str, url: str, job_id: str) -> Optional[Dict]:
        """Parse job HTML (already fetched via HTTP request) and return job dict.

        This mirrors the extraction behavior of scrape_job_page but avoids using a
        full Playwright Page, making it faster for large-scale scraping when JS
        execution is not strictly required for the fields we extract.
        """
        try:
            # Fast parsing: prefer selectolax if configured and available
            if getattr(self.config, 'USE_SELECTOLAX', False) and SELECTOLAX_AVAILABLE:
                try:
                    doc = SelectolaxParser(html)
                    # title extraction via CSS-like searches
                    title_node = doc.css_first('h1') or doc.css_first('.job-title') or doc.css_first('[itemprop="title"]')
                    title = title_node.text(deep=False).strip() if title_node is not None else ''
                    # company / city heuristics (best-effort)
                    comp_node = doc.css_first('.vdab-company') or doc.css_first('.job-company')
                    company = comp_node.text().strip() if comp_node is not None else ''
                    city_node = doc.css_first('.job-location') or doc.css_first('.location')
                    city = city_node.text().strip() if city_node is not None else ''
                    # build a BeautifulSoup for container heuristics
                    job_soup = BeautifulSoup(html, 'lxml')
                    jsonld = extract_jsonld_job(job_soup)
                    title = clean_text_field(jsonld.get('title') or title or title_from_url(url))
                    company = clean_text_field(jsonld.get('company') or company)
                    city = clean_text_field(jsonld.get('city') or city)
                    if jsonld.get('description'):
                        desc_text = jsonld.get('description')
                    else:
                        cont = find_content_container(job_soup)
                        desc_text = cont.get_text(' ', strip=True) if cont is not None else ' '.join(job_soup.get_text(' ', strip=True).split()[:3000])
                except Exception:
                    job_soup = BeautifulSoup(html, 'lxml')
                    jsonld = extract_jsonld_job(job_soup)
                    title = clean_text_field(jsonld.get('title') or self.extract_title(job_soup, url) or title_from_url(url))
                    company = clean_text_field(jsonld.get('company') or self.extract_text(job_soup, ['.vdab-company', '.job-company', '[class*="company"]', 'strong']))
                    city = clean_text_field(jsonld.get('city') or self.extract_text(job_soup, ['.job-location', '.location', '[class*="location"]']))
                    if jsonld.get('description'):
                        desc_text = jsonld.get('description')
                    else:
                        cont = find_content_container(job_soup)
                        if cont is not None:
                            desc_text = cont.get_text(' ', strip=True)
                        else:
                            desc_text = ' '.join(job_soup.get_text(' ', strip=True).split()[:3000])

                logger.info(f"[html-parse] Extracted fields for {url}: title='{title}' company='{company}' city='{city}'")
            else:
                job_soup = BeautifulSoup(html, 'lxml')
                jsonld = extract_jsonld_job(job_soup)
                title = clean_text_field(jsonld.get('title') or self.extract_title(job_soup, url))
                company = clean_text_field(jsonld.get('company') or self.extract_text(job_soup, ['.vdab-company', '.job-company', '[class*="company"]', 'strong']))
                city = clean_text_field(jsonld.get('city') or self.extract_text(job_soup, ['.job-location', '.location', '[class*="location"]']))
                if jsonld.get('description'):
                    desc_text = jsonld.get('description')
                else:
                    cont = find_content_container(job_soup)
                    if cont is not None:
                        desc_text = cont.get_text(' ', strip=True)
                    else:
                        desc_text = ' '.join(job_soup.get_text(' ', strip=True).split()[:3000])

            # JSON-LD fallback (same as page path)
            if (not title) or (not company) or (not desc_text):
                try:
                    for script in job_soup.select('script[type="application/ld+json"]'):
                        try:
                            data = json.loads(script.string or script.get_text())
                        except Exception:
                            continue
                        items = data if isinstance(data, list) else [data]
                        for it in items:
                            if not isinstance(it, dict):
                                continue
                            typ = (it.get('@type') or '').lower()
                            if typ == 'jobposting' or any(k in it for k in ('jobLocation', 'hiringOrganization', 'title')):
                                if not title and it.get('title'):
                                    title = it.get('title')
                                if not company:
                                    hiring = it.get('hiringOrganization') or {}
                                    if isinstance(hiring, dict):
                                        comp = hiring.get('name') or hiring.get('companyName')
                                        if comp:
                                            company = comp
                                if (not desc_text or desc_text.strip() == '') and it.get('description'):
                                    desc_text = BeautifulSoup(it.get('description'), 'lxml').get_text(" ", strip=True)
                                if title and company and desc_text:
                                    break
                        if title and company and desc_text:
                            break
                except Exception:
                    pass

            posted_on = extract_posted_on(job_soup, desc_text)
            sections = extract_sections(job_soup, desc_text)

            combined_text = ' '.join(filter(None, [desc_text, sections.get('profiel', ''), sections.get('anbod', ''), sections.get('functieomschrijving', '')]))
            feats = extract_features(combined_text)
            try:
                aanbod_text = sections.get('anbod', '') if isinstance(sections, dict) else ''
                if aanbod_text:
                    salary_from_anbod = extract_salary(aanbod_text)
                    if salary_from_anbod and salary_from_anbod != 'Not specified':
                        feats['salary'] = salary_from_anbod
            except Exception:
                pass

            job = {
                "job_id": job_id,
                "title": title,
                "company": company,
                "city": city,
                "contract_type": extract_contract_type(desc_text),
                "posted_on": posted_on,
                "detail_url": url,
                "domain": url.split("/jobs/")[-1].split("/")[0] if "/jobs/" in url else "unknown",
                "scraped_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "functieomschrijving": sections.get('functieomschrijving', ''),
                "profiel": sections.get('profiel', ''),
                "professionele_vaardigheden": sections.get('professionele_vaardigheden', ''),
                "persoonlijke_vaardigheden": extract_personal_skills(combined_text, job_soup),
                "anbod": sections.get('anbod', ''),
                "full_description": desc_text,
                **feats,
            }

            logger.info(f"[scrape_job_html] Extracted fields for {url}: title='{title}' company='{company}' city='{city}' jsonld={jsonld}")

            if (not job.get('city')) or (job.get('city') and 'vdab' in job.get('city').lower()):
                found_city = extract_city_from_text(desc_text, soup=job_soup)
                if found_city:
                    job['city'] = found_city

            if validate_job_data(job):
                return job
            else:
                logger.warning(f"Invalid job data for {url}")
                return None
        except Exception as e:
            logger.debug(f"Failed to parse job HTML for {url}: {e}")
            return None
    
    def extract_text(self, soup: BeautifulSoup, selectors: List[str]) -> str:
        """Extract text using multiple possible selectors."""
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                text = element.get_text(strip=True)
                if text:
                    return clean_text_field(text)
        return ""

    def extract_title(self, soup: BeautifulSoup, url: str) -> str:
        """Extract a job title using multiple heuristics and prefer non-generic values.

        Order:
        1. JSON-LD JobPosting.title
        2. meta property og:title / twitter:title / meta[name=title]
        3. H1 candidates that are not generic site titles
        4. Other selectors (.vacature, .job-title, [itemprop=title], .vacancy__title)
        5. Fallback to <title> tag, but filter out generic values like 'Vind een job'
        """
        # 1) JSON-LD JobPosting
        try:
            for script in soup.select('script[type="application/ld+json"]'):
                try:
                    data = json.loads(script.string or script.get_text())
                except Exception:
                    continue
                items = data if isinstance(data, list) else [data]
                for it in items:
                    if isinstance(it, dict):
                        typ = (it.get('@type') or '').lower()
                        if typ == 'jobposting' or any(k in it for k in ('jobLocation', 'hiringOrganization', 'title')):
                            t = it.get('title')
                            if t:
                                t = BeautifulSoup(t, 'lxml').get_text(' ', strip=True)
                                if t:
                                    return t
        except Exception:
            pass

        # 2) Meta tags
        meta_selectors = [
            'meta[property="og:title"]', 'meta[name="twitter:title"]', 'meta[name="title"]', 'meta[property="twitter:title"]'
        ]
        for sel in meta_selectors:
            m = soup.select_one(sel)
            if m:
                val = m.get('content') or m.get('value') or ''
                if val:
                    val = val.strip()
                    if not self._is_generic_title(val):
                        return val

        # 3) h1 candidates
        generic_blacklist = [
            'vind een job', 'vind een opleiding', 'vacatures - vdab', 'vacatures', 'jobs', 'home'
        ]
        for h in soup.find_all(re.compile('^h[1-3]$')):
            txt = (h.get_text(' ', strip=True) or '').strip()
            if not txt:
                continue
            low = txt.lower()
            if any(g in low for g in generic_blacklist):
                continue
            # sanity: title length reasonable
            if 3 <= len(txt) <= 200:
                return txt

        # 4) other selectors
        other_selectors = ['[itemprop="title"]', '.vacature__title', '.vacancy__title', '.job-title', '.vacature', '.vacancy', '[class*="title"]']
        for sel in other_selectors:
            el = soup.select_one(sel)
            if el:
                txt = el.get_text(' ', strip=True)
                if txt and not self._is_generic_title(txt):
                    return txt

        # 5) fallback to <title> tag, but filter generic site chrome
        ttag = soup.title.string if soup.title and soup.title.string else ''
        if ttag:
            ttag = ttag.strip()
            if not self._is_generic_title(ttag):
                return ttag

        # nothing meaningful found
        return ""

    def _is_generic_title(self, txt: str) -> bool:
        if not txt:
            return True
        low = txt.lower()
        generic_tokens = ['vind een job', 'vind een opleiding', 'vacatures', 'vdab', 'jobs', 'home', 'zoek']
        # also detect titles that are just site name or too short
        if any(tok in low for tok in generic_tokens):
            return True
        if len(txt) < 3:
            return True
        # if title contains many nav words (social links etc.) consider generic
        nav_indicators = ['facebook', 'twitter', 'linkedin', 'instagram', 'menu', 'zoeken']
        nav_count = sum(1 for ni in nav_indicators if ni in low)
        if nav_count >= 2:
            return True
        return False

    def is_likely_vacancy(self, soup: BeautifulSoup, html: str, url: str, title: str) -> bool:
        """Return True when the page looks like a real vacancy page.

        Heuristics (conservative):
        - title must exist and not be generic (uses _is_generic_title)
        - Prefer pages that include JSON-LD JobPosting or identifiable vacancy metadata
        - Accept pages that include clear job-related signals like 'solliciteer',
          'functieomschrijving', 'referentienummer' or 'VDAB-vacaturenummer'
        - Otherwise reject to avoid capturing landing/search pages (e.g. 'Opleidingen')
        """
        try:
            if not title or self._is_generic_title(title):
                return False

            # Check for JSON-LD JobPosting or structured job metadata
            try:
                for script in soup.select('script[type="application/ld+json"]'):
                    try:
                        data = json.loads(script.string or script.get_text())
                    except Exception:
                        continue
                    items = data if isinstance(data, list) else [data]
                    for it in items:
                        if isinstance(it, dict):
                            typ = (it.get('@type') or '').lower()
                            if 'jobposting' in typ or typ == 'jobposting':
                                return True
                            # presence of identifier/hiringOrganization/jobLocation is a strong signal
                            if any(k in it for k in ('identifier', 'hiringOrganization', 'jobLocation')):
                                return True
            except Exception:
                pass

            # Look for explicit VDAB vacancy identifiers or reference numbers in the HTML
            if re.search(r"vdab[-\s]?vacaturenummer|vdab[-\s]?vacaturenummer|referentie[:\s]", html, flags=re.IGNORECASE):
                return True

            # Look for common job-page CTAs or sections
            if re.search(r"\b(solliciteer|solliciteer nu|solliciteren|hoe solliciteer|vacature|vacaturenummer|functieomschrijving|profiel|plaats tewerkstelling)\b", html, flags=re.IGNORECASE):
                return True

        except Exception:
            # Any unexpected parsing issue -> be conservative and reject
            return False

        return False
    
    async def get_domains(self, page) -> List[str]:
        """Extract available job domains from the base page."""
        try:
            await page.goto(self.config.BASE_URL, wait_until="domcontentloaded", timeout=self.config.TIMEOUT)
            await self.random_delay()
            
            html = await page.content()
            soup = BeautifulSoup(html, 'lxml')
            
            domains = []
            # Try a few heuristics to find domain links (site structure may vary)
            # 1) anchors with obvious jobs path
            for a in soup.find_all('a', href=True):
                href = a.get('href', '')
                if not href:
                    continue
                # normalize absolute-path links against site root
                if href.startswith('/'):
                    full = urljoin(SITE_ROOT, href)
                else:
                    full = urljoin(self.config.BASE_URL + '/', href) if not href.startswith('http') else href

                domain = ''
                if '/vindeenjob/jobs/' in full:
                    domain = full.split('/vindeenjob/jobs/')[-1].split('/')[0]
                elif '/jobs/' in full and '/vindeenjob' not in full:
                    # accept either '/jobs/<domain>' as well
                    domain = full.split('/jobs/')[-1].split('/')[0]
                elif '/vacature/' in full or '/vacatures/' in full:
                    # some pages link directly to vacancy detail or nested paths; try to infer domain
                    # look for a segment earlier in the path that matches known domain keys
                    parts = [p for p in urlparse(full).path.split('/') if p]
                    # scan parts for any known domain key
                    for p in parts:
                        if p in DOMAIN_CODE_MAP:
                            domain = p
                            break
                    # fallback: take the last meaningful token if nothing else
                    if not domain and parts:
                        # try to find a token that looks like a domain (no digits, short)
                        for p in reversed(parts):
                            if not re.search(r"\d", p) and len(p) > 1 and not p.startswith('vacature'):
                                domain = p
                                break

                if domain:
                    domain = domain.strip().strip('/')
                    if domain and domain not in domains:
                        domains.append(domain)

            # 2) selects/options: sometimes the domains are rendered in a drop-down
            for sel in soup.find_all('select'):
                for opt in sel.find_all('option'):
                    val = (opt.get('value') or '').strip()
                    txt = (opt.get_text() or '').strip()
                    cand = ''
                    if val and ('/vindeenjob/jobs/' in val or '/jobs/' in val):
                        full = urljoin(self.config.BASE_URL + '/', val) if not val.startswith('http') else val
                        if '/vindeenjob/jobs/' in full:
                            cand = full.split('/vindeenjob/jobs/')[-1].split('/')[0]
                        elif '/jobs/' in full:
                            cand = full.split('/jobs/')[-1].split('/')[0]
                    # sometimes option text contains the domain key
                    if not cand and txt and txt.lower() in DOMAIN_CODE_MAP:
                        cand = txt.lower()
                    if cand:
                        cand = cand.strip()
                        if cand not in domains:
                            domains.append(cand)
            
            logger.info(f"Found {len(domains)} unique domains")
            logger.debug(f"Sample hrefs on base page: {[a.get('href') for a in soup.find_all('a', href=True)[:10]]}")
            if not domains:
                # Fallback: use known domain keys (will be slower but keeps scraper running)
                logger.warning("No domains discovered on the base page — falling back to known DOMAIN_CODE_MAP keys")
                domains = list(DOMAIN_CODE_MAP.keys())
            return sorted(domains)
            
        except Exception as e:
            logger.error(f"Failed to extract domains: {e}")
            return []

    async def get_domains_aiohttp(self, session: 'aiohttp.ClientSession') -> List[str]:
        """Fetch domain list using aiohttp (fast path)."""
        try:
            # BASE_URL already points to the jobs root (e.g. '.../vindeenjob/jobs')
            url = self.config.BASE_URL
            async with session.get(url) as r:
                if r.status != 200:
                    logger.warning(f"Domain list request returned {r.status}")
                    return []
                html = await r.text()
            soup = BeautifulSoup(html, 'lxml')
            domains = []
            # anchors
            for a in soup.select('a'):
                href = a.get('href', '')
                if not href:
                    continue
                full = urljoin(self.config.BASE_URL + '/', href) if not href.startswith('http') else href
                domain = ''
                if '/vindeenjob/jobs/' in full:
                    domain = full.split('/vindeenjob/jobs/')[-1].split('/')[0]
                elif '/jobs/' in full and '/vindeenjob' not in full:
                    domain = full.split('/jobs/')[-1].split('/')[0]
                elif '/vacature/' in full or '/vacatures/' in full:
                    parts = [p for p in urlparse(full).path.split('/') if p]
                    for p in parts:
                        if p in DOMAIN_CODE_MAP:
                            domain = p
                            break
                    if not domain and parts:
                        for p in reversed(parts):
                            if not re.search(r"\d", p) and len(p) > 1 and not p.startswith('vacature'):
                                domain = p
                                break
                if domain:
                    domain = domain.strip().strip('/')
                    if domain and domain not in domains:
                        domains.append(domain)
            # selects/options fallback
            for sel in soup.find_all('select'):
                for opt in sel.find_all('option'):
                    val = (opt.get('value') or '').strip()
                    txt = (opt.get_text() or '').strip()
                    cand = ''
                    if val and ('/vindeenjob/jobs/' in val or '/jobs/' in val):
                        full = urljoin(self.config.BASE_URL + '/', val) if not val.startswith('http') else val
                        if '/vindeenjob/jobs/' in full:
                            cand = full.split('/vindeenjob/jobs/')[-1].split('/')[0]
                        elif '/jobs/' in full:
                            cand = full.split('/jobs/')[-1].split('/')[0]
                    if not cand and txt and txt.lower() in DOMAIN_CODE_MAP:
                        cand = txt.lower()
                    if cand:
                        cand = cand.strip()
                        if cand not in domains:
                            domains.append(cand)
            if not domains:
                domains = list(DOMAIN_CODE_MAP.keys())
            return sorted(domains)
        except Exception as e:
            logger.exception('Failed to fetch domains via aiohttp')
            return []

    async def scrape_vdab_aiohttp(self, provided_domains: Optional[List[str]] = None) -> pd.DataFrame:
        """High-throughput aiohttp-based scraper. Falls back to existing parsing helpers."""
        if aiohttp is None:
            raise RuntimeError('aiohttp not installed')

        results = []
        timeout = aiohttp.ClientTimeout(total=30)
        headers = {'User-Agent': self.config.USER_AGENT, 'Accept-Language': 'nl-BE,nl;q=0.9,en;q=0.8'}

        async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
            if provided_domains:
                domains = provided_domains
            else:
                domains = await self.get_domains_aiohttp(session)
            logger.info(f"Found {len(domains)} domains via aiohttp")

            # If configured for multiple OS-level workers, spawn child processes and exit
            if getattr(self.config, 'WORKERS', 1) > 1 and not provided_domains:
                workers = int(getattr(self.config, 'WORKERS', 1))
                # split domains into approximately equal chunks
                chunk_size = math.ceil(len(domains) / workers)
                procs = []
                for wi in range(workers):
                    chunk = domains[wi*chunk_size:(wi+1)*chunk_size]
                    if not chunk:
                        continue
                    # build per-worker SAVE_PATH to avoid collisions
                    base, ext = os.path.splitext(self.config.SAVE_PATH)
                    worker_save = f"{base}_w{wi}{ext}"
                    env = os.environ.copy()
                    env['SAVE_PATH'] = worker_save
                    cmd = [sys.executable, '-m', 'data_scrapping.vdab_1', '--domains'] + chunk
                    logger.info(f"Spawning worker {wi} for {len(chunk)} domains -> {worker_save}")
                    p = subprocess.Popen(cmd, env=env)
                    procs.append(p)
                # wait for children
                for p in procs:
                    p.wait()
                # once all workers finish, merge outputs into main SAVE_PATH
                all_jobs = []
                for wi in range(workers):
                    base, ext = os.path.splitext(self.config.SAVE_PATH)
                    worker_save = f"{base}_w{wi}{ext}"
                    if os.path.exists(worker_save):
                        try:
                            dfw = pd.read_csv(worker_save)
                            all_jobs.append(dfw)
                        except Exception:
                            continue
                if all_jobs:
                    df = pd.concat(all_jobs, ignore_index=True)
                    df.to_csv(self.config.SAVE_PATH, index=False)
                    logger.info(f"Merged {len(all_jobs)} worker outputs into {self.config.SAVE_PATH}")
                    self.print_summary(df)
                    return df
                else:
                    logger.warning('No worker outputs found to merge')
                    return pd.DataFrame()

            # concurrency semaphore
            concurrency = self.config.FAST_CONCURRENCY if (getattr(self.config, 'FAST_MODE', False) or getattr(self.config, 'QUICK_MODE', False)) else self.config.CONCURRENCY
            sem = asyncio.Semaphore(concurrency)

            async def fetch_listing(domain: str):
                domain_jobs = []
                offset = 0
                processed = 0
                page_size = 50  # number of items per listing page; mirrors notebook approach


                # Use offset/limit pagination similar to the notebook implementation which
                # targets the 'product-tile' elements and extracts per-tile links.
                while True:
                    list_url = f"{SITE_ROOT}/vindeenjob/jobs/{domain}?limit={page_size}&offset={offset}"
                    try:
                        async with session.get(list_url) as r:
                            if r.status != 200:
                                logger.debug(f"Listing {list_url} returned status {r.status}")
                                break
                            html = await r.text()
                    except Exception as e:
                        logger.debug(f"Listing request failed for {list_url}: {e}")
                        break

                    soup = BeautifulSoup(html, 'lxml')
                    tiles = soup.select('div.product-tile')

                    links = []
                    if tiles:
                        for tile in tiles:
                            a = tile.select_one('a.product-link') or tile.select_one('a')
                            if not a:
                                continue
                            href = a.get('href')
                            if not href:
                                continue
                            u = href.split('#')[0]
                            if u.startswith('/'):
                                u = urljoin(SITE_ROOT, u)
                            parsed_path = urlparse(u).path or ''
                            if not re.search(r"/vacatures/\d+", parsed_path) and not re.search(r"/vindeenjob/vacatures/\d+", parsed_path):
                                continue
                            if u in links:
                                continue
                            links.append(u)
                    else:
                        # fallback: scan anchors for vacancy links
                        anchors = soup.find_all('a', href=True)
                        for a in anchors:
                            href = a.get('href')
                            if not href:
                                continue
                            u = href.split('#')[0]
                            if u.startswith('/'):
                                u = urljoin(SITE_ROOT, u)
                            parsed_path = urlparse(u).path or ''
                            if not re.search(r"/vacatures/\d+", parsed_path) and not re.search(r"/vindeenjob/vacatures/\d+", parsed_path) and not re.search(r"/vacature/\d+", parsed_path):
                                continue
                            if u in links:
                                continue
                            # avoid training/opleiding anchors
                            txt = a.get_text(' ', strip=True) or ''
                            if re.search(r"\b(opleiding|opleidingen|vind een opleiding)\b", txt, flags=re.IGNORECASE):
                                continue
                            links.append(u)

                    if not links:
                        break

                    # fetch details concurrently but bounded by sem
                    async def process_link(u):
                        nonlocal processed
                        async with sem:
                            try:
                                async with session.get(u) as r:
                                    if r.status != 200:
                                        return
                                    job_html = await r.text()
                            except Exception:
                                return
                            # Quick guard: skip pages that look like 'opleiding' / training landing pages
                            if re.search(r"\b(opleiding|opleidingen|vind een opleiding)\b", job_html, flags=re.IGNORECASE):
                                logger.debug(f"Skipping training/opleiding page: {u}")
                                return
                            processed += 1
                            domain_code = DOMAIN_CODE_MAP.get(domain, domain[:2].title() if domain else 'XX')
                            job_id = f"vdab-{domain_code}{processed:05d}"
                            job = await self.scrape_job_html(job_html, u, job_id)
                            if job:
                                job['domain'] = domain
                                job['domain_code'] = DOMAIN_CODE_MAP.get(domain, '')
                                results.append(job)
                                if len(results) % self.config.SAVE_EVERY == 0:
                                    self.save_progress()

                    tasks = [asyncio.create_task(process_link(u)) for u in links]
                    await asyncio.gather(*tasks)

                    # stop conditions: respect per-run LIMIT unless FETCH_ALL set
                    if (not getattr(self.config, 'FETCH_ALL', False)) and self.config.LIMIT and len(results) >= self.config.LIMIT:
                        break

                    # advance offset and continue
                    offset += page_size

                return

            # run domains sequentially to avoid hitting remote too hard; this can be parallelized later
            for domain in domains:
                logger.info(f"Scraping domain via aiohttp: {domain}")
                await fetch_listing(domain)
                self.save_progress()
                # small pause between domains
                await asyncio.sleep(0.1 if getattr(self.config, 'FAST_MODE', False) else 0.5)

        # final save and return
        if results:
            df = pd.DataFrame(results)
            # For CSV output, convert list fields to a CSV-friendly string (keep JSON as lists)
            df_csv = df.copy()
            if 'persoonlijke_vaardigheden' in df_csv.columns:
                # join lists into semicolon-separated strings for Excel-friendly viewing
                df_csv['persoonlijke_vaardigheden'] = df_csv['persoonlijke_vaardigheden'].apply(
                    lambda v: '; '.join(v) if isinstance(v, (list, tuple)) else (v if pd.notnull(v) else '')
                )
            df_csv.to_csv(self.config.SAVE_PATH, index=False)
            self.print_summary(df)
            return df
        else:
            logger.warning('No jobs scraped via aiohttp')
            return pd.DataFrame()
    
    async def scrape_domain(self, page, domain: str) -> List[Dict]:
        """Scrape all jobs from a specific domain.

        This function streams page-by-page and processes vacancy links as they are
        discovered instead of collecting all links first. It supports FETCH_ALL mode
        (fetch until pagination ends or MAX_PAGES reached) and emits progress logs
        during long runs.
        """
        domain_jobs = []
        logger.info(f"Scraping domain: {domain}")

        try:
            seen = set()
            page_no = 1
            processed_count = 0

            # concurrency controls (respect FAST_MODE or QUICK_MODE)
            # dynamic concurrency: prefer FAST_CONCURRENCY for aggressive runs
            concurrency = self.config.FAST_CONCURRENCY if (getattr(self.config, 'FAST_MODE', False) or getattr(self.config, 'QUICK_MODE', False)) else self.config.CONCURRENCY
            sem = asyncio.Semaphore(concurrency)

            job_bar = None

            async def _process_links(links):
                nonlocal processed_count
                logger.debug(f"_process_links received {len(links)} links; processed_count starting at {processed_count}")

                # Use a simple worker pool where each worker reuses its page instance.
                # This avoids creating/closing a page per job which is expensive.
                cleaned_links = []
                for url in links:
                    if not url:
                        continue
                    u = url.split('#')[0]
                    if u in seen:
                        continue
                    # normalize relative links
                    if u.startswith('/'):
                        u = urljoin(self.config.BASE_URL, u)
                    cleaned_links.append(u)

                if not cleaned_links:
                    return

                pool_size = min(concurrency, max(1, len(cleaned_links)))
                queue = asyncio.Queue()
                for u in cleaned_links:
                    await queue.put(u)

                async def worker(worker_page):
                    nonlocal processed_count
                    while not queue.empty():
                        try:
                            u = queue.get_nowait()
                        except asyncio.QueueEmpty:
                            break
                        if not u:
                            continue
                        if u in seen:
                            continue
                        seen.add(u)

                        processed_count += 1
                        domain_code = DOMAIN_CODE_MAP.get(domain, domain[:2].title() if domain else 'XX')
                        job_id = f"vdab-{domain_code}{processed_count:05d}"

                        try:
                            async with sem:
                                try:
                                    job = await self.scrape_job_page(worker_page, u, job_id)
                                except Exception as e:
                                    logger.debug(f"Failed to scrape job {u}: {e}")
                                    job = None
                        except Exception as e:
                            logger.debug(f"Semaphore/worker error for {u}: {e}")
                            job = None

                        if job:
                            if not job.get('domain') or job.get('domain') == 'unknown':
                                job['domain'] = domain
                            job['domain_code'] = DOMAIN_CODE_MAP.get(job['domain'], '')
                            domain_jobs.append(job)
                            self.results.append(job)
                            # periodic save
                            if len(self.results) % self.config.SAVE_EVERY == 0:
                                self.save_progress()
                            # update domain progress bar
                            if job_bar is not None:
                                try:
                                    job_bar.update(1)
                                except Exception:
                                    pass

                # If configured, use fast request-based fetching which avoids creating
                # heavyweight Page objects per job. This fetches HTML via the context
                # request API and reuses a lightweight worker coroutine.
                if getattr(self.config, 'USE_REQUESTS_FOR_DETAILS', False):
                    async def req_worker():
                        nonlocal processed_count
                        while not queue.empty():
                            try:
                                u = queue.get_nowait()
                            except asyncio.QueueEmpty:
                                break
                            if not u:
                                continue
                            if u in seen:
                                continue
                            seen.add(u)

                            processed_count += 1
                            domain_code = DOMAIN_CODE_MAP.get(domain, domain[:2].title() if domain else 'XX')
                            job_id = f"vdab-{domain_code}{processed_count:05d}"

                            try:
                                async with sem:
                                    try:
                                        # Use context.request to GET the page HTML quickly
                                        r = await page.context.request.get(u, timeout=self.config.PAGE_TIMEOUT_MS)
                                        if r.status != 200:
                                            logger.debug(f"Request for {u} returned status {r.status}")
                                            job = None
                                        else:
                                            html = await r.text()
                                            # Reuse existing parsing logic by creating a BeautifulSoup from HTML
                                            job = None
                                            try:
                                                # create a temporary lightweight 'page' equivalent by
                                                # passing html into scrape_job_page via a small wrapper
                                                # We'll call a new helper that accepts raw html
                                                job = await self.scrape_job_html(html, u, job_id)
                                            except Exception as e:
                                                logger.debug(f"Failed to parse job HTML for {u}: {e}")
                                                job = None
                                    except Exception as e:
                                        logger.debug(f"Request worker error for {u}: {e}")
                                        job = None
                            except Exception as e:
                                logger.debug(f"Semaphore/worker error for request {u}: {e}")
                                job = None

                            if job:
                                if not job.get('domain') or job.get('domain') == 'unknown':
                                    job['domain'] = domain
                                job['domain_code'] = DOMAIN_CODE_MAP.get(job['domain'], '')
                                domain_jobs.append(job)
                                self.results.append(job)
                                # periodic save
                                if len(self.results) % self.config.SAVE_EVERY == 0:
                                    self.save_progress()
                                if job_bar is not None:
                                    try:
                                        job_bar.update(1)
                                    except Exception:
                                        pass

                    workers = [asyncio.create_task(req_worker()) for _ in range(pool_size)]
                    await asyncio.gather(*workers)

                else:
                    # create pool pages (slower fallback)
                    pages = []
                    try:
                        for _ in range(pool_size):
                            p = await page.context.new_page()
                            pages.append(p)

                        workers = [asyncio.create_task(worker(p)) for p in pages]
                        await asyncio.gather(*workers)
                    finally:
                        for p in pages:
                            try:
                                await p.close()
                            except Exception:
                                pass

            # Main pagination loop: use offset/limit pagination (matches notebook) and
            # extract 'div.product-tile' blocks which reliably contain job links.
            page_size = 50
            offset = 0
            consecutive_empty = 0
            while offset < (self.config.MAX_PAGES * page_size):
                paged_url = f"{SITE_ROOT}/vindeenjob/jobs/{domain}?limit={page_size}&offset={offset}"
                try:
                    await page.goto(paged_url, wait_until="domcontentloaded", timeout=self.config.PAGE_TIMEOUT_MS)
                except Exception:
                    logger.debug(f"Failed to load offset {offset} for {domain}; stopping pagination")
                    break

                # allow JS to render (shorter in FAST_MODE)
                await asyncio.sleep(0.08 if getattr(self.config, 'FAST_MODE', False) else 0.25)

                # parse rendered HTML and look for product tiles or vacancy anchors
                html = await page.content()
                soup = BeautifulSoup(html, 'lxml')
                tiles = soup.select('div.product-tile')

                new_links = []
                if tiles:
                    consecutive_empty = 0
                    for tile in tiles:
                        a = tile.select_one('a.product-link') or tile.select_one('a')
                        if not a:
                            continue
                        href = a.get('href')
                        if not href:
                            continue
                        u = href.split('#')[0]
                        if u.startswith('/'):
                            u = urljoin(SITE_ROOT, u)

                        # Accept only vacancy pages that include a numeric vacancy id
                        parsed_path = urlparse(u).path or ''
                        if not re.search(r"/vacatures/\d+", parsed_path) and not re.search(r"/vindeenjob/vacatures/\d+", parsed_path):
                            continue
                        if u in seen:
                            continue
                        # Quick guard: if the tile contains obvious 'opleiding' text, skip
                        tile_text = tile.get_text(' ', strip=True)
                        if re.search(r"\b(opleiding|opleidingen|vind een opleiding)\b", tile_text, flags=re.IGNORECASE):
                            logger.debug(f"Skipping tile with opleiding text for {u}")
                            continue
                        new_links.append(u)
                else:
                    # No product-tile blocks found: broaden search to anchors and other selectors
                    logger.debug(f"No product tiles found for {domain} at {offset}; falling back to anchor scan")
                    anchors = soup.find_all('a', href=True)
                    for a in anchors:
                        href = a.get('href')
                        if not href:
                            continue
                        u = href.split('#')[0]
                        if u.startswith('/'):
                            u = urljoin(SITE_ROOT, u)
                        parsed_path = urlparse(u).path or ''
                        # Accept vacancy pages with numeric ID
                        if not re.search(r"/vacatures/\d+", parsed_path) and not re.search(r"/vindeenjob/vacatures/\d+", parsed_path) and not re.search(r"/vacature/\d+", parsed_path):
                            continue
                        if u in seen:
                            continue
                        # avoid navigation/utility links
                        txt = a.get_text(' ', strip=True) or ''
                        if re.search(r"\b(opleiding|opleidingen|vind een opleiding|opleidings)\b", txt, flags=re.IGNORECASE):
                            continue
                        new_links.append(u)

                    # as a last resort, search for other tile-like containers
                    if not new_links:
                        extra_tiles = soup.select('.vacature, .vacancy, li.vacancy, article.vacancy, div.job-tile, div.vacature')
                        for tile in extra_tiles:
                            a = tile.select_one('a')
                            if not a:
                                continue
                            href = a.get('href')
                            if not href:
                                continue
                            u = href.split('#')[0]
                            if u.startswith('/'):
                                u = urljoin(SITE_ROOT, u)
                            parsed_path = urlparse(u).path or ''
                            if not re.search(r"/vacatures/\d+", parsed_path) and not re.search(r"/vindeenjob/vacatures/\d+", parsed_path):
                                continue
                            if u in seen:
                                continue
                            new_links.append(u)

                # (suppressed per-offset discovery log for clean output)

                if not new_links:
                    consecutive_empty += 1
                    logger.debug(f"No vacancy links found for {domain} at {offset} (consecutive {consecutive_empty})")
                    if consecutive_empty >= getattr(self.config, 'EMPTY_PAGE_GUARD', 3):
                        logger.info(f"No vacancy links found for {domain} at {offset} for {consecutive_empty} consecutive pages; stopping")
                        break
                    else:
                        offset += page_size
                        continue

                if TQDM_AVAILABLE and job_bar is None:
                    job_bar = tqdm(total=0, desc=f"{domain} jobs", unit='jobs')

                # process links immediately
                await _process_links(new_links)

                # Stop if we've reached the per-domain LIMIT and not in FETCH_ALL mode
                if (not getattr(self.config, 'FETCH_ALL', False)) and self.config.LIMIT and len(domain_jobs) >= self.config.LIMIT:
                    logger.info(f"Reached limit {self.config.LIMIT} for domain {domain}")
                    break

                # advance offset
                offset += page_size

                # show light progress for very long runs
                if offset // page_size % 50 == 0:
                    logger.info(f"{domain}: scanned {offset // page_size} listing pages, found {len(domain_jobs)} jobs so far")

            if job_bar is not None:
                try:
                    job_bar.close()
                except Exception:
                    pass

            logger.info(f"Completed domain {domain}: {len(domain_jobs)} jobs (pages scanned: {page_no-1})")

        except Exception as e:
            logger.error(f"Error scraping domain {domain}: {e}")

        return domain_jobs
    
    def save_progress(self):
        """Save current progress to CSV."""
        if self.results:
            df = pd.DataFrame(self.results)
            # Ensure the CSV columns follow a stable, expected order matching the
            # previous output format requested by the user.
            desired_columns = [
                'job_id','title','company','city','contract_type','posted_on','detail_url','domain','scraped_at',
                'functieomschrijving','profiel','professionele_vaardigheden','persoonlijke_vaardigheden','anbod','full_description',
                'academic_level','years_experience','salary',
                'computer_skill','ai_skill','data_analysis_skill','communication_skill','leadership_skill',
                'project_management_skill','customer_service_skill','sales_skill','technical_skill','creative_skill',
                'finance_skill','hr_skill','administrative_skill','dutch_language_skill','french_language_skill',
                'english_language_skill','project_management','dutch_language','french_language','english_language',
                'domain_code','salary_structured'
            ]

            # Populate any missing columns with sensible defaults
            for col in desired_columns:
                if col not in df.columns:
                    # default for skills: 'No' for *_skill fields
                    if col.endswith('_skill'):
                        df[col] = 'No'
                    # for aggregate language/project flags, copy from skill columns if present
                    elif col in ('project_management', 'dutch_language', 'french_language', 'english_language'):
                        skill_col = col + '_skill' if not col.endswith('_skill') else col
                        if skill_col in df.columns:
                            df[col] = df[skill_col].replace({True: 'Yes', False: 'No'}).fillna('No')
                        else:
                            df[col] = 'No'
                    else:
                        df[col] = ''

            # Reorder columns; keep any additional columns after the desired ones
            extra_cols = [c for c in df.columns if c not in desired_columns]
            df = df[desired_columns + extra_cols]

            df.to_csv(self.config.SAVE_PATH, index=False)
            # also save JSON alongside CSV (same base name)
            try:
                json_path = os.path.splitext(self.config.SAVE_PATH)[0] + '.json'
                def _map_job_for_json(job: Dict) -> Dict:
                    # Ensure all requested keys are present, using safe defaults
                    return {
                        "job_id": job.get("job_id", ""),
                        "title": job.get("title", ""),
                        "company": job.get("company", ""),
                        "city": job.get("city", ""),
                        "contract_type": job.get("contract_type", ""),
                        "posted_on": job.get("posted_on", ""),
                        "detail_url": job.get("detail_url", ""),
                        "original_url": job.get("original_url", job.get("detail_url", "")),
                        "domain": job.get("domain", ""),
                        "scraped_at": job.get("scraped_at", datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                        "functieomschrijving": job.get("functieomschrijving", ""),
                        "profiel": job.get("profiel", ""),
                        "professionele_vaardigheden": job.get("professionele_vaardigheden", ""),
                        "persoonlijke_vaardigheden": job.get("persoonlijke_vaardigheden", []),
                        "anbod": job.get("anbod", ""),
                        "full_description": job.get("full_description", ""),
                        "academic_level": job.get("academic_level", "Not specified"),
                        "years_experience": job.get("years_experience", 0),
                        "salary": job.get("salary", "Not specified"),
                        # skills
                        "computer_skill": job.get("computer_skill", "No"),
                        "ai_skill": job.get("ai_skill", "No"),
                        "data_analysis_skill": job.get("data_analysis_skill", "No"),
                        "communication_skill": job.get("communication_skill", "No"),
                        "leadership_skill": job.get("leadership_skill", "No"),
                        "project_management_skill": job.get("project_management_skill", job.get("project_management", "No")),
                        "customer_service_skill": job.get("customer_service_skill", "No"),
                        "sales_skill": job.get("sales_skill", "No"),
                        "technical_skill": job.get("technical_skill", "No"),
                        "creative_skill": job.get("creative_skill", "No"),
                        "finance_skill": job.get("finance_skill", "No"),
                        "hr_skill": job.get("hr_skill", "No"),
                        "administrative_skill": job.get("administrative_skill", "No"),
                        "dutch_language_skill": job.get("dutch_language_skill", job.get("dutch_language", "No")),
                        "french_language_skill": job.get("french_language_skill", job.get("french_language", "No")),
                        "english_language_skill": job.get("english_language_skill", job.get("english_language", "No")),
                        # also include aggregate flags matching the legacy CSV
                        "project_management": job.get("project_management", job.get("project_management_skill", "No")),
                        "dutch_language": job.get("dutch_language", job.get("dutch_language_skill", "No")),
                        "french_language": job.get("french_language", job.get("french_language_skill", "No")),
                        "english_language": job.get("english_language", job.get("english_language_skill", "No")),
                        "domain_code": job.get("domain_code", job.get("domain", "")[:2].title()),
                        "salary_structured": job.get("salary_structured", job.get("salary", "")),
                    }

                # Write only the most recent SAVE_EVERY jobs to JSON (user requested batch saves)
                batch_start = max(0, len(self.results) - int(self.config.SAVE_EVERY))
                recent = self.results[batch_start:]
                # Diagnostic: log the persoonlijke_vaardigheden for the recent batch so it's
                # easy to verify the extractor is producing values before we write the JSON.
                try:
                    diag = [(j.get('job_id', ''), j.get('persoonlijke_vaardigheden', [])) for j in recent]
                    # Emit as INFO so this diagnostic is visible in standard runs
                    logger.info(f"Recent persoonlijke_vaardigheden (job_id -> values): {diag}")
                except Exception:
                    logger.info('Failed to produce persoonlijke_vaardigheden diagnostic list')

                json_list = [_map_job_for_json(j) for j in recent]
                with open(json_path, 'w', encoding='utf-8') as jf:
                    json.dump(json_list, jf, ensure_ascii=False, indent=2)
                logger.info(f"Progress saved: {len(self.results)} jobs to {self.config.SAVE_PATH} and wrote {len(json_list)} recent jobs to {json_path}")
            except Exception:
                logger.exception('Failed to save JSON progress file')
    
    async def scrape_vdab_playwright(self, provided_domains: Optional[List[str]] = None) -> pd.DataFrame:
        """Main scraping function."""
        logger.info("Starting VDAB scraper...")
        # If aiohttp fast path is enabled and aiohttp is available, use it instead
        if getattr(self.config, 'USE_AIOHTTP_FOR_FETCH', False) and aiohttp is not None:
            logger.info("Using aiohttp-based fast fetch path")
            try:
                return await self.scrape_vdab_aiohttp(provided_domains=provided_domains)
            except Exception as e:
                logger.warning(f"aiohttp path failed, falling back to Playwright: {e}")

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
            # Create a browser context with the desired User-Agent for robustness
            context_args = {}
            if getattr(self.config, 'USER_AGENT', None):
                context_args['user_agent'] = self.config.USER_AGENT
            # reduce resource loading by blocking images/styles/fonts/media which speeds up navigation
            context = await browser.new_context(**context_args)

            # Block non-essential resources to speed up page loads
            try:
                async def _route_handler(route, request):
                    rtype = request.resource_type
                    # Defensive: guard abort/continue calls against driver pipe errors
                    try:
                        if rtype in ("image", "stylesheet", "font", "media"):
                            try:
                                await route.abort()
                            except Exception:
                                # best-effort: ignore abort failures
                                logger.debug(f"route.abort() failed for {request.url}")
                        else:
                            try:
                                await route.continue_()
                            except Exception:
                                logger.debug(f"route.continue() failed for {request.url}")
                    except Exception as e:
                        # swallow any unexpected routing errors to avoid crashing
                        logger.debug(f"_route_handler error: {e}")

                # Only intercept heavy/static resource patterns to reduce handler pressure
                try:
                    patterns = ["**/*.{png,jpg,jpeg,svg,css,woff,woff2,ttf}"]
                    for pat in patterns:
                        await context.route(pat, _route_handler)
                except Exception:
                    # fall back to the broader route if pattern registration fails
                    try:
                        await context.route("**/*", _route_handler)
                    except Exception:
                        logger.debug("Failed to set specific route patterns; continuing without route interception")
            except Exception:
                # route may fail in some Playwright versions; ignore and continue
                logger.debug("Failed to set route handler for resource blocking; continuing without it")

            # Send a compact Accept-Language header to improve localized responses
            try:
                await context.set_extra_http_headers({"accept-language": "nl-BE,nl;q=0.9,en;q=0.8"})
            except Exception:
                pass
            page = await context.new_page()
            
            try:
                # Get available domains (or use provided ones)
                if provided_domains:
                    domains = provided_domains
                    logger.info(f"Using provided domains: {domains}")
                else:
                    domains = await self.get_domains(page)
                    if not domains:
                        logger.error("No domains found. Stopping scraper.")
                        return pd.DataFrame()
                
                # Scrape each domain (show progress if available)
                domains_iter = tqdm(domains, desc="Domains") if TQDM_AVAILABLE else domains
                domain_count = 0
                for domain in domains_iter:
                    # Wrap domain scraping to handle driver/browser/context unexpected closure
                    try:
                        domain_jobs = await self.scrape_domain(page, domain)
                    except Exception as e:
                        msg = str(e).lower()
                        # If the browser/context/page unexpectedly closed, attempt one recovery
                        if any(tok in msg for tok in ("target closed", "target page, context or browser has been closed", "epipe", "broken pipe")):
                            logger.warning(f"Playwright driver error while scraping domain {domain}: {e}. Attempting to recreate context and retry once.")
                            try:
                                # close and recreate context/page
                                try:
                                    await page.close()
                                except Exception:
                                    pass
                                try:
                                    await context.close()
                                except Exception:
                                    pass
                                context = await browser.new_context(**context_args)
                                try:
                                    await context.set_extra_http_headers({"accept-language": "nl-BE,nl;q=0.9,en;q=0.8"})
                                except Exception:
                                    pass
                                try:
                                    for pat in ("**/*.{png,jpg,jpeg,svg,css,woff,woff2,ttf}",):
                                        await context.route(pat, _route_handler)
                                except Exception:
                                    try:
                                        await context.route("**/*", _route_handler)
                                    except Exception:
                                        logger.debug("Failed to set route handler on recreated context")
                                page = await context.new_page()
                                # retry domain once
                                domain_jobs = await self.scrape_domain(page, domain)
                            except Exception as e2:
                                logger.error(f"Failed to recover and scrape domain {domain}: {e2}")
                                domain_jobs = []
                        else:
                            logger.error(f"Error scraping domain {domain}: {e}")
                            domain_jobs = []
                    self.results.extend(domain_jobs)
                    domain_count += 1

                    pwrite(f"Completed {domain}: {len(domain_jobs)} jobs")
                    self.save_progress()
                    # Take a longer break between domains; significantly shorter in FAST_MODE
                    await asyncio.sleep(0.2 if getattr(self.config, 'FAST_MODE', False) else 2)

                    # Periodically restart the browser context to avoid long-lived pipe/socket issues
                    try:
                        restart_every = int(getattr(self.config, 'RESTART_CONTEXT_EVERY_DOMAINS', 0) or 0)
                        if restart_every > 0 and (domain_count % restart_every) == 0:
                            logger.info(f"Restarting browser context after {domain_count} domains to improve stability...")
                            try:
                                await page.close()
                            except Exception:
                                pass
                            try:
                                await context.close()
                            except Exception:
                                pass
                            # create fresh context and page
                            context = await browser.new_context(**context_args)
                            try:
                                await context.set_extra_http_headers({"accept-language": "nl-BE,nl;q=0.9,en;q=0.8"})
                            except Exception:
                                pass
                            try:
                                await context.route("**/*", _route_handler)
                            except Exception:
                                logger.debug("Failed to set route handler on restarted context; continuing")
                            page = await context.new_page()
                            # small sleep to let the new context stabilize
                            await asyncio.sleep(0.5)
                    except Exception:
                        # don't fail the whole run if restart logic hits an unexpected error
                        logger.debug("Context restart logic hit an exception; continuing")
                
            except Exception as e:
                logger.error(f"Unexpected error during scraping: {e}")
            finally:
                await browser.close()
        
        # Final save
        if self.results:
            df = pd.DataFrame(self.results)
            # Prepare CSV-friendly copy where list fields are joined
            df_csv = df.copy()
            if 'persoonlijke_vaardigheden' in df_csv.columns:
                df_csv['persoonlijke_vaardigheden'] = df_csv['persoonlijke_vaardigheden'].apply(
                    lambda v: '; '.join(v) if isinstance(v, (list, tuple)) else (v if pd.notnull(v) else '')
                )
            df_csv.to_csv(self.config.SAVE_PATH, index=False)
            try:
                json_path = os.path.splitext(self.config.SAVE_PATH)[0] + '.json'

                def _map_job_for_json(job: Dict) -> Dict:
                    return {
                        "job_id": job.get("job_id", ""),
                        "title": job.get("title", ""),
                        "company": job.get("company", ""),
                        "city": job.get("city", ""),
                        "contract_type": job.get("contract_type", ""),
                        "posted_on": job.get("posted_on", ""),
                        "detail_url": job.get("detail_url", ""),
                        "original_url": job.get("original_url", job.get("detail_url", "")),
                        "domain": job.get("domain", ""),
                        "scraped_at": job.get("scraped_at", datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                        "functieomschrijving": job.get("functieomschrijving", ""),
                        "profiel": job.get("profiel", ""),
                        "professionele_vaardigheden": job.get("professionele_vaardigheden", ""),
                        "persoonlijke_vaardigheden": job.get("persoonlijke_vaardigheden", []),
                        "anbod": job.get("anbod", ""),
                        "full_description": job.get("full_description", ""),
                        "academic_level": job.get("academic_level", "Not specified"),
                        "years_experience": job.get("years_experience", 0),
                        "salary": job.get("salary", "Not specified"),
                        "computer_skill": job.get("computer_skill", "No"),
                        "ai_skill": job.get("ai_skill", "No"),
                        "data_analysis_skill": job.get("data_analysis_skill", "No"),
                        "communication_skill": job.get("communication_skill", "No"),
                        "leadership_skill": job.get("leadership_skill", "No"),
                        "project_management": job.get("project_management", "No"),
                        "customer_service_skill": job.get("customer_service_skill", "No"),
                        "sales_skill": job.get("sales_skill", "No"),
                        "technical_skill": job.get("technical_skill", "No"),
                        "creative_skill": job.get("creative_skill", "No"),
                        "finance_skill": job.get("finance_skill", "No"),
                        "hr_skill": job.get("hr_skill", "No"),
                        "administrative_skill": job.get("administrative_skill", "No"),
                        "dutch_language": job.get("dutch_language", "No"),
                        "french_language": job.get("french_language", "No"),
                        "english_language": job.get("english_language", "No"),
                        "spanish_language": job.get("spanish_language", "No"),
                        "italian_language": job.get("italian_language", "No"),
                    }

                json_list = [_map_job_for_json(j) for j in self.results]
                with open(json_path, 'w', encoding='utf-8') as jf:
                    json.dump(json_list, jf, ensure_ascii=False, indent=2)
                logger.info(f"Scraping completed! {len(df)} jobs saved to {self.config.SAVE_PATH} and {json_path}")
            except Exception:
                logger.exception('Failed to save final JSON file')
            
            # Print summary
            self.print_summary(df)
            return df
        else:
            logger.warning("No jobs were scraped.")
            return pd.DataFrame()
    
    def print_summary(self, df: pd.DataFrame):
        """Print a summary of the scraped data."""
        if df.empty:
            return
            
        logger.info("\n" + "="*50)
        logger.info("SCRAPING SUMMARY")
        logger.info("="*50)
        logger.info(f"Total jobs: {len(df)}")
        logger.info(f"Domains: {df['domain'].nunique()}")
        logger.info(f"Companies: {df['company'].nunique()}")
        
        # Top domains
        top_domains = df['domain'].value_counts().head(5)
        logger.info("\nTop 5 domains:")
        for domain, count in top_domains.items():
            logger.info(f"  {domain}: {count} jobs")
        
        # Academic level distribution
        academic_dist = df['academic_level'].value_counts()
        logger.info("\nAcademic level distribution:")
        for level, count in academic_dist.items():
            logger.info(f"  {level}: {count} jobs")

# --- Main execution ---
async def main(domains: Optional[List[str]] = None):
    """Main async function to run the scraper. Accepts optional domains list."""
    scraper = VdabScraper(config)
    return await scraper.scrape_vdab_playwright(provided_domains=domains)

def run_scraper(domains: Optional[List[str]] = None):
    """Run the scraper with proper async handling. Pass optional domains."""
    try:
        return asyncio.run(main(domains))
    except RuntimeError as e:
        if "asyncio.run() cannot be called from a running event loop" in str(e):
            logger.info("Running in async environment (e.g., Jupyter)")
            # In Jupyter, you would use: await main(domains)
            return None
        else:
            raise

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="VDAB Playwright & AIOHTTP fast scraper")
    parser.add_argument("--domains", "-d", nargs="+", help="Domain keys to scrape (e.g., ict)")
    parser.add_argument("--limit", type=int, help="Maximum jobs per domain to fetch")
    parser.add_argument("--page-timeout", type=int, help="Navigation timeout per page in milliseconds")
    parser.add_argument("--user-agent", type=str, help="User-Agent string to send with requests")
    parser.add_argument("--all", action="store_true", help="Fetch all pages for each domain (overrides --limit)")
    parser.add_argument("--aiohttp-fast", action="store_true", help="Use aiohttp fast mode (bypass Playwright)")
    args = parser.parse_args()

    # Apply CLI overrides
    if args.limit:
        config.LIMIT = args.limit
    if args.all:
        config.FETCH_ALL = True
    if args.page_timeout:
        config.PAGE_TIMEOUT_MS = int(args.page_timeout)
    if args.user_agent:
        config.USER_AGENT = args.user_agent

    if args.aiohttp_fast:
        # Use aiohttp fast mode
        asyncio.run(aiohttp_fast_scrape(args.domains, limit=args.limit or 0, concurrency=32))
    else:
        df = run_scraper(domains=args.domains)
        if df is not None and not df.empty:
            print(f"\nScraping completed! Check '{config.SAVE_PATH}' for results.")
        else:
            print("Scraping may still be running in async environment...")
            print("If using Jupyter, run: await scrape_vdab_playwright()")