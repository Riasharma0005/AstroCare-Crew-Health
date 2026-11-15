"""The Ares-Orion Chronicle: a short serialized story told through the five NASA hazards.
Chapters unlock as the mission advances; every chapter ends with a real field note and a line from the crew member's own data.
All story text is original to AstroCare."""
from . import rules

# (key, unlock_day, hazard, title, paragraphs, field_note, poem_key)
CHAPTERS = [
    dict(n=1, day=1, hazard="radiation", title="The Quiet Sun", poem="stardust",
         text=["{name} learned to read the Sun the way a sailor reads weather. Out here there is no sky to hide behind, only a thin wall of shielding "
               "and a small, honest number on a wrist dosimeter that ticks upward every day.",
               "Most days it stayed close to {typ} mSv. The storm shelter door stayed open like an invitation nobody wanted to accept, "
               "but {name} checked it every morning anyway, the way you check a lifeboat you hope never to use."],
         note="NASA's Human Research Program calls space radiation stealthy and among the most hazardous parts of spaceflight. "
              "The Canadian Space Agency adds that neutrons make up about 30% of the radiation on the ISS, which is why continuous, autonomous measurement matters.",
         habit="Log your dose daily and know exactly where your shelter is."),
    dict(n=2, day=7, hazard="gravity", title="The Weight of Almost Nothing", poem="universe",
         text=["Every step on {place} was a small decision. {gravity} meant a jump was a little too long and a stumble was a little too slow, "
               "and {name}'s body kept asking an old question in a new language: how heavy am I, really?",
               "The treadmill became a kind of promise. Bones, muscles, the inner ear and the heart were all quietly renegotiating with a gravity "
               "they had never met, and the only argument they respected was daily work."],
         note="NASA describes how muscles, bones, the inner ear and organs must adjust to each new gravity, and later to Earth's again. "
              "On Mars that means about three-eighths of Earth's pull, possibly for up to two years.",
         habit="Hit your exercise target. It is the closest thing to a daily medicine."),
    dict(n=3, day=14, hazard="distance", title="The Long Silence", poem="universe",
         text=["A message home was no longer a conversation. It was a letter, tossed across a dark that took its time to answer. "
               "{name} learned to ask a question and then go on living inside the pause.",
               "That was the real lesson of {place}: help was real, but it was far. So the first response to any problem had to be {name}'s own, "
               "calm and practiced, with Earth as the second voice in the room, not the first."],
         note="NASA notes that instructions, supplies and medical care get harder to receive the deeper astronauts travel. "
              "Mars averages around 140 million miles from Earth, and a mission could last roughly three years instead of a three-day lunar trip.",
         habit="Know your protocols, keep the medical kit current, and send short, clear status reports early."),
    dict(n=4, day=21, hazard="env", title="Walls That Breathe", poem="stardust",
         text=["The habitat was not just a home. It was a machine that {name} lived inside, and a living thing too: air that had been "
               "breathed before, a faint hum that never stopped, and a microscopic crowd riding every surface.",
               "{name} began to notice it the way you notice a clock only when it stops. The scrubbers, the filters, the temperature, the light. "
               "To stay well here was to be a gentle caretaker of the air itself."],
         note="NASA lists temperature, pressure, lighting, noise and the microbial community, along with immune responses, as the everyday "
              "factors of a safe closed environment.",
         habit="Check scrubbers and filters, clean shared surfaces, and report breathing symptoms early."),
    dict(n=5, day=28, hazard="isolation", title="Faces in the Dark", poem="girl",
         text=["By now the crew knew each other's silences. The same four faces at the same small table, the same jokes worn smooth as river stones. "
               "Evenings grew long, and {name} began to write in the back of the log, not reports but questions.",
               "Nothing was wrong, exactly. The loneliness was a weather system, not a verdict. And weather, {name} had learned, can be "
               "met: with a call home, a shared meal, a slow breath, a few honest lines on a page."],
         note="NASA studies how groups isolated and confined for long periods respond, and stresses that crews must be carefully chosen, "
              "trained and supported. It also notes that the five hazards can feed off one another.",
         habit="Protect sleep, keep a daily call, and tell someone when a heavy day lasts more than a few."),
    dict(n=6, day=45, hazard="env", title="Epilogue: Stardust", poem="stardust", epilogue=True,
         text=["The five hazards never arrived one at a time. A noisy night shortened sleep, short sleep thinned patience, thin patience made the "
               "silence heavier. {name} finally understood why care had to be connected too: every number was one star in a single sky.",
               "On the last page of the log {name} wrote nothing technical at all. Only that everything in this body was once forged inside a star, "
               "and that it had come a very long way to be tired, and curious, and here."],
         note="Because hazards interact, AstroCare reads sleep, mood, exercise, radiation, air and contact together instead of one at a time.",
         habit="Look at the whole sky, not just one star."),
]

