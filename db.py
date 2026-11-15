"""One small SQLite database for the whole app (data/astrocare_v3.db)."""
import random
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "astrocare_v3.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS profiles(astro_id TEXT PRIMARY KEY, name TEXT, mission TEXT, environment TEXT,
  day INTEGER, duration INTEGER, updated TEXT);
CREATE TABLE IF NOT EXISTS vitals(astro_id TEXT, day INTEGER, hr REAL, spo2 REAL, temp REAL, sys REAL, dia REAL,
  glucose REAL, sleep REAL, mood REAL, stress REAL, fatigue REAL, symptoms TEXT, note TEXT, ts TEXT,
  PRIMARY KEY(astro_id, day));
CREATE TABLE IF NOT EXISTS daily_log(astro_id TEXT, day INTEGER, radiation REAL, exercise REAL, co2 REAL,
  social REAL, ts TEXT, PRIMARY KEY(astro_id, day));
CREATE TABLE IF NOT EXISTS tasks(astro_id TEXT, day INTEGER, key TEXT, done INTEGER, PRIMARY KEY(astro_id, day, key));
CREATE TABLE IF NOT EXISTS xp(id INTEGER PRIMARY KEY AUTOINCREMENT, astro_id TEXT, source TEXT, xp INTEGER, day INTEGER, ts TEXT);
CREATE TABLE IF NOT EXISTS diary(id INTEGER PRIMARY KEY AUTOINCREMENT, astro_id TEXT, day INTEGER, kind TEXT, title TEXT, body TEXT,
  mood TEXT, shared INTEGER DEFAULT 0, show_name INTEGER DEFAULT 1, ts TEXT);
