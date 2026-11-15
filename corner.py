"""Creative Corner: story, diary and a quiet reading corner.
  Chronicle      - five hazard chapters + epilogue that unlock as the mission advances
  Daily log      - a first-person entry written from today's real data
  Write          - a private diary for thoughts, poems and letters home
  My diary       - everything you saved; poems can be shared with the crew
  Reading corner - Ria Sharma's poems, plus poems other astronauts chose to share (a calm, stress-relieving read)"""
import html
import re

import streamlit as st

from . import core, db, poems, rules, story, theme

SECTIONS = ["Chronicle", "Daily log", "Write", "My diary", "Reading corner"]
KINDS = ["Thought", "Poem", "Letter home"]
MOODS = ["heavy", "low", "okay", "good", "bright"]
CARE = re.compile(r"suicid|kill myself|self.?harm|want to die|end my life|hurt myself|don'?t want to be here", re.I)
SHELVES = ["Ria Sharma's poems", "Crew shelf"]


# ---------------------------------------------------------------- helpers
def _stanza_html(text):
    blocks = [b for b in text.strip().split("\n\n") if b.strip()]
    return "".join(f'<div class="stz">{"<br>".join(html.escape(l, quote=False) for l in b.split(chr(10)))}</div>' for b in blocks)


def _care_panel():
    theme.show(theme.item("users", "Thank you for writing that down",
                          "It sounds like it was a heavy moment. Your entry is saved privately and was not shared. Please talk to your crew medical officer, "
                          "flight psychologist or a crewmate today. You do not have to carry this alone. If you are on Earth and in danger, call your local emergency number. "
                          "Pip is also here to talk.", 1))
    st.button("Talk to Pip", key="care_pip", on_click=core.goto, args=(core.P_PIP,))


# ---------------------------------------------------------------- story sections
def _chronicle(ctx):
    day = ctx["day"]
    unl = {c["n"] for c in story.unlocked(day)}
    st.session_state.setdefault("chap", story.latest(day)["n"])
    nodes = "".join(f'<div class="node {"on" if c["n"] in unl else ""}"><s></s>{c["title"] if not c.get("epilogue") else "Epilogue"}</div>' for c in story.CHAPTERS)
    theme.show(f'<div class="panel"><b>The Ares-Orion Chronicle</b> <span class="muted">· five hazards, five chapters. New chapters unlock as the mission advances.</span><div class="nodes">{nodes}</div></div>')
    n = st.selectbox("Chapter", [c["n"] for c in story.CHAPTERS], key="chap",
                     format_func=lambda i: f"{i}. {story.CHAPTERS[i - 1]['title']}" + ("" if i in unl else "  (locked)"))
    ch = story.CHAPTERS[n - 1]
    if n not in unl:
        theme.show(f'<div class="panel" style="text-align:center;padding:34px"><span style="color:#8ec5ff">{theme.icon("lock", 30)}</span>'
                   f'<div class="chtitle" style="margin-top:8px">{ch["title"]}</div><div class="muted">Unlocks on mission day {ch["day"]}. You are on day {day}. '
                   'Use “Advance one mission day” in the sidebar to keep the story moving.</div></div>')
        return
    h = rules.HAZARDS[ch["hazard"]]
    paras = "".join(f"<p>{html.escape(story.fill(t, ctx))}</p>" for t in ch["text"])
    theme.show(f'<div class="panel story" style="padding:26px 30px"><div class="chnum">Chapter {n} · <span style="color:{h["color"]}">{h["name"]}</span></div>'
               f'<div class="chtitle">{ch["title"]}</div>{paras}'
               f'<div class="field"><b>Your numbers.</b> {story.data_line(ch, ctx)}</div>'
               f'<div class="field"><b>Field note.</b> {ch["note"]} <a href="{h["url"]}" target="_blank">NASA hazard page</a></div>'
               f'<div class="field"><b>Daily habit.</b> {ch["habit"]}</div></div>')
    c1, c2 = st.columns(2)
    c1.button(f"Open the {h['name'].split(' and ')[0].lower()} dashboard", key="ch_haz", on_click=core.goto, args=(core.P_HAZ,))
    c2.button(f"Read the resonant poem: {poems.POEMS[ch['poem']]['title']}", key="ch_poem", on_click=st.session_state.update,
              kwargs=dict(jtab="Reading corner", shelf=SHELVES[0], poem_sel=ch["poem"]))


def _daily(ctx):
    entry = story.daily_entry(ctx)
    theme.show(f'<div class="panel story" style="padding:26px 30px"><div class="chnum">Log of {ctx["prof"]["name"]} · mission day {ctx["day"]} · {ctx["env_name"]}</div>'
               f'<p style="margin-top:14px">{html.escape(entry)}</p>'
               '<div class="muted">Written from today\'s real readings by AstroCare. Calm, specific, never a diagnosis. Change your numbers and the log changes.</div></div>')
    st.download_button("Download this log entry (.txt)", entry, file_name=f"log_day{ctx['day']}.txt", mime="text/plain")


