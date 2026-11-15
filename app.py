"""AstroCare: crew health intelligence for long-duration spaceflight.  Run with:  streamlit run app.py

Seven views, one connected brain:
  Mission Control · Health Lab · Body Explorer · Hazard Zone · Creative Corner · Pip Companion · Game Zone
Professional mission-control look everywhere, with a playful alien-planet style reserved for Pip and the Game Zone.
Educational prototype with SIMULATED demo data. Not a medical device.
"""
import streamlit as st

from modules import body, corner, core, db, hazards, health, home, games, pip, rules, theme
from modules.rules import ENVS

st.set_page_config(page_title="AstroCare · Crew Health Intelligence", page_icon="🪐", layout="wide", initial_sidebar_state="expanded")
db.ensure_demo()

ss = st.session_state
ids = [p["astro_id"] for p in db.list_profiles()]
if ss.get("aid") not in ids:
    ss["aid"] = ids[0]
ss.setdefault("nav", core.PAGES[0])
if ss["nav"] not in core.PAGES:
    ss["nav"] = core.PAGES[0]
theme.inject(cute=ss["nav"] in core.CUTE_PAGES)


def _save_profile():
    a = ss["aid"]
    new_id, name = ss[f"pf_id_{a}"].strip(), ss[f"pf_name_{a}"].strip()
    if not new_id or not name:
        ss["toast"] = "Please enter both an ID and a name."
        return
    dur = int(ss[f"pf_dur_{a}"])
    db.save_profile(new_id, name, ss[f"pf_mis_{a}"].strip() or "MISSION-01", ss[f"pf_env_{a}"], min(int(ss[f"pf_day_{a}"]), dur), dur)
    ss["aid"] = new_id
    ss["toast"] = "Profile saved"


ctx = core.build_ctx(ss["aid"])
prof, r = ctx["prof"], ctx["rank"]

# ------------------------------------------------------------------ sidebar
with st.sidebar:
    theme.show(f'<div style="display:flex;align-items:center;gap:10px;margin:4px 0 10px"><span style="color:#8ec5ff">{theme.icon("orbit", 30)}</span>'
               '<div><div style="font-family:var(--head);font-weight:700;font-size:1.3rem;letter-spacing:-.02em;color:#fff">AstroCare</div>'
               '<div class="muted">Crew health intelligence</div></div></div>')
    st.radio("Navigate", core.PAGES, key="nav", label_visibility="collapsed")
    theme.show(f'<div class="panel" style="margin-top:12px;padding:14px 16px"><div style="font-family:var(--head);font-weight:600;color:#fff">{prof["name"]}</div>'
               f'<div class="muted">{ctx["env_name"]} · day {ctx["day"]} of {ctx["duration"]}</div>'
               f'<div style="margin-top:10px;display:flex;justify-content:space-between"><b>{r["name"]}</b><span class="muted">{ctx["xp"]} XP</span></div>'
               f'<div class="bar" style="height:6px;margin:6px 0"><i style="width:{max(r["pct"] * 100, 4):.0f}%"></i></div>'
               f'<div class="muted">{ctx["streak"]}-day check-in streak{(" · " + str(r["to_next"]) + " XP to " + r["next"]) if r["next"] else ""}</div></div>')
    with st.expander("Crew and mission setup"):
        profiles = db.list_profiles()
        if len(profiles) > 1:
            st.selectbox("Active astronaut", ids, key="aid", format_func=lambda i: next(p["name"] for p in profiles if p["astro_id"] == i))
        a = ss["aid"]
        st.text_input("Astronaut ID", prof["astro_id"], key=f"pf_id_{a}", help="Change the ID to create a new astronaut.")
        st.text_input("Name", prof["name"], key=f"pf_name_{a}")
        st.text_input("Mission", prof["mission"], key=f"pf_mis_{a}")
        envs = list(ENVS)
        st.selectbox("Environment", envs, index=envs.index(prof["environment"]), key=f"pf_env_{a}")
        st.number_input("Mission day", 1, 3000, int(prof["day"]), key=f"pf_day_{a}")
        st.number_input("Total days", 1, 3000, int(prof["duration"]), key=f"pf_dur_{a}")
        st.button("Save profile", on_click=_save_profile, width="stretch")
        if st.button("Advance one mission day", width="stretch", disabled=ctx["day"] >= ctx["duration"]):
            db.set_day(a, ctx["day"] + 1)
            ss["toast"] = f"Mission day {ctx['day'] + 1}"
            st.rerun()
        st.divider()
        sure = st.checkbox("Reset everything to the demo mission", key="sure_reset")
        if st.button("Reset demo data", disabled=not sure, width="stretch"):
            db.reset_all()
            db.seed_demo()
            ss["aid"] = "AST-001"
            ss.pop("seen_nonces", None)
            st.rerun()
    st.caption("Prototype · simulated demo data · not a medical device")

if msg := ss.pop("toast", None):
    st.toast(msg)

# ------------------------------------------------------------------ pages
ROUTES = {core.P_HOME: home.render, core.P_HEALTH: health.render, core.P_BODY: body.render, core.P_HAZ: hazards.render,
          core.P_JOURNAL: corner.render, core.P_PIP: pip.render, core.P_GAMES: games.render}
ROUTES[ss["nav"]](ctx)

links = " · ".join(f'<a href="{u}" target="_blank" style="color:#8ec5ff">{n.split(":")[0]}{": " + n.split(":")[1].strip() if ":" in n else ""}</a>' for n, u in rules.SOURCES[:5])
theme.show(f'<div class="muted" style="text-align:center;margin-top:30px;line-height:1.7">Built on public resources from NASA Human Research Program and the Canadian Space Agency<br>{links}<br>'
           'Educational prototype · simulated data · not for clinical use · mission protocols and flight surgeons always come first<br>Original poems by Ria Sharma.</div>')
