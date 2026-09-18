from __future__ import annotations
import asyncio, logging
from pathlib import Path
from .config import load_config
from .supabase_store import UzzapStore
from .engine import GameManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
log=logging.getLogger('uzzapbot')

async def main() -> None:
    cfg=load_config()
    store=UzzapStore(cfg.supabase_url,cfg.supabase_key,cfg.bot_name)
    await store.connect()
    last=await store.latest_id()
    log.info('Connected. Starting after room_messages id=%s', last)
    # main.py is repo/uzzapbot/bot/main.py; datasets live in the repository root.
    data_root=Path(__file__).resolve().parents[2]
    manager=GameManager(cfg,store,data_root)
    while True:
        try:
            messages=await store.poll_messages(last)
            for msg in messages:
                last=max(last,int(msg['id']))
                if str(msg.get('sender') or '').casefold()==cfg.bot_name.casefold(): continue
                if cfg.bot_sender_id and str(msg.get('sender_id') or '')==cfg.bot_sender_id: continue
                handled=await manager.command(msg)
                if handled: continue
                room=str(msg.get('room_name') or '')
                game=manager.sessions.get(room)
                if game and game.started:
                    await manager.handle_answer(msg,game)
        except asyncio.CancelledError:
            raise
        except Exception:
            log.exception('Bot loop error; retrying')
            await asyncio.sleep(max(2.0,cfg.poll_seconds*2))
        await asyncio.sleep(cfg.poll_seconds)

if __name__=='__main__':
    asyncio.run(main())