# ---------------------------------------------------------------- write
def _save():
    ss = st.session_state
    aid = ss["aid"]
    day = db.get_profile(aid)["day"]
    body = ss.get("w_body", "").strip()
    if not body:
        ss["toast"] = "Write a line or two first."
        return
    kind = ss["w_kind"]
    title = ss.get("w_title", "").strip() or {"Thought": "Untitled thought", "Poem": "Untitled poem", "Letter home": "Letter home"}[kind]
    care = bool(CARE.search(f"{title} {body}"))
    share = kind == "Poem" and ss.get("w_share", False) and not care
    db.save_entry(aid, day, kind.lower(), title, body, ss.get("w_mood", "okay"), int(share), int(ss.get("w_name", True)))
    got = db.award(aid, "diary", 8, day)
    msg = "Saved to your diary." + (" +8 XP" if got else "")
    if share and db.award(aid, "poem_shared", 10, day):
        msg = "Poem saved and shared with the crew. +10 XP"
    ss["toast"] = msg
    ss["care"] = care
    ss["w_body"], ss["w_title"], ss["w_share"] = "", "", False


def _write(ctx):
    day = ctx["day"]
    theme.show(f'<div class="panel"><h4>{theme.icon("pen", 18)} Your little diary</h4><div class="muted">A private place for thoughts, poems and letters home. '
               'Nothing is shared unless you choose to share a poem. Writing is a gentle way to look after behavioral health on long missions.</div></div>')
    theme.show(f'<div class="item" style="margin-top:10px"><span style="color:#f0b27a">{theme.icon("book", 20)}</span><div><div class="t">A spark for today</div>'
               f'<div class="excerpt" style="font-size:1.1rem">{html.escape(story.prompt_for(day))}</div></div></div>')
    st.write("")
    st.session_state.setdefault("w_kind", KINDS[0])
    kind = st.radio("What are you writing?", KINDS, key="w_kind", horizontal=True)
    st.text_input("Title (optional)", key="w_title")
    ph = {"Thought": "Whatever is on your mind tonight…", "Poem": "Write your poem here. Line breaks and blank lines between stanzas are kept.",
          "Letter home": "Dear…"}[kind]
    st.text_area("Write here", key="w_body", height=240, placeholder=ph)
    st.select_slider("How are you feeling as you write?", MOODS, value="okay", key="w_mood")
    if kind == "Poem":
        st.checkbox("Share this poem in the Reading corner so other astronauts can read it", key="w_share")
        st.checkbox("Show my name with it (otherwise it appears as “A crewmate”)", value=True, key="w_name")
    st.button("Save to my diary", type="primary", on_click=_save)
    if st.session_state.pop("care", False):
        _care_panel()


# ---------------------------------------------------------------- diary
def _diary(ctx):
    aid = ctx["aid"]
    items = ctx["diary"]
    if not items:
        theme.show('<div class="panel" style="text-align:center;padding:30px"><b>Your diary is empty</b><div class="muted">Open “Write” to add your first page.</div></div>')
        return
    shared = sum(1 for e in items if e["shared"])
    theme.show(f'<div class="panel"><b>{len(items)} pages</b> <span class="muted">· {shared} shared poem(s) · stored on this device, private to you</span></div>')
    diary_txt = "\n\n".join(f"[Mission day {e['day']} · {e['kind']} · {e['title']}]\n{e['body']}" for e in reversed(items))
    st.download_button("Download my whole diary (.txt)", diary_txt, file_name=f"diary_{aid}.txt", mime="text/plain")
    kinds = st.multiselect("Show", [k.lower() for k in KINDS], default=[k.lower() for k in KINDS])
    stars = db.star_counts()
    for e in [x for x in items if x["kind"] in kinds]:
        eid = e["id"]
        chips = theme.plain_tag(e["kind"].capitalize(), "#8ec5ff") + theme.plain_tag(f"day {e['day']}", theme.GREY) + theme.plain_tag(e["mood"], "#f0b27a")
        if e["shared"]:
            chips += theme.plain_tag(f"shared · {stars.get(eid, 0)} star(s)", "#5fd3a0")
        body = _stanza_html(e["body"]) if e["kind"] == "poem" else "<p>" + html.escape(e["body"]).replace("\n", "<br>") + "</p>"
        theme.show(f'<div class="panel story" style="margin-top:12px"><div class="chtitle" style="font-size:1.25rem">{html.escape(e["title"])}</div>'
                   f'<div style="margin-bottom:10px">{chips}</div><div class="{"" if e["kind"] == "poem" else ""}">{body}</div></div>')
        c1, c2, c3 = st.columns([1.3, 1.3, 1])
        if e["kind"] == "poem":
            if e["shared"]:
                c1.button("Remove from crew shelf", key=f"un_{eid}", on_click=db.set_shared, args=(eid, aid, 0))
            elif CARE.search(f"{e['title']} {e['body']}"):
                c1.caption("This poem stays private. Talk to someone you trust if it feels heavy.")
            else:
                c1.button("Share on crew shelf", key=f"sh_{eid}", on_click=db.set_shared, args=(eid, aid, 1))
        with c2.expander("Edit"):
            nt = st.text_input("Title", e["title"], key=f"et_{eid}")
            nb = st.text_area("Text", e["body"], height=160, key=f"eb_{eid}")
            st.button("Update", key=f"up_{eid}", on_click=db.update_entry, args=(eid, aid, nt, nb))
        with c3.expander("Delete"):
            ok = st.checkbox("Yes, delete this page", key=f"dc_{eid}")
            if st.button("Delete", key=f"dl_{eid}", disabled=not ok):
                db.delete_entry(eid, aid)
                st.rerun()


