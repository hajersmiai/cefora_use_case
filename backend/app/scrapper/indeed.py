from __future__ import annotations
from bs4 import BeautifulSoup
from datetime import datetime
from .base import BaseScraper
from .normalizer import url_hash, normalize_region, extract_skills

class IndeedScraper(BaseScraper):
    source = "indeed"

    def search_urls(self, query: str, location: str = "Belgium", pages: int = 1) -> list[str]:
        base = "https://be.indeed.com/jobs"
        urls = []
        for p in range(pages):
            start = p * 10
            urls.append(f"{base}?q={query.replace(' ','+')}&l={location.replace(' ','+')}&start={start}")
        return urls

    def parse(self, html: str):
        soup = BeautifulSoup(html, "lxml")
        cards = soup.select("a[data-jk], .job_seen_beacon")
        for c in cards:
            a = c if c.name == "a" else c.select_one("a[href]")
            if not a:
                continue
            href = a.get("href")
            if href and href.startswith("/"):
                href = "https://be.indeed.com" + href
            title = (a.get_text() or "").strip()
            company = (c.select_one(".companyName") or c.select_one("[data-company-name]"))
            company = company.get_text(strip=True) if company else ""
            loc = (c.select_one(".companyLocation") or c.select_one("[data-testid='text-location']")).get_text(strip=True) if (c.select_one(".companyLocation") or c.select_one("[data-testid='text-location'])) else ""
            desc = (c.select_one(".job-snippet") or c.select_one("[data-testid='snippet']")).get_text(" ", strip=True) if (c.select_one(".job-snippet") or c.select_one("[data-testid='snippet'])) else ""

            yield {
                "source": self.source,
                "job_url": href,
                "url_hash": url_hash(href),
                "title": title[:300],
                "company": company[:300],
                "location_raw": loc[:300],
                "region": normalize_region(loc),
                "country": "Belgium",
                "posted_at": None,
                "scraped_at": datetime.utcnow(),
                "description": desc,
                "contract_type": "",
                "salary_raw": "",
                "sector": "",
                "profession": "",
                "skills": extract_skills(f"{title} {desc}"),
            }