from __future__ import annotations
import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Config:
    supabase_url: str
    supabase_key: str
    bot_name: str
    bot_sender_id: str | None
    admin_ids: frozenset[str]
    admin_usernames: frozenset[str]
    poll_seconds: float
    default_points: int
    default_limit: int


def _csv(name: str) -> frozenset[str]:
    return frozenset(x.strip().lower() for x in os.getenv(name, '').split(',') if x.strip())


def load_config() -> Config:
    url = os.getenv('SUPABASE_URL', '').strip()
    key = os.getenv('SUPABASE_KEY', '').strip()
    if not url or not key:
        raise RuntimeError('SUPABASE_URL and SUPABASE_KEY are required')
    return Config(
        supabase_url=url,
        supabase_key=key,
        bot_name=os.getenv('BOT_NAME', 'uzzapbot').strip(),
        bot_sender_id=os.getenv('BOT_SENDER_ID', '').strip() or None,
        admin_ids=_csv('ADMIN_IDS'),
        admin_usernames=_csv('ADMIN_USERNAMES'),
        poll_seconds=max(0.25, float(os.getenv('POLL_SECONDS', '1.0'))),
        default_points=max(1, int(os.getenv('DEFAULT_POINTS', '10'))),
        default_limit=max(1, int(os.getenv('DEFAULT_LIMIT', '100'))),
    )
