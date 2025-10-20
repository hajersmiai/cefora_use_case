from __future__ import annotations
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from db.database import SessionLocal
from db.models import JobPosting

class Writer:
    def __init__(self):
        self.db = SessionLocal()

    def upsert_job(self, item: dict) -> bool:
        job = JobPosting(**item)
        self.db.add(job)
        try:
            self.db.commit()
            return True
        except IntegrityError:
            self.db.rollback()
            return False

    def close(self):
        self.db.close()
