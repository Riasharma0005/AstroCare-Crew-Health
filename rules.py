"""AstroCare rules engine (transparent, rule-based; no black box).

Two layers decide every colour:
  1. A general reference range (educational, adult resting values).
  2. YOUR OWN baseline: your last <=14 readings. 'Unusual for you' = >= 2 standard deviations
     in the unhealthy direction.
Final level = the worse of the two (baseline alone can only raise to Watch).
Educational prototype - NOT a diagnostic tool. Mission protocols always win.
"""
import pandas as pd  # type: ignore[import-not-found]

LEVEL_NAME = {0: "Steady", 1: "Watch", 2: "Alert"}

# level: 0 steady, 1 watch, 2 alert
# green / amber = (low, high) inclusive. bad = direction that is unhealthy (-1 low, +1 high, 0 both)
PARAMS = {
    "hr": dict(label="Heart rate", unit="bpm", icon="heart", green=(50, 100), amber=(40, 120), bad=0, floor=3, dec=0, tag="gravity", organ="heart"),
    "spo2": dict(label="Blood oxygen", unit="% SpO₂", icon="wind", green=(95, 100), amber=(92, 100), bad=-1, floor=0.8, dec=0, tag="env", organ="lungs"),
    "temp": dict(label="Body temperature", unit="°C", icon="thermo", green=(36.1, 37.5), amber=(35.5, 38.0), bad=0, floor=0.2, dec=1, tag="env", organ="gut"),
    "sys": dict(label="Systolic BP", unit="mmHg", icon="gauge", green=(90, 129), amber=(80, 139), bad=0, floor=4, dec=0, tag="gravity", organ="heart"),
    "dia": dict(label="Diastolic BP", unit="mmHg", icon="gauge", green=(60, 84), amber=(50, 89), bad=0, floor=3, dec=0, tag="gravity", organ="heart"),
    "glucose": dict(label="Blood glucose", unit="mg/dL", icon="cube", green=(70, 99), amber=(60, 125), bad=0, floor=5, dec=0, tag="env", organ="gut"),
    "sleep": dict(label="Sleep", unit="hours", icon="moon", green=(7, 9), amber=(6, 10.5), bad=-1, floor=0.4, dec=1, tag="isolation", organ="brain"),
    "mood": dict(label="Mood", unit="/10", icon="smile", green=(6, 10), amber=(4, 10), bad=-1, floor=0.8, dec=0, tag="isolation", organ="brain"),
    "stress": dict(label="Stress", unit="/10", icon="swirl", green=(0, 4), amber=(0, 7), bad=1, floor=0.8, dec=0, tag="isolation", organ="brain"),
    "fatigue": dict(label="Fatigue", unit="/10", icon="battery", green=(0, 4), amber=(0, 7), bad=1, floor=0.8, dec=0, tag="isolation", organ="brain"),
    "reaction": dict(label="Reaction time", unit="ms", icon="zap", green=(0, 300), amber=(0, 400), bad=1, floor=12, dec=0, tag="isolation", organ="brain"),
}
VITAL_KEYS = list(PARAMS)

# how-to guide: device / how / why it matters in space
GUIDE = {
    "hr": ("Wrist or chest heart-rate monitor, or a pulse oximeter.",
           "Sit calmly for 5 minutes, same posture every day, and read the value once it settles.",
           "Microgravity shifts body fluids toward the head and the heart works less against gravity, so the cardiovascular system can decondition. Stress, poor sleep and radiation also move heart rate."),
    "spo2": ("Fingertip pulse oximeter.",
             "Keep your hand warm and still, remove nail polish, wait for a steady number.",
             "Closed habitats can build up CO₂ and dust (lunar and Mars dust is sharp and irritating). Falling oxygen saturation is an early warning that air quality or lungs need attention."),
    "temp": ("Medical thermometer (forehead or ear).",
             "Measure at a similar time each day, not right after exercise or a hot drink.",
             "Shared air and surfaces help germs spread in a small crew, and stress and radiation can change immune function. A fever is easy to miss without a daily number."),
    "sys": ("Automatic blood-pressure cuff.",
            "Sit, feet supported, arm at heart height. Rest 5 minutes, take two readings and log the second.",
            "Fluid shifts and heart deconditioning change blood pressure. Light-headedness when you stand after landing is a known effect."),
    "dia": ("Automatic blood-pressure cuff (same measurement as systolic).",
            "Same technique as systolic. The two numbers come from one reading.", "See systolic: both numbers tell the story of your circulation."),
    "glucose": ("Fingerstick glucose meter.",
                "Measure fasting (before eating) when you can and note it. Meals change the number a lot.",
                "Stress, disrupted routines, less activity and altered diet can all change how the body handles sugar. Food variety and appetite change in flight."),
    "sleep": ("Sleep log or approved wearable.",
              "Log the hours you actually slept, not the time in bed.",
              "Light cycles are artificial and every sunrise/sunset on a station is 90 minutes. Noise, stress and schedule shifts shorten sleep, and short sleep slows thinking and mood."),
    "mood": ("Your own check-in (1 = very low, 10 = great).", "Rate how you felt today, honestly. It is private-by-default in this prototype.",
             "Isolation and confinement are an official NASA hazard. Small changes in mood are the earliest sign something needs support."),
    "stress": ("Your own check-in (1 = calm, 10 = overwhelmed).", "Rate your day on average, not just the worst moment.",
               "Long missions with a tiny crew and high stakes build stress. Spotting a rising trend early lets you act before it affects work."),
    "fatigue": ("Your own check-in (1 = fresh, 10 = exhausted).", "Rate how tired you feel, separate from sleep hours.",
                "Fatigue plus short sleep is risky for complex tasks like EVA, docking or medical procedures."),
    "reaction": ("The Reflex Test in Game Zone.", "Play the 5-round test while rested; it logs your average automatically.",
                 "A quick alertness check: reaction time slows with fatigue, so it is a fast, objective sign of how rested you really are."),
}

