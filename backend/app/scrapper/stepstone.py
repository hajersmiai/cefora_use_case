from __future__ import annotations
from bs4 import BeautifulSoup
from datetime import datetime
from .base import BaseScraper
from .normalizer import url_hash, normalize_region, extract_skills

class StepstoneScraper(BaseScraper):
    source = "stepstone"

    def search_urls(self, query: str, location: str = "Belgium", pages: int = 1) -> list[str]:
        # StepStone search uses q / location params; exact pattern may vary by locale.
        base = "https://www.stepstone.be/en/jobs/"
        urls = []
        for p in range(1, pages + 1):
            urls.append(f"{base}?q={query.replace(' ', '+')}&location={location.replace(' ','+')}?page={p}")
        return urls

    def parse(self, html: str):
        soup = BeautifulSoup(html, "lxml")
        # The exact class names can change; these are safe-ish fallback patterns
        cards = soup.select("[data-at='job-item']") or soup.select("article")
        for c in cards:
            a = c.select_one("a[href*='/job/']")
            if not a: 
                continue
            href = a.get("href")
            title = (a.get_text() or "").strip()
            company = (c.select_one("[data-at='job-item-company-name']") or c.select_one(".company")).get_text(strip=True) if (c.select_one("[data-at='job-item-company-name']") or c.select_one(".company")) else ""
            loc = (c.select_one("[data-at='job-item-location']") or c.select_one(".location")).get_text(strip=True) if (c.select_one("[data-at='job-item-location']") or c.select_one(".location")) else ""
            desc = (c.select_one("[data-at='job-item-description']") or c.select_one(".description")).get_text(" ", strip=True) if (c.select_one("[data-at='job-item-description']") or c.select_one(".description")) else ""

            yield {
                "source": self.source,
                "job_url": href,
                "url_hash": url_hash(href),
                "title": title[:300],
                "company": company[:300],
                "location_raw": loc[:300],
                "region": normalize_region(loc),
                "country": "Belgium",
                "posted_at": None,  # filled on detail page if needed
                "scraped_at": datetime.utcnow(),
                "description": desc,
                "contract_type": "",
                "salary_raw": "",
                "sector": "",
                "profession": "",
                "skills": extract_skills(f"{title} {desc}"),
            }
