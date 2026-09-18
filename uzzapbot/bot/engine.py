from __future__ import annotations
import asyncio
from collections import defaultdict
from .config import Config
from .data import DataBank
from .games import GameFactory, Game, answer_matches
from .formatting import color, render_question

HELP = '''[c03]uzzapbot game commands
[c12]!game start <game> [limit] — admin only
[c12]!game stop — admin only
[c12]!game pause / resume — admin only
[c12]!game status
[c12]!game score
[c12]!game leaderboard
[c12]!game join
[c12]!game clue
[c12]!game repost
[c12]!game next — admin only
[c12]!game help
[c07]Games: math, mathminus, mathmultiply, algebra1-3, trivia, anime, gtaopm, gtaforeign, logic, wordhunt, tagalog, twist, random, random1-4, randomgta'''

class GameManager:
    def __init__(self, config: Config, store, data_root):
        self.config=config; self.store=store; self.factory=GameFactory(DataBank(data_root))
        self.sessions: dict[str, Game] = {}
        self.locks=defaultdict(asyncio.Lock)

    def is_admin(self, msg: dict) -> bool:
        sid=(msg.get('sender_id') or '').lower(); user=(msg.get('sender') or '').lower()
        return sid in self.config.admin_ids or user in self.config.admin_usernames

    async def send(self, room: str, text: str):
        await self.store.send(room, text, self.config.bot_sender_id)

    async def start(self, room, mode, limit):
        async with self.locks[room]:
            if room in self.sessions and self.sessions[room].started:
                await self.send(room, color(8,'A game is already running. Use !game stop first.')); return
            try:
                g=self.factory.create(mode, room, self.config.default_points, limit)
            except Exception:
                await self.send(room, color(8,f'Unknown game: {mode}. Use !game help.')); return
            self.sessions[room]=g
            await self.send(room, f'{color(3,"GAME START")} {color(12,g.name)} — {color(7,str(g.points))} points, target {color(7,str(g.limit))}.')
            await self.post_question(g)

    async def post_question(self,g:Game):
        if not g.current:
            await self.send(g.room, color(8,'No more questions are available. Game ended.'))
            g.started=False; return
        g.answered=False
        await self.send(g.room, render_question(g.current.question))

    async def stop(self,room):
        async with self.locks[room]:
            g=self.sessions.pop(room,None)
            if not g: await self.send(room,color(8,'No active game.')); return
            winner=max(g.players.values(),key=lambda p:(p.score,p.correct),default=None)
            if winner: await self.send(room,f'{color(3,"GAME OVER")} {color(12,winner.name)} wins with {winner.score} points.')
            else: await self.send(room,color(7,'Game stopped. No scores yet.'))

    async def next_question(self,g:Game):
        random_mode=g.metadata.get('random_mode')
        if random_mode:
            new=self.factory.create(random_mode,g.room,g.points,g.limit)
            new.players=g.players
            self.sessions[g.room]=new
            await self.post_question(new); return
        mode=g.mode
        if mode in {'math','mathminus','mathmultiply','algebra1','algebra2','algebra3'}:
            new=self.factory.create(mode,g.room,g.points,g.limit); new.players=g.players; new.used=g.used
            self.sessions[g.room]=new; await self.post_question(new); return
        pool=g.metadata.get('pool',[])
        g.current=self.factory.data.question(pool,g.used) if pool else self.factory.create(mode,g.room,g.points,g.limit).current
        await self.post_question(g)

    async def handle_answer(self,msg:dict,g:Game):
        if g.paused or not g.started or g.answered or not g.current: return
        body=str(msg.get('body') or '').strip()
        if not body or body.startswith('!'): return
        if not answer_matches(body,g.current.answer): return
        key=str(msg.get('sender_id') or msg.get('sender') or 'unknown')
        name=str(msg.get('sender') or key)
        p=g.add_player(key,name)
        p.score += g.points; p.correct += 1; g.answered=True
        await self.send(g.room,f'{color(3,"✓ CORRECT")} {color(12,p.name)} +{g.points}  {color(7,"Score:")} {p.score}')
        if p.score >= g.limit:
            await self.send(g.room,f'{color(3,"🏆 WINNER")} {color(12,p.name)} reached {g.limit} points!')
            g.started=False; return
        await asyncio.sleep(0.8)
        if g.started and self.sessions.get(g.room) is g: await self.next_question(g)

    async def command(self,msg:dict):
        room=str(msg.get('room_name') or '')
        if not room: return False
        body=str(msg.get('body') or '').strip(); low=body.casefold()
        if not low.startswith('!game'): return False
        args=body.split(); cmd=args[1].casefold() if len(args)>1 else 'help'; admin=self.is_admin(msg)
        if cmd in {'help','?'}: await self.send(room,HELP); return True
        if cmd=='start':
            if not admin: await self.send(room,color(8,'Game start is admin-only during testing.')); return True
            mode=args[2] if len(args)>2 else 'random'; limit=int(args[3]) if len(args)>3 and args[3].isdigit() else self.config.default_limit
            await self.start(room,mode,limit); return True
        g=self.sessions.get(room)
        if cmd=='stop':
            if admin: await self.stop(room)
            else: await self.send(room,color(8,'Game control is admin-only during testing.'))
            return True
        if cmd in {'pause','resume','next'}:
            if not admin: await self.send(room,color(8,'Game control is admin-only during testing.')); return True
            if not g: await self.send(room,color(8,'No active game.')); return True
            if cmd=='pause': g.paused=True; await self.send(room,color(7,'Game paused.'))
            elif cmd=='resume': g.paused=False; await self.send(room,color(7,'Game resumed.'))
            else: await self.next_question(g)
            return True
        if cmd=='status':
            if not g: await self.send(room,color(7,'No active game.')); return True
            state='paused' if g.paused else ('running' if g.started else 'finished')
            await self.send(room,f'{color(3,g.name)} — {state} — target {g.limit} — players {len(g.players)}'); return True
        if cmd in {'score','leaderboard'}:
            if not g or not g.players: await self.send(room,color(7,'No scores yet.')); return True
            rows=sorted(g.players.values(),key=lambda p:(-p.score,-p.correct,p.name.casefold()))[:10]
            text=' | '.join(f'{i}. {p.name}: {p.score}' for i,p in enumerate(rows,1))
            await self.send(room,color(12,'Leaderboard: ')+text); return True
        if cmd=='join':
            if g: g.add_player(str(msg.get('sender_id') or msg.get('sender')),str(msg.get('sender') or 'player')); await self.send(room,color(7,'You joined the game.'))
            return True
        if cmd=='clue':
            if not g or not g.current: return True
            a=g.current.answer; hint=' '.join(c if c.isspace() else '_' for c in a)
            await self.send(room,color(7,f'Clue: {hint}')); return True
        if cmd=='repost':
            if g: await self.post_question(g)
            return True
        return True
