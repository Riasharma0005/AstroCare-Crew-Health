"""Connective tissue: one context object feeds every page, so all pages agree."""
import pandas as pd
import streamlit as st

from . import db, rules
from .rules import ENVS, NASA_LIMIT_MSV, CO2_LEVELS, SOCIAL_MIN_TARGET, PARAMS

RANKS = [(0, "Cadet", "🌱"), (200, "Pilot", "🚀"), (600, "Navigator", "🧭"), (1200, "Commander", "🛰️"), (2000, "Galactic Captain", "👑")]
P_HOME, P_HEALTH, P_BODY, P_HAZ, P_JOURNAL, P_PIP, P_GAMES = ("Mission Control", "Health Lab", "Body Explorer", "Hazard Zone", "Creative Corner", "Pip Companion", "Game Zone")
PAGES = [P_HOME, P_HEALTH, P_BODY, P_HAZ, P_JOURNAL, P_PIP, P_GAMES]
CUTE_PAGES = {P_PIP, P_GAMES}


def goto(page, **extra):
    st.session_state["nav"] = page
    st.session_state.update(extra)


def rank_info(xp):
    idx = max(i for i, r in enumerate(RANKS) if xp >= r[0])
    name, icon = RANKS[idx][1], RANKS[idx][2]
    if idx + 1 < len(RANKS):
        lo, hi = RANKS[idx][0], RANKS[idx + 1][0]
        return dict(name=name, icon=icon, next=RANKS[idx + 1][1], pct=(xp - lo) / (hi - lo), to_next=hi - xp)
    return dict(name=name, icon=icon, next=None, pct=1.0, to_next=0)


def _streak(days, today):
    s = set(int(d) for d in days)
    d = today if today in s else today - 1
    n = 0
    while d in s:
        n += 1
        d -= 1
    return n


def build_ctx(aid):
    prof = db.get_profile(aid)
    env = ENVS[prof["environment"]]
    vit, daily = db.vitals_df(aid), db.daily_df(aid)
    ev = rules.evaluate(vit, prof["environment"])
    xp = db.xp_total(aid)
    day = prof["day"]
    row = daily[daily["day"] == day]
    ctx = dict(aid=aid, prof=prof, env=env, env_name=prof["environment"], day=day, duration=prof["duration"],
               vit=vit, daily=daily, ev=ev, xp=xp, rank=rank_info(xp), today_daily=(row.iloc[0].to_dict() if len(row) else None),
               streak=_streak(vit["day"].tolist() if len(vit) else [], day), scores=db.game_scores(aid), diary=db.diary(aid))
    ctx["tasks"] = tasks_for(ctx)
    ctx["insights"] = insights(ctx)
    return ctx


# ---------------------------------------------------------------- daily missions
def tasks_for(ctx):
    env, day, aid = ctx["env"], ctx["day"], ctx["aid"]
    vit, td = ctx["vit"], ctx["today_daily"]
    manual = db.done_tasks(aid, day)
    key, icon, label = env["task"]
    return [
        dict(key="checkin", icon="pulse", label="Daily health check-in", xp=20, done=bool(len(vit)) and day in set(vit["day"]), auto=True, go=P_HEALTH),
        dict(key="hazlog", icon="alert", label="Log today's hazards (radiation, air, contact)", xp=10, done=td is not None, auto=True, go=P_HAZ),
        dict(key="exercise", icon="weight", label=f"Exercise {env['ex_target']} min", xp=15, done=bool(td and td["exercise"] >= env["ex_target"]), auto=True, go=P_HAZ),
        dict(key="social", icon="users", label=f"Chat with crew or family ({SOCIAL_MIN_TARGET}+ min)", xp=0, done=bool(td and td["social"] >= SOCIAL_MIN_TARGET), auto=True, go=P_HAZ),
        dict(key="reflect", icon="pen", label="Write in your diary (Creative Corner)", xp=8, done=any(r["day"] == day for r in ctx["diary"]), auto=True, go=P_JOURNAL),
        dict(key="play", icon="game", label="Play one Game Zone mini-game", xp=0, done=db.plays_on_day(aid, day) > 0, auto=True, go=P_GAMES),
        dict(key="hydrate", icon="drop", label="Hydrate and eat a balanced meal", xp=5, done="hydrate" in manual, auto=False),
        dict(key=key, icon=icon, label=label, xp=5, done=key in manual, auto=False),
    ]


def award_daily(ctx, radiation, exercise, co2, social):
    """Called after the hazard log is saved: XP for logging and for hitting targets."""
    aid, day, env = ctx["aid"], ctx["day"], ctx["env"]
    got = db.award(aid, "hazard_log", 10, day)
    if exercise >= env["ex_target"]:
        got |= db.award(aid, "task:exercise", 15, day)
    return got


