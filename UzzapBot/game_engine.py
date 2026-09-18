"""Modern, Pydroid-safe game engine inspired by the legacy Gamebot.

The engine is intentionally independent of networking so it can be tested locally.
It supports Uzzap [c01]..[c30] formatting in all generated messages.
"""
from __future__ import annotations

import math
import random
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from config import DATA_DIR, DEFAULT_LIMIT, DEFAULT_POINTS

C_TITLE = "[c03]"
C_TEXT = "[c01]"
C_GOOD = "[c10]"
C_HINT = "[c12]"
C_ERROR = "[c08]"


def clean_answer(value: str) -> str:
    value = value.casefold().strip()
    value = re.sub(r"[^\w\s]", "", value, flags=re.UNICODE)
    return re.sub(r"\s+", " ", value)


def load_lines(name: str) -> list[str]:
    path = DATA_DIR / name
    if not path.exists():
        return []
    return [x.strip() for x in path.read_text(encoding="utf-8", errors="replace").splitlines() if x.strip()]


def load_qa(name: str) -> list[tuple[str, str]]:
    result: list[tuple[str, str]] = []
    for line in load_lines(name):
        parts = line.split(",", 2)
        if len(parts) == 3:
            q = parts[1].strip()
            a = parts[2].strip()
            if q.upper().startswith("Q."):
                q = q[2:].strip()
            result.append((q, a))
    return result


@dataclass
class Player:
    user_id: str
    username: str
    nickname: str
    score: int = 0


@dataclass
class GameSession:
    room: str
    game: str
    points: int = DEFAULT_POINTS
    limit: int = DEFAULT_LIMIT
    players: dict[str, Player] = field(default_factory=dict)
    question: str = ""
    answers: set[str] = field(default_factory=set)
    display_answer: str = ""
    used: set[int] = field(default_factory=set)
    paused: bool = False
    started_at: float = field(default_factory=time.time)

    def add_player(self, user_id: str, username: str, nickname: str) -> Player:
        if user_id not in self.players:
            self.players[user_id] = Player(user_id, username, nickname)
        return self.players[user_id]

    def leaderboard(self) -> list[Player]:
        return sorted(self.players.values(), key=lambda p: (-p.score, p.nickname.casefold()))


