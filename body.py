"""🧍 Body Explorer: clickable human figure. Colours come from the SAME rules engine as the rest of the app
(general reference ranges + your own baseline), so the body, the dashboard and Pip always agree."""
import json
import re

import streamlit as st
import streamlit.components.v1 as components

from . import core, rules, theme

ORGAN_PARAMS = {"brain": ["sleep", "mood", "stress", "fatigue", "reaction"], "heart": ["hr", "sys", "dia"],
                "lungs": ["spo2"], "gut": ["temp", "glucose"], "eyes": [], "bones": []}

# Educational overview based on NASA Human Research Program themes. General information only.
ORGANS = {
    "brain": {
        "name": "Brain & Mind", "icon": "🧠",
        "function": "Controls thinking, mood, sleep and coordination.",
        "effects": [
            "Isolation & confinement: stress, low mood and sleep disruption are recognised risks.",
            "Microgravity: fluid shifts toward the head and the balance system must re-adapt.",
            "Radiation: NASA studies possible effects on the central nervous system on long missions.",
        ],
        "tracks": "Sleep duration (Health Lab) and mood / stress / fatigue (Health Lab).",
        "how": "Sleep is logged from a sleep log or approved device. Mood and stress are self-reported "
               "check-ins. Doing them at the same time each day makes your own pattern easier to read.",
        "flag": "Severe or sudden headache, confusion, fainting, or low mood / anxiety that persists or "
                "stops you functioning. Use your mission's psychological-support procedure.",
        "counter": ["Keep a regular sleep schedule", "Schedule social contact and downtime",
                    "Short relaxation or breathing exercises", "Use ground psychological support"],
    },
    "eyes": {
        "name": "Eyes & Vision", "icon": "👁️",
        "function": "Vision depends on the eye and the optic nerve.",
        "effects": [
            "Microgravity: head-ward fluid shift is linked to Spaceflight Associated Neuro-ocular "
            "Syndrome (SANS): optic-disc swelling and changes in near vision.",
            "Closed environments: dust and dry air can irritate eyes.",
        ],
        "tracks": "Not measured by AstroCare. On real missions, vision tests and eye imaging are used.",
        "how": "Periodic vision checks and eye imaging are performed under flight-surgeon protocols.",
        "flag": "Blurred vision, new difficulty reading, flashes of light or eye pain. Report early.",
        "counter": ["Follow scheduled vision checks", "Report any change in vision early",
                    "Follow flight-surgeon guidance"],
    },
    "heart": {
        "name": "Heart & Circulation", "icon": "❤️",
        "function": "Pumps blood to the whole body.",
        "effects": [
            "Microgravity: fluids shift upward and the cardiovascular system can decondition.",
            "Radiation: NASA studies possible long-term cardiovascular effects.",
            "Standing up after return to gravity can cause light-headedness.",
        ],
        "tracks": "Heart rate and blood pressure (Health Lab).",
        "how": "Use the approved heart-rate monitor and BP cuff. Rest first and measure in the same "
               "posture each time so changes are comparable.",
        "flag": "Chest pain, fainting, severe breathlessness or a racing / irregular heartbeat. "
                "Contact the crew medical officer immediately per protocol.",
        "counter": ["Regular aerobic exercise (treadmill / cycle)", "Resistive exercise",
                    "Stay hydrated as advised", "Follow the mission exercise plan"],
    },
    "lungs": {
        "name": "Lungs & Oxygen", "icon": "🫁",
        "function": "Brings oxygen into the blood and removes carbon dioxide.",
        "effects": [
            "Closed environments: air quality, CO₂ build-up and airborne dust matter.",
            "Lunar / Mars dust can irritate the airways and eyes.",
        ],
        "tracks": "SpO₂ (an estimate of how much haemoglobin is carrying oxygen).",
        "how": "Use an approved pulse oximeter. Keep still, keep the sensor site warm and clean, and "
               "follow device instructions.",
        "flag": "Shortness of breath, persistent cough, chest tightness or irritation after dust exposure.",
        "counter": ["Dust control and suit hygiene", "Habitat air-quality checks per protocol",
                    "Report breathing symptoms early"],
    },
    "gut": {
        "name": "Gut, Metabolism & Immunity", "icon": "🛡️",
        "function": "Digests food, manages energy and supports defence against illness.",
        "effects": [
            "Closed environments: shared air and surfaces, and changes in the microbiome.",
            "Stress, sleep loss and radiation can change immune function.",
            "Food variety and appetite can change in spaceflight.",
        ],
        "tracks": "Body temperature and blood glucose (Health Lab).",
        "how": "Use the approved thermometer and glucose device. Note meal timing, because it affects glucose.",
        "flag": "Fever, persistent illness, wounds that heal slowly, or severe stomach symptoms.",
        "counter": ["Good hand and surface hygiene", "Balanced nutrition as planned",
                    "Adequate sleep", "Habitat cleaning routine"],
    },
    "bones": {
        "name": "Bones & Muscles", "icon": "🦴",
        "function": "Support the body and enable movement.",
        "effects": [
            "Microgravity: weight-bearing bones can lose density and muscles can weaken.",
            "Reduced gravity on the Moon or Mars still changes loading compared with Earth.",
        ],
        "tracks": "Daily exercise minutes in the Hazard Zone, against your mission target. Real missions also use imaging and strength tests.",
        "how": "Bone density is assessed with imaging before and after missions. Exercise sessions are logged.",
        "flag": "Persistent bone, joint or back pain, or an injury during exercise or surface activity.",
        "counter": ["Daily resistive exercise", "Aerobic exercise", "Nutrition for bone health as advised",
                    "Use the mission exercise equipment correctly"],
    },
}

