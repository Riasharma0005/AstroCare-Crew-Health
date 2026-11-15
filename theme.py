"""AstroCare theme.

Two visual languages, one galaxy:
  * PRO  (default): a mission-control look. Deep ink background, hairline panels, mono telemetry, a planet-horizon
    hero that changes with the mission environment, and clean line icons.
  * CUTE (Pip Companion + Game Zone only): candy nebula, smiling planets, Pip the alien.
Fonts load from Google Fonts when online and fall back to system fonts offline.
"""
import urllib.parse

import streamlit as st

LEVELS = {0: ("Steady", "#5fd3a0", "●"), 1: ("Watch", "#e8b04a", "●"), 2: ("Alert", "#ef6b73", "●")}
GREY = "#7587a3"
ICE, SUN = "#8ec5ff", "#f0b27a"


def rgba(h, a):
    h = h.lstrip("#")
    return f"rgba({int(h[0:2], 16)},{int(h[2:4], 16)},{int(h[4:6], 16)},{a})"


# ---------------------------------------------------------------- line icons (24x24, stroke = currentColor)
_I = {
    "orbit": "<circle cx='12' cy='12' r='2.6'/><ellipse cx='12' cy='12' rx='10' ry='4.2' transform='rotate(-28 12 12)'/>",
    "flask": "<path d='M9 3h6M10 3v6l-5.2 9.2A2 2 0 0 0 6.5 21h11a2 2 0 0 0 1.7-2.8L14 9V3'/><path d='M7.5 15h9'/>",
    "body": "<circle cx='12' cy='7' r='3.5'/><path d='M5 21v-2a5 5 0 0 1 5-5h4a5 5 0 0 1 5 5v2'/>",
    "alert": "<path d='M12 3.5 2.5 20h19L12 3.5z'/><path d='M12 10v4.5'/><circle cx='12' cy='17.3' r='.6'/>",
    "book": "<path d='M4 5a2 2 0 0 1 2-2h13v16H6a2 2 0 0 0-2 2V5z'/><path d='M8 7h7M8 11h5'/>",
    "face": "<circle cx='12' cy='12' r='9'/><path d='M8.5 14.2s1.4 2 3.5 2 3.5-2 3.5-2'/><circle cx='9' cy='10' r='.7'/><circle cx='15' cy='10' r='.7'/>",
    "game": "<rect x='2.5' y='7' width='19' height='10.5' rx='5'/><path d='M7 10.5v3.5M5.3 12.2h3.4'/><circle cx='15.5' cy='11' r='.8'/><circle cx='18' cy='13.2' r='.8'/>",
    "heart": "<path d='M12 20.5S3.5 15.5 3.5 9.7A4.7 4.7 0 0 1 12 7a4.7 4.7 0 0 1 8.5 2.7c0 5.8-8.5 10.8-8.5 10.8z'/>",
    "pulse": "<path d='M3 12h4l2.5-6.5 4.5 13 2.5-6.5H21'/>",
    "wind": "<path d='M3 8h10a2.8 2.8 0 1 0-2.8-2.8M3 12h15a2.8 2.8 0 1 1-2.8 2.8M3 16h7'/>",
    "thermo": "<path d='M14 14.6V5a2 2 0 0 0-4 0v9.6a4 4 0 1 0 4 0z'/>",
    "gauge": "<path d='M12 20.5a8.5 8.5 0 1 1 8.5-8.5'/><path d='M12 12l4-4'/>",
    "cube": "<path d='M12 3l8 4.5v9L12 21l-8-4.5v-9L12 3z'/><path d='M12 21v-9M4 7.5l8 4.5 8-4.5'/>",
    "moon": "<path d='M19.5 14.2A8 8 0 1 1 9.8 4.5a6.4 6.4 0 0 0 9.7 9.7z'/>",
    "smile": "<circle cx='12' cy='12' r='9'/><path d='M8.5 14.2s1.4 2 3.5 2 3.5-2 3.5-2'/><path d='M9 9.8h.01M15 9.8h.01'/>",
    "swirl": "<path d='M12 12.5a1.5 1.5 0 1 1 1.5-1.5'/><path d='M13.5 11A3.5 3.5 0 1 0 10 14.5 5.5 5.5 0 1 0 12 5'/>",
    "battery": "<rect x='2.5' y='8' width='17' height='8' rx='2'/><path d='M22 11v2M6 11v2'/>",
    "zap": "<path d='M13 2.5 4.5 13.5H11l-1 8 8.5-11H12l1-8z'/>",
    "sun": "<circle cx='12' cy='12' r='3.8'/><path d='M12 2.5v2.4M12 19.1v2.4M2.5 12h2.4M19.1 12h2.4M5.3 5.3l1.7 1.7M17 17l1.7 1.7M18.7 5.3 17 7M7 17l-1.7 1.7'/>",
    "users": "<circle cx='9' cy='8.5' r='3.2'/><path d='M2.8 20v-1.5a4.5 4.5 0 0 1 4.5-4.5h3.4a4.5 4.5 0 0 1 4.5 4.5V20'/><path d='M16 5.6a3.2 3.2 0 0 1 0 5.8M18 14.2a4.5 4.5 0 0 1 3.2 4.3V20'/>",
    "signal": "<path d='M4.5 12a10 10 0 0 1 15 0M7.5 15a6 6 0 0 1 9 0'/><circle cx='12' cy='18.6' r='.9'/>",
    "weight": "<path d='M7 4h10l3 16H4L7 4z'/><circle cx='12' cy='9' r='1.8'/>",
    "drop": "<path d='M12 3s6.3 6.6 6.3 11.2a6.3 6.3 0 0 1-12.6 0C5.7 9.6 12 3 12 3z'/>",
    "check": "<path d='M5 12.5l4.2 4.2L19 7'/>",
    "lock": "<rect x='5' y='10.5' width='14' height='10' rx='2'/><path d='M8 10.5V8a4 4 0 0 1 8 0v2.5'/>",
    "arrow": "<path d='M5 12h14M13 6l6 6-6 6'/>",
    "doc": "<path d='M6 3h8l4 4v14H6V3z'/><path d='M14 3v4h4M9 12h6M9 16h6'/>",
    "pen": "<path d='M4 20l1-4L16.5 4.5a2 2 0 0 1 3 3L8 19l-4 1z'/>",
    "target": "<circle cx='12' cy='12' r='8.5'/><circle cx='12' cy='12' r='4.5'/><circle cx='12' cy='12' r='.9'/>",
    "link": "<path d='M10 14a4 4 0 0 0 5.6 0l3-3a4 4 0 0 0-5.6-5.6l-1 1M14 10a4 4 0 0 0-5.6 0l-3 3a4 4 0 0 0 5.6 5.6l1-1'/>",
}
NAV_ICONS = ["orbit", "flask", "body", "alert", "book", "face", "game"]


