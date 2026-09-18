from __future__ import annotations
from dataclasses import dataclass, field
import random, re
from rapidfuzz.fuzz import ratio
from .data import DataBank, QA
from .formatting import normalize_answer

@dataclass
class Player:
    key: str
    name: str
    score: int = 0
    correct: int = 0

@dataclass
class Game:
    name: str
    room: str
    points: int = 10
    limit: int = 100
    players: dict[str, Player] = field(default_factory=dict)
    used: set[str] = field(default_factory=set)
    current: QA | None = None
    started: bool = True
    paused: bool = False
    answered: bool = False
    mode: str = ''
    metadata: dict = field(default_factory=dict)

    def add_player(self, key: str, name: str) -> Player:
        return self.players.setdefault(key, Player(key, name))

    def winner(self) -> Player | None:
        candidates = [p for p in self.players.values() if p.score >= self.limit]
        return max(candidates, key=lambda p: (p.score, p.correct), default=None)

class GameFactory:
    def __init__(self, data: DataBank): self.data = data

    def qa_game(self, name: str, room: str, pool: list[QA], points: int, limit: int, mode: str) -> Game:
        g = Game(name, room, points, limit, mode=mode, metadata={'pool': pool})
        g.current = self.data.question(pool, g.used)
        return g

    def create(self, mode: str, room: str, points: int, limit: int) -> Game:
        m = mode.casefold().replace('-', '').replace('_', '').replace(' ', '')
        if m in {'math','addition'}:
            return self.math(room, points, limit)
        if m in {'mathminus','subtraction'}:
            return self.mathminus(room, points, limit)
        if m in {'mathmultiply','multiplication'}:
            return self.mathmultiply(room, points, limit)
        if m in {'algebra1','algebra2','algebra3'}:
            return self.algebra(m, room, points, limit)
        mapping = {
            'trivia': ('Zgen-info.txt', 'General Trivia'),
            'gentrivia': ('Zgen-info.txt', 'General Trivia'),
            'anime': ('Zanime-trivia.txt', 'Anime Trivia'),
            'animetrivia': ('Zanime-trivia.txt', 'Anime Trivia'),
            'gtaforeign': ('Zgta-foreign.txt', 'GTA Foreign'),
            'gtaopm': ('Zgta-opm.txt', 'GTA OPM'),
            'logic': ('Zlogic.txt', 'Logic/Rebus'),
        }
        if m in mapping:
            file_name, title = mapping[m]
            return self.qa_game(title, room, self.data.qa(file_name), points, limit, m)
        if m in {'wordhunt','englishwordhunt'}: return self.wordhunt(room, points, limit, False)
        if m in {'tagalog','tagalogwordhunt'}: return self.wordhunt(room, points, limit, True)
        if m in {'twist','texttwist'}: return self.twist(room, points, limit)
        if m in {'random','random1','random2','random3','random4'}: return self.random_game(m, room, points, limit)
        if m in {'randomgta'}: return self.random_gta(room, points, limit)
        raise ValueError(f'Unknown game: {mode}')

    def math(self, room, points, limit):
        a,b = random.randint(1,50), random.randint(1,50)
        return Game('Math', room, points, limit, mode='math', current=QA(str(random.random()), f'{a} + {b} = ?', str(a+b)))
    def mathminus(self, room, points, limit):
        a,b = random.randint(1,100), random.randint(1,100); a,b=max(a,b),min(a,b)
        return Game('Math Minus', room, points, limit, mode='mathminus', current=QA(str(random.random()), f'{a} - {b} = ?', str(a-b)))
    def mathmultiply(self, room, points, limit):
        a,b = random.randint(1,15), random.randint(1,15)
        return Game('Math Multiply', room, points, limit, mode='mathmultiply', current=QA(str(random.random()), f'{a} × {b} = ?', str(a*b)))
    def algebra(self, mode, room, points, limit):
        a,b,x = random.randint(1,12), random.randint(1,12), random.randint(1,20)
        if mode == 'algebra1':
            q=f'{a}x + {b} = {a*x+b}  → x = ?'; ans=str(x)
        elif mode == 'algebra2':
            q=f'{a}x - {b} = {a*x-b}  → x = ?'; ans=str(x)
        else:
            q=f'{a} × x × {b} = {a*x*b}  → x = ?'; ans=str(x)
        return Game(mode.title(), room, points, limit, mode=mode, current=QA(str(random.random()), q, ans))
    def wordhunt(self, room, points, limit, tagalog):
        words=self.data.words('salita.txt' if tagalog else 'words.txt')
        w=random.choice(words).word.upper()
        letters=' '.join(random.sample(list(w), len(w)))
        return Game('Tagalog Wordhunt' if tagalog else 'Wordhunt', room, points, limit, mode='tagalog' if tagalog else 'wordhunt', current=QA(str(random.random()), f'Unscramble: {letters}', w))
    def twist(self, room, points, limit):
        words=self.data.words('words.txt'); w=random.choice([x.word.upper() for x in words if 4 <= len(x.word) <= 8])
        letters=' '.join(random.sample(list(w), len(w)))
        return Game('Text Twist', room, points, limit, mode='twist', current=QA(str(random.random()), f'TWIST: {letters}', w))
    def random_game(self, mode, room, points, limit):
        pools={
            'random':['math','mathminus','mathmultiply','trivia','anime','logic','wordhunt','tagalog','twist','algebra1','algebra2','algebra3'],
            'random1':['math','trivia','wordhunt','twist'],
            'random2':['math','trivia','anime','logic','wordhunt','twist'],
            'random3':['math','mathminus','mathmultiply','algebra1','algebra2','algebra3','trivia','anime','gtaopm','gtaforeign','logic','wordhunt','tagalog','twist'],
            'random4':['math','algebra1','trivia','anime','gtaopm','logic','twist'],
        }
        return self.create(random.choice(pools.get(mode, pools['random'])), room, points, limit)
    def random_gta(self, room, points, limit):
        return self.create(random.choice(['gtaopm','gtaforeign']), room, points, limit)

def answer_matches(guess: str, answer: str) -> bool:
    a,b=normalize_answer(guess),normalize_answer(answer)
    if not a or not b: return False
    if a == b: return True
    aliases=[normalize_answer(x) for x in re.split(r'\s*(?:/|\||;|,)\s*', answer) if x.strip()]
    if a in aliases: return True
    return ratio(a,b) >= 97