HAZARDS = [
    {"name": "☢️ Radiation", "organs": ["brain", "heart", "gut"],
     "text": "Space radiation can affect tissues over time; long-term risks are an active NASA research area."},
    {"name": "👥 Isolation", "organs": ["brain"],
     "text": "Confinement, small crews and monotony can affect mood, stress and sleep."},
    {"name": "📡 Distance", "organs": [],
     "text": "Distance means delayed communication and slow resupply, so crews need medical autonomy. "
             "It affects how quickly help can reach you, rather than one organ."},
    {"name": "🪐 Gravity fields", "organs": ["bones", "heart", "eyes", "brain"],
     "text": "Microgravity and reduced gravity change how fluids, bones, muscles and balance work."},
    {"name": "🫧 Closed environment", "organs": ["lungs", "gut", "eyes"],
     "text": "Shared air, dust, noise and surfaces in a small habitat affect breathing and immunity."},
]

_HTML = r"""
<!DOCTYPE html><html><head><meta charset="utf-8"><style>
*{box-sizing:border-box} body{margin:0;background:transparent;color:#f4ecff;font-family:'IBM Plex Sans','ui-rounded','Segoe UI',system-ui,sans-serif}
.wrap{display:flex;flex-wrap:wrap;gap:18px}
.left{flex:0 0 270px}.right{flex:1 1 340px;min-width:300px}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:12px}
.chip{cursor:pointer;border:1px solid #2b4a70;background:#0e1b38;color:#cfe3f8;border-radius:20px;padding:6px 12px;font-size:12px}
.chip.on{background:#14305a;border-color:#8ec5ff;box-shadow:0 0 12px rgba(124,77,255,.5)}
#hz{font-size:12px;color:#a9bfd8;min-height:34px;margin-bottom:10px}
svg{width:100%;max-width:270px;display:block;margin:auto}
.body{fill:rgba(255,255,255,.07);stroke:#6f8fb8;stroke-width:2}
.organ{cursor:pointer;stroke-width:2.5;fill-opacity:.55;transition:all .2s}
.organ:hover{fill-opacity:.85;filter:drop-shadow(0 0 6px #8ec5ff)}
.organ.sel{stroke:#fff;fill-opacity:.9;filter:drop-shadow(0 0 10px #fff)}
.organ.hl{animation:pulse 1.2s infinite}
@keyframes pulse{50%{filter:drop-shadow(0 0 12px #8ec5ff);stroke:#cbb8ff}}
.legend{font-size:11px;color:#9fb6d0;text-align:center;margin-top:8px}
.dot{display:inline-block;width:9px;height:9px;border-radius:50%;margin:0 3px 0 8px}
.pills{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:12px}
.pill{cursor:pointer;border:1px solid #29466c;background:#0e1b38;border-radius:10px;padding:6px 10px;font-size:12px;color:#cfe3f8}
.pill.sel{border-color:#8ec5ff;background:#14305a}
.card{background:linear-gradient(160deg,rgba(14,26,44,.92),rgba(8,16,30,.92));border:1.5px solid rgba(142,175,214,.28);border-radius:24px;padding:18px}
h2{margin:0;color:#fff;font-size:24px;font-family:'Sora','ui-rounded',sans-serif}
.badge{display:inline-block;margin-top:8px;font-size:12px;padding:4px 10px;border-radius:14px;border:1px solid currentColor}
details{margin-top:9px;background:#0f1b33;border-radius:10px;padding:8px 12px;border:1px solid #213a5c}
summary{cursor:pointer;font-weight:700;color:#8ec5ff;font-size:13px}
details p,details li{font-size:13px;color:#c6d6ea;line-height:1.45;margin:6px 0}
ul{margin:6px 0;padding-left:18px}
.note{font-size:11px;color:#7f98b3;margin-top:10px}
</style></head><body><div class="wrap">
<div class="left">
 <div class="chips" id="chips"></div><div id="hz">Tap a hazard to see which body systems it affects.</div>
 <svg viewBox="0 0 240 500" id="svg">
  <circle class="body" cx="120" cy="58" r="42"/><rect class="body" x="108" y="96" width="24" height="22" rx="8"/>
  <rect class="body" x="68" y="112" width="104" height="176" rx="34"/>
  <rect class="body" x="38" y="122" width="26" height="172" rx="13"/><rect class="body" x="176" y="122" width="26" height="172" rx="13"/>
  <rect class="body" x="76" y="288" width="40" height="200" rx="18"/><rect class="body" x="124" y="288" width="40" height="200" rx="18"/>
  <g class="organ" data-k="bones"><rect x="38" y="122" width="26" height="172" rx="13"/><rect x="176" y="122" width="26" height="172" rx="13"/>
   <rect x="76" y="288" width="40" height="200" rx="18"/><rect x="124" y="288" width="40" height="200" rx="18"/></g>
  <g class="organ" data-k="gut"><ellipse cx="120" cy="246" rx="36" ry="28"/></g>
  <g class="organ" data-k="lungs"><ellipse cx="94" cy="172" rx="21" ry="38"/><ellipse cx="146" cy="172" rx="21" ry="38"/></g>
  <g class="organ" data-k="heart"><path d="M120 214 C96 196,102 168,120 180 C138 168,144 196,120 214Z"/></g>
  <g class="organ" data-k="brain"><ellipse cx="120" cy="44" rx="28" ry="20"/></g>
  <g class="organ" data-k="eyes"><ellipse cx="107" cy="70" rx="8" ry="5"/><ellipse cx="133" cy="70" rx="8" ry="5"/></g>
 </svg>
 <div class="legend"><span class="dot" style="background:#5fd3a0"></span>steady<span class="dot" style="background:#e8b04a"></span>watch<span class="dot" style="background:#ef6b73"></span>alert<span class="dot" style="background:#7587a3"></span>not tracked</div>
</div>
<div class="right"><div class="pills" id="pills"></div><div class="card" id="panel"></div>
<div class="note">Colours combine a general reference range with YOUR OWN recent history. Educational overview inspired by NASA Human Research Program themes. Not a diagnosis: mission protocols and flight surgeons decide real actions.</div></div>
</div>
<script>
const D=__DATA__; const COL={green:"#5fd3a0",amber:"#e8b04a",red:"#ef6b73",grey:"#7587a3"};
let sel=null, hz=null;
const els={}; document.querySelectorAll(".organ").forEach(e=>{els[e.dataset.k]=e;
  const c=COL[D.status[e.dataset.k].state]; e.querySelectorAll("*").forEach(s=>{s.style.fill=c;s.style.stroke=c});
  e.addEventListener("click",()=>pick(e.dataset.k));});
const pills=document.getElementById("pills");
Object.keys(D.organs).forEach(k=>{const b=document.createElement("div");b.className="pill";b.id="p-"+k;
  b.textContent=D.organs[k].icon+" "+D.organs[k].name;b.onclick=()=>pick(k);pills.appendChild(b);});
const chips=document.getElementById("chips");
D.hazards.forEach((h,i)=>{const c=document.createElement("div");c.className="chip";c.textContent=h.name;
  c.onclick=()=>{hz=(hz===i?null:i);draw();};chips.appendChild(c);});
function li(a){return "<ul>"+a.map(x=>"<li>"+x+"</li>").join("")+"</ul>";}
function pick(k){sel=k;draw();}
function draw(){
  document.querySelectorAll(".chip").forEach((c,i)=>c.classList.toggle("on",hz===i));
  document.getElementById("hz").textContent=hz===null?"Tap a hazard to see which body systems it affects.":D.hazards[hz].text;
  Object.keys(els).forEach(k=>{els[k].classList.toggle("sel",sel===k);
    els[k].classList.toggle("hl",hz!==null&&D.hazards[hz].organs.includes(k));
    document.getElementById("p-"+k).classList.toggle("sel",sel===k);});
  const p=document.getElementById("panel");
  if(!sel){p.innerHTML="<h2>👆 Choose a body system</h2><p style='color:#a9bfd8'>Tap an organ on the figure or one of the buttons above. You will see how spaceflight affects it, what to measure and when to contact the crew medical officer.</p>";return;}
  const o=D.organs[sel], s=D.status[sel], c=COL[s.state];
  p.innerHTML="<h2>"+o.icon+" "+o.name+"</h2><div class='badge' style='color:"+c+"'>"+s.text+"</div>"
  +"<details open><summary>What it does</summary><p>"+o.function+"</p></details>"
  +"<details><summary>How spaceflight affects it</summary>"+li(o.effects)+"</details>"
  +"<details><summary>What AstroCare tracks</summary><p>"+o.tracks+"</p></details>"
  +"<details><summary>Why &amp; how to measure</summary><p>"+o.how+"</p></details>"
  +"<details><summary>⚠️ Tell your crew medical officer / flight surgeon if…</summary><p>"+o.flag+"</p></details>"
  +"<details><summary>🛠️ Common countermeasures</summary>"+li(o.counter)+"</details>";}
draw();
</script></body></html>
"""