def icon(name, size=18, color=None):
    c = f"color:{color};" if color else ""
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" '
            f'stroke-linecap="round" stroke-linejoin="round" style="{c}vertical-align:-3px;flex:0 0 auto">{_I.get(name, _I["orbit"])}</svg>')


def _mask(name):
    svg = (f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.8' "
           f"stroke-linecap='round' stroke-linejoin='round'>{_I[name]}</svg>")
    return "url(\"data:image/svg+xml;utf8," + urllib.parse.quote(svg, safe="/:=' ") + "\")"


def _nav_css():
    out = []
    for i, n in enumerate(NAV_ICONS, 1):
        m = _mask(n)
        out.append(f'[data-testid="stSidebar"] [role="radiogroup"] label:nth-of-type({i}) p::before{{-webkit-mask:{m} center/contain no-repeat;mask:{m} center/contain no-repeat}}')
    return "\n".join(out)


# ---------------------------------------------------------------- PRO css
_PRO = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;600;700&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&family=Newsreader:ital,wght@0,400;0,500;1,400&family=Fredoka:wght@500;600&family=Nunito:wght@600;800&display=swap');
:root{--bg:#050a13;--panel:rgba(13,23,39,.80);--line:rgba(142,175,214,.17);--line2:rgba(142,175,214,.30);--text:#e6edf8;--muted:#8da1bd;
--ice:#8ec5ff;--sun:#f0b27a;--ok:#5fd3a0;--warn:#e8b04a;--bad:#ef6b73;
--head:'Sora','Segoe UI',system-ui,sans-serif;--body:'IBM Plex Sans','Segoe UI',system-ui,sans-serif;--mono:'IBM Plex Mono',ui-monospace,'SFMono-Regular',Consolas,monospace;--serif:'Newsreader',Georgia,'Times New Roman',serif;
--chead:'Fredoka','ui-rounded','Arial Rounded MT Bold','Segoe UI',sans-serif;--cbody:'Nunito','ui-rounded','Segoe UI',sans-serif}
@keyframes bob{0%,100%{transform:translateY(0)}50%{transform:translateY(-7px)}}
@keyframes rise{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}
@keyframes twinkle{0%,100%{opacity:.35}50%{opacity:.95}}
@keyframes drift{from{background-position:0 0}to{background-position:-900px 560px}}
html,body,.stApp,[class*="css"]{font-family:var(--body)}
.stApp{color:var(--text);background:radial-gradient(1100px 560px at 78% -10%,rgba(58,108,190,.24),transparent 62%),
 radial-gradient(900px 520px at -5% 108%,rgba(240,178,122,.09),transparent 60%),#050a13!important}
.stApp::before{content:"";position:fixed;inset:0;z-index:0;pointer-events:none;opacity:.55;
 background-image:radial-gradient(1px 1px at 22px 34px,#fff,transparent),radial-gradient(1px 1px at 140px 96px,#cfe3ff,transparent),
 radial-gradient(1.4px 1.4px at 230px 170px,#fff,transparent),radial-gradient(1px 1px at 320px 64px,#ffe9d2,transparent),radial-gradient(1px 1px at 410px 220px,#fff,transparent);background-size:460px 280px}
[data-testid="stHeader"]{background:transparent}
.block-container{position:relative;z-index:1;padding-top:1.1rem;padding-bottom:3rem;max-width:1240px}
h1,h2,h3,h4,.stTabs button[role="tab"]{font-family:var(--head)!important;letter-spacing:-.01em;color:var(--text)!important}
p,li,label,.stMarkdown{color:#cbd6e8}
a{color:var(--ice)}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#08111f 0%,#050a13 100%)!important;border-right:1px solid var(--line)}
[data-testid="stSidebar"] [role="radiogroup"]{gap:2px}
[data-testid="stSidebar"] [role="radiogroup"] label{background:transparent;border:1px solid transparent;border-radius:10px;padding:8px 12px;width:100%;transition:all .15s}
[data-testid="stSidebar"] [role="radiogroup"] label:hover{background:rgba(142,197,255,.07)}
[data-testid="stSidebar"] [role="radiogroup"] label > div:first-child{display:none}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked){background:rgba(142,197,255,.12);border-color:rgba(142,197,255,.35)}
[data-testid="stSidebar"] [role="radiogroup"] label p{font-family:var(--body);font-weight:500;font-size:.96rem;display:flex;align-items:center;margin:0}
[data-testid="stSidebar"] [role="radiogroup"] label p::before{content:"";width:18px;height:18px;margin-right:11px;background:currentColor;opacity:.85;flex:0 0 auto}
/*NAVICONS*/
.stButton>button,.stFormSubmitButton>button,.stDownloadButton>button{border-radius:10px;border:1px solid rgba(142,197,255,.4);background:rgba(142,197,255,.06);
 color:#dcebff;font-weight:600;font-family:var(--body);transition:all .15s}
.stButton>button:hover,.stFormSubmitButton>button:hover,.stDownloadButton>button:hover{border-color:var(--ice);background:rgba(142,197,255,.15);color:#fff}
.stButton>button[kind="primary"],.stFormSubmitButton>button[kind="primary"],.stFormSubmitButton>button[kind="primaryFormSubmit"],.stDownloadButton>button[kind="primary"]{background:var(--ice);color:#04101f;border-color:var(--ice)}
.stTabs [data-baseweb="tab-list"]{gap:2px;border-bottom:1px solid var(--line)}
.stTabs button[role="tab"]{padding:9px 16px;font-weight:600;font-size:.95rem;color:var(--muted)!important}
.stTabs button[role="tab"][aria-selected="true"]{color:#fff!important}
[data-baseweb="input"],[data-baseweb="base-input"],[data-baseweb="select"]>div,textarea{background:rgba(255,255,255,.04)!important;border-radius:10px!important}
[data-testid="stExpander"]{border:1px solid var(--line)!important;border-radius:14px!important;background:rgba(255,255,255,.025)}
[data-testid="stForm"]{border:1px solid var(--line);border-radius:16px;background:rgba(255,255,255,.02)}
[data-testid="stChatMessage"]{background:rgba(255,255,255,.04);border-radius:14px;border:1px solid var(--line)}
[data-testid="stMetric"]{background:rgba(255,255,255,.04);border:1px solid var(--line);border-radius:12px;padding:10px 14px}
hr{border-color:var(--line)!important}

/* ---------- hero: planet horizon ---------- */
.hz{position:relative;overflow:hidden;border-radius:20px;border:1px solid var(--line2);min-height:236px;background:linear-gradient(180deg,#07101f 0%,#050a13 100%);isolation:isolate}
.hz-stars{position:absolute;inset:0;z-index:0;opacity:.8;background-image:radial-gradient(1px 1px at 30px 40px,#fff,transparent),radial-gradient(1.3px 1.3px at 190px 90px,#d8e8ff,transparent),
 radial-gradient(1px 1px at 330px 30px,#fff,transparent),radial-gradient(1px 1px at 470px 120px,#ffe9d2,transparent),radial-gradient(1.2px 1.2px at 600px 60px,#fff,transparent),radial-gradient(1px 1px at 720px 140px,#fff,transparent);background-size:780px 200px}
.hz-orbit{position:absolute;z-index:0;right:-8%;top:-60%;width:66%;height:170%;border:1px solid rgba(142,197,255,.20);border-radius:50%;transform:rotate(-14deg)}
.hz-orbit::after{content:"";position:absolute;left:12%;top:11%;width:7px;height:7px;border-radius:50%;background:var(--ice);box-shadow:0 0 12px var(--ice)}
.hz-limb{position:absolute;z-index:1;left:-20%;right:-20%;top:80%;height:260%;border-radius:50%;
 background:radial-gradient(ellipse at 50% 0%,var(--l1) 0%,var(--l2) 14%,#050a13 52%);box-shadow:0 -1px 0 rgba(255,255,255,.45),0 -10px 46px var(--lg)}
.hz-limb::before{content:"";position:absolute;inset:0;border-radius:50%;box-shadow:inset 0 16px 34px -10px var(--lg)}
.hz-sun{position:absolute;z-index:1;right:12%;bottom:6%;width:200px;height:200px;background:radial-gradient(circle,rgba(255,244,222,.95) 0%,rgba(255,210,150,.32) 22%,transparent 62%)}
.hz-body{position:relative;z-index:3;padding:26px 30px 24px;max-width:760px}
.hz-kick{color:var(--muted);font-size:.86rem;font-weight:500}
.hz-title{font-family:var(--head);font-weight:600;font-size:2.15rem;line-height:1.12;color:#fff;margin-top:6px;letter-spacing:-.025em}
.hz-sub{color:#b9c8df;margin-top:9px;font-size:1rem;max-width:640px}
.hz-epi{font-family:var(--serif);font-style:italic;color:#e8d7bd;margin-top:10px;font-size:1.05rem}
.ro-strip{display:flex;gap:0;flex-wrap:wrap;margin-top:14px;border:1px solid var(--line);border-radius:14px;background:var(--panel);overflow:hidden}
.ro{flex:1 1 150px;padding:10px 16px;border-right:1px solid var(--line)}
.ro:last-child{border-right:0}
.ro .k{color:var(--muted);font-size:.76rem}
.ro .v{font-family:var(--mono);font-size:1.12rem;margin-top:2px;color:#fff}
/* ---------- panels, tiles, tags ---------- */
.panel{background:var(--panel);border:1px solid var(--line);border-radius:16px;padding:16px 18px;color:var(--text)}
.panel h4{margin:0 0 6px;font-family:var(--head);font-size:1.02rem;font-weight:600;display:flex;align-items:center;gap:9px}
.muted{color:var(--muted);font-size:.86rem}
.sec{display:flex;align-items:center;gap:14px;margin:20px 0 10px;font-family:var(--head);font-weight:600;font-size:1.05rem;color:#fff}
.sec i{flex:1;height:1px;background:var(--line)}
.tag{display:inline-flex;align-items:center;gap:6px;padding:2px 10px;border-radius:999px;font-size:.76rem;font-weight:600;color:var(--c);border:1px solid color-mix(in srgb,var(--c) 45%,transparent);background:color-mix(in srgb,var(--c) 10%,transparent)}
.tag b{width:7px;height:7px;border-radius:50%;background:var(--c);box-shadow:0 0 8px var(--c)}
.tile{background:var(--panel);border:1px solid var(--line);border-left:3px solid var(--c);border-radius:14px;padding:12px 14px;height:100%}
.tile .lab{color:var(--muted);font-size:.8rem;display:flex;align-items:center;gap:7px}
.tile .val{font-family:var(--mono);font-size:1.75rem;color:#fff;line-height:1.2;margin-top:4px}
.tile .unit{font-size:.78rem;color:var(--muted);margin-left:4px}
.tile .sub{font-size:.74rem;color:var(--muted);margin-top:4px}
.item{display:flex;gap:12px;align-items:flex-start;padding:10px 13px;border:1px solid var(--line);border-radius:12px;background:rgba(255,255,255,.025);margin-top:8px}
.item.done{border-color:rgba(95,211,160,.35);background:rgba(95,211,160,.06)}
.item .t{font-weight:600;color:#fff;font-size:.93rem}
.bar{height:8px;border-radius:99px;background:rgba(255,255,255,.08);position:relative;margin:12px 0 6px}
.bar i{display:block;height:100%;border-radius:99px;background:linear-gradient(90deg,#4a86d8,var(--ice),var(--sun))}
.nodes{display:flex;gap:0;margin-top:8px}
.node{flex:1;text-align:center;position:relative;font-size:.74rem;color:var(--muted)}
.node::before{content:"";position:absolute;top:9px;left:-50%;right:50%;height:1px;background:var(--line2)}
.node:first-child::before{display:none}
.node s{display:block;width:19px;height:19px;border-radius:50%;margin:0 auto 5px;border:1px solid var(--line2);background:#07101f;position:relative;z-index:1;text-decoration:none}
.node.on s{background:var(--ice);border-color:var(--ice);box-shadow:0 0 14px rgba(142,197,255,.6)}
.node.on{color:#e6edf8}
.nav-t{padding:14px;border:1px solid var(--line);border-radius:14px;background:var(--panel);height:100%}
.nav-t .t{font-family:var(--head);font-weight:600;color:#fff;margin-top:8px;font-size:.98rem}
.nav-t .d{color:var(--muted);font-size:.8rem;margin-top:3px;min-height:34px}
/* ---------- story + poems ---------- */
.story p{font-family:var(--serif);font-size:1.12rem;line-height:1.75;color:#dfe6f2;margin:0 0 14px}
.chnum{font-family:var(--mono);color:var(--sun);font-size:.82rem}
.chtitle{font-family:var(--head);font-weight:600;font-size:1.55rem;color:#fff;letter-spacing:-.02em;margin:2px 0 10px}
.field{border-left:2px solid var(--ice);padding:6px 0 6px 14px;margin:6px 0 4px;color:#b9c8df;font-size:.9rem}
.field b{color:#fff}
.poem{position:relative;border:1px solid var(--line2);border-radius:20px;padding:34px 40px;background:radial-gradient(500px 240px at 90% 0%,rgba(240,178,122,.10),transparent 70%),radial-gradient(500px 300px at 0% 100%,rgba(90,140,220,.12),transparent 70%),rgba(8,15,28,.85)}
.poem h2{font-family:var(--serif)!important;font-weight:500;font-size:2.1rem;margin:0;color:#fff;letter-spacing:0}
.poem .by{font-family:var(--body);color:var(--sun);font-size:.9rem;margin:6px 0 22px}
.stz{font-family:var(--serif);font-size:1.18rem;line-height:1.85;color:#e6ecf7;margin:0 0 24px;padding-left:18px;border-left:1px solid rgba(240,178,122,.4);animation:rise .9s both}
.stz:nth-of-type(2){animation-delay:.12s}.stz:nth-of-type(3){animation-delay:.24s}.stz:nth-of-type(4){animation-delay:.36s}.stz:nth-of-type(5){animation-delay:.48s}.stz:nth-of-type(6){animation-delay:.6s}.stz:nth-of-type(7){animation-delay:.72s}
.excerpt{font-family:var(--serif);font-style:italic;font-size:1.15rem;line-height:1.6;color:#f1dfc6}
@media (max-width:760px){.hz-title{font-size:1.6rem}.poem{padding:22px 20px}}
@media (prefers-reduced-motion:reduce){.stz{animation:none}.pl,.pip{animation:none}}

/* ---------- cute planets & Pip (used only on Pip + Game Zone) ---------- */
.pl{position:relative;width:var(--s);height:var(--s);flex:0 0 auto;margin:0 auto;animation:bob 5.5s ease-in-out infinite}
.pl .ball{position:absolute;inset:0;border-radius:50%;z-index:2;background:radial-gradient(circle at 30% 26%,var(--a) 0%,var(--b) 80%);box-shadow:inset calc(var(--s)*-.08) calc(var(--s)*-.1) 0 rgba(0,0,0,.16),0 0 calc(var(--s)*.35) var(--g)}
.pl .ring{position:absolute;left:-30%;right:-30%;top:33%;bottom:33%;border:calc(var(--s)*.07) solid var(--r);border-radius:50%;transform:rotate(-17deg);z-index:1}
.pl .ring.front{z-index:3;clip-path:inset(50% 0 0 0)}
.pl .spot{position:absolute;border-radius:50%;background:rgba(0,0,0,.13);z-index:3}
.pl .face{position:absolute;inset:0;z-index:4}
.pl .eye{position:absolute;top:38%;width:13%;height:17%;background:#2b1659;border-radius:50%}
.pl .eye::after{content:"";position:absolute;top:16%;left:24%;width:36%;height:36%;background:#fff;border-radius:50%}
.pl .eye.l{left:29%}.pl .eye.r{left:58%}
.pl .mouth{position:absolute;left:41%;top:60%;width:18%;height:9%;border:calc(var(--s)*.03) solid #2b1659;border-top:none;border-radius:0 0 100px 100px}
.pl .cheek{position:absolute;top:57%;width:13%;height:8%;background:rgba(255,110,160,.55);border-radius:50%}
.pl .cheek.l{left:15%}.pl .cheek.r{left:72%}
.pl.wow .mouth{width:9%;height:11%;left:45.5%;border:none;background:#2b1659;border-radius:50%;top:61%}
.pl.sleepy .eye{height:5%;top:44%;border-radius:6px}.pl.sleepy .eye::after{display:none}.pl.sleepy .mouth{width:10%;left:45%}
.pip{position:relative;width:var(--s);height:calc(var(--s)*1.15);margin:0 auto;animation:bob 4.5s ease-in-out infinite}
.pip .ant{position:absolute;top:0;width:3.5%;height:26%;background:#6df2c4;border-radius:4px;transform-origin:bottom}
.pip .ant.l{left:30%;transform:rotate(-20deg)}.pip .ant.r{right:30%;transform:rotate(20deg)}
.pip .ant::before{content:"";position:absolute;top:-45%;left:50%;transform:translateX(-50%);width:340%;aspect-ratio:1;border-radius:50%;background:#ff8fd8;box-shadow:0 0 12px #ff8fd8}
.pip .body{position:absolute;left:6%;right:6%;top:20%;bottom:0;border-radius:50% 50% 44% 44%;background:radial-gradient(circle at 32% 25%,#b9ffe9,#4fe0b0 75%);box-shadow:inset -8px -10px 0 rgba(0,0,0,.12),0 0 28px rgba(109,242,196,.45)}
.pip .e{position:absolute;top:30%;width:22%;height:27%;background:#2b1659;border-radius:50%}
.pip .e::after{content:"";position:absolute;top:14%;left:24%;width:38%;height:38%;background:#fff;border-radius:50%}
.pip .e.l{left:20%}.pip .e.r{right:20%}
.pip .m{position:absolute;left:41%;top:66%;width:18%;height:10%;border:3px solid #2b1659;border-top:none;border-radius:0 0 100px 100px}
.pip .c{position:absolute;top:62%;width:14%;height:9%;background:rgba(255,110,160,.55);border-radius:50%}
.pip .c.l{left:9%}.pip .c.r{right:9%}
</style>
"""

# ---------------------------------------------------------------- CUTE overrides (Pip + Game Zone)
_CUTE = """
<style>
.stApp{background:radial-gradient(ellipse at 85% -5%,rgba(255,143,216,.28),transparent 42%),radial-gradient(ellipse at 0% 100%,rgba(120,200,255,.20),transparent 45%),radial-gradient(ellipse at 50% 50%,#2a1670 0%,#14093a 70%)!important}
.stApp::before{opacity:.8;animation:twinkle 6s ease-in-out infinite}
.stApp::after{content:"";position:fixed;inset:0;z-index:0;pointer-events:none;opacity:.45;background-image:radial-gradient(1.5px 1.5px at 60px 80px,#b9fff0,transparent),radial-gradient(2px 2px at 420px 120px,#e5d6ff,transparent);background-size:560px 340px;animation:drift 260s linear infinite}
h1,h2,h3,h4,.stTabs button[role="tab"]{font-family:var(--chead)!important}
html,body,.stApp,[class*="css"]{font-family:var(--cbody)}
.stButton>button,.stFormSubmitButton>button,.stDownloadButton>button{border-radius:999px;border:2px solid rgba(255,143,216,.65);background:rgba(255,143,216,.12);color:#ffe9f8;font-family:var(--chead);padding:.35rem 1.1rem}
.stButton>button:hover{border-color:#fff;box-shadow:0 0 18px rgba(255,143,216,.55);transform:translateY(-2px)}
.stButton>button[kind="primary"],.stFormSubmitButton>button[kind="primary"],.stFormSubmitButton>button[kind="primaryFormSubmit"]{background:linear-gradient(90deg,#ff8fd8,#b79cff);color:#2b1659;border-color:transparent}
.stTabs button[role="tab"][aria-selected="true"]{background:rgba(255,143,216,.14);border-radius:16px 16px 0 0}
[data-testid="stExpander"],[data-testid="stForm"]{border-radius:22px!important;border-color:rgba(183,156,255,.3)!important}
.ccard{background:linear-gradient(160deg,rgba(70,44,150,.62),rgba(32,18,86,.62));border:1.5px solid rgba(183,156,255,.30);border-radius:26px;padding:18px 20px;box-shadow:0 10px 30px rgba(8,2,30,.35);color:#f4ecff}
.ccard h4{margin:0 0 6px;font-family:var(--chead);font-size:1.15rem}
.cmuted{color:#b9a9e6;font-size:.86rem}
.chero{position:relative;overflow:hidden;border-radius:34px;padding:26px 30px;display:flex;align-items:center;gap:26px;flex-wrap:wrap;background:radial-gradient(circle at 88% 20%,rgba(255,143,216,.38),transparent 42%),linear-gradient(120deg,#3b1f95,#22115f 60%,#2d1a78);border:2px solid rgba(255,143,216,.45);box-shadow:0 14px 44px rgba(10,3,40,.5)}
.chero .txt{flex:1 1 320px;min-width:260px}
.ctitle{font-family:var(--chead);font-weight:700;font-size:2.1rem;line-height:1.1;color:#fff}
.csub{color:#e3d6ff;margin-top:8px}
.cchip{display:inline-flex;align-items:center;gap:6px;padding:4px 13px;border-radius:999px;font-weight:800;font-size:.78rem;border:1.5px solid;margin:8px 8px 0 0}
.cstat{background:linear-gradient(160deg,rgba(70,44,150,.55),rgba(32,18,86,.55));border:1.5px solid rgba(183,156,255,.3);border-radius:22px;padding:12px 14px;height:100%}
.cstat .lab{color:#b9a9e6;font-size:.8rem;font-weight:700}.cstat .val{font-family:var(--chead);font-size:1.9rem;font-weight:700;color:#fff}.cstat .unit{font-size:.8rem;color:#b9a9e6;margin-left:3px}
.ctrack{height:16px;border-radius:99px;background:rgba(255,255,255,.10);position:relative;margin:12px 0 4px}
.cfill{height:100%;border-radius:99px;background:linear-gradient(90deg,#6df2c4,#78c8ff,#b79cff,#ff8fd8)}
.crocket{position:absolute;top:-13px;font-size:24px;transform:translateX(-50%)}
.crow{display:flex;gap:10px;align-items:center;padding:9px 12px;border-radius:16px;background:rgba(255,255,255,.05);margin-top:8px;border:1px solid rgba(183,156,255,.18)}
.cbadge{display:inline-block;text-align:center;width:104px;padding:10px 6px;margin:5px;border-radius:20px;background:rgba(255,255,255,.06);border:1.5px solid rgba(183,156,255,.3);vertical-align:top}
.cbadge.on{background:rgba(255,211,107,.14);border-color:#ffd36b;box-shadow:0 0 16px rgba(255,211,107,.25)}
.cbadge.off{opacity:.45;filter:grayscale(.8)}
.cbadge .i{font-size:1.9rem}.cbadge .n{font-weight:800;font-size:.78rem;margin-top:2px}.cbadge .d{font-size:.66rem;color:#b9a9e6}
</style>
"""

ENV_SCENE = {  # (limb light, limb dark, atmosphere glow)
    "Mars Base": ("#f4a47c", "#7c2f2b", "rgba(240,140,100,.55)"),
    "Lunar Base": ("#ece9f2", "#4b4b60", "rgba(214,214,238,.40)"),
    "Space Station": ("#8fd0ff", "#12397a", "rgba(110,180,255,.62)"),
    "Spacecraft": ("#b9a7ff", "#2b2060", "rgba(170,150,255,.48)"),
    "Planetary Rover": ("#f4c690", "#6c3e22", "rgba(240,182,112,.52)"),
}


def inject(cute=False):
    css = _PRO.replace("/*NAVICONS*/", _nav_css())
    st.html(css + (_CUTE if cute else ""))


# ---------------------------------------------------------------- PRO components
def tag(level, text=None):
    name, col, _ = LEVELS.get(level, ("No data", GREY, "●"))
    return f'<span class="tag" style="--c:{col}"><b></b>{text or name}</span>'


def plain_tag(text, col=ICE):
    return f'<span class="tag" style="--c:{col}"><b></b>{text}</span>'


def hero(title, sub, kicker="", env=None, epigraph="", chips=""):
    l1, l2, lg = ENV_SCENE.get(env, ENV_SCENE["Space Station"])
    return (f'<div class="hz" style="--l1:{l1};--l2:{l2};--lg:{lg}"><div class="hz-stars"></div><div class="hz-orbit"></div>'
            f'<div class="hz-sun"></div><div class="hz-limb"></div><div class="hz-body"><div class="hz-kick">{kicker}</div>'
            f'<div class="hz-title">{title}</div><div class="hz-sub">{sub}</div>'
            f'{f"<div class=hz-epi>{epigraph}</div>" if epigraph else ""}<div style="margin-top:12px;display:flex;gap:8px;flex-wrap:wrap">{chips}</div></div></div>')


def readouts(items):
    return '<div class="ro-strip">' + "".join(f'<div class="ro"><div class="k">{k}</div><div class="v">{v}</div></div>' for k, v in items) + "</div>"


def section(title):
    return f'<div class="sec"><span>{title}</span><i></i></div>'


def tile(icon_name, label, value, unit="", level=None, sub=""):
    col = LEVELS[level][1] if level is not None else GREY
    t = tag(level) if level is not None else ""
    return (f'<div class="tile" style="--c:{col}"><div class="lab">{icon(icon_name, 16)} {label}</div>'
            f'<div class="val">{value}<span class="unit">{unit}</span></div><div style="margin-top:6px">{t}</div><div class="sub">{sub}</div></div>')


def item(icon_name, title, text="", level=None, done=False):
    col = LEVELS[level][1] if level is not None else ICE
    style = f' style="border-color:{rgba(col, .45)};background:{rgba(col, .07)}"' if level is not None else ""
    body = f'<div class="t">{title}</div>' + (f'<div class="muted">{text}</div>' if text else "")
    return f'<div class="item{" done" if done else ""}"{style}><span style="color:{col}">{icon(icon_name, 20)}</span><div style="flex:1">{body}</div></div>'


def style_fig(fig, h=300):
    fig.update_layout(height=h, margin=dict(l=8, r=8, t=30, b=8), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font=dict(color="#c4d2e8", family="IBM Plex Sans, Segoe UI, sans-serif"), legend=dict(orientation="h", y=1.12, x=0),
                      hoverlabel=dict(bgcolor="#0d1727", bordercolor="#8ec5ff"))
    fig.update_xaxes(gridcolor="rgba(142,175,214,.10)", zeroline=False, linecolor="rgba(142,175,214,.25)")
    fig.update_yaxes(gridcolor="rgba(142,175,214,.10)", zeroline=False)
    return fig


def show(html):
    st.html(html)


# ---------------------------------------------------------------- CUTE components (Pip + Game Zone)
def planet(a, b, size=96, ring=None, mood="happy", spots=True):
    ring_html = (f'<div class="ring" style="--r:{ring}"></div><div class="ring front" style="--r:{ring}"></div>' if ring else "")
    spot_html = ('<div class="spot" style="left:66%;top:20%;width:15%;height:15%"></div>'
                 '<div class="spot" style="left:12%;top:72%;width:11%;height:11%"></div>') if spots else ""
    return (f'<div class="pl {mood}" style="--s:{size}px;--a:{a};--b:{b};--g:{rgba(a, .55)}">{ring_html}<div class="ball"></div>{spot_html}'
            f'<div class="face"><div class="eye l"></div><div class="eye r"></div><div class="cheek l"></div><div class="cheek r"></div><div class="mouth"></div></div></div>')


def pip(size=120):
    return (f'<div class="pip" style="--s:{size}px"><div class="ant l"></div><div class="ant r"></div><div class="body"><div class="e l"></div>'
            '<div class="e r"></div><div class="c l"></div><div class="c r"></div><div class="m"></div></div></div>')


PLANETS = {"mint": ("#9bffe0", "#2fbf94", "#ffd36b"), "pink": ("#ffb8ea", "#d052b0", "#b79cff"), "sun": ("#ffe39a", "#f08a3c", "#ff8fd8"),
           "lav": ("#d8c8ff", "#7a4fd8", "#78c8ff"), "sky": ("#a8dcff", "#3d7be0", "#ffd36b"), "coral": ("#ffb3a0", "#d24f5a", "#ffd36b"),
           "moon": ("#f1edff", "#a79fd6", None)}


def cute(name, size=96, mood="happy", ring=True):
    a, b, r = PLANETS[name]
    return planet(a, b, size, r if ring else None, mood)


CL = {0: ("Steady", "#6df2c4", "😊"), 1: ("Watch", "#ffd36b", "😮"), 2: ("Alert", "#ff7a90", "😟")}


def cute_chip(text, col="#b79cff"):
    return f'<span class="cchip" style="color:{col};border-color:{col};background:{rgba(col, .12)}">{text}</span>'


def cute_level_chip(level, text=None):
    n, col, emo = CL[level]
    return cute_chip(f"{emo} {text or n}", col)


def cute_hero(title, sub, planet_html, chips=""):
    return (f'<div class="chero"><div class="txt"><div class="ctitle">{title}</div><div class="csub">{sub}</div><div>{chips}</div></div>{planet_html}</div>')


def cute_stat(icon_txt, label, value, unit=""):
    return f'<div class="cstat"><div class="lab">{icon_txt} {label}</div><div class="val">{value}<span class="unit">{unit}</span></div></div>'
