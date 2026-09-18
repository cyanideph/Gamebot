from __future__ import annotations
import asyncio
from datetime import datetime, timezone
from typing import Any, Callable, Awaitable
from supabase import acreate_client, AsyncClient

MessageHandler = Callable[[dict[str, Any]], Awaitable[None]]

class UzzapStore:
    def __init__(self, url: str, key: str, bot_name: str):
        self.url, self.key, self.bot_name = url, key, bot_name
        self.client: AsyncClient | None = None
        self._last_id = 0

    async def connect(self) -> None:
        self.client = await acreate_client(self.url, self.key)

    def _require(self) -> AsyncClient:
        if self.client is None:
            raise RuntimeError('Supabase client is not connected')
        return self.client

    async def latest_id(self) -> int:
        c = self._require()
        r = await c.table('room_messages').select('id').order('id', desc=True).limit(1).execute()
        return int(r.data[0]['id']) if r.data else 0

    async def poll_messages(self, after_id: int, limit: int = 100) -> list[dict[str, Any]]:
        c = self._require()
        r = await (c.table('room_messages').select('id,room_name,sender,body,is_system,created_at,sender_id')
                   .gt('id', after_id).order('id').limit(limit).execute())
        return r.data or []

    async def send(self, room: str, body: str, sender_id: str | None = None) -> dict[str, Any]:
        c = self._require()
        row = {
            'room_name': room,
            'sender': self.bot_name,
            'body': body,
            'is_system': True,
        }
        if sender_id:
            row['sender_id'] = sender_id
        r = await c.table('room_messages').insert(row).execute()
        return r.data[0] if r.data else row

    async def profile(self, sender_id: str | None, username: str | None) -> dict[str, Any] | None:
        c = self._require()
        if sender_id:
            r = await c.table('profiles').select('id,username,nickname').eq('id', sender_id).limit(1).execute()
            if r.data: return r.data[0]
        if username:
            r = await c.table('profiles').select('id,username,nickname').eq('username', username).limit(1).execute()
            if r.data: return r.data[0]
        return None
