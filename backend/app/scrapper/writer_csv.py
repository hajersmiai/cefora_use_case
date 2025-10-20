from __future__ import annotations
import csv, os
from pathlib import Path

class CsvWriter:
    def __init__(self, path: str | None = None):
        self.path = Path(path or "scraped_jobs.csv")
        self.fieldnames = ["source","job_url","title","company","location_raw","region","country","posted_at","description","contract_type","salary_raw","sector","profession","skills"]
        self._init()

    def _init(self):
        new = not self.path.exists()
        self.f = open(self.path, "a", newline="", encoding="utf-8")
        self.w = csv.DictWriter(self.f, fieldnames=self.fieldnames)
        if new:
            self.w.writeheader()

    def upsert_job(self, item: dict) -> bool:
        # naive append; dedupe happens in DB path; here we just export
        row = {k: item.get(k, "") for k in self.fieldnames}
        self.w.writerow(row); self.f.flush()
        return True

    def close(self):
        self.f.close()
