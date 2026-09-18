"""Configuration for the Pydroid UzzapBot."""
from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")

SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip()
BOT_NAME = os.getenv("BOT_NAME", "uzzapbot").strip()
BOT_SENDER_ID = os.getenv("BOT_SENDER_ID", "").strip()
ADMIN_IDS = {x.strip() for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()}
ADMIN_USERNAMES = {x.strip().lower() for x in os.getenv("ADMIN_USERNAMES", "").split(",") if x.strip()}
POLL_SECONDS = float(os.getenv("POLL_SECONDS", "1.0"))
DEFAULT_POINTS = int(os.getenv("DEFAULT_POINTS", "10"))
DEFAULT_LIMIT = int(os.getenv("DEFAULT_LIMIT", "100"))
DATA_DIR = ROOT / "data"


def validate() -> None:
    missing = [name for name, value in (("SUPABASE_URL", SUPABASE_URL), ("SUPABASE_KEY", SUPABASE_KEY), ("BOT_SENDER_ID", BOT_SENDER_ID)) if not value]
    if missing:
        raise RuntimeError("Missing configuration: " + ", ".join(missing))
