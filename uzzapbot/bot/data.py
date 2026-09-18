from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import csv, random, re
from .formatting import normalize_answer

@dataclass(frozen=True)
class QA:
    ident: str
    question: str
    answer: str

@dataclass(frozen=True)
class Word:
    word: str

class DataBank:
    def __init__(self, root: Path):
        self.root = root
        self._cache: dict[str, list] = {}

    def _file(self, *names: str) -> Path:
        for name in names:
            p = self.root / name
            if p.exists(): return p
        raise FileNotFoundError(', '.join(names))

    def qa(self, *names: str) -> list[QA]:
        key = '|'.join(names)
        if key in self._cache: return self._cache[key]
        rows: list[QA] = []
        p = self._file(*names)
        for raw in p.read_text(encoding='utf-8', errors='replace').splitlines():
            line = raw.strip()
            if not line or line.startswith('#'): continue
            try:
                parts = next(csv.reader([line]))
            except Exception:
                continue
            if len(parts) >= 3:
                ident, question, answer = parts[0].strip(), parts[1].strip(), ','.join(parts[2:]).strip()
                question = re.sub(r'^Q\.?', '', question, flags=re.I).strip()
                if question and answer: rows.append(QA(ident, question, answer))
        self._cache[key] = rows
        return rows

    def words(self, *names: str) -> list[Word]:
        key = 'WORDS|' + '|'.join(names)
        if key in self._cache: return self._cache[key]
        p = self._file(*names)
        rows = [Word(x.strip()) for x in p.read_text(encoding='utf-8', errors='replace').splitlines() if x.strip() and x.strip().isalpha()]
        self._cache[key] = rows
        return rows

    def question(self, pool: list[QA], used: set[str]) -> QA | None:
        available = [x for x in pool if x.ident not in used]
        if not available:
            used.clear()
            available = pool[:]
        if not available: return None
        item = random.choice(available)
        used.add(item.ident)
        return item
