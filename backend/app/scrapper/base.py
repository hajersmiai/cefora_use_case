from __future__ import annotations
import os, random, time
from typing import Iterable, Dict
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from tenacity import retry, stop_after_attempt, wait_exponential_jitter

TIMEOUT = int(os.getenv("HTTP_TIMEOUT", "20"))
DELAY_MIN = float(os.getenv("REQUEST_DELAY_MIN", "1.0"))
DELAY_MAX = float(os.getenv("REQUEST_DELAY_MAX", "2.5"))
PROXY_URL = os.getenv("PROXY_URL") or None

ua = UserAgent()

def _headers():
    return {"User-Agent": ua.random, "Accept-Language": "en;q=0.9,fr;q=0.8,nl;q=0.8"}

class BaseScraper:
    source = "base"

    def __init__(self, writer, session: requests.Session | None = None):
        self.writer = writer
        self.session = session or requests.Session()
        if PROXY_URL:
            self.session.proxies.update({"http": PROXY_URL, "https": PROXY_URL})

    def polite_wait(self):
        time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))

    @retry(stop=stop_after_attempt(3), wait=wait_exponential_jitter(1, 3))
    def get(self, url: str) -> requests.Response:
        resp = self.session.get(url, headers=_headers(), timeout=TIMEOUT)
        resp.raise_for_status()
        return resp

    def parse(self, html: str) -> Iterable[Dict]:
        """Override in child class."""
        raise NotImplementedError

    def run(self, urls: list[str]) -> int:
        saved = 0
        for url in urls:
            self.polite_wait()
            r = self.get(url)
            jobs = self.parse(r.text)
            for item in jobs:
                ok = self.writer.upsert_job(item)
                saved += int(ok)
        return saved
