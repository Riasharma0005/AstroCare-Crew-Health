"""Hazard Zone: NASA's five hazards of human spaceflight, each linked to the indicators it moves.
Content paraphrased from NASA Human Research Program (nasa.gov/hrp/hazards, /risks) and the Canadian Space Agency."""
import plotly.graph_objects as go
import streamlit as st

from . import core, db, rules, theme
from .rules import NASA_LIMIT_MSV, CO2_LEVELS, SOCIAL_MIN_TARGET

HZ = rules.HAZARDS


def _card(key, ctx, lead, bullets, counters, risks):
    h = HZ[key]
    lvl = core.hazard_status(ctx).get(key, 0)
    lis = "".join(f"<li>{b}</li>" for b in bullets)
    cs = "".join(f"<li>{c}</li>" for c in counters)
    rk = " · ".join(f'<a href="{u}" target="_blank" style="color:#8ec5ff">{n}</a>' for n, u in risks)
    theme.show(f'<div class="panel" style="border-left:3px solid {h["color"]}"><h4><span style="color:{h["color"]}">{theme.icon(h["icon"], 20)}</span> {h["name"]} {theme.tag(lvl)}</h4>'
               f'<div style="color:#cbd6e8">{lead}</div>'
               f'<div style="display:flex;gap:28px;flex-wrap:wrap;margin-top:10px"><div style="flex:1 1 280px"><b>How it shows up in your health</b><ul style="margin:4px 0">{lis}</ul></div>'
               f'<div style="flex:1 1 280px"><b>Countermeasures</b><ul style="margin:4px 0">{cs}</ul></div></div>'
               f'<div class="muted" style="margin-top:6px">NASA risks linked here: {rk} · <a href="{h["url"]}" target="_blank" style="color:#8ec5ff">NASA hazard page</a></div></div>')
    for it in [i for i in ctx["insights"] if i["tag"] == key and i["level"] >= 1]:
        theme.show(theme.item(it["icon"], it["title"], it["text"], it["level"]))


def _bar(d, col, target, color, unit, tlabel):
    fig = go.Figure(go.Bar(x=d["day"], y=d[col], marker_color=color, hovertemplate="Day %{x}: %{y}<extra></extra>"))
    if target:
        fig.add_hline(y=target, line_dash="dot", line_color="#5fd3a0", annotation_text=tlabel, annotation_font_color="#5fd3a0")
    fig.update_yaxes(title=unit)
    fig.update_xaxes(title="Mission day")
    st.plotly_chart(theme.style_fig(fig, 270), width="stretch", config={"displayModeBar": False})


def _log_form(ctx):
    aid, day, env = ctx["aid"], ctx["day"], ctx["env"]
    t = ctx["today_daily"]
    with st.expander(f"Log hazards for mission day {day}" + ("  ·  saved" if t else ""), expanded=t is None):
        with st.form(f"hz_{aid}_{day}"):
            c1, c2, c3, c4 = st.columns(4)
            rad = c1.number_input("Radiation dose (mSv)", 0.0, 100.0, float(t["radiation"] if t else env["rad_typ"]), 0.01, format="%.2f",
                                  help=f"From your dosimeter. Typical here is about {env['rad_typ']} mSv/day.")
            ex = c2.number_input("Exercise (min)", 0, 300, int(t["exercise"] if t else 0), 5, help=f"Target for {ctx['env_name']}: {env['ex_target']} min.")
            co2 = c3.number_input("Cabin CO₂ (ppm)", 300, 20000, int(t["co2"] if t else 2000), 50)
            soc = c4.number_input("Social contact (min)", 0, 600, int(t["social"] if t else 30), 5, help="Time spent talking with crew or family.")
            if st.form_submit_button("Save hazard log", type="primary", width="stretch"):
                db.save_daily(aid, day, rad, ex, co2, soc)
                got = core.award_daily(ctx, rad, ex, co2, soc)
                st.session_state["toast"] = "Hazard log saved. +XP" if got else "Hazard log updated"
                st.rerun()