# ---------------------------------------------------------------- badges
def badges(ctx):
    sc, v, d = ctx["scores"], ctx["vit"], ctx["daily"]

    def best(game, low=False):
        s = sc[sc["game"] == game]["score"] if len(sc) else pd.Series(dtype=float)
        return None if s.empty else (s.min() if low else s.max())

    ex_days = int((d["exercise"] >= ctx["env"]["ex_target"]).sum()) if len(d) else 0
    br = int((sc["game"] == "breath").sum()) if len(sc) else 0
    b = lambda x, ok: (x[0], x[1], x[2], bool(ok))
    return [
        b(("🛰️", "First Contact", "First check-in"), len(v) >= 1),
        b(("🔥", "Week Streak", "7 check-in days in a row"), ctx["streak"] >= 7),
        b(("⚡", "Sharp Reflexes", "Reflex avg ≤ 250 ms"), best("reflex", True) is not None and best("reflex", True) <= 250),
        b(("🛸", "Star Dodger", "Asteroid score ≥ 150"), (best("dodge") or 0) >= 150),
        b(("🌈", "Memory Master", "Planet Memory level 8+"), (best("memory") or 0) >= 8),
        b(("🫧", "Calm Orbit", "3 breathing sessions"), br >= 3),
        b(("💪", "Iron Bones", "Exercise goal on 7 days"), ex_days >= 7),
        b(("☄️", "Hazard Scholar", "Perfect hazard quiz"), (best("quiz") or 0) >= 5),
        b(("✍️", "Storyteller", "3 diary entries"), len(ctx["diary"]) >= 3),
        b(("🌠", "Poet of the Crew", "Shared a poem"), any(e["kind"] == "poem" and e["shared"] for e in ctx["diary"])),
    ]


# ---------------------------------------------------------------- the insight engine
def hazard_status(ctx):
    """Level per hazard from logged data (used by Hazard Zone and insights)."""
    d, env, day = ctx["daily"], ctx["env"], ctx["day"]
    rec = d[d["day"] > day - 6] if len(d) else d
    out = {}
    long = d[d["day"] > day - 10] if len(d) else d   # radiation effects are watched for ~10 days
    rad_spike = long[long["radiation"] >= 3 * env["rad_typ"]] if len(long) else long
    out["radiation"] = 0 if rad_spike.empty else (2 if (rad_spike["radiation"] >= 8 * env["rad_typ"]).any() else 1)
    out["gravity"] = 0
    if len(rec) >= 3:
        pct = rec["exercise"].tail(3).mean() / env["ex_target"]
        out["gravity"] = 2 if pct < .4 else (1 if pct < .6 else 0)
    out["isolation"] = 1 if len(rec) >= 3 and rec["social"].tail(5).mean() < SOCIAL_MIN_TARGET else 0
    out["env"] = 0
    if len(rec):
        c = rec["co2"].tail(3).max()
        out["env"] = 2 if c >= CO2_LEVELS[1] else (1 if c >= CO2_LEVELS[0] else 0)
    out["distance"] = 0
    return out


def insights(ctx):
    ev, env, day, vit, d = ctx["ev"], ctx["env"], ctx["day"], ctx["vit"], ctx["daily"]
    out = []
    # symptoms in the last two days
    if len(vit):
        for _, r in vit[vit["day"] >= day - 1].iterrows():
            lvl, items = rules.symptom_level(r.get("symptoms"))
            if items:
                out.append(dict(level=max(lvl, 1), icon="alert", tag="env", title=f"Symptoms logged: {', '.join(items)}",
                                text="Red-flag symptoms need prompt medical contact." if lvl == 2 else "Mild symptoms: rest, hydrate, and mention them at your next medical check-in.",
                                go=P_HEALTH))
    # indicators flagged recently
    for k, i in ev.items():
        if i["level"] >= 1 and day - i["day"] <= 3:
            p = PARAMS[k]
            out.append(dict(level=i["level"], icon=p["icon"], tag=p["tag"], title=f"{p['label']}: {rules.LEVEL_NAME[i['level']]}",
                            text=i["reason"], go=P_HEALTH))
    # compound fatigue stack
    stack = [ev.get(k) for k in ("sleep", "fatigue", "reaction")]
    if all(s and s["level"] >= 1 for s in stack):
        long = min(s["days_flagged"] for s in stack) >= 3
        out.append(dict(level=2 if long else 1, icon="battery", tag="isolation", title="Fatigue stack detected",
                        text="Short sleep, high fatigue and slower reactions together can affect decisions. Protect your rest and postpone risky tasks. "
                             + ("This has lasted 3+ days: tell your crew medical officer." if long else "Watch whether it continues."),
                        go=P_GAMES))
    # hazards from the daily log
    hz = hazard_status(ctx)
    if len(d):
        rec = d[d["day"] > day - 6]
        sp = d[(d["day"] > day - 10) & (d["radiation"] >= 3 * env["rad_typ"])]
        if not sp.empty:
            r = sp.sort_values("radiation").iloc[-1]
            out.append(dict(level=hz["radiation"], icon="sun", tag="radiation", title=f"Radiation spike on day {int(r['day'])}",
                            text=f"{r['radiation']:.1f} mSv/day vs a typical ~{env['rad_typ']} here. Review shelter drills and watch fatigue and sleep over the next days.",
                            go=P_HAZ))
        if hz["gravity"]:
            out.append(dict(level=hz["gravity"], icon="weight", tag="gravity", title="Exercise below target",
                            text=f"Your last 3 days average {rec['exercise'].tail(3).mean():.0f} min vs a target of {env['ex_target']}. Exercise protects bones, muscles and the heart.",
                            go=P_HAZ))
        if hz["isolation"]:
            out.append(dict(level=1, icon="users", tag="isolation", title="Low social contact",
                            text=f"Under {SOCIAL_MIN_TARGET} min a day recently. Schedule a call with crew or family: contact is a proven buffer against isolation stress.",
                            go=P_HAZ))
        if hz["env"]:
            out.append(dict(level=hz["env"], icon="wind", tag="env", title="Cabin CO₂ is climbing",
                            text=f"Recent peak {rec['co2'].tail(3).max():.0f} ppm. Check scrubbers and ventilation per your habitat checklist.", go=P_HAZ))
    # escalation hint with comms delay
    if any(i["level"] == 2 for i in out):
        out.append(dict(level=2, icon="signal", tag="distance", title="Escalate now",
                        text=f"Ground delay here is {env['delay']}. {env['autonomy']}", go=P_PIP))
    if not (len(vit) and day in set(vit["day"])):
        out.append(dict(level=0, icon="doc", tag="env", title="Today's check-in is waiting", text="One minute in the Health Lab keeps your trends accurate.", go=P_HEALTH))
    return sorted(out, key=lambda x: -x["level"])