class GameEngine:
    ALIASES = {
        "math": "math", "addition": "math", "mathminus": "mathminus", "minus": "mathminus",
        "mathmultiply": "mathmultiply", "multiply": "mathmultiply", "algebra1": "algebra1",
        "algebra2": "algebra2", "algebra3": "algebra3", "trivia": "trivia", "gen-info-trivia": "trivia",
        "anime": "anime", "animetrivia": "anime", "gtaopm": "gtaopm", "gta-foreign": "gtaforeign",
        "gtaforeign": "gtaforeign", "logic": "logic", "wordhunt": "wordhunt", "english": "wordhunt",
        "tagalog": "tagalog", "twist": "twist", "texttwist": "twist",
    }

    def __init__(self) -> None:
        self.sessions: dict[str, GameSession] = {}
        self.datasets: dict[str, list] = {}
        self._load()

    def _load(self) -> None:
        self.datasets["trivia"] = load_qa("Zgen-info.txt")
        self.datasets["anime"] = load_qa("Zanime-trivia.txt")
        self.datasets["gtaforeign"] = load_qa("Zgta-foreign.txt")
        self.datasets["gtaopm"] = load_qa("Zgta-opm.txt")
        self.datasets["logic"] = load_qa("Zlogic.txt")
        self.datasets["wordhunt"] = load_lines("words.txt")
        self.datasets["tagalog"] = load_lines("salita.txt")

    def normalize_game(self, name: str) -> str:
        key = name.strip().casefold().replace("_", "-")
        return self.ALIASES.get(key, key)

    def start(self, room: str, name: str, points: int = DEFAULT_POINTS, limit: int = DEFAULT_LIMIT) -> GameSession:
        game = self.normalize_game(name)
        session = GameSession(room, game, points, limit)
        self.sessions[room] = session
        self.next_question(session)
        return session

    def stop(self, room: str) -> GameSession | None:
        return self.sessions.pop(room, None)

    def get(self, room: str) -> GameSession | None:
        return self.sessions.get(room)

    def next_question(self, s: GameSession) -> str:
        if s.game in {"math", "mathminus", "mathmultiply", "algebra1", "algebra2", "algebra3"}:
            q, answers = self._math_question(s.game)
        elif s.game in self.datasets:
            data = self.datasets[s.game]
            if not data:
                q, answers = "Dataset is missing or empty.", {""}
            else:
                available = [i for i in range(len(data)) if i not in s.used]
                if not available:
                    s.used.clear(); available = list(range(len(data)))
                i = random.choice(available); s.used.add(i)
                item = data[i]
                if s.game in {"wordhunt", "tagalog"}:
                    word = str(item); q = f"Unscramble this word: {self._scramble(word)}"; answers = {clean_answer(word)}
                else:
                    q, a = item; answers = {clean_answer(a)}
        elif s.game == "twist":
            words = self.datasets.get("wordhunt", [])
            word = random.choice(words) if words else "PYTHON"
            q = f"Unscramble: {self._scramble(word)}"; answers = {clean_answer(word)}
        else:
            q, answers = self._math_question("math")
        s.question, s.answers = q, answers
        s.display_answer = next(iter(answers), "")
        return f"{C_TITLE}{s.game.upper()}\n{C_TEXT}{q}"

    def _scramble(self, word: str) -> str:
        chars = list(word.upper())
        if len(chars) > 1:
            original = "".join(chars)
            for _ in range(10):
                random.shuffle(chars)
                if "".join(chars) != original:
                    break
        return "".join(chars)

    def _math_question(self, game: str) -> tuple[str, set[str]]:
        a, b = random.randint(1, 50), random.randint(1, 50)
        if game == "mathminus":
            a, b = max(a, b), min(a, b); result = a - b; symbol = "-"
        elif game == "mathmultiply":
            a, b = random.randint(2, 20), random.randint(2, 20); result = a * b; symbol = "×"
        elif game == "algebra1":
            x, k, y = random.randint(1, 20), random.randint(1, 9), random.randint(1, 20); result = x*k + y; return f"{k}x + {y} = {result}  (x=?)", {str(x)}
        elif game == "algebra2":
            x, k, y = random.randint(1, 20), random.randint(1, 9), random.randint(1, 20); result = x*k - y; return f"{k}x - {y} = {result}  (x=?)", {str(x)}
        elif game == "algebra3":
            x, k, y = random.randint(1, 12), random.randint(1, 6), random.randint(1, 12); result = x*k*y; return f"{k} × x × {y} = {result}  (x=?)", {str(x)}
        else:
            result = a + b; symbol = "+"
        return f"{a} {symbol} {b} = ?", {str(result)}

    def answer(self, room: str, user_id: str, username: str, nickname: str, text: str) -> tuple[bool, str | None]:
        s = self.sessions.get(room)
        if not s or s.paused or not s.answers:
            return False, None
        if clean_answer(text) not in s.answers:
            return False, None
        p = s.add_player(user_id, username, nickname)
        p.score += s.points
        message = f"{C_GOOD}{nickname} +{s.points} points!  Score: {p.score}/{s.limit}"
        if p.score >= s.limit:
            message += f"\n{C_GOOD}{nickname} wins!"
            self.sessions.pop(room, None)
            return True, message
        self.next_question(s)
        return True, message + "\n" + f"{C_TEXT}{s.question}"

    def status(self, room: str) -> str:
        s = self.sessions.get(room)
        if not s: return f"{C_ERROR}No game is running in this room."
        return f"{C_TEXT}Game: {s.game}\nPoints: {s.points}\nLimit: {s.limit}\nPlayers: {len(s.players)}\nStatus: {'paused' if s.paused else 'running'}"

    def leaderboard_text(self, room: str) -> str:
        s = self.sessions.get(room)
        if not s: return f"{C_ERROR}No active game."
        rows = [f"{i}. {p.nickname} — {p.score}" for i, p in enumerate(s.leaderboard(), 1)]
        return C_TITLE + "LEADERBOARD\n" + ("\n".join(rows) if rows else C_TEXT + "No players yet.")

    def clue(self, room: str) -> str:
        s = self.sessions.get(room)
        if not s or not s.display_answer: return f"{C_ERROR}No active question."
        a = s.display_answer
        hint = a[:1] + ("_" * max(0, len(a)-1))
        return f"{C_HINT}CLUE: {hint}"

    def repost(self, room: str) -> str:
        s = self.sessions.get(room)
        return f"{C_TEXT}{s.question}" if s else f"{C_ERROR}No active game."
