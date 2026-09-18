from __future__ import annotations
import re

# Uzzap color markers are preserved. The Android client is responsible for rendering [c01]..[c30].
COLOR_RE = re.compile(r'\[c(?:0[1-9]|[12]\d|30)\]', re.I)

EMOTICON_CODES = [
    ':)', ':D', ';) ', ':P', ':(', ':o', '<3', '^^', '-_-', 'T_T'
]

def color(n: int, text: str) -> str:
    n = max(1, min(30, int(n)))
    return f'[c{n:02d}]{text}'

def normalize_answer(value: str) -> str:
    value = value.casefold().strip()
    value = re.sub(r'\s+', ' ', value)
    value = re.sub(r'[\u200b\u200c\u200d]', '', value)
    value = re.sub(r'^[\s\W]+|[\s\W]+$', '', value, flags=re.UNICODE)
    return value

def strip_colors(value: str) -> str:
    return COLOR_RE.sub('', value)

def render_question(question: str, answer_hint: str | None = None) -> str:
    out = f'{color(3, "GAMEBOT")} {color(12, question)}'
    if answer_hint:
        out += f' {color(7, answer_hint)}'
    return out