PROMPTS = [
    "If you could hang a star for every thought of someone you love, who would your brightest one be for, and why?",
    "Which choice today did you make for yourself, rather than because the schedule made it for you?",
    "What part of you feels like it was once a star: a habit, a memory, a kind of courage?",
    "What does silence sound like in your habitat tonight, and what would you like to say into it?",
    "Name one thing that surprised you about your own body this week.",
    "Who on the crew helped you today, and have you told them?",
    "If tomorrow's log began with one good sentence, what would you want it to be?",
]


def unlocked(day):
    return [c for c in CHAPTERS if day >= c["day"]]


def locked(day):
    return [c for c in CHAPTERS if day < c["day"]]


def latest(day):
    u = unlocked(day)
    return u[-1] if u else CHAPTERS[0]


def fill(text, ctx):
    surname = ctx["prof"]["name"].split()[-1]
    env = ctx["env"]
    return text.format(name=surname, place=ctx["env_name"], gravity=env["gravity"], typ=env["rad_typ"])


def data_line(ch, ctx):
    """One sentence of the crew member's real numbers, so the story reflects the person reading it."""
    d, env, h = ctx["daily"], ctx["env"], ch["hazard"]
    if not len(d):
        return "Log your hazards in the Hazard Zone and this chapter will reflect your own numbers."
    if ch["n"] == 1:
        return f"In your log: {d['radiation'].sum():.1f} mSv so far, with a peak of {d['radiation'].max():.1f} mSv in a single day."
    if ch["n"] == 2:
        return f"In your log: exercise averaged {d['exercise'].mean():.0f} min a day against a target of {env['ex_target']}."
    if ch["n"] == 3:
        return f"Your ground delay here is {env['delay']}. Autonomy is part of your health plan."
    if ch["n"] == 4:
        return f"In your log: cabin CO₂ peaked at {d['co2'].max():.0f} ppm (watch above {rules.CO2_LEVELS[0]})."
    if ch["n"] == 5:
        return f"In your log: social contact averaged {d['social'].mean():.0f} min a day, with a low of {d['social'].min():.0f}."
    return f"Overall status today: {rules.LEVEL_NAME[rules.overall(ctx['ev'])] if ctx['ev'] else 'no check-in yet'}."


def daily_entry(ctx):
    """A first-person log entry written from today's data. Calm, specific, never diagnostic."""
    ev, name, day = ctx["ev"], ctx["prof"]["name"].split()[-1], ctx["day"]
    env = ctx["env"]
    lvl = rules.overall(ev)
    if lvl is None:
        return (f"Day {day}. The log is still blank. {name} took a breath, looked at {ctx['env_name']} through the small window, "
                "and decided the first number would be the hardest one to write down.")
    parts = [f"Day {day} on {ctx['env_name']}. " + {0: "A steady one.", 1: "A day that asked for a little extra attention.", 2: "A heavy one."}[lvl]]
    if "sleep" in ev:
        s = ev["sleep"]["value"]
        parts.append(f"Slept {s:.1f} hours. " + ("The morning came easily." if s >= 7 else "The morning arrived before I was ready." if s >= 6 else "Rest was thin and I can feel it in everything."))
    if "stress" in ev and "mood" in ev:
        st_, md = ev["stress"]["value"], ev["mood"]["value"]
        if st_ >= 7 or md <= 4:
            parts.append(f"Stress sits at {st_:.0f} and mood at {md:.0f}. I wrote that down plainly instead of pretending, and that already helped.")
        else:
            parts.append(f"Stress {st_:.0f}, mood {md:.0f}. The crew table was loud with jokes tonight.")
    if "reaction" in ev and ev["reaction"]["level"] >= 1:
        parts.append(f"My reflexes tested slower, {ev['reaction']['value']:.0f} ms, a fair warning to protect my rest before any big task.")
    top = [i for i in ctx["insights"] if i["tag"] in ("radiation", "gravity", "env", "isolation") and i["level"] >= 1 and "check-in" not in i["title"]]
    if top:
        parts.append(f"Noted for the surgeon: {top[0]['title'].lower()}.")
    parts.append(env["epigraph"])
    return " ".join(parts)


def prompt_for(day):
    return PROMPTS[(day - 1) % len(PROMPTS)]
