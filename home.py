"""Mission Control: the hub. Status at a glance, today's missions, connected insights, story and poem of the day."""
import streamlit as st

from . import core, db, poems, rules, story, theme


def _toggle(aid, day, key, xp):
    done = st.session_state.get(f"t_{aid}_{day}_{key}", False)
    db.set_task(aid, day, key, done)
    if done and xp and db.award(aid, f"task:{key}", xp, day):
        st.session_state["toast"] = f"Mission complete. +{xp} XP"


def render(ctx):
    p, env, ev, day = ctx["prof"], ctx["env"], ctx["ev"], ctx["day"]
    lvl = rules.overall(ev)
    chips = (theme.tag(lvl, f"Crew status: {rules.LEVEL_NAME[lvl]}") if lvl is not None else theme.plain_tag("No readings yet", theme.GREY))
    chips += theme.plain_tag(f"{ctx['streak']}-day check-in streak", "#e8b04a") + theme.plain_tag(f"{ctx['rank']['name']} · {ctx['xp']} XP", "#a58bff")
    theme.show(theme.hero(f"{ctx['env_name']}, mission day {day}", f"{p['name']} · {env['tagline']}", f"Mission Control · {p['mission']}",
                          ctx["env_name"], env["epigraph"], chips))
    ch = story.latest(day)
    nch = len(story.unlocked(day))
    theme.show(theme.readouts([("Mission elapsed", f"Day {day} / {ctx['duration']}"), ("Ground delay", env["delay"]), ("Gravity", env["gravity"]),
                               ("Crew status", rules.LEVEL_NAME[lvl] if lvl is not None else "No data"), ("Story", f"Chapter {nch} of {len(story.CHAPTERS)}")]))
    pct = min(100, day / ctx["duration"] * 100)
    nodes = "".join(f'<div class="node {"on" if day >= c["day"] else ""}"><s></s>{c["title"] if not c.get("epilogue") else "Epilogue"}</div>' for c in story.CHAPTERS)
    theme.show(f'<div class="panel" style="margin-top:12px"><div style="display:flex;justify-content:space-between"><b>Mission trajectory</b>'
               f'<span class="muted">{pct:.0f}% complete · chapters unlock as the mission advances</span></div><div class="bar"><i style="width:{pct}%"></i></div>'
               f'<div class="nodes">{nodes}</div></div>')

    # ---- vitals snapshot
    theme.show(theme.section("Crew vitals"))
    if not ev:
        theme.show('<div class="panel">No check-ins yet. Open the Health Lab to log your first one.</div>')
    else:
        keys = ["hr", "spo2", "bp", "glucose", "sleep", "mood"]
        for col, k in zip(st.columns(6), keys):
            with col:
                if k == "bp":
                    if "sys" in ev and "dia" in ev:
                        s, d = ev["sys"], ev["dia"]
                        theme.show(theme.tile("gauge", "Blood pressure", f"{s['value']:.0f}/{d['value']:.0f}", "mmHg", max(s["level"], d["level"]), f"Day {s['day']}"))
                elif k in ev:
                    i, pr = ev[k], rules.PARAMS[k]
                    sub = f"your usual ~{i['mean']:.{max(pr['dec'], 1)}f}" if i["mean"] is not None else f"Day {i['day']}"
                    theme.show(theme.tile(pr["icon"], pr["label"], f"{i['value']:.{pr['dec']}f}", pr["unit"], i["level"], sub))

    # ---- missions + insights
    theme.show(theme.section("Today"))
    left, right = st.columns([1, 1.15], gap="large")
    with left:
        done_n = sum(t["done"] for t in ctx["tasks"])
        theme.show(f'<div class="panel"><h4>{theme.icon("target", 18)} Daily missions <span class="muted" style="font-weight:400">{done_n} of {len(ctx["tasks"])} complete</span></h4>'
                   '<div class="muted">Ticks fill in as you use the app. Each one earns XP.</div></div>')
        for t in ctx["tasks"]:
            c1, c2 = st.columns([5, 1.4])
            with c1:
                if t["auto"]:
                    theme.show(theme.item(t["icon"], t["label"], done=t["done"]))
                else:
                    st.checkbox(f'{t["label"]}  (+{t["xp"]} XP)', value=t["done"], key=f"t_{ctx['aid']}_{day}_{t['key']}",
                                on_change=_toggle, args=(ctx["aid"], day, t["key"], t["xp"]))
            with c2:
                if t["auto"] and not t["done"]:
                    st.button("Open", key=f"go_{t['key']}", on_click=core.goto, args=(t["go"],))
    with right:
        theme.show(f'<div class="panel"><h4>{theme.icon("pulse", 18)} Connected insights</h4><div class="muted">Your vitals, hazards and routines read together.</div></div>')
        top = ctx["insights"][:4]
        if not top:
            theme.show(theme.item("check", "Everything looks steady", "Keep up the routine.", 0))
        for i, it in enumerate(top):
            c1, c2 = st.columns([5, 1.4])
            with c1:
                theme.show(theme.item(it["icon"], it["title"], it["text"], it["level"]))
            with c2:
                st.button("Open", key=f"ins_{i}", on_click=core.goto, args=(it["go"],))

    # ---- story, log, poem
    theme.show(theme.section("Story and reading"))
    c1, c2, c3 = st.columns(3, gap="medium")
    with c1:
        first = story.fill(ch["text"][0], ctx)
        theme.show(f'<div class="panel story" style="height:100%"><div class="chnum">Chapter {ch["n"]} · {rules.HAZARDS[ch["hazard"]]["name"]}</div>'
                   f'<div class="chtitle" style="font-size:1.2rem">{ch["title"]}</div><p style="font-size:.98rem;margin-bottom:0">{first[:230].rsplit(" ", 1)[0]}…</p></div>')
        st.button("Continue reading", key="rd_ch", on_click=core.goto, args=(core.P_JOURNAL,), kwargs=dict(jtab="Chronicle", chap=ch["n"]))
    with c2:
        entry = story.daily_entry(ctx)
        theme.show(f'<div class="panel story" style="height:100%"><div class="chnum">Log of {p["name"].split()[-1]} · day {day}</div>'
                   f'<p style="font-size:.98rem;margin:10px 0 0">{entry[:240].rsplit(" ", 1)[0]}…</p></div>')
        st.button("Open the daily log", key="rd_log", on_click=core.goto, args=(core.P_JOURNAL,), kwargs=dict(jtab="Daily log"))
    with c3:
        key = core.poem_today(ctx)
        a, b = poems.EXCERPTS[key]
        theme.show(f'<div class="panel" style="height:100%"><div class="chnum">From the reading corner</div><div class="chtitle" style="font-size:1.2rem">{poems.POEMS[key]["title"]}</div>'
                   f'<div class="excerpt">{a}<br>{b}</div><div class="muted" style="margin-top:8px">by {poems.AUTHOR}</div></div>')
        st.button("Open the reading corner", key="rd_poem", on_click=core.goto, args=(core.P_JOURNAL,), kwargs=dict(jtab="Reading corner", shelf="Ria Sharma's poems", poem_sel=key))

    # ---- explore
    theme.show(theme.section("Explore"))
    items = [(core.P_HEALTH, "flask", "Check in, trends, guides, surgeon report"), (core.P_BODY, "body", "Tap the body, see how space changes it"),
             (core.P_HAZ, "alert", "NASA's five hazards, tracked for you"), (core.P_JOURNAL, "book", "Story, your diary, and a poetry reading corner"),
             (core.P_PIP, "face", "Ask Pip about space health"), (core.P_GAMES, "game", "Arcade games that train body and brain")]
    for col, (name, ic, desc) in zip(st.columns(6), items):
        with col:
            theme.show(f'<div class="nav-t"><span style="color:#8ec5ff">{theme.icon(ic, 22)}</span><div class="t">{name}</div><div class="d">{desc}</div></div>')
            st.button("Open", key=f"pt_{name}", on_click=core.goto, args=(name,), width="stretch")
