"""👾 Pip Companion: a friendly, rule-based space-health guide.
No cloud AI: Pip answers from a curated knowledge base AND from the astronaut's own data.
Safety first: emergencies and self-harm words always get an escalation message, never a lecture."""
import re

import streamlit as st

from . import core, rules, theme
from .rules import PARAMS

EMERGENCY = r"chest pain|can'?t breathe|cannot breathe|trouble breathing|faint|unconscious|bleeding|seizure|stroke|overdose"
SELF_HARM = r"suicid|kill myself|self.?harm|want to die|end my life|hurt myself"

QUICK = ["How am I doing?", "What should I do today?", "Why is my sleep important?", "Tell me about radiation",
         "I feel lonely or stressed", "When should I call the flight surgeon?", "How do I protect my bones?"]


def _flag_lines(ctx):
    fl = [(k, i) for k, i in ctx["ev"].items() if i["level"] >= 1]
    return [f"**{PARAMS[k]['label']}** is on {rules.LEVEL_NAME[i['level']]} ({i['value']:.{PARAMS[k]['dec']}f} {PARAMS[k]['unit']})" for k, i in sorted(fl, key=lambda x: -x[1]['level'])]


def _mine(ctx, key):
    i = ctx["ev"].get(key)
    if not i:
        return ""
    p = PARAMS[key]
    return f"\n\n📊 *Your data:* {p['label']} is **{i['value']:.{p['dec']}f} {p['unit']}** ({rules.LEVEL_NAME[i['level']]}). {i['reason']}"


def answer(q, ctx):
    t = q.lower()
    env, name = ctx["env"], ctx["prof"]["name"].split()[-1]
    if re.search(SELF_HARM, t):
        return ("💜 I'm really glad you told me. Please contact your **crew medical officer or flight psychologist right now**, and stay with a crew member. "
                "You don't have to carry this alone. If you are on Earth and in danger, call your local emergency number immediately.")
    if re.search(EMERGENCY, t):
        return ("🚨 **This could be urgent.** Alert your crew and the crew medical officer now and follow your mission emergency protocol. "
                f"{env['autonomy']} I can't diagnose, so please don't wait for me.")
    if re.search(r"how am i|status|doing|my health|overview", t):
        fl = _flag_lines(ctx)
        if not ctx["ev"]:
            return "I don't have any check-ins from you yet. Open the **Health Lab** and log one. It takes about a minute! ⭐"
        head = f"Here's your picture, {name}: overall **{rules.LEVEL_NAME[rules.overall(ctx['ev'])]}**."
        body = ("\n\n" + "\n".join(f"- {x}" for x in fl)) if fl else "\n\nEverything tracked looks steady. 🌟"
        ins = [i for i in ctx["insights"] if i["level"] >= 1][:2]
        extra = ("\n\n**Connected insights:**\n" + "\n".join(f"- {i['title']}: {i['text']}" for i in ins)) if ins else ""
        return head + body + extra
    if re.search(r"today|to ?do|task|mission|what should i", t):
        todo = [x for x in ctx["tasks"] if not x["done"]]
        if not todo:
            return "All of today's missions are done. 🎉 Maybe a game of Asteroid Dodge as a reward?"
        return "Here's what's left today:\n" + "\n".join(f"- {x['icon']} {x['label']}" + (f" (+{x['xp']} XP)" if x["xp"] else "") for x in todo)
    if re.search(r"sleep|tired|fatigue|insomnia|rest", t):
        return ("🌙 Sleep is your most powerful countermeasure. Light cycles in space are artificial, so keep a fixed schedule, dim lights before bed, "
                "and cut screens late. Short sleep slows thinking, mood and reaction time, which is why AstroCare compares them together." + _mine(ctx, "sleep") + _mine(ctx, "reaction"))
    if re.search(r"radiat|solar|cosmic|dose|msv", t):
        d = ctx["daily"]
        tot = f"\n\n📊 *Your data:* **{d['radiation'].sum():.1f} mSv** logged so far ({d['radiation'].sum() / rules.NASA_LIMIT_MSV * 100:.1f}% of the NASA {rules.NASA_LIMIT_MSV} mSv career limit)." if len(d) else ""
        return ("☢️ Space radiation comes from galactic cosmic rays and solar particle events. Over years it raises cancer and possibly heart and brain risks; "
                f"short solar storms can add fatigue. Typical dose here is about {env['rad_typ']} mSv/day. Use the storm shelter during alerts and check your dosimeter." + tot)
    if re.search(r"bone|muscle|exercise|workout|gravity|strength|treadmill", t):
        d = ctx["daily"]
        mine = f"\n\n📊 *Your data:* last 3 days average **{d['exercise'].tail(3).mean():.0f} min** vs a target of {env['ex_target']}." if len(d) >= 3 else ""
        return (f"💪 In {env['gravity']}, bones and muscles get less loading and can weaken. Daily resistive plus aerobic exercise is the main defence, "
                "with good protein, calcium and vitamin D as advised." + mine)
    if re.search(r"lonel|isolat|stress|mood|anxi|homesick|sad|mental|calm|breath", t):
        return ("👥 Isolation and confinement are an official NASA hazard, and feeling this way is normal. Try: a call with someone you love, a shared meal, "
                "a few honest lines in your **Creative Corner** diary, and **Orbit Breathing** in the Game Zone. If it lasts more than a few days or gets heavy, talk to your flight psychologist." + _mine(ctx, "stress") + _mine(ctx, "mood"))
    if re.search(r"poem|poetry|story|chapter|chronicle|journal|reflect|verse", t):
        from . import poems, story
        key = core.poem_today(ctx)
        a, b = poems.EXCERPTS[key]
        n = len(story.unlocked(ctx["day"]))
        return (f"📖 Open the **Creative Corner**: {n} of {len(story.CHAPTERS)} story chapters are unlocked, you can keep a private diary, "
                f"and the reading corner has original poems by {poems.AUTHOR} plus poems fellow astronauts shared. For today I'd pick *{poems.POEMS[key]['title']}*:\n\n> {a}  \n> {b}")
    if re.search(r"heart|blood pressure|\bbp\b|pulse|cardio", t):
        return ("💓 In space, fluids shift upward and the heart works less against gravity, so it can lose fitness over time. Exercise helps most. "
                "Measure seated after 5 calm minutes, always the same way." + _mine(ctx, "hr") + _mine(ctx, "sys"))
    if re.search(r"glucose|sugar|food|nutrition|diet|eat|meal|hydrat|water", t):
        return ("🍎 Stress, activity changes and food variety shift how the body handles sugar. Eat regular balanced meals, hydrate, and measure glucose fasting when you can." + _mine(ctx, "glucose"))
    if re.search(r"oxygen|spo2|lung|dust|co2|air|cabin", t):
        return ("🫁 Closed habitats can build up CO₂ and dust. Falling SpO₂, headaches or drowsiness are early flags. Check scrubbers, filters and airlock dust control." + _mine(ctx, "spo2"))
    if re.search(r"temp|fever|sick|ill|infection|immune", t):
        return ("🌡️ A shared habitat spreads germs easily and stress can weaken immunity. Wipe shared surfaces and tell your crew medical officer about a fever or lasting illness." + _mine(ctx, "temp"))
    if re.search(r"call|flight surgeon|doctor|medical|escalate|delay|ground|distance|when should", t):
        return (f"📡 **When to call:** any red-flag symptom (chest pain, trouble breathing, fainting, blurred vision, racing heartbeat) or any indicator on Alert that stays Alert after a careful re-measurement. "
                f"Also tell the crew medical officer if a Watch lasts 3 or more days. Delay here: {env['delay']}. {env['autonomy']}")
    if re.search(r"game|play|xp|rank|badge|level", t):
        r = ctx["rank"]
        return f"🎮 You are a **{r['icon']} {r['name']}** with {ctx['xp']} XP" + (f" ({r['to_next']} XP to {r['next']})." if r["next"] else ".") + " Games train reflexes, memory and calm, and the Reflex Test feeds your health trends!"
    if re.search(r"report|surgeon|summary|export", t):
        return "📄 Open **Health Lab → Surgeon report** for a one-page summary you can download and send to the flight surgeon."
    if re.search(r"hello|hi\b|hey|thanks|thank", t):
        return f"Hi {name}! 👋 I'm Pip. Ask me about sleep, radiation, bones, stress, your numbers, or what to do today."
    return ("I'm Pip, and I know about the **five NASA hazards** (radiation, isolation, distance, gravity, closed environments), your **vitals**, exercise, sleep, "
            "mood and when to call for help. Try one of the quick questions! I'm an education guide, not a doctor. 💜")


