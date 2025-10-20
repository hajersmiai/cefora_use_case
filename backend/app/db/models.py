from __future__ import annotations
from sqlalchemy.orm import declarative_base, Mapped, mapped_column
from sqlalchemy import String, Integer, DateTime, Text, UniqueConstraint, JSON
from datetime import datetime

Base = declarative_base()

class JobPosting(Base):
    __tablename__ = "job_postings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(String(50), index=True)
    job_url: Mapped[str] = mapped_column(Text)
    url_hash: Mapped[str] = mapped_column(String(64), index=True)

    title: Mapped[str] = mapped_column(String(300))
    company: Mapped[str] = mapped_column(String(300), index=True, default="")
    location_raw: Mapped[str] = mapped_column(String(300), default="")
    region: Mapped[str] = mapped_column(String(100), index=True, default="")
    country: Mapped[str] = mapped_column(String(100), default="Belgium")

    posted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    scraped_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    description: Mapped[str] = mapped_column(Text, default="")
    contract_type: Mapped[str] = mapped_column(String(80), default="")
    salary_raw: Mapped[str] = mapped_column(String(120), default="")

    sector: Mapped[str] = mapped_column(String(120), default="")
    profession: Mapped[str] = mapped_column(String(120), default="")
    skills: Mapped[dict] = mapped_column(JSON, default={})

    __table_args__ = (
        UniqueConstraint("source", "url_hash", name="uix_source_urlhash"),
    )
