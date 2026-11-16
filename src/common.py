"""Cấu hình chung Day 7: kết nối vector store Day 6 (pgvector, bảng chunks_b)."""
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
DAY6 = ROOT.parent.parent / "Day6" / "Lab6" / "starter"
load_dotenv(DAY6 / ".env")      # DATABASE_URL, OPENAI_API_KEY (không in/không commit)
load_dotenv(ROOT / ".env")      # ghi đè nếu có

TABLE = "chunks_b"              # Day 6 chiến lược B: by_paragraph(max_size=500)
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"   # embedding Day 6, 384 chiều
DATA = ROOT / "data"
RESULTS = ROOT / "results"


def db_url():
    return os.environ["DATABASE_URL"]
