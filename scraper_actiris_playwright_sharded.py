import asyncio, argparse, os, re, time, json, random
from datetime import datetime
import pandas as pd
from playwright.async_api import async_playwright

BASE = "https://www.actiris.brussels"
LIST_TPL = "https://www.actiris.brussels/fr/citoyens/offres-d-emploi/?localisation=Tout&keywordSearchType=Partout&page={page}"
DETAIL_SUBSTR = "/detail-offre-d-emploi/?reference="

def clean(s):
    if not s: return None
    return re.sub(r"\s+", " ", s).strip()

def ensure_dir(p):
    os.makedirs(p, exist_ok=True)

async def run_shard(start_page:int, end_page:int, out_prefix:str,
                    throttle:float=0.6, max_concurrency:int=6):
    """
    Scrape un intervalle [start_page, end_page].
    Sauvegarde un snapshot CSV après chaque page + un CSV final du shard.
    """
    ensure_dir("data/raw")
    snapshot = f"{out_prefix}_latest.csv"         # écrasé après chaque page
    finalcsv = f"{out_prefix}_{start_page}-{end_page}.csv"
    finalparq = f"{out_prefix}_{start_page}-{end_page}.parquet"

    # Reprise
    rows = []
    seen_refs = set()
    if os.path.exists(snapshot):
        try:
            prev = pd.read_csv(snapshot, dtype=str).fillna("")
            rows = prev.to_dict(orient="records")
            seen_refs = {r.get("reference","") for r in rows if r.get("reference")}
            print(f"↻ Reprise: {len(rows)} lignes, {len(seen_refs)} refs uniques déjà chargées depuis {snapshot}")
        except Exception as e:
            print(f"⚠️ Impossible de relire le snapshot: {e}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"),
            locale="fr-FR",
        )

        # ⚡ Bloque images, fonts, css pour accélérer
        async def route_block(route):
            req = route.request
            if req.resource_type in ("image", "font", "stylesheet"):
                await route.abort()
            else:
                await route.continue_()
        await context.route("**/*", route_block)

        page = await context.new_page()

        for pg in range(start_page, end_page + 1):
            list_url = LIST_TPL.format(page=pg)
            print(f"[LIST] {list_url}")
            try:
                await page.goto(list_url, wait_until="networkidle", timeout=60000)
            except Exception as e:
                print(f"⚠️ Erreur page liste {pg}: {e}")
                continue

            # Récupère liens de fiches
            anchors = await page.locator("a").all()
            detail_urls = []
            for a in anchors:
                href = await a.get_attribute("href")
                if href and DETAIL_SUBSTR in href:
                    if href.startswith("/"):
                        href = BASE + href
                    detail_urls.append(href)
            detail_urls = sorted(set(detail_urls))
            print(f"  → {len(detail_urls)} offres trouvées (page {pg})")

            # Concurrence contrôlée
            sem = asyncio.Semaphore(max_concurrency)

            async def scrape_detail(u):
                async with sem:
                    d = await context.new_page()
                    try:
                        await d.goto(u, wait_until="domcontentloaded", timeout=60000)

                        # Titre: premier heading visible (évite “strict mode h1”)
                        title = None
                        try:
                            title = await d.get_by_role("heading").first.text_content()
                            title = clean(title)
                        except:
                            try:
                                title = clean(await d.locator("h1").first.text_content())
                            except:
                                title = None

                        body_txt = clean(await d.locator("body").inner_text())

                        def after(label):
                            m = re.search(fr"{label}\s*:\s*([^\n\r]+)", body_txt, re.IGNORECASE)
                            return clean(m.group(1)) if m else None

                        ref = None
                        mref = re.search(r"Référence\s+(\d+)", body_txt)
                        if mref:
                            ref = mref.group(1)

                        created = None
                        mdate = re.search(r"Créé\s+le\s+([0-9]{2}\s\w+\s[0-9]{4})", body_txt, re.IGNORECASE)
                        if mdate:
                            created = mdate.group(1)

                        lieu   = after("Lieu")
                        temps  = after("Temps de travail")
                        contrat= after("Type de contrat")
                        famille= after("Famille de métiers")

                        desc = None
                        mdesc = re.search(
                            r"(Description de la fonction.*?)(Famille de métiers|Compétences|Profil|Avantages|Postuler|$)",
                            body_txt, re.IGNORECASE | re.DOTALL
                        )
                        if mdesc:
                            desc = clean(mdesc.group(1).replace("Description de la fonction",""))

                        record = {
                            "url": u, "reference": ref, "title": title, "created": created,
                            "lieu": lieu, "temps_travail": temps, "type_contrat": contrat,
                            "famille_metiers": famille, "description": desc, "page": pg
                        }

                        key = ref or f"{title}|{lieu}|{u}"
                        if ref and ref in seen_refs:
                            pass
                        else:
                            rows.append(record)
                            if ref: seen_refs.add(ref)

                        await d.close()
                        # Throttle + jitter
                        await asyncio.sleep(throttle + random.uniform(0, 0.3))
                    except Exception as e:
                        print(f"  ⚠️ Erreur fiche {u}: {e}")
                        try: await d.close()
                        except: pass
                        await asyncio.sleep(throttle)

            await asyncio.gather(*[scrape_detail(u) for u in detail_urls])

            # Snapshot après chaque page
            df = pd.DataFrame(rows).fillna("")
            df = df.drop_duplicates(subset=["reference", "title", "lieu", "url"], keep="first")
            df.to_csv(snapshot, index=False)
            print(f"💾 Snapshot: {len(df)} lignes → {snapshot}")

            # Petites pauses entre pages
            await asyncio.sleep(0.5)

        await context.close()
        await browser.close()

    # Fichiers finaux du shard
    df = pd.DataFrame(rows).fillna("")
    df = df.drop_duplicates(subset=["reference", "title", "lieu", "url"], keep="first")
    df.to_csv(finalcsv, index=False)
    try:
        df.to_parquet(finalparq, index=False)
    except Exception as e:
        print("⚠️ Parquet non écrit (pyarrow non installé ?):", e)
    print(f"✅ Shard terminé: {len(df)} lignes → {finalcsv}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--start-page", type=int, required=True)
    ap.add_argument("--end-page", type=int, required=True)
    ap.add_argument("--out-prefix", type=str, default="data/raw/actiris")
    ap.add_argument("--throttle", type=float, default=0.6)
    ap.add_argument("--concurrency", type=int, default=6)
    args = ap.parse_args()

    os.makedirs("data/raw", exist_ok=True)
    asyncio.run(run_shard(
        start_page=args.start_page,
        end_page=args.end_page,
        out_prefix=args.out_prefix,
        throttle=args.throttle,
        max_concurrency=args.concurrency
    ))