def build_body_html(status):
    data = {"organs": ORGANS, "hazards": HAZARDS, "status": status}
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    return _HTML.replace("__DATA__", payload)


def organ_status(ctx):
    ev, hz, vit, day = ctx["ev"], core.hazard_status(ctx), ctx["vit"], ctx["day"]
    names = {0: "green", 1: "amber", 2: "red"}
    out = {}
    for organ, keys in ORGAN_PARAMS.items():
        found = [(k, ev[k]) for k in keys if k in ev]
        if organ == "lungs" and hz["env"]:
            out[organ] = dict(state=names[hz["env"]], text="Cabin CO₂ is elevated (see Hazard Zone). Check ventilation and scrubbers.")
            continue
        if organ == "bones":
            if len(ctx["daily"]) >= 3:
                lvl = hz["gravity"]
                out[organ] = dict(state=names[lvl], text="Exercise is below target. Daily loading protects bones and muscles." if lvl else "Exercise is on track, which protects bones and muscles.")
            else:
                out[organ] = dict(state="grey", text="Log exercise in the Hazard Zone to see this.")
            continue
        if organ == "eyes":
            vlvl = 0
            if len(vit):
                recent = vit[vit["day"] >= day - 2]
                for s in recent["symptoms"].fillna(""):
                    if "Blurred vision" in s:
                        vlvl = 2
                    elif "Eye strain" in s:
                        vlvl = max(vlvl, 1)
            out[organ] = (dict(state=names[vlvl], text="Vision symptom logged recently. Report vision changes early.") if vlvl
                          else dict(state="grey", text="Not measured here. Real missions use vision tests and eye imaging. Report any change early."))
            continue
        if not found:
            out[organ] = dict(state="grey", text="No readings yet.")
            continue
        worst = max(i["level"] for _, i in found)
        if worst == 0:
            out[organ] = dict(state="green", text="All tracked indicators look steady.")
        else:
            parts = [f"{rules.PARAMS[k]['label']} {i['value']:.{rules.PARAMS[k]['dec']}f} {rules.PARAMS[k]['unit']}" for k, i in found if i["level"] == worst]
            out[organ] = dict(state=names[worst], text="Needs attention: " + "; ".join(parts) + ". See Health Lab for the reason and next step.")
    return out


