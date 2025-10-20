#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scraper Stepstone (BE) – Playwright (async)

✅ FR + NL
✅ Récupération de la description complète (via JSON-LD JobPosting + fallback DOM)
✅ Gestion erreurs HTTP/2 + backoff + retry
✅ Anti-cookie robuste (FR/NL)
✅ Snapshot CSV incrémental pour reprise
✅ Concurrency réglable pour les pages "détail"
✅ Throttle entre pages de liste

Exemples d'utilisation :

python scraper_stepstone_playwright.py \
  --search-url "https://www.stepstone.be/emplois?searchOrigin=Resultlist_top-search&page={page}" \
  --start-page 1 --end-page 1000 \
  --languages fr,nl \
  --out-prefix data/raw/stepstone \
  --throttle 0.8 --concurrency 4 | tee data/raw/stepstone_run.log

Notes :
- Le scraper déduplique automatiquement les liens.
- Le snapshot « {out-prefix}_latest.csv » est écrit après chaque page.
- En cas de blocage net::ERR_HTTP2_PROTOCOL_ERROR, on relance la page et,
  si nécessaire, on reconstruit un nouveau contexte/navigateur.
"""

import asyncio
import argparse
import contextlib
import json
import random
import re
import sys
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Tuple

from playwright.async_api import async_playwright, Browser, BrowserContext, Page, TimeoutError as PWTimeoutError

import csv

# --------------------------- Utilitaires d'affichage ---------------------------

def ts() -> str:
    return time.strftime("[%H:%M:%S]")


def log_info(msg: str) -> None:
    print(f"{ts()} {msg}", flush=True)


# --------------------------- UA / Contexte / Cookies ---------------------------

UA_POOL = [
    # Quelques user agents desktop récents
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
]

LANG_TO_LOCALE = {
    "fr": ("fr-BE", "fr-FR,fr;q=0.9,en;q=0.8"),
    "nl": ("nl-BE", "nl-BE,nl;q=0.9,en;q=0.8"),
}

COOKIE_ACCEPT_TEXTS = [
    # FR / NL / EN
    "Tout accepter",
    "Accepter tout",
    "Accepter",
    "J'accepte",
    "Alles accepteren",
    "Accepteer alles",
    "Accepteren",
    "I accept",
    "Accept all",
]

COOKIE_REJECT_TEXTS = [
    "Tout refuser",
    "Refuser",
    "Weigeren",
    "Reject all",
]


async def make_context(browser: Browser, lang: str) -> BrowserContext:
    locale, accept_lang = LANG_TO_LOCALE.get(lang, ("fr-BE", "fr-FR,fr;q=0.9,en;q=0.8"))
    ua = random.choice(UA_POOL)
    context = await browser.new_context(
        locale=locale,
        user_agent=ua,
        viewport={"width": 1366, "height": 850},
        extra_http_headers={"Accept-Language": accept_lang},
    )
    return context


async def click_any_button_by_text(page: Page, texts: List[str]) -> bool:
    # Essaye un clique par texte (robuste)
    for t in texts:
        # boutons / spans / divs cliquables
        loc = page.locator(f"button:has-text('{t}'), role=button[name='{t}']")
        if await loc.count():
            with contextlib.suppress(Exception):
                await loc.first.click(timeout=2000)
                return True
        loc2 = page.locator(f"text={t}")
        if await loc2.count():
            with contextlib.suppress(Exception):
                await loc2.first.click(timeout=2000)
                return True
    return False


async def handle_cookies(page: Page) -> None:
    # tente en douceur, sans casser si rien
    with contextlib.suppress(Exception):
        await page.wait_for_load_state("domcontentloaded", timeout=6000)
    # Certains CMP utilisent un iframe
    # On scanne la page et les frames
    tried = False
    try:
        if await click_any_button_by_text(page, COOKIE_ACCEPT_TEXTS):
            return
        if await click_any_button_by_text(page, COOKIE_REJECT_TEXTS):
            return
        # frames
        for f in page.frames:
            if f == page.main_frame:
                continue
            if await click_any_button_by_text(f, COOKIE_ACCEPT_TEXTS):
                tried = True
                break
            if await click_any_button_by_text(f, COOKIE_REJECT_TEXTS):
                tried = True
                break
    except Exception:
        pass
    if not tried:
        # fallback : chercher bouton avec data-testid ou aria-label courant
        with contextlib.suppress(Exception):
            loc = page.locator("button[aria-label*='accept'], button[data-testid*='accept']")
            if await loc.count():
                await loc.first.click(timeout=1500)


# --------------------------- Navigation robuste ---------------------------

HTTP2_ERR_PATTERN = re.compile(r"HTTP2_PROTOCOL_ERROR|ERR_HTTP2|HTTP/2")


async def goto_resilient(page: Page, url: str, max_retries: int = 4, timeout: int = 30000) -> None:
    delay = 1.2
    last_err = None
    for attempt in range(1, max_retries + 1):
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=timeout)
            return
        except Exception as e:
            last_err = e
            msg = str(e)
            if HTTP2_ERR_PATTERN.search(msg):
                log_info(f"⚠️ HTTP/2 error – retry {attempt}/{max_retries} après {delay:.1f}s")
                await asyncio.sleep(delay)
                delay *= 1.8
                # petite ruse : changer l'UA entre les retries
                with contextlib.suppress(Exception):
                    await page.context.set_extra_http_headers({
                        "Accept-Language": page.context._options.get("extraHTTPHeaders", {}).get("Accept-Language", "fr"),
                        "Cache-Control": "no-cache",
                    })
                continue
            # autres erreurs (timeouts inclus)
            log_info(f"⚠️ goto error – retry {attempt}/{max_retries} après {delay:.1f}s : {msg}")
            await asyncio.sleep(delay)
            delay *= 1.6
    # si on sort de la boucle
    raise last_err if last_err else RuntimeError("goto_resilient: unknown error")


# --------------------------- Parsing des pages ---------------------------

JOB_URL_PAT = re.compile(r"^https?://(www\.)?stepstone\.be/.*", re.I)

LIST_DETAIL_HINTS = [
    "/offre", "/offers", "/job/", "/jobs/", "/vacature", "/vacatures", "/joblisting", "/detail", "/bewerbung", 
]


def looks_like_job_url(href: str) -> bool:
    if not href:
        return False
    if not JOB_URL_PAT.match(href):
        return False
    if any(s in href for s in ("/company/", "/bedrijf/", "/employeur/", "/search", "/emplois", "/vacatures?", "/?search")):
        return False
    return any(h in href for h in LIST_DETAIL_HINTS)


async def extract_list_links(page: Page) -> List[str]:
    hrefs = set()
    anchors = page.locator("a[href]")
    count = await anchors.count()
    for i in range(min(count, 3000)):
        with contextlib.suppress(Exception):
            href = await anchors.nth(i).get_attribute("href")
            if not href:
                continue
            if href.startswith("/"):
                href = f"https://www.stepstone.be{href}"
            if looks_like_job_url(href):
                hrefs.add(href.split("?")[0])
    return sorted(hrefs)


def clean_text(x: Optional[str]) -> str:
    if not x:
        return ""
    return re.sub(r"\s+", " ", x).strip()


def first_not_empty(*vals: Optional[str]) -> str:
    for v in vals:
        v = clean_text(v)
        if v:
            return v
    return ""


@dataclass
class JobRow:
    lang: str
    list_page: int
    job_url: str
    title: str = ""
    company: str = ""
    location: str = ""
    datePosted: str = ""
    employmentType: str = ""
    identifier: str = ""
    hiringOrganization: str = ""
    industry: str = ""
    workHours: str = ""
    baseSalary: str = ""
    jobLocationType: str = ""
    description_text: str = ""


async def parse_job_jsonld(page: Page) -> Dict[str, Any]:
    # Cherche JSON-LD JobPosting
    scripts = page.locator("script[type='application/ld+json']")
    results: Dict[str, Any] = {}
    n = await scripts.count()
    for i in range(n):
        with contextlib.suppress(Exception):
            raw = await scripts.nth(i).text_content()
            if not raw:
                continue
            data = json.loads(raw)
            # parfois liste de blocs
            blocks = data if isinstance(data, list) else [data]
            for b in blocks:
                if isinstance(b, dict) and b.get("@type") in ("JobPosting", ["JobPosting"]):
                    results = b
                    return results
    return results


async def parse_job_dom(page: Page) -> Dict[str, Any]:
    # Fallback DOM si pas de JSON-LD
    out: Dict[str, Any] = {}
    sel_title = "h1, h1 span"
    sel_company = "[data-at='job-company-name'], a[rel='nofollow'][href*='company'], .company, [class*='company']"
    sel_location = "[data-at='job-location'], .location, [class*='location']"

    with contextlib.suppress(Exception):
        out["title"] = clean_text(await page.locator(sel_title).first.text_content())
    with contextlib.suppress(Exception):
        out["hiringOrganization"] = clean_text(await page.locator(sel_company).first.text_content())
    with contextlib.suppress(Exception):
        out["jobLocation"] = clean_text(await page.locator(sel_location).first.text_content())
    with contextlib.suppress(Exception):
        # description globale
        desc_node = page.locator("article, [data-at='job-description'], .job-section, .job-description").first
        out["description"] = clean_text(await desc_node.inner_text())
    return out


async def scrape_job_detail(ctx: BrowserContext, lang: str, job_url: str, list_page_idx: int, max_retries: int) -> JobRow:
    page = await ctx.new_page()
    row = JobRow(lang=lang, list_page=list_page_idx, job_url=job_url)
    try:
        await goto_resilient(page, job_url, max_retries=max_retries)
        await handle_cookies(page)
        # essaye JSON-LD d'abord
        data = await parse_job_jsonld(page)
        if data:
            row.title = first_not_empty(data.get("title"), data.get("name"))
            org = data.get("hiringOrganization")
            if isinstance(org, dict):
                row.hiringOrganization = first_not_empty(org.get("name"))
            else:
                row.hiringOrganization = clean_text(org)
            row.company = row.hiringOrganization

            loc = data.get("jobLocation")
            if isinstance(loc, list) and loc:
                loc = loc[0]
            if isinstance(loc, dict):
                address = loc.get("address")
                if isinstance(address, dict):
                    row.location = first_not_empty(
                        address.get("addressLocality"), address.get("addressRegion"), address.get("addressCountry")
                    )
                else:
                    row.location = clean_text(str(address))
            else:
                row.location = clean_text(str(loc))

            row.datePosted = clean_text(data.get("datePosted"))
            row.employmentType = clean_text(data.get("employmentType"))
            identifier = data.get("identifier")
            if isinstance(identifier, dict):
                row.identifier = first_not_empty(identifier.get("value"), identifier.get("name"))
            else:
                row.identifier = clean_text(str(identifier))
            # salaire
            base = data.get("baseSalary")
            if isinstance(base, dict):
                out = []
                with contextlib.suppress(Exception):
                    v = base.get("value")
                    if isinstance(v, dict):
                        out.append(str(v.get("value")))
                        out.append(str(v.get("unitText")))
                with contextlib.suppress(Exception):
                    out.append(str(base.get("currency")))
                row.baseSalary = clean_text(" ".join([x for x in out if x and x != "None"]))
            row.jobLocationType = clean_text(data.get("jobLocationType"))
            # description : retirer html
            desc = data.get("description")
            if isinstance(desc, str):
                # supprimer tags HTML basiques si présents
                row.description_text = clean_text(re.sub(r"<[^>]+>", " ", desc))
        # fallback DOM si incomplet
        if not row.title or not row.description_text:
            dom = await parse_job_dom(page)
            row.title = row.title or clean_text(dom.get("title"))
            comp = dom.get("hiringOrganization")
            if comp:
                row.hiringOrganization = row.hiringOrganization or clean_text(comp)
                row.company = row.company or row.hiringOrganization
            row.location = row.location or clean_text(dom.get("jobLocation"))
            if not row.description_text:
                row.description_text = clean_text(dom.get("description"))

    finally:
        with contextlib.suppress(Exception):
            await page.close()
    return row


# --------------------------- CSV Snapshot & Reprise ---------------------------

CSV_FIELDS = [
    "lang",
    "list_page",
    "job_url",
    "title",
    "company",
    "location",
    "datePosted",
    "employmentType",
    "identifier",
    "hiringOrganization",
    "industry",
    "workHours",
    "baseSalary",
    "jobLocationType",
    "description_text",
]


def read_existing_latest(latest_path: Path) -> Tuple[List[Dict[str, str]], Set[str]]:
    rows: List[Dict[str, str]] = []
    seen: Set[str] = set()
    if latest_path.exists() and latest_path.stat().st_size > 0:
        try:
            with latest_path.open("r", newline='', encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for r in reader:
                    rows.append(r)
                    if r.get("job_url"):
                        seen.add(r["job_url"])
        except Exception as e:
            log_info(f"⚠️ Impossible de relire le snapshot: {e}")
    return rows, seen


def write_csv(path: Path, items: List[JobRow]) -> None:
    # append ou write selon existance
    write_header = not path.exists() or path.stat().st_size == 0
    with path.open("a", newline='', encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        if write_header:
            w.writeheader()
        for it in items:
            w.writerow(asdict(it))


def write_latest_snapshot(path: Path, all_rows: List[Dict[str, str]]) -> None:
    with path.open("w", newline='', encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        w.writeheader()
        for r in all_rows:
            # ne garder que les champs connus
            w.writerow({k: r.get(k, "") for k in CSV_FIELDS})


# --------------------------- Orchestration ---------------------------

async def process_range_for_lang(browser: Browser, lang: str, search_url_tpl: str, start: int, end: int,
                                 out_prefix: Path, throttle: float, concurrency: int, max_retries: int,
                                 resume_rows: List[Dict[str, str]], seen_urls: Set[str]) -> List[Dict[str, str]]:
    # contexte dédié à la langue
    context = await make_context(browser, lang)

    # accumulateur
    all_rows: List[Dict[str, str]] = list(resume_rows) if resume_rows else []

    latest_path = out_prefix.parent / f"{out_prefix.name}_latest.csv"

    # Sem pour détails
    sem = asyncio.Semaphore(concurrency)

    async def scrape_one(u: str, page_idx: int) -> Optional[JobRow]:
        async with sem:
            try:
                return await scrape_job_detail(context, lang, u, page_idx, max_retries)
            except Exception as e:
                log_info(f"⚠️ Erreur détail: {e}")
                return None

    for i, page_num in enumerate(range(start, end + 1), start=1):
        pct = (i / (end - start + 1)) * 100
        log_info(f"📄 Page {page_num - start + 1}/{end - start + 1} ({pct:.1f}%) – {len([r for r in all_rows if r.get('lang')==lang])} offres cumulées [{lang}]")
        list_url = search_url_tpl.format(page=page_num)
        log_info(f"[LIST] {list_url}")

        list_page: Optional[Page] = None
        try:
            list_page = await context.new_page()
            await goto_resilient(list_page, list_url, max_retries=max_retries)
            await handle_cookies(list_page)

            links = await extract_list_links(list_page)
            new_links = [u for u in links if u not in seen_urls]
            for u in new_links:
                seen_urls.add(u)
            log_info(f"  → {len(links)} liens détectés, {len(new_links)} nouveaux")

            # scrape détails en parallèle
            tasks = [asyncio.create_task(scrape_one(u, page_num)) for u in new_links]
            results = [r for r in await asyncio.gather(*tasks) if r]

            # enregistrement incrémental (fichier final et snapshot)
            if results:
                # append vers {out_prefix}_{start}-{end}.csv => pas encore, on fera à la fin
                # mais snapshot latest immédiat
                for r in results:
                    all_rows.append({k: getattr(r, k) for k in CSV_FIELDS})
                # snapshot latest
                write_latest_snapshot(latest_path, all_rows)
                log_info(f"💾 Snapshot: {len(all_rows)} lignes → {latest_path}")

        except Exception as e:
            log_info(f"⚠️ Erreur chargement page liste {page_num}: {e}\nCall log:\n  - navigating to \"{list_url}\", waiting until \"domcontentloaded\"")
        finally:
            with contextlib.suppress(Exception):
                if list_page:
                    await list_page.close()

        # throttle entre pages de liste
        await asyncio.sleep(throttle)

    # close context langue
    with contextlib.suppress(Exception):
        await context.close()

    return all_rows


async def main_async(args: argparse.Namespace) -> None:
    out_prefix = Path(args.out_prefix)
    out_prefix.parent.mkdir(parents=True, exist_ok=True)

    start_page = int(args.start_page)
    end_page = int(args.end_page)
    if end_page < start_page:
        raise SystemExit("--end-page doit être ≥ --start-page")

    # Fichiers out
    latest_path = out_prefix.parent / f"{out_prefix.name}_latest.csv"
    final_path = out_prefix.parent / f"{out_prefix.name}_{start_page}-{end_page}.csv"

    # Reprise
    resume_rows, seen = read_existing_latest(latest_path)

    langs = [x.strip().lower() for x in args.languages.split(",") if x.strip()]
    log_info(f"🌐 Langues: {', '.join(langs)} – Concurrency: {args.concurrency} – Throttle: {args.throttle}s – Retries: {args.max_retries}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=not args.show)

        # Itération par langue
        all_rows: List[Dict[str, str]] = resume_rows
        for lg in langs:
            all_rows = await process_range_for_lang(
                browser=browser,
                lang=lg,
                search_url_tpl=args.search_url,
                start=start_page,
                end=end_page,
                out_prefix=out_prefix,
                throttle=args.throttle,
                concurrency=args.concurrency,
                max_retries=args.max_retries,
                resume_rows=all_rows,
                seen_urls=seen,
            )

        # écriture du fichier final
        # On réécrit proprement toutes les lignes triées par langue puis page
        rows_ordered = sorted(all_rows, key=lambda r: (r.get("lang",""), int(r.get("list_page", 0))))
        with final_path.open("w", newline='', encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=CSV_FIELDS)
            w.writeheader()
            for r in rows_ordered:
                w.writerow({k: r.get(k, "") for k in CSV_FIELDS})

        log_info(f"✅ Terminé: {len(rows_ordered)} lignes → {final_path}")


# --------------------------- CLI ---------------------------

def build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Scraper Stepstone (Playwright)")
    p.add_argument("--search-url", required=True, help="URL template avec {page} (ex: https://www.stepstone.be/emplois?searchOrigin=Resultlist_top-search&page={page})")
    p.add_argument("--start-page", type=int, required=True)
    p.add_argument("--end-page", type=int, required=True)
    p.add_argument("--languages", default="fr,nl", help="Langues à utiliser (locales/Accept-Language) séparées par virgule. Ex: fr,nl")
    p.add_argument("--out-prefix", required=True, help="Préfixe de sortie (sans extension)")
    p.add_argument("--throttle", type=float, default=0.8, help="Pause (secondes) entre pages de liste")
    p.add_argument("--concurrency", type=int, default=4, help="Nb. max de jobs (pages détail) en parallèle")
    p.add_argument("--max-retries", type=int, default=4, help="Nb. de retries pour goto_resilient")
    p.add_argument("--show", action="store_true", help="Afficher le navigateur (headful)")
    return p


def main() -> None:
    parser = build_argparser()
    args = parser.parse_args()
    try:
        asyncio.run(main_async(args))
    except KeyboardInterrupt:
        log_info("🛑 Interrompu par l'utilisateur")
        sys.exit(130)


if __name__ == "__main__":
    main()