SYMPTOMS = {  # symptom -> level (2 = report promptly)
    "Headache": 1, "Dizziness": 1, "Nausea": 1, "Back pain": 1, "Joint / bone pain": 1, "Skin rash or irritation": 1,
    "Fever or chills": 1, "Low mood or anxiety": 1, "Eye strain": 1,
    "Blurred vision": 2, "Chest pain": 2, "Trouble breathing": 2, "Fainting": 2, "Racing or irregular heartbeat": 2,
}

# ----------------------------------------------------------------------------- environments
ENVS = {
    "Space Station": dict(icon="🛰️", planet="sky", tagline="Orbiting home, 400 km up", epigraph="Sixteen sunrises a day, and every one of them is a reason to keep a sleep schedule.",
                          gravity="Microgravity (≈0 g)", delay="≈1 second", rtt_min=0.02,
                          autonomy="Ground medical support is near real-time. Still follow your onboard checklist first.",
                          rad_typ=0.6, ex_target=120,
                          focus="Microgravity: bones, muscles, fluid shifts, sleep with 16 sunrises a day.",
                          task=("air", "wind", "Check air vents and filters")),
    "Spacecraft": dict(icon="🚀", planet="lav", tagline="Cruising between worlds", epigraph="Between worlds, the only horizon is the one you carry with you.",
                       gravity="Microgravity (≈0 g)", delay="seconds to minutes, growing with distance", rtt_min=0.5,
                       autonomy="Ground contact slows as you travel; treat the first response as yours.",
                       rad_typ=1.8, ex_target=90,
                       focus="Deep-space radiation, confinement, a tiny shared cabin.",
                       task=("cabin", "wind", "Wipe shared surfaces and check cabin CO₂")),
    "Lunar Base": dict(icon="🌕", planet="moon", tagline="Dusty footprints on the Moon", epigraph="Gray silence, a black sky, and an Earth hanging overhead like a small blue lantern.",
                       gravity="Lunar gravity (≈0.16 g)", delay="≈1.3 seconds one way", rtt_min=0.05,
                       autonomy="Ground replies are quick, but surface emergencies still start with you.",
                       rad_typ=1.3, ex_target=60,
                       focus="Sharp lunar dust, surface radiation, partial gravity, long EVAs.",
                       task=("dust", "target", "Dust control: wipe suits, check the airlock")),
    "Mars Base": dict(icon="🔴", planet="coral", tagline="Rusty red, very far from home", epigraph="Rust-colored quiet, and a message home that will take its time.",
                      gravity="Mars gravity (≈0.38 g)", delay="3–22 minutes one way", rtt_min=26,
                      autonomy="A reply from Earth can take up to ~44 minutes round trip. Start your own protocol, then message the ground.",
                      rad_typ=0.64, ex_target=75,
                      focus="Communication delay, isolation, dust and partial gravity.",
                      task=("window", "signal", "Plan your next ground-contact window")),
    "Planetary Rover": dict(icon="🛞", planet="sun", tagline="Roving across a new world", epigraph="Tracks behind, the unknown ahead, and a base that feels very far away.",
                            gravity="Surface gravity (0.16–0.38 g)", delay="same as home base", rtt_min=5,
                            autonomy="You are far from the base: carry the kit, know the protocol, call early.",
                            rad_typ=1.0, ex_target=45,
                            focus="Long drives, vibration, posture, surface radiation and dust.",
                            task=("posture", "body", "Posture and stretch break from the seat")),
}