CREATE TABLE IF NOT EXISTS stars(entry_id INTEGER, astro_id TEXT, ts TEXT, PRIMARY KEY(entry_id, astro_id));
CREATE TABLE IF NOT EXISTS game_scores(id INTEGER PRIMARY KEY AUTOINCREMENT, astro_id TEXT, game TEXT, score REAL, day INTEGER, ts TEXT);
"""


@contextmanager
def conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    try:
        yield c
        c.commit()
    finally:
        c.close()


def _now():
    return datetime.now().isoformat(timespec="seconds")


def init():
    with conn() as c:
        c.executescript(SCHEMA)


# ---------------------------------------------------------------- profiles
def list_profiles():
    with conn() as c:
        return [dict(r) for r in c.execute("SELECT * FROM profiles ORDER BY name")]


def get_profile(aid):
    with conn() as c:
        r = c.execute("SELECT * FROM profiles WHERE astro_id=?", (aid,)).fetchone()
    return dict(r) if r else None


def save_profile(aid, name, mission, env, day, duration):
    with conn() as c:
        c.execute("""INSERT INTO profiles VALUES(?,?,?,?,?,?,?) ON CONFLICT(astro_id) DO UPDATE SET
            name=excluded.name, mission=excluded.mission, environment=excluded.environment,
            day=excluded.day, duration=excluded.duration, updated=excluded.updated""",
                  (aid, name, mission, env, int(day), int(duration), _now()))


def set_day(aid, day):
    with conn() as c:
        c.execute("UPDATE profiles SET day=?, updated=? WHERE astro_id=?", (int(day), _now(), aid))


# ---------------------------------------------------------------- vitals & daily log
def vitals_df(aid):
    with conn() as c:
        v = pd.read_sql_query("SELECT * FROM vitals WHERE astro_id=? ORDER BY day", c, params=(aid,))
        r = pd.read_sql_query("SELECT day, AVG(score) AS reaction FROM game_scores WHERE astro_id=? AND game='reflex' GROUP BY day",
                              c, params=(aid,))
    return v.merge(r, on="day", how="left")


def save_vitals(aid, day, d):
    cols = ["hr", "spo2", "temp", "sys", "dia", "glucose", "sleep", "mood", "stress", "fatigue", "symptoms", "note"]
    with conn() as c:
        c.execute(f"""INSERT INTO vitals(astro_id, day, {','.join(cols)}, ts) VALUES(?,?,{','.join('?' * len(cols))},?)
            ON CONFLICT(astro_id, day) DO UPDATE SET {','.join(f'{k}=excluded.{k}' for k in cols)}, ts=excluded.ts""",
                  (aid, int(day), *[d.get(k) for k in cols], _now()))


def daily_df(aid):
    with conn() as c:
        return pd.read_sql_query("SELECT * FROM daily_log WHERE astro_id=? ORDER BY day", c, params=(aid,))


def save_daily(aid, day, radiation, exercise, co2, social):
    with conn() as c:
        c.execute("""INSERT INTO daily_log VALUES(?,?,?,?,?,?,?) ON CONFLICT(astro_id, day) DO UPDATE SET
            radiation=excluded.radiation, exercise=excluded.exercise, co2=excluded.co2,
            social=excluded.social, ts=excluded.ts""", (aid, int(day), radiation, exercise, co2, social, _now()))


# ---------------------------------------------------------------- tasks, xp, games
def done_tasks(aid, day):
    with conn() as c:
        return {r["key"] for r in c.execute("SELECT key FROM tasks WHERE astro_id=? AND day=? AND done=1", (aid, day))}


def set_task(aid, day, key, done):
    with conn() as c:
        c.execute("""INSERT INTO tasks VALUES(?,?,?,?) ON CONFLICT(astro_id, day, key) DO UPDATE SET done=excluded.done""",
                  (aid, int(day), key, int(done)))


def award(aid, source, xp, day, cap=1):
    """Give XP unless this source already hit its per-day cap. Returns True if awarded."""
    with conn() as c:
        n = c.execute("SELECT COUNT(*) FROM xp WHERE astro_id=? AND source=? AND day=?", (aid, source, day)).fetchone()[0]
        if n >= cap or xp <= 0:
            return False
        c.execute("INSERT INTO xp(astro_id, source, xp, day, ts) VALUES(?,?,?,?,?)", (aid, source, int(xp), int(day), _now()))
    return True


def xp_total(aid):
    with conn() as c:
        return c.execute("SELECT COALESCE(SUM(xp),0) FROM xp WHERE astro_id=?", (aid,)).fetchone()[0]


def xp_breakdown(aid):
    with conn() as c:
        return pd.read_sql_query("SELECT source, SUM(xp) AS xp, COUNT(*) AS n FROM xp WHERE astro_id=? GROUP BY source ORDER BY xp DESC",
                                 c, params=(aid,))


def add_game_score(aid, game, score, day):
    with conn() as c:
        c.execute("INSERT INTO game_scores(astro_id, game, score, day, ts) VALUES(?,?,?,?,?)", (aid, game, float(score), int(day), _now()))


def game_scores(aid):
    with conn() as c:
        return pd.read_sql_query("SELECT * FROM game_scores WHERE astro_id=? ORDER BY id", c, params=(aid,))


def plays_on_day(aid, day, game=None):
    q, p = "SELECT COUNT(*) FROM game_scores WHERE astro_id=? AND day=?", [aid, day]
    if game:
        q, p = q + " AND game=?", p + [game]
    with conn() as c:
        return c.execute(q, p).fetchone()[0]


def reaction_on_day(aid, day):
    with conn() as c:
        r = c.execute("SELECT AVG(score) FROM game_scores WHERE astro_id=? AND game='reflex' AND day=?", (aid, day)).fetchone()[0]
    return r


# ---------------------------------------------------------------- diary (private) + crew shelf (shared poems)
def save_entry(aid, day, kind, title, body, mood="okay", shared=0, show_name=1):
    with conn() as c:
        cur = c.execute("INSERT INTO diary(astro_id, day, kind, title, body, mood, shared, show_name, ts) VALUES(?,?,?,?,?,?,?,?,?)",
                        (aid, int(day), kind, title, body, mood, int(shared), int(show_name), _now()))
        return cur.lastrowid


def update_entry(eid, aid, title, body):
    with conn() as c:
        c.execute("UPDATE diary SET title=?, body=? WHERE id=? AND astro_id=?", (title, body, eid, aid))


def set_shared(eid, aid, shared):
    with conn() as c:
        c.execute("UPDATE diary SET shared=? WHERE id=? AND astro_id=? AND kind='poem'", (int(shared), eid, aid))


def delete_entry(eid, aid):
    with conn() as c:
        c.execute("DELETE FROM diary WHERE id=? AND astro_id=?", (eid, aid))
        c.execute("DELETE FROM stars WHERE entry_id=?", (eid,))


def diary(aid):
    with conn() as c:
        return [dict(r) for r in c.execute("SELECT * FROM diary WHERE astro_id=? ORDER BY id DESC", (aid,))]


def shelf():
    """Poems that crew members chose to share, newest first, with author name and mission."""
    with conn() as c:
        return [dict(r) for r in c.execute("""SELECT d.*, p.name AS author, p.mission AS mission FROM diary d
            LEFT JOIN profiles p ON p.astro_id=d.astro_id WHERE d.kind='poem' AND d.shared=1 ORDER BY d.id DESC""")]


def star(eid, aid):
    with conn() as c:
        cur = c.execute("INSERT OR IGNORE INTO stars VALUES(?,?,?)", (eid, aid, _now()))
        return cur.rowcount > 0


def star_counts():
    with conn() as c:
        return {r["entry_id"]: r["n"] for r in c.execute("SELECT entry_id, COUNT(*) AS n FROM stars GROUP BY entry_id")}


def starred_by(aid):
    with conn() as c:
        return {r["entry_id"] for r in c.execute("SELECT entry_id FROM stars WHERE astro_id=?", (aid,))}


# ---------------------------------------------------------------- demo mission
def reset_all():
    with conn() as c:
        for t in ("profiles", "vitals", "daily_log", "tasks", "xp", "game_scores", "diary", "stars"):
            c.execute(f"DELETE FROM {t}")


def seed_demo(aid="AST-001"):
    """A 30-day Mars mission with a story: from ~day 18 sleep shrinks, stress and fatigue climb,
    reactions slow; a solar particle event hits on day 22; exercise and contact drop; CO2 creeps up."""
    rnd = random.Random(7)
    g = rnd.gauss
    save_profile(aid, "Cmdr Nova Reyes", "ARES-ORION", "Mars Base", 30, 180)
    clip = lambda x, lo, hi: max(lo, min(hi, x))
    for d in range(1, 30):
        if d == 12:  # one missed check-in, like real life
            continue
        late = max(0, d - 17)
        vit = dict(
            hr=round(66 + g(0, 2.5) + min(9, late * 1.0)), spo2=round(clip(97.6 + g(0, .6), 93, 100)),
            temp=round(36.7 + g(0, .18), 1), sys=round(113 + g(0, 3) + min(14, max(0, d - 19) * .9)),
            dia=round(74 + g(0, 2) + min(8, max(0, d - 19) * .45)), glucose=round(88 + g(0, 4) + min(14, max(0, d - 21) * 1.4)),
            sleep=round(clip(7.3 + g(0, .3) - min(1.8, late * .24), 4, 9), 1),
            mood=round(clip(7.6 + g(0, .6) - min(3, late * .3), 1, 10)),
            stress=round(clip(3 + g(0, .7) + min(3.8, late * .38), 1, 10)),
            fatigue=round(clip(3 + g(0, .7) + min(3.5, late * .35), 1, 10)),
            symptoms="Headache" if d in (27, 28) else ("Back pain" if d == 24 else ""),
            note="Solar storm shelter drill" if d == 22 else "")
        save_vitals(aid, d, vit)
        award(aid, "checkin", 20, d)
        add_game_score(aid, "reflex", round(255 + g(0, 9) + min(78, late * 8.5)), d)
        rad = 3.2 if d == 22 else (1.9 if d == 23 else round(0.64 * (1 + g(0, .12)), 2))
        ex = round(clip(78 + g(0, 7), 50, 100)) if not 19 <= d <= 24 else round(clip(30 + g(0, 8), 5, 50))
        co2 = round(2000 + g(0, 160) + (900 + (d - 25) * 150 if d >= 25 else 0))
        soc = round(clip(52 + g(0, 9), 20, 90)) if not 20 <= d <= 29 else round(clip(12 + g(0, 5), 0, 24))
        save_daily(aid, d, rad, ex, co2, soc)
        award(aid, "hazard_log", 10, d)
        if ex >= 75:
            award(aid, "task:exercise", 15, d)
        if d % 3 == 0:
            award(aid, "task:hydrate", 5, d)
    for day, title, body in [
            (21, "What silence sounds like", "Like the scrubbers breathing. I used to hate it. Tonight it felt like company."),
            (25, "Thank you, Marek", "Marek covered my filter check without being asked. I told him at dinner. He pretended not to care and smiled anyway."),
            (28, "For tomorrow", "Tomorrow I will sleep before the numbers have to tell me to.")]:
        save_entry(aid, day, "thought", title, body, "okay")
        award(aid, "diary", 8, day)
    for day, game, score in [(5, "dodge", 96), (14, "dodge", 168), (26, "dodge", 140), (8, "memory", 5), (20, "memory", 7),
                             (10, "quiz", 4), (25, "quiz", 5)] + [(x, "breath", 4) for x in range(21, 28)]:
        add_game_score(aid, game, score, day)
    for day, src, x in [(5, "game:dodge", 12), (14, "game:dodge", 18), (8, "game:memory", 15), (20, "game:memory", 21),
                        (10, "game:quiz", 16), (25, "game:quiz", 20)] + [(x, "game:breath", 10) for x in range(21, 28)]:
        award(aid, src, x, day)


_POEM_A = """The scrubbers breathe the way my mother did,
slow in, slow out, a patient kind of tide.
I count their hum instead of counting days,
and somewhere in the count I am not afraid.

Down the corridor a crewmate laughs in sleep.
The walls hold all of us like cupped hands hold a flame.
Outside, the rust-colored dark rehearses its silence.
Inside, we keep the small lights on, by name."""

_POEM_B = """Today the wind wrote nothing on the dome,
so I wrote my own: a spiral, a sun, a door.
Tea steamed against the glass like a small cloud,
and for one minute Earth was not so far.

I called my sister. She was late for work.
Her voice took eleven minutes to arrive,
and I loved every one of them,
the way you love a sunrise that is on its way."""


def seed_crew():
    """Two crewmates with sample poems on the crew shelf, so the shared reading corner is alive in the demo."""
    save_profile("AST-002", "Dr. Marek Voss", "ARES-ORION", "Mars Base", 30, 180)
    save_profile("AST-003", "Lt. Imani Okoye", "ARES-ORION", "Mars Base", 30, 180)
    save_entry("AST-002", 19, "poem", "Night Shift at the Scrubbers", _POEM_A, "okay", shared=1, show_name=1)
    save_entry("AST-003", 24, "poem", "Red Dust, Warm Tea", _POEM_B, "good", shared=1, show_name=1)


def ensure_demo():
    init()
    if not list_profiles():
        seed_demo()
        seed_crew()
