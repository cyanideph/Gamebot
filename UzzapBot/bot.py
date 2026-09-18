"""Pydroid entry point for UzzapBot."""
from __future__ import annotations

import logging
import time

from config import BOT_NAME, ADMIN_IDS, ADMIN_USERNAMES, POLL_SECONDS, validate
from database import Database
from game_engine import GameEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger("uzzapbot")

HELP = """[c03]UZZAPBOT GAME COMMANDS
[c01]!game start math
!game start trivia
!game start anime
!game start gtaopm
!game start gtaforeign
!game start logic
!game start wordhunt
!game start tagalog
!game start twist
!game start algebra1
!game start algebra2
!game start algebra3
!game stop
!game pause
!game resume
!game next
!game clue
!game repost
!game status
!game score
!game leaderboard"""


def is_admin(msg: dict) -> bool:
    uid = str(msg.get("sender_id") or "")
    username = str(msg.get("sender") or "").casefold()
    return uid in ADMIN_IDS or username in ADMIN_USERNAMES


def main() -> None:
    validate()
    db = Database()
    games = GameEngine()
    log.info("%s connected; polling every %.1fs", BOT_NAME, POLL_SECONDS)

    while True:
        try:
            for msg in db.poll_messages():
                room = str(msg.get("room_name") or "").strip()
                text = str(msg.get("body") or "").strip()
                username = str(msg.get("sender") or "").strip()
                uid = str(msg.get("sender_id") or "")
                if not room or not text:
                    continue

                # Active games accept normal player answers before command parsing.
                session = games.get(room)
                if session and not text.lower().startswith("!game") and not text.startswith("/"):
                    profile = db.profile(uid, username) or {}
                    nickname = str(profile.get("nickname") or username)
                    _, response = games.answer(room, uid, username, nickname, text)
                    if response:
                        db.send(room, response)
                        continue

                if not text.lower().startswith("!game"):
                    continue
                if not is_admin(msg):
                    db.send(room, "[c08]Game controls are admin-only during testing.")
                    continue

                args = text.split()
                sub = args[1].casefold() if len(args) > 1 else "help"

                if sub == "help":
                    db.send(room, HELP)
                elif sub == "start":
                    game = args[2] if len(args) > 2 else "math"
                    points = int(args[3]) if len(args) > 3 and args[3].isdigit() else None
                    limit = int(args[4]) if len(args) > 4 and args[4].isdigit() else None
                    s = games.start(room, game, points or None or 10, limit or None or 100)
                    db.send(room, games.repost(room))
                elif sub == "stop":
                    games.stop(room); db.send(room, "[c08]Game stopped.")
                elif sub == "pause":
                    s = games.get(room)
                    if s: s.paused = True
                    db.send(room, "[c12]Game paused.")
                elif sub == "resume":
                    s = games.get(room)
                    if s: s.paused = False
                    db.send(room, "[c10]Game resumed.\n" + games.repost(room))
                elif sub == "next":
                    s = games.get(room); db.send(room, games.next_question(s) if s else "[c08]No active game.")
                elif sub == "clue": db.send(room, games.clue(room))
                elif sub == "repost": db.send(room, games.repost(room))
                elif sub == "status": db.send(room, games.status(room))
                elif sub in {"score", "leaderboard"}: db.send(room, games.leaderboard_text(room))
                else: db.send(room, "[c08]Unknown game command. Use !game help")

            time.sleep(POLL_SECONDS)
        except KeyboardInterrupt:
            log.info("Bot stopped by user")
            return
        except Exception:
            log.exception("Bot loop error; reconnecting")
            time.sleep(max(POLL_SECONDS, 2.0))


if __name__ == "__main__":
    main()