NASA_LIMIT_MSV = 600          # NASA career effective-dose limit (all astronauts)
CO2_LEVELS = (2500, 5000)     # demo thresholds (ppm): amber, red. Use your habitat's official limits.
SOCIAL_MIN_TARGET = 15

HAZARDS = {
    "radiation": dict(icon="sun", name="Space radiation", color="#f0a35e", url="https://www.nasa.gov/hrp/hazard-space-radiation/"),
    "isolation": dict(icon="users", name="Isolation and confinement", color="#a58bff", url="https://www.nasa.gov/hrp/hazard-isolation-and-confinement/"),
    "distance": dict(icon="signal", name="Distance from Earth", color="#6fb7ff", url="https://www.nasa.gov/hrp/hazard-distance-from-earth/"),
    "gravity": dict(icon="weight", name="Gravity fields", color="#7ad0b8", url="https://www.nasa.gov/hrp/hazard-gravity-fields/"),
    "env": dict(icon="wind", name="Hostile and closed environments", color="#59d0c5", url="https://www.nasa.gov/hrp/hazard-hostile-closed-environments/"),
}

# NASA Human Research Program risks (https://www.nasa.gov/hrp/risks/) -> where AstroCare watches for them
_R = "https://www.nasa.gov/reference/"
RISKS = [
    ("Altered immune system responses", "Temperature, skin and fever symptoms", _R + "risk-of-altered-immune-system-responses/"),
    ("Altered sensorimotor and vestibular function", "Dizziness and nausea symptoms", _R + "risk-of-altered-sensorimotor-and-vestibular-function/"),
    ("Cardiovascular adaptations", "Heart rate, blood pressure", _R + "risk-of-cardiovascular-adaptations/"),
    ("Decompression sickness", "Education only (EVA procedure risk)", _R + "risk-of-decompression-sickness/"),
    ("Host-microorganism interactions", "Temperature, illness symptoms, surface-cleaning task", _R + "risk-of-host-microorganism-interactions/"),
    ("Hypoxia", "Blood oxygen (SpO2), cabin CO2", _R + "risk-of-hypoxia/"),
    ("Inadequate food and nutrition", "Blood glucose, hydration and meal task", _R + "risk-of-inadequate-food-and-nutrition/"),
    ("Injury and compromised performance from spacewalks", "Fatigue, reaction time", _R + "risk-of-injury-and-compromised-performance-from-extravehicular-activity-eva/"),
    ("Reduced cardiorespiratory and musculoskeletal fitness", "Daily exercise minutes", _R + "risk-of-reduced-cardiorespiratory-and-musculoskeletal-fitness/"),
    ("Spaceflight Associated Neuro-ocular Syndrome (SANS)", "Vision symptoms", _R + "risk-of-spaceflight-associated-neuro-ocular-syndrome-sans/"),
    ("Spaceflight-induced bone changes", "Daily exercise minutes", _R + "risk-of-spaceflight-induced-bone-changes/"),
    ("Behavioral changes and psychiatric disorders", "Mood, stress, diary writing", _R + "risk-of-behavioral-conditions-and-psychiatric-disorders/"),
    ("Inadequate teamwork", "Social contact minutes", _R + "risk-of-inadequate-teamwork/"),
    ("Inadequate sleep and irregular schedules", "Sleep hours, fatigue, reaction time", _R + "risk-from-inadequate-sleep-and-irregular-schedules/"),
    ("Inadequate systems operations support", "Autonomy checklist (Distance)", _R + "risk-of-inadequate-systems-operations-support/"),
    ("Injury from dynamic loads", "Education only (landing risk)", _R + "risk-of-injury-from-dynamic-loads/"),
    ("Radiation-induced cancers", "Daily radiation dose vs limit", _R + "risk-of-radiation-induced-cancers/"),
]

SOURCES = [
    ("NASA HRP: 5 Hazards of Human Spaceflight", "https://www.nasa.gov/hrp/hazards/"),
    ("NASA HRP: Risks of Human Spaceflight", "https://www.nasa.gov/hrp/risks/"),
    ("NASA HRP: Ongoing research in space", "https://www.nasa.gov/hrp/ongoing-hrp-research/"),
    ("CSA: Monitoring radiation for astronaut health", "https://www.asc-csa.gc.ca/eng/news/articles/2026/2026-02-26-monitoring-radiation-astronaut-health.asp"),
    ("CSA: Why do we conduct science experiments in space?", "https://www.asc-csa.gc.ca/eng/iss/science/why-do-we-conduct-science-experiments-in-space.asp"),
]

