"""🎮 Game Zone: arcade games that feed the rest of the app.
   ⚡ Reflex Test   -> becomes your 'Reaction time' health indicator (fatigue check)
   🫧 Orbit Breathing -> stress relief, XP and a badge
   🛸 Asteroid Dodge / 🌈 Planet Memory / 🧠 Hazard Quiz -> XP, ranks and badges
Each game sends its score straight back to Python through a tiny custom component."""
import random
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

from . import core, db, poems, rules, theme

_game = components.declare_component("astro_games", path=str(Path(__file__).parent / "games_component"))

XP_CAP = {"dodge": 3, "reflex": 2, "memory": 3, "breath": 2, "quiz": 2}
LABEL = {"dodge": "🛸 Asteroid Dodge", "reflex": "⚡ Reflex Test", "memory": "🌈 Planet Memory", "breath": "🫧 Orbit Breathing", "quiz": "🧠 Hazard Quiz"}


def _xp_for(game, score):
    if game == "dodge":
        return 5 + min(25, int(score) // 15)
    if game == "reflex":
        return 10 + (10 if score <= 250 else 5 if score <= 300 else 0)
    if game == "memory":
        return min(30, 4 + 3 * int(score))
    if game == "breath":
        return 10
    if game == "quiz":
        return 4 * int(score)
    return 0


def _handle(ctx, res):
    """Process a result sent from a game exactly once, then refresh the page."""
    if not isinstance(res, dict) or "nonce" not in res:
        return
    seen = st.session_state.setdefault("seen_nonces", set())
    if res["nonce"] in seen:
        return
    seen.add(res["nonce"])
    g, sc = res["game"], float(res["score"])
    db.add_game_score(ctx["aid"], g, sc, ctx["day"])
    xp = _xp_for(g, sc)
    got = db.award(ctx["aid"], f"game:{g}", xp, ctx["day"], cap=XP_CAP[g])
    extra = " · logged as today's reaction indicator ⚡" if g == "reflex" else ""
    st.session_state["toast"] = (f"{LABEL[g]}: +{xp} XP ⭐{extra}" if got else f"{LABEL[g]} saved (daily XP limit reached){extra}")
    st.rerun()


def _play(ctx, game, title, blurb):
    st.caption(blurb)
    res = _game(game=game, key=f"cmp_{game}_{ctx['aid']}", default=None, verses=poems.BREATH_VERSES)
    _handle(ctx, res)


QUIZ = [
    ("Which of these is NOT one of NASA's five hazards of human spaceflight?", ["Space radiation", "Isolation and confinement", "Rising ocean tides", "Distance from Earth"], 2,
     "The five are radiation, isolation and confinement, distance from Earth, gravity fields, and hostile closed environments."),
    ("What is the main defence against bone and muscle loss in space?", ["Sleeping more", "Daily resistive and aerobic exercise", "Drinking more water", "Wearing warm clothes"], 1,
     "Without gravity's load, bones and muscles weaken. Daily exercise is the key countermeasure."),
    ("What is a solar particle event?", ["A bright sunrise", "A burst of high-energy particles from the Sun", "A habitat power cut", "A meteor shower"], 1,
     "These bursts raise radiation dose, so crews shelter in the best-shielded area."),
    ("Why does distance from Earth make health care harder?", ["Gravity is stronger", "Help and resupply take much longer", "Doctors are not allowed to talk", "Food spoils faster"], 1,
     "Delays of minutes to hours mean crews need medical autonomy."),
    ("SpO₂ estimates…", ["How fast you breathe", "How much haemoglobin is carrying oxygen", "Your blood sugar", "Your lung size"], 1,
     "A pulse oximeter estimates oxygen saturation of the blood."),
    ("In microgravity, body fluids shift mainly toward the…", ["Feet", "Hands", "Head", "Stomach"], 2,
     "The head-ward fluid shift is linked to puffy faces and vision changes (SANS)."),
    ("Why compare your numbers with your OWN baseline?", ["Because every body is different and small changes show early", "It is more fun", "Reference ranges are always wrong", "It replaces the doctor"], 0,
     "Personal baselines catch drifts that a general range would miss."),
    ("An indicator is on Alert and stays Alert after a careful re-measure. What now?", ["Ignore it", "Play a game", "Contact the crew medical officer / flight surgeon", "Sleep it off"], 2,
     "Confirmed alerts need medical contact. Follow the mission protocol."),
    ("Rising cabin CO₂ can cause…", ["Headaches and drowsiness", "Stronger muscles", "Faster healing", "Better sleep"], 0,
     "CO₂ build-up is a classic closed-environment hazard."),
    ("Best way to measure blood pressure?", ["Right after exercise", "Seated and rested, same way every day", "While walking", "Only when you feel ill"], 1,
     "Consistent technique makes day-to-day changes meaningful."),
    ("Which habit best protects mood during isolation?", ["Skipping meals", "Working non-stop", "Regular social contact and routines", "Avoiding sunlight-like lighting"], 2,
     "Contact and routine are proven buffers against isolation stress."),
    ("One-way radio delay between Mars and Earth is up to roughly…", ["1 second", "22 minutes", "2 hours", "1 day"], 1,
     "It ranges from about 3 to 22 minutes depending on planetary positions."),
]


def _quiz(ctx):
    aid = ctx["aid"]
    sk = f"quiz_seed_{aid}"
    st.session_state.setdefault(sk, random.randint(1, 10_000))
    qs = random.Random(st.session_state[sk]).sample(QUIZ, 5)
    st.caption("Five questions about the five hazards. +4 XP per correct answer.")
    with st.form(f"quiz_{aid}_{st.session_state[sk]}"):
        picks = [st.radio(f"{i + 1}. {q[0]}", q[1], index=None, key=f"qz_{aid}_{st.session_state[sk]}_{i}") for i, q in enumerate(qs)]
        sub = st.form_submit_button("Submit answers", type="primary")
    if sub:
        if any(p is None for p in picks):
            st.warning("Answer all five questions first.")
        else:
            score = sum(q[1][q[2]] == p for q, p in zip(qs, picks))
            for q, p in zip(qs, picks):
                ok = q[1][q[2]] == p
                st.markdown(f"{'✅' if ok else '❌'} **{q[1][q[2]]}**: {q[3]}")
            db.add_game_score(aid, "quiz", score, ctx["day"])
            got = db.award(aid, "game:quiz", _xp_for("quiz", score), ctx["day"], cap=XP_CAP["quiz"])
            st.success(f"You scored {score}/5!" + (f" +{_xp_for('quiz', score)} XP ⭐" if got else " (daily XP limit reached)"))
            if score == 5:
                st.balloons()
    if st.button("🔀 New questions", key="newquiz"):
        st.session_state[sk] = random.randint(1, 10_000)
        st.rerun()


def _hall(ctx):
    sc = ctx["scores"]
    cols = st.columns(5)

    def best(g, low=False):
        s = sc[sc["game"] == g]["score"] if len(sc) else []
        return None if len(s) == 0 else (s.min() if low else s.max())

    items = [("⚡", "Best reflex", best("reflex", True), "ms"), ("🛸", "Best dodge", best("dodge"), "pts"), ("🌈", "Best memory", best("memory"), "steps"),
             ("🫧", "Breathing", int((sc["game"] == "breath").sum()) if len(sc) else 0, "sessions"), ("🧠", "Best quiz", best("quiz"), "/ 5")]
    for col, (ic, lab, v, u) in zip(cols, items):
        with col:
            theme.show(theme.cute_stat(ic, lab, "–" if v is None else f"{v:.0f}", u))
    st.write("")
    bd = db.xp_breakdown(ctx["aid"])
    if len(bd):
        fig = go.Figure(go.Bar(x=bd["xp"], y=bd["source"], orientation="h", marker_color="#ff8fd8"))
        fig.update_yaxes(autorange="reversed")
        fig.update_xaxes(title="XP")
        st.markdown("##### ⭐ Where your XP came from")
        st.plotly_chart(theme.style_fig(fig, 280), width="stretch", config={"displayModeBar": False})
    st.markdown("##### 🏅 Badges")
    theme.show("".join(f'<div class="cbadge {"on" if ok else "off"}"><div class="i">{i}</div><div class="n">{n}</div><div class="d">{d}</div></div>' for i, n, d, ok in core.badges(ctx)))


def render(ctx):
    r = ctx["rank"]
    nxt = f"{r['to_next']} XP to {r['next']}" if r["next"] else "Max rank!"
    theme.show(theme.cute_hero("Game Zone", "Arcade fun that trains your body and brain. Your scores feed your rank, badges and even your health trends.",
                          theme.cute("sky", 110, "wow"),
                          theme.cute_chip(f"{r['icon']} {r['name']}", "#ff8fd8") + theme.cute_chip(f"⭐ {ctx['xp']} XP · {nxt}", "#ffd36b")
                          + theme.cute_chip("⚡ Reflex Test updates your Health Lab", "#6df2c4")))
    theme.show(f'<div class="ccard" style="margin-top:12px"><div class="ctrack"><div class="cfill" style="width:{max(r["pct"] * 100, 3):.0f}%"></div>'
               f'<div class="crocket" style="left:{max(r["pct"] * 100, 3):.0f}%">🚀</div></div></div>')
    st.write("")
    tabs = st.tabs(["🛸 Asteroid Dodge", "⚡ Reflex Test", "🌈 Planet Memory", "🫧 Orbit Breathing", "🧠 Hazard Quiz", "🏆 Hall of Fame"])
    with tabs[0]:
        _play(ctx, "dodge", "Asteroid Dodge", "Pilot your UFO through the asteroid belt. Great for hand-eye coordination. Up to 3 XP-earning runs a day.")
    with tabs[1]:
        _play(ctx, "reflex", "Reflex Test", "5 rounds. Your average is saved as today's reaction time, a quick fatigue check in your Health Lab trends.")
    with tabs[2]:
        _play(ctx, "memory", "Planet Memory", "Repeat the glowing planet pattern. Trains working memory, which suffers when you are tired.")
    with tabs[3]:
        _play(ctx, "breath", "Orbit Breathing", "One minute of 4-4-6 breathing to calm stress, with lines from Ria Sharma's poem Stardust to read as you breathe.")
    with tabs[4]:
        _quiz(ctx)
    with tabs[5]:
        _hall(ctx)
