"""Small Supabase adapter for the Pydroid bot."""
from __future__ import annotations

import time
from typing import Any
from supabase import create_client
from config import SUPABASE_URL, SUPABASE_KEY, BOT_SENDER_ID, BOT_NAME


class Database:
    def __init__(self) -> None:
        self.client = create_client(SUPABASE_URL, SUPABASE_KEY)
        self.last_id = self._latest_id()

    def _latest_id(self) -> int:
        r = self.client.table("room_messages").select("id").order("id", desc=True).limit(1).execute()
        rows = r.data or []
        return int(rows[0]["id"]) if rows else 0

    def poll_messages(self) -> list[dict[str, Any]]:
        r = (self.client.table("room_messages").select("id,room_name,sender,body,is_system,created_at,sender_id")
             .gt("id", self.last_id).order("id").limit(100).execute())
        rows = r.data or []
        if rows:
            self.last_id = max(int(x["id"]) for x in rows)
        return [x for x in rows if str(x.get("sender_id") or "") != BOT_SENDER_ID and str(x.get("sender") or "").lower() != BOT_NAME.lower()]

    def send(self, room_name: str, body: str) -> None:
        self.client.table("room_messages").insert({
            "room_name": room_name,
            "sender": BOT_NAME,
            "body": body,
            "is_system": True,
            "sender_id": BOT_SENDER_ID,
        }).execute()

    def profile(self, user_id: str | None, username: str | None) -> dict[str, Any] | None:
        if user_id:
            r = self.client.table("profiles").select("id,username,nickname").eq("id", user_id).limit(1).execute()
            if r.data:
                return r.data[0]
        if username:
            r = self.client.table("profiles").select("id,username,nickname").eq("username", username).limit(1).execute()
            if r.data:
                return r.data[0]
        return None