# ----------------------------------------------------------------------------- level logic
def range_text(key):
    p = PARAMS[key]
    lo, hi = p["green"]
    if lo <= 0:
        return f"≤ {hi:g} {p['unit']}"
    if key in ("spo2", "mood"):
        return f"≥ {lo:g} {p['unit']}"
    return f"{lo:g}–{hi:g} {p['unit']}"


def ref_level(key, v):
    p = PARAMS[key]
    if p["green"][0] <= v <= p["green"][1]:
        return 0
    if p["amber"][0] <= v <= p["amber"][1]:
        return 1
    return 2


def _baseline(prev):
    h = prev.dropna().tail(14)
    if len(h) < 5:
        return None
    return float(h.mean()), float(h.std(ddof=0))


def _judge(key, v, base):
    p = PARAMS[key]
    ref = ref_level(key, v)
    lvl, z, mean = ref, None, None
    if base:
        mean = base[0]
        z = (v - mean) / max(base[1], p["floor"])
        unusual = (z * p["bad"] >= 2) if p["bad"] else abs(z) >= 2
        if unusual:
            lvl = max(lvl, 1)
    return lvl, ref, z, mean


def levels_by_day(vit):
    """DataFrame (index = mission day, columns = indicators) of levels using an expanding baseline."""
    if vit is None or vit.empty:
        return pd.DataFrame()
    vit = vit.sort_values("day").reset_index(drop=True)
    rows = {}
    for i, r in vit.iterrows():
        d = {}
        for k in VITAL_KEYS:
            v = r.get(k)
            if pd.isna(v):
                d[k] = None
                continue
            d[k] = _judge(k, float(v), _baseline(vit[k].iloc[:i]))[0]
        rows[int(r["day"])] = d
    return pd.DataFrame.from_dict(rows, orient="index")


def evaluate(vit, env_name=None):
    """Latest judgement for every indicator -> {key: info}."""
    if vit is None or vit.empty:
        return {}
    vit = vit.sort_values("day").reset_index(drop=True)
    lv = levels_by_day(vit)
    env = ENVS.get(env_name or "", {})
    out = {}
    for k in VITAL_KEYS:
        s = vit[k]
        if s.dropna().empty:
            continue
        i = s.last_valid_index()
        v = float(s.iloc[i])
        lvl, ref, z, mean = _judge(k, v, _baseline(s.iloc[:i]))
        p = PARAMS[k]
        # consecutive flagged readings ending now
        col = lv[k].dropna() if k in lv else pd.Series(dtype=float)
        n = 0
        for x in reversed(col.tolist()):
            if x >= 1:
                n += 1
            else:
                break
        parts = []
        if ref >= 1:
            parts.append(f"{v:.{p['dec']}f} {p['unit']} is outside the general reference range ({range_text(k)}).")
        if z is not None and ((z * p["bad"] >= 2) if p["bad"] else abs(z) >= 2):
            parts.append(f"It is {abs(z):.1f}× your usual variation away from your own average (~{mean:.{max(p['dec'], 1)}f}).")
        if not parts:
            parts.append(f"Within the reference range ({range_text(k)})" + (f" and close to your usual ~{mean:.{max(p['dec'], 1)}f}." if mean is not None else "."))
        if n >= 3 and lvl >= 1:
            parts.append(f"It has been flagged {n} readings in a row.")
        out[k] = dict(value=v, level=lvl, ref=ref, z=z, mean=mean, day=int(vit["day"].iloc[i]),
                      days_flagged=n, reason=" ".join(parts), action=action_text(lvl, env, n))
    return out


def action_text(level, env=None, n=0):
    env = env or {}
    if level == 0:
        return "Looking steady. Keep your routine."
    if level == 1:
        t = "Re-measure in about an hour with careful technique, then check sleep, hydration and exercise."
        if n >= 3:
            t += " Because it persists, tell your crew medical officer at the next check-in."
        return t
    t = "Re-measure now. If it is confirmed, contact your crew medical officer / flight surgeon and follow your mission protocol."
    if env.get("autonomy"):
        t += " " + env["autonomy"]
    return t


def symptom_level(symptoms):
    if not symptoms:
        return 0, []
    items = [s.strip() for s in str(symptoms).split(",") if s.strip()]
    lvl = max([SYMPTOMS.get(s, 1) for s in items] + [0])
    return lvl, items


def overall(ev):
    return max([i["level"] for i in ev.values()] + [0]) if ev else None
