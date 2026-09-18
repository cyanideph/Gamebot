# UzzapBot Python

Modern Python rewrite of the legacy Gamebot, designed for the Uzzap Supabase backend. The legacy source/data remain untouched; this branch adds a new engine rather than replacing the original.

## Included game families
- Math, subtraction, multiplication
- Algebra 1/2/3
- General trivia
- Anime trivia
- GTA OPM / GTA Foreign song datasets
- Logic/Rebus
- English Wordhunt
- Tagalog Wordhunt
- Text Twist
- Random and GTA-random modes
- Clue, repost, next, pause/resume, score and leaderboard

## Uzzap integration
The bot reads/writes the existing `public.room_messages` table. It preserves `[c01]` through `[c30]` markers so the Android Uzzap renderer remains responsible for colors.

The first implementation intentionally uses **polling** instead of requiring a Supabase Realtime schema migration. This is safer for the existing production database and works on a phone. Realtime can be added later after verifying the project's publication/RLS configuration.

## Android/Termux setup
```bash
pkg update
pkg install python git
cd Gamebot/uzzapbot
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
nano .env
python -m bot
```

Never commit `.env`, passwords, service-role/secret keys, or database connection strings.

## Environment
- `SUPABASE_URL`: project URL
- `SUPABASE_KEY`: key appropriate for the bot's RLS policies
- `BOT_NAME=uzzapbot`
- `BOT_SENDER_ID`: optional profile UUID
- `ADMIN_IDS`: comma-separated profile UUIDs
- `ADMIN_USERNAMES`: comma-separated admin usernames

## Commands
```text
!game help
!game start math [limit]
!game start trivia [limit]
!game start anime [limit]
!game start gtaopm [limit]
!game start gtaforeign [limit]
!game start logic [limit]
!game start wordhunt [limit]
!game start tagalog [limit]
!game start twist [limit]
!game start algebra1 [limit]
!game start algebra2 [limit]
!game start algebra3 [limit]
!game start random [limit]
!game start random1 [limit]
!game start random2 [limit]
!game start random3 [limit]
!game start random4 [limit]
!game start randomgta [limit]
!game stop
!game pause
!game resume
!game next
!game join
!game clue
!game repost
!game status
!game score
!game leaderboard
```

During testing, start/stop/pause/resume/next are admin-only.

## Safety design
- Ignores its own messages.
- Keeps one game session per room.
- Prevents duplicate question IDs within a pool until exhausted.
- Normalizes answers before comparison.
- Uses exact/alias/fuzzy matching at a high threshold rather than unsafe substring matching.
- Does not make Supabase schema changes.