def render(ctx):
    lvl = rules.overall(ctx["ev"])
    sc = theme.pip(120)
    theme.show(theme.cute_hero("Pip Companion", "Your friendly alien guide. Ask Pip about space health and Pip will use your own data to answer.", sc,
                          (theme.cute_level_chip(lvl, f"You: {rules.LEVEL_NAME[lvl]}") if lvl is not None else "") + theme.cute_chip("rule-based · works offline", "#78c8ff")))
    st.write("")
    ss = st.session_state
    key = f"pip_msgs_{ctx['aid']}"
    if key not in ss:
        top = [i for i in ctx["insights"] if i["level"] >= 1][:1]
        hello = f"Hi {ctx['prof']['name'].split()[-1]}! I'm Pip 👾. " + (f"I noticed: **{top[0]['title']}**. Want to talk about it?" if top else "Everything looks steady today. Ask me anything!")
        ss[key] = [("assistant", hello)]
    qcols = st.columns(4)
    for n, qq in enumerate(QUICK):
        if qcols[n % 4].button(qq, key=f"q_{n}", width="stretch"):
            ss[key] += [("user", qq), ("assistant", answer(qq, ctx))]
    for role, msg in ss[key]:
        with st.chat_message(role, avatar="👾" if role == "assistant" else "🧑‍🚀"):
            st.markdown(msg)
    if q := st.chat_input("Ask Pip about space health…"):
        ss[key] += [("user", q), ("assistant", answer(q, ctx))]
        st.rerun()
    st.caption("Pip shares general education, not medical advice. In an emergency follow your mission protocol and contact the crew medical officer.")