def _interplay(ctx):
    """NASA notes the hazards can feed off one another. Show which of YOUR hazards are active together."""
    hz = core.hazard_status(ctx)
    active = [k for k, v in hz.items() if v >= 1]
    ev = ctx["ev"]
    if ev.get("sleep") and ev["sleep"]["level"] >= 1:
        active.append("sleep")
    names = {"radiation": "radiation", "isolation": "low contact", "distance": "distance", "gravity": "low exercise", "env": "cabin air", "sleep": "short sleep"}
    if len(active) >= 2:
        chain = " + ".join(names[a] for a in active)
        theme.show(theme.item("pulse", "Hazards are overlapping", f"Right now: {chain}. NASA notes the hazards can feed off one another, so AstroCare reads them together. "
                                                                  "Tackle the easiest lever first (sleep, contact or exercise).", 1))


def render(ctx):
    env, d = ctx["env"], ctx["daily"]
    hz = core.hazard_status(ctx)
    worst = max(hz.values())
    theme.show(theme.hero("Hazard Zone", f"NASA's five hazards of human spaceflight, tuned for {ctx['env_name']}. {env['focus']}", "Human Research Program · five hazards",
                          ctx["env_name"], chips=theme.tag(worst, f"Hazards: {rules.LEVEL_NAME[worst]}")))
    st.write("")
    _interplay(ctx)
    _log_form(ctx)
    tabs = st.tabs([HZ[k]["name"].split(" and ")[0] for k in HZ])

    with tabs[0]:
        _card("radiation", ctx, "Invisible to the eye, space radiation is one of the most hazardous parts of spaceflight, from the Sun and from deep space.",
              ["Long term: NASA tracks radiation-induced cancer risk and other effects on the body.",
               "After a solar storm, watch sleep, fatigue and mood over the following days.",
               "Neutrons contribute about 30% of radiation on the ISS (Canadian Space Agency), so measurement must be continuous."],
              ["Shelter during solar particle events", "Check the dosimeter daily", "Plan spacewalks around space-weather alerts"],
              [("Radiation-induced cancers", rules.RISKS[-1][2])])
        if len(d):
            tot = d["radiation"].sum()
            pct = min(100, tot / NASA_LIMIT_MSV * 100)
            theme.show(f'<div class="panel" style="margin-top:10px"><b>Cumulative logged dose: {tot:.1f} mSv</b> <span class="muted">of the {NASA_LIMIT_MSV} mSv NASA career limit ({pct:.1f}%)</span>'
                       f'<div class="bar"><i style="width:{max(pct, 1)}%"></i></div></div>')
            _bar(d, "radiation", env["rad_typ"] * 3, HZ["radiation"]["color"], "mSv/day", "spike threshold (3× typical)")

    with tabs[1]:
        _card("isolation", ctx, "Groups far from Earth, isolated and confined in a small space for a long time, show behavioral responses. Crews are carefully chosen, trained and supported.",
              ["Rising stress or falling mood often appears in the Health Lab days before anything else.",
               "Low social contact together with poor sleep is a classic warning pattern."],
              ["A daily call with crew or family", "A fixed sleep routine", "Orbit Breathing in the Game Zone, or a page in your Creative Corner diary", "Use ground psychological support"],
              [("Behavioral changes", rules.RISKS[11][2]), ("Teamwork", rules.RISKS[12][2]), ("Sleep", rules.RISKS[13][2])])
        if len(d):
            fig = go.Figure(go.Bar(x=d["day"], y=d["social"], marker_color=HZ["isolation"]["color"], name="Social contact (min)"))
            fig.add_hline(y=SOCIAL_MIN_TARGET, line_dash="dot", line_color="#5fd3a0", annotation_text="minimum goal", annotation_font_color="#5fd3a0")
            v = ctx["vit"]
            if len(v):
                fig.add_trace(go.Scatter(x=v["day"], y=v["mood"], name="Mood (/10)", yaxis="y2", line=dict(color="#f0b27a", width=2.5)))
                fig.update_layout(yaxis2=dict(overlaying="y", side="right", range=[0, 10], showgrid=False, title="Mood"))
            fig.update_xaxes(title="Mission day")
            fig.update_yaxes(title="minutes")
            st.plotly_chart(theme.style_fig(fig, 290), width="stretch", config={"displayModeBar": False})

    with tabs[2]:
        _card("distance", ctx, "Instructions, supplies and medical care get harder to receive as crews go deeper. Mars averages around 140 million miles from Earth, "
                               "so planning and self-sufficiency are the plan.",
              ["No single indicator moves, but the cost of a late call rises with delay.", f"One-way delay here: <b>{env['delay']}</b>."],
              ["Know your emergency protocols by heart", "Keep the medical kit inventory current", "Send a clear, short status report early"],
              [("Inadequate systems operations support", rules.RISKS[14][2])])
        rtt = env["rtt_min"]
        theme.show(f'<div class="panel" style="margin-top:10px"><h4>{theme.icon("signal", 18)} Delay simulator</h4><div class="muted">If you report a problem at T+0, the earliest reply arrives about '
                   f'<b>{rtt:g} min</b> later (round trip).</div></div>')
        for t_, what in [("T+0", "You notice a red-flag indicator and start your onboard protocol"), ("T+1 min", "You re-measure and send a short status message"),
                         (f"T+{rtt + 1:g} min", "Earliest ground reply reaches you")]:
            theme.show(theme.item("target", t_, what))
        st.markdown("**Autonomy checklist**")
        for i, it in enumerate(["I know where the medical kit is", "I know my emergency contact procedure", "Medications and supplies checked this week", "Next ground-contact window planned"]):
            st.checkbox(it, key=f"auto_{ctx['aid']}_{i}")

    with tabs[3]:
        _card("gravity", ctx, f"Muscles, bones, the inner ear and organs must adjust to each new gravity. You are in {env['gravity']}.",
              ["Without loading, bones weaken and muscles lose strength. On Mars NASA expects about three-eighths of Earth's gravity for up to two years.",
               "Fluids shift, so heart rate and blood pressure can drift, and the eyes can change (SANS)."],
              ["Daily resistive and aerobic exercise", "Nutrition for bone health as advised", "Report back pain, dizziness or vision changes early"],
              [("Bone changes", rules.RISKS[10][2]), ("Fitness", rules.RISKS[8][2]), ("Cardiovascular", rules.RISKS[2][2]), ("SANS", rules.RISKS[9][2])])
        if len(d):
            _bar(d, "exercise", env["ex_target"], HZ["gravity"]["color"], "minutes", f"target {env['ex_target']} min")

    with tabs[4]:
        _card("env", ctx, "A spacecraft is a home and a machine. Temperature, pressure, lighting, noise, microbes and air all shape how the crew feels and how the immune system responds.",
              ["High CO₂ causes headaches and drowsiness. Falling SpO₂ and a rising temperature are early flags.", "Dust (especially lunar and Martian) irritates eyes and airways."],
              ["Check scrubbers and filters", "Dust control at the airlock", "Clean shared surfaces", "Report breathing symptoms early"],
              [("Hypoxia", rules.RISKS[5][2]), ("Host-microorganism interactions", rules.RISKS[4][2]), ("Immune responses", rules.RISKS[0][2])])
        if len(d):
            fig = go.Figure(go.Scatter(x=d["day"], y=d["co2"], mode="lines+markers", line=dict(color=HZ["env"]["color"], width=2.5), name="CO₂ (ppm)"))
            fig.add_hline(y=CO2_LEVELS[0], line_dash="dot", line_color="#e8b04a", annotation_text="watch", annotation_font_color="#e8b04a")
            fig.add_hline(y=CO2_LEVELS[1], line_dash="dot", line_color="#ef6b73", annotation_text="alert", annotation_font_color="#ef6b73")
            fig.update_xaxes(title="Mission day")
            fig.update_yaxes(title="ppm")
            st.plotly_chart(theme.style_fig(fig, 290), width="stretch", config={"displayModeBar": False})
            st.caption("Demo thresholds. Always use your habitat's official CO₂ limits.")

    with st.expander("Sources and references"):
        for n, u in rules.SOURCES:
            st.markdown(f"- [{n}]({u})")
        st.caption("AstroCare paraphrases these public resources for education. It is not an official NASA or CSA product.")