def render(ctx):
    lvl = rules.overall(ctx["ev"])
    theme.show(theme.hero("Body Explorer", "Tap a body system, or a NASA hazard, to see what spaceflight does and how you are doing right now.",
                          "Human Research Program · risks to health", ctx["env_name"],
                          chips=theme.tag(lvl, f"Overall: {rules.LEVEL_NAME[lvl]}") if lvl is not None else ""))
    st.write("")
    components.html(build_body_html(organ_status(ctx)), height=800, scrolling=True)
    c1, c2 = st.columns(2)
    c1.button("Add today's check-in", on_click=core.goto, args=(core.P_HEALTH,), key="be_go1")
    c2.button("Open the Hazard Zone", on_click=core.goto, args=(core.P_HAZ,), key="be_go2")
    with st.expander("NASA risk atlas: where AstroCare watches for each risk"):
        st.caption("Risks identified by NASA's Human Research Program, and the AstroCare indicator that reflects each one.")
        rows = "\n".join(f"| [{n}]({u}) | {t} |" for n, t, u in ((a, b, c) for a, b, c in rules.RISKS))
        st.markdown("| NASA risk | Where AstroCare watches |\n|---|---|\n" + rows)
        st.caption("Source: nasa.gov/hrp/risks. Paraphrased for education.")