# ---------------------------------------------------------------- reading corner
def _poem_card(title, by, text, small=False):
    h2 = f'<h2 style="font-size:{1.6 if small else 2.1}rem">{html.escape(title)}</h2>'
    theme.show(f'<div class="poem" style="padding:{"26px 30px" if small else "34px 40px"}">{h2}<div class="by">{html.escape(by)}</div>{_stanza_html(text)}</div>')


def _star(eid):
    aid = st.session_state["aid"]
    if db.star(eid, aid):
        db.award(aid, "kindness", 2, db.get_profile(aid)["day"], cap=5)
        st.session_state["toast"] = "Star sent. The poet will be glad."


def _reading(ctx):
    aid = ctx["aid"]
    theme.show(f'<div class="panel"><h4>{theme.icon("book", 18)} Reading corner</h4><div class="muted">A quiet place to slow down. Read one stanza, breathe, read the next. '
               'Poems by Ria Sharma, and poems fellow astronauts chose to share.</div></div>')
    st.session_state.setdefault("shelf", SHELVES[0])
    shelf = st.radio("Shelf", SHELVES, key="shelf", horizontal=True, label_visibility="collapsed")
    st.write("")
    if shelf == SHELVES[0]:
        keys = list(poems.POEMS)
        st.session_state.setdefault("poem_sel", core.poem_today(ctx))
        sel = st.radio("Poem", keys, key="poem_sel", horizontal=True, format_func=lambda k: poems.POEMS[k]["title"], label_visibility="collapsed")
        _poem_card(poems.POEMS[sel]["title"], f"by {poems.AUTHOR}", poems.POEMS[sel]["text"])
        theme.show(f'<div class="muted" style="margin-top:6px">{poems.COPYRIGHT}</div>')
        if sel == core.poem_today(ctx):
            st.caption("Suggested for you today, based on how your mission is going.")
        st.caption("Some poems carry longing and loneliness. If a line stays heavy, talk with Pip, a crewmate, or your flight psychologist.")
    else:
        entries = db.shelf()
        mine_stars, counts = db.starred_by(aid), db.star_counts()
        if not entries:
            theme.show('<div class="panel" style="text-align:center;padding:30px"><b>The crew shelf is empty</b><div class="muted">Be the first: write a poem and choose to share it.</div></div>')
        for e in entries:
            who = (e["author"] or "A crewmate") if e["show_name"] else "A crewmate"
            _poem_card(e["title"], f"by {who} · {e['mission'] or 'mission'} · day {e['day']}", e["body"], small=True)
            n = counts.get(e["id"], 0)
            c1, c2 = st.columns([1, 3])
            if e["astro_id"] == aid:
                c1.caption("You shared this")
            else:
                c1.button("Send a star" if e["id"] not in mine_stars else "Star sent", key=f"star_{e['id']}", on_click=_star, args=(e["id"],),
                          disabled=e["id"] in mine_stars)
            c2.caption(f"{n} star(s)")
        st.caption("Poems shared here appear for every astronaut using this AstroCare installation. On a real mission they would sync over the habitat network. Only poems you choose to share ever appear here.")
        st.button("Write a poem of your own", key="rd_write", on_click=st.session_state.update, kwargs=dict(jtab="Write", w_kind="Poem"))
    with st.expander("A small reading ritual for stress relief"):
        st.markdown("Breathe in for four counts on the first line, out for six on the second. Read slowly. Pause after each stanza and notice one thing you can feel in your body. "
                    "Two or three poems are enough.")
        st.button("Try Orbit Breathing", key="rd_breath", on_click=core.goto, args=(core.P_GAMES,))


def render(ctx):
    n = len(story.unlocked(ctx["day"]))
    theme.show(theme.hero("Creative Corner", "Story, a private diary, and a quiet reading corner for the long stretch between measurements.",
                          f"Chapter {n} of {len(story.CHAPTERS)} unlocked", ctx["env_name"], ctx["env"]["epigraph"]))
    st.write("")
    st.session_state.setdefault("jtab", SECTIONS[0])
    if st.session_state["jtab"] not in SECTIONS:
        st.session_state["jtab"] = SECTIONS[0]
    tab = st.radio("Section", SECTIONS, key="jtab", horizontal=True, label_visibility="collapsed")
    st.write("")
    {"Chronicle": _chronicle, "Daily log": _daily, "Write": _write, "My diary": _diary, "Reading corner": _reading}[tab](ctx)