# ---------------------------------------------------------------- flight surgeon report
def build_report(ctx):
    p, env, ev, day = ctx["prof"], ctx["env"], ctx["ev"], ctx["day"]
    d, vit = ctx["daily"], ctx["vit"]
    L = [f"# AstroCare crew health summary", "",
         f"**Crew member:** {p['name']} ({p['astro_id']})  ",
         f"**Mission:** {p['mission']}  |  **Environment:** {ctx['env_name']}  |  **Mission day:** {day} of {ctx['duration']}  ",
         f"**Ground delay:** {env['delay']}  |  **Gravity:** {env['gravity']}", "",
         "## Indicator status (latest reading)", "",
         "| Indicator | Value | Status | Day | Own average | Reference |", "|---|---|---|---|---|---|"]
    for k, i in sorted(ev.items(), key=lambda kv: -kv[1]["level"]):
        pr = PARAMS[k]
        avg = f"{i['mean']:.{max(pr['dec'], 1)}f}" if i["mean"] is not None else "-"
        L.append(f"| {pr['label']} | {i['value']:.{pr['dec']}f} {pr['unit']} | {rules.LEVEL_NAME[i['level']]} | {i['day']} | {avg} | {rules.range_text(k)} |")
    L += ["", "## Flags and recommended actions", ""]
    flagged = [(k, i) for k, i in ev.items() if i["level"] >= 1]
    L += [f"- **{PARAMS[k]['label']}** ({rules.LEVEL_NAME[i['level']]}, {i['days_flagged']} reading(s) flagged): {i['reason']}" for k, i in flagged] or ["- No indicators flagged."]
    L += ["", "## Connected insights", ""] + [f"- {i['icon']} **{i['title']}**: {i['text']}" for i in ctx["insights"] if i["level"] >= 1] or ["- None."]
    if len(vit):
        r7 = vit[vit["day"] > day - 8]
        L += ["", "## Last 7 days (averages)", ""]
        L += [f"- {PARAMS[k]['label']}: {r7[k].mean():.{max(PARAMS[k]['dec'], 1)}f} {PARAMS[k]['unit']}" for k in ("hr", "sys", "dia", "glucose", "sleep", "mood", "stress", "fatigue", "reaction") if r7[k].notna().any()]
        syms = [f"day {int(r['day'])}: {r['symptoms']}" for _, r in r7.iterrows() if r.get("symptoms")]
        L += ["", "**Symptoms:** " + ("; ".join(syms) if syms else "none logged")]
    if len(d):
        r7 = d[d["day"] > day - 8]
        L += ["", "## Hazard log", "",
              f"- Cumulative radiation logged: **{d['radiation'].sum():.1f} mSv** ({d['radiation'].sum() / NASA_LIMIT_MSV * 100:.1f}% of the {NASA_LIMIT_MSV} mSv NASA career limit)",
              f"- Last 7 days: radiation avg {r7['radiation'].mean():.2f} mSv/day, exercise avg {r7['exercise'].mean():.0f} min (target {env['ex_target']}), "
              f"CO₂ max {r7['co2'].max():.0f} ppm, social contact avg {r7['social'].mean():.0f} min/day"]
    L += ["", f"**Engagement:** {ctx['streak']}-day check-in streak, rank {ctx['rank']['name']}.", "",
          "> Prototype for education and decision support. Not a diagnosis. Follow mission medical protocols; contact the flight surgeon for any red-flag symptom."]
    return "\n".join(L)


def poem_today(ctx):
    """Gently suggest one of the author's poems from how the crew member is doing."""
    from . import poems
    hz = hazard_status(ctx)
    return poems.poem_for(rules.overall(ctx["ev"]) or 0, hz["isolation"] >= 1)
