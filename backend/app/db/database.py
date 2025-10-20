from __future__ import annotations
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

# If DB_URL is not provided, default to local SQLite file
DB_URL = os.getenv("DB_URL", f"sqlite:///{Path(__file__).resolve().parents[1] / 'vacaviz.db'}")

# SQLite needs check_same_thread=False for multi-module use
connect_args = {"check_same_thread": False} if DB_URL.startswith("sqlite") else {}

engine = create_engine(DB_URL, pool_pre_ping=True, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()