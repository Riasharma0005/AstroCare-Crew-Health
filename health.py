"""Health Lab: daily check-in (vitals + wellness + symptoms), trends, how-to guide, surgeon report."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from . import core, db, rules, theme
from .rules import PARAMS

DEFAULTS = dict(hr=68, spo2=98, temp=36.7, sys=115, dia=75, glucose=90, sleep=7.2, mood=7, stress=4, fatigue=4)
LC = {0: "#5fd3a0", 1: "#e8b04a", 2: "#ef6b73"}


def _defaults(ctx):
    d, vit, sym = dict(DEFAULTS), ctx["vit"], []
    if len(vit):
        today = vit[vit["day"] == ctx["day"]]
        src = today.iloc[-1] if len(today) else vit.iloc[-1]
        for k in d:
            if pd.notna(src[k]):
                d[k] = float(src[k])
        if len(today) and src["symptoms"]:
            sym = [s for s in str(src["symptoms"]).split(",") if s.strip() in rules.SYMPTOMS]
            sym = [s.strip() for s in sym]
    return d, sym


def _checkin(ctx):
    aid, day = ctx["aid"], ctx["day"]
    d, sym = _defaults(ctx)
    done = bool(len(ctx["vit"])) and day in set(ctx["vit"]["day"])
    theme.show(f'<div class="panel"><h4>{theme.icon("pulse", 18)} Mission day {day} check-in {theme.tag(0, "saved today") if done else theme.plain_tag("waiting", "#e8b04a")}</h4>'
               '<div class="muted">About a minute. Unsure how to measure something? See “How to measure”. Hover the ? icons for tips.</div></div>')
    with st.form(f"ci_{aid}_{day}"):
        k = lambda n: f"ci_{aid}_{day}_{n}"
        c1, c2, c3, c4 = st.columns(4)
        hr = c1.number_input("Heart rate (bpm)", 20, 220, int(d["hr"]), 1, key=k("hr"), help="Resting, seated, after 5 minutes of calm.")
        spo2 = c2.number_input("Blood oxygen (%)", 70, 100, int(d["spo2"]), 1, key=k("spo2"), help="Fingertip pulse oximeter.")
        temp = c3.number_input("Temperature (°C)", 33.0, 42.0, float(d["temp"]), 0.1, key=k("temp"), format="%.1f")
        sleep = c4.number_input("Sleep last night (h)", 0.0, 16.0, float(d["sleep"]), 0.1, key=k("sleep"), format="%.1f")
        c5, c6, c7, _ = st.columns(4)
        sys_ = c5.number_input("Systolic BP (mmHg)", 60, 260, int(d["sys"]), 1, key=k("sys"))
        dia = c6.number_input("Diastolic BP (mmHg)", 30, 160, int(d["dia"]), 1, key=k("dia"))
        glu = c7.number_input("Glucose (mg/dL)", 30, 500, int(d["glucose"]), 1, key=k("glucose"), help="Fasting is best. Note it if you just ate.")
        s1, s2, s3 = st.columns(3)
        mood = s1.slider("Mood (1 low, 10 great)", 1, 10, int(d["mood"]), key=k("mood"))
        stress = s2.slider("Stress (1 calm, 10 overwhelmed)", 1, 10, int(d["stress"]), key=k("stress"))
        fat = s3.slider("Fatigue (1 fresh, 10 exhausted)", 1, 10, int(d["fatigue"]), key=k("fatigue"))
        syms = st.multiselect("Any symptoms today?", list(rules.SYMPTOMS), default=sym, key=k("sym"))
        note = st.text_input("Note (optional)", key=k("note"))
        go_ = st.form_submit_button("Save check-in", type="primary", width="stretch")
    if go_:
        if dia >= sys_:
            st.error("Diastolic pressure should be lower than systolic. Please re-check the cuff reading.")
        else:
            db.save_vitals(aid, day, dict(hr=hr, spo2=spo2, temp=temp, sys=sys_, dia=dia, glucose=glu, sleep=sleep, mood=mood,
                                          stress=stress, fatigue=fat, symptoms=", ".join(syms), note=note))
            got = db.award(aid, "checkin", 20, day)
            st.session_state["toast"] = "Check-in saved. +20 XP" if got else "Check-in updated"
            st.rerun()

    ev = ctx["ev"]
    if not ev:
        return
    theme.show(theme.section("What your numbers say"))
    items = sorted(ev.items(), key=lambda kv: (-kv[1]["level"], kv[0]))
    cols = st.columns(4)
    for n, (key, i) in enumerate(items):
        pr = PARAMS[key]
        with cols[n % 4]:
            theme.show(theme.tile(pr["icon"], pr["label"], f"{i['value']:.{pr['dec']}f}", pr["unit"], i["level"], f"Day {i['day']} · reference {rules.range_text(key)}"))
            st.write("")
    if "reaction" not in ev:
        st.caption("Reaction time appears here after you play the Reflex Test in Game Zone.")
    flagged = [(k_, i) for k_, i in items if i["level"] >= 1]
    for key, i in flagged:
        pr = PARAMS[key]
        with st.expander(f"{pr['label']}: {rules.LEVEL_NAME[i['level']]}. Why, and what to do", expanded=i["level"] == 2):
            st.markdown(f"**Why:** {i['reason']}")
            st.markdown(f"**What to do:** {i['action']}")
    if not flagged:
        theme.show(theme.item("check", "Every tracked indicator is steady", "Nicely done.", 0))


def _trends(ctx):
    vit = ctx["vit"]
    if len(vit) < 2:
        st.info("Save a few check-ins to see trends. Load the demo mission from the sidebar to preview.")
        return
    lv = rules.levels_by_day(vit)
    keys = [k for k in rules.VITAL_KEYS if vit[k].notna().sum() >= 2]
    k = st.selectbox("Indicator", keys, format_func=lambda x: f"{PARAMS[x]['label']} ({PARAMS[x]['unit']})")
    pr, s = PARAMS[k], vit[["day", k]].dropna()
    g, vals = pr["green"], s[k]
    lo = min(vals.min(), g[0] if g[0] > 0 else vals.min())
    hi = max(vals.max(), vals.max() if k in ("spo2", "mood") else g[1])
    pad = max((hi - lo) * .18, pr["floor"])
    fig = go.Figure()
    fig.add_hrect(y0=max(g[0], lo - pad), y1=min(g[1], hi + pad), fillcolor="rgba(95,211,160,.09)", line_width=0,
                  annotation_text="reference range", annotation_position="top left", annotation_font_color="#5fd3a0")
    h = vals.tail(15).iloc[:-1] if len(vals) > 5 else None
    if h is not None and len(h) >= 5:
        m, sd = h.mean(), max(h.std(ddof=0), pr["floor"])
        fig.add_hrect(y0=m - 2 * sd, y1=m + 2 * sd, fillcolor="rgba(142,197,255,.10)", line_width=0)
        fig.add_hline(y=m, line_dash="dot", line_color="#8ec5ff", annotation_text="your usual", annotation_position="bottom right", annotation_font_color="#8ec5ff")
    cols = [LC[int(lv.loc[int(d), k])] if int(d) in lv.index and pd.notna(lv.loc[int(d), k]) else theme.GREY for d in s["day"]]
    fig.add_trace(go.Scatter(x=s["day"], y=s[k], mode="lines+markers", line=dict(color="#c4d6ee", width=2, shape="spline"),
                             marker=dict(size=10, color=cols, line=dict(color="#050a13", width=1.5)), name=pr["label"], hovertemplate="Day %{x}: %{y}<extra></extra>"))
    if st.toggle("Mark radiation-spike days", value=True):
        d = ctx["daily"]
        for _, r in d[d["radiation"] >= 3 * ctx["env"]["rad_typ"]].iterrows():
            fig.add_vline(x=r["day"], line_dash="dash", line_color="#f0a35e", annotation_text="radiation", annotation_position="top", annotation_font_color="#f0a35e")
    fig.update_yaxes(range=[lo - pad, hi + pad], title=pr["unit"])
    fig.update_xaxes(title="Mission day", dtick=2)
    st.plotly_chart(theme.style_fig(fig, 340), width="stretch", config={"displayModeBar": False})
    st.caption("Dot colour is the status that day. Blue band is your own usual range, green band is the general reference range.")
    theme.show(theme.section("Mission status map"))
    z = lv.astype(float)
    fig2 = go.Figure(go.Heatmap(z=z.T.values, x=z.index, y=[PARAMS[c]["label"] for c in z.columns], zmin=0, zmax=2, showscale=False, xgap=3, ygap=3,
                                colorscale=[[0, "#3f9e7b"], [.5, "#e8b04a"], [1, "#ef6b73"]], hovertemplate="Day %{x} · %{y}: level %{z}<extra></extra>"))
    fig2.update_yaxes(autorange="reversed")
    st.plotly_chart(theme.style_fig(fig2, 380), width="stretch", config={"displayModeBar": False})


def _guide(ctx):
    st.caption("Why each measurement matters, how to take it well, and what the colours mean. Grounded in NASA Human Research Program risks.")
    for k in [x for x in rules.VITAL_KEYS if x != "dia"]:
        pr = PARAMS[k]
        dev, how, why = rules.GUIDE[k]
        with st.expander(pr["label"]):
            st.markdown(f"**Device:** {dev}\n\n**How:** {how}\n\n**Why it matters in space:** {why}")
            a = pr["amber"]
            st.markdown(f"**Steady:** {rules.range_text(k)}  ·  **Watch zone:** {a[0]:g}–{a[1]:g} {pr['unit']}  ·  **Alert:** beyond that.")
            if k == "sys":
                st.caption("Diastolic (the lower number) comes from the same cuff reading.")
    st.info("Colours combine a general reference range with **your own baseline** (your last ~14 readings). Steady does not mean “perfectly healthy”, "
            "and Watch or Alert is not a diagnosis. They tell you when to look closer or call for help.")


def _report(ctx):
    md = core.build_report(ctx)
    st.download_button("Download report for the flight surgeon (.md)", md, file_name=f"astrocare_{ctx['aid']}_day{ctx['day']}.md", mime="text/markdown", type="primary")
    with st.container(border=True):
        st.markdown(md)


def render(ctx):
    lvl = rules.overall(ctx["ev"])
    chips = theme.tag(lvl, f"Overall: {rules.LEVEL_NAME[lvl]}") if lvl is not None else ""
    theme.show(theme.hero("Health Lab", "Measure, understand, act. Every colour comes with a reason and a next step.", f"Mission day {ctx['day']}",
                          ctx["env_name"], chips=chips))
    st.write("")
    t1, t2, t3, t4 = st.tabs(["Daily check-in", "Trends", "How to measure", "Surgeon report"])
    with t1:
        _checkin(ctx)
    with t2:
        _trends(ctx)
    with t3:
        _guide(ctx)
    with t4:
        _report(ctx)
