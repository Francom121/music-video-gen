"""Streamlit web UI — Music Video Generator + Story Studio."""
import os
import tempfile
import json
import datetime
from pathlib import Path

import streamlit as st

# ── .env path (same folder as this file) ─────────────────────────────────────
ENV_PATH = Path(__file__).parent / ".env"

try:
    from dotenv import load_dotenv
    load_dotenv(ENV_PATH)
except ImportError:
    pass


def _save_api_key(key: str):
    """Persist ANTHROPIC_API_KEY into .env so it survives restarts."""
    lines = []
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text().splitlines():
            if not line.startswith("ANTHROPIC_API_KEY="):
                lines.append(line)
    lines.append(f"ANTHROPIC_API_KEY={key}")
    ENV_PATH.write_text("\n".join(lines) + "\n")
    os.environ["ANTHROPIC_API_KEY"] = key


# ── projects directory ────────────────────────────────────────────────────────
PROJECTS_DIR = Path.home() / "Documents" / "Music to Video App" / "projects"
PROJECTS_DIR.mkdir(parents=True, exist_ok=True)

st.set_page_config(
    page_title="Music Video Generator",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
*, *::before, *::after { font-family: 'Inter', system-ui, sans-serif !important; box-sizing: border-box; }

.stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
    background: radial-gradient(ellipse 80% 60% at 15% 40%, #1e0840 0%, #07020f 45%, #020610 100%) !important;
}
[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stAppViewContainer"]::before {
    content:''; position:fixed; top:-15%; left:-5%; width:55vw; height:55vw;
    background:radial-gradient(circle,rgba(120,50,255,.13) 0%,transparent 65%);
    pointer-events:none; z-index:0;
}
[data-testid="stAppViewContainer"]::after {
    content:''; position:fixed; bottom:-10%; right:-5%; width:45vw; height:45vw;
    background:radial-gradient(circle,rgba(40,80,255,.07) 0%,transparent 65%);
    pointer-events:none; z-index:0;
}

/* sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg,rgba(14,6,32,.97) 0%,rgba(6,3,16,.99) 100%) !important;
    border-right: 1px solid rgba(130,80,255,.18) !important;
}
[data-testid="stSidebar"] > div:first-child { padding-top:1rem !important; }
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stMarkdown { color:rgba(185,165,255,.75) !important; }
[data-testid="stSidebar"] input,
[data-testid="stSidebar"] textarea {
    background:rgba(255,255,255,.04) !important;
    border:1px solid rgba(130,80,255,.22) !important;
    border-radius:10px !important; color:#e2dff0 !important; caret-color:#a78bfa;
}
[data-testid="stSidebar"] input:focus,
[data-testid="stSidebar"] textarea:focus {
    border-color:rgba(160,110,255,.55) !important;
    box-shadow:0 0 0 3px rgba(130,60,255,.12) !important; outline:none !important;
}
[data-testid="stSidebar"] [data-baseweb="select"] > div {
    background:rgba(255,255,255,.04) !important;
    border:1px solid rgba(130,80,255,.22) !important;
    border-radius:10px !important; color:#e2dff0 !important;
}

/* saved project list items */
.proj-item {
    background:rgba(255,255,255,.03);
    border:1px solid rgba(130,80,255,.18);
    border-radius:10px; padding:.6rem .85rem;
    margin-bottom:.4rem; cursor:pointer;
    transition:all .18s;
}
.proj-item:hover { background:rgba(130,60,255,.1); border-color:rgba(160,110,255,.38); }
.proj-name { font-weight:700; font-size:.88rem; color:rgba(221,214,254,.9); }
.proj-meta { font-size:.72rem; color:rgba(148,112,255,.5); margin-top:.1rem; }

/* main */
.block-container { padding:2rem 2.5rem 4rem !important; max-width:1380px; }

h1 {
    background:linear-gradient(120deg,#c4b5fd 0%,#8b5cf6 55%,#60a5fa 100%) !important;
    -webkit-background-clip:text !important; -webkit-text-fill-color:transparent !important;
    background-clip:text !important; font-size:2.3rem !important; font-weight:800 !important;
    letter-spacing:-.025em !important; line-height:1.1 !important;
}
h2 { color:#c4b5fd !important; font-weight:700 !important; }
h3 { color:#a78bfa !important; font-weight:600 !important; }

input, textarea, [data-baseweb="textarea"] textarea {
    background:rgba(255,255,255,.04) !important;
    border:1px solid rgba(130,80,255,.22) !important;
    border-radius:10px !important; color:#e2dff0 !important; caret-color:#a78bfa;
}
input:focus, textarea:focus {
    border-color:rgba(160,110,255,.55) !important;
    box-shadow:0 0 0 3px rgba(130,60,255,.12) !important;
}
[data-baseweb="select"] > div {
    background:rgba(255,255,255,.04) !important;
    border:1px solid rgba(130,80,255,.22) !important; border-radius:10px !important;
}
[data-baseweb="popover"] { background:#120826 !important; border:1px solid rgba(130,80,255,.25) !important; border-radius:10px !important; }
[data-baseweb="menu"] { background:#120826 !important; }
[data-baseweb="option"]:hover { background:rgba(130,60,255,.18) !important; }

/* file uploader — hide ALL internal content, show clean drop zone via pseudo */
[data-testid="stFileUploader"] label { display:none !important; }
[data-testid="stFileUploader"] section {
    position:relative !important;
    background:rgba(255,255,255,.025) !important;
    border:1.5px dashed rgba(130,80,255,.32) !important;
    border-radius:12px !important;
    transition:border-color .2s, background .2s;
    min-height:44px !important;
    padding:0 !important;
    cursor:pointer !important;
    overflow:hidden !important;
}
[data-testid="stFileUploader"] section:hover {
    border-color:rgba(160,110,255,.6) !important;
    background:rgba(120,60,255,.06) !important;
}
/* fake label shown to user */
[data-testid="stFileUploader"] section::after {
    content:'📎  Click or drag & drop to upload';
    position:absolute; inset:0;
    display:flex; align-items:center; justify-content:center;
    font-size:.8rem; font-weight:600;
    color:rgba(196,165,253,.75);
    pointer-events:none;
}
/* make the dropzone fill the whole section so clicks/drops work */
[data-testid="stFileUploaderDropzone"] {
    position:absolute !important; inset:0 !important;
    background:transparent !important;
    min-height:unset !important;
    padding:0 !important;
    gap:0 !important;
}
/* hide all the internal Streamlit-rendered children visually */
[data-testid="stFileUploaderDropzoneInstructions"],
[data-testid="stFileUploaderDropzone"] > span,
[data-testid="stFileUploaderDropzone"] button {
    opacity:0 !important;
    pointer-events:none !important;
    position:absolute !important;
    inset:0 !important;
    width:100% !important;
    height:100% !important;
}
/* but keep the actual hidden <input> interactive for click-to-browse */
[data-testid="stFileUploaderDropzoneInput"] {
    opacity:0 !important;
    position:absolute !important;
    inset:0 !important;
    width:100% !important;
    height:100% !important;
    cursor:pointer !important;
    pointer-events:all !important;
}

/* primary button */
button[kind="primary"], [data-testid="baseButton-primary"] {
    background:linear-gradient(135deg,#7c3aed 0%,#5b21b6 100%) !important;
    border:1px solid rgba(196,165,253,.3) !important; border-radius:12px !important;
    color:#fff !important; font-weight:700 !important; font-size:.98rem !important;
    letter-spacing:.02em !important;
    box-shadow:0 4px 20px rgba(124,58,237,.45),inset 0 1px 0 rgba(255,255,255,.12) !important;
    transition:all .2s ease !important; padding:.65rem 1.4rem !important;
}
button[kind="primary"]:hover { background:linear-gradient(135deg,#8b4ff8 0%,#6d28d9 100%) !important; box-shadow:0 6px 28px rgba(139,92,246,.6),inset 0 1px 0 rgba(255,255,255,.18) !important; transform:translateY(-1px) !important; }
button[kind="primary"]:disabled { background:rgba(80,40,140,.28) !important; color:rgba(196,165,253,.3) !important; box-shadow:none !important; transform:none !important; }

/* secondary */
button[kind="secondary"], [data-testid="baseButton-secondary"],
.stDownloadButton button {
    background:rgba(255,255,255,.04) !important;
    border:1px solid rgba(130,80,255,.28) !important; border-radius:10px !important;
    color:#c4b5fd !important; font-weight:500 !important; transition:all .2s ease !important;
}
button[kind="secondary"]:hover, .stDownloadButton button:hover {
    background:rgba(130,60,255,.12) !important; border-color:rgba(160,110,255,.5) !important;
    box-shadow:0 3px 14px rgba(120,50,220,.22) !important;
}

/* tabs */
[data-baseweb="tab-list"] {
    background:rgba(255,255,255,.03) !important;
    border:1px solid rgba(130,80,255,.14) !important; border-radius:12px !important;
    padding:4px !important; gap:3px !important;
}
[data-baseweb="tab"] {
    background:transparent !important; border:none !important; border-radius:9px !important;
    color:rgba(196,181,255,.55) !important; font-weight:500 !important;
    padding:.45rem 1.1rem !important; transition:all .18s !important;
}
[data-baseweb="tab"]:hover { color:rgba(196,181,255,.85) !important; background:rgba(130,60,255,.08) !important; }
[aria-selected="true"][data-baseweb="tab"] {
    background:linear-gradient(135deg,rgba(124,58,237,.38) 0%,rgba(91,33,182,.35) 100%) !important;
    color:#e9d5ff !important; font-weight:700 !important;
    box-shadow:0 2px 8px rgba(100,40,220,.3) !important;
}

/* metrics */
[data-testid="metric-container"] {
    background:rgba(255,255,255,.035) !important; border:1px solid rgba(130,80,255,.18) !important;
    border-radius:14px !important; padding:1rem 1.2rem !important;
    box-shadow:0 4px 16px rgba(0,0,0,.35),inset 0 1px 0 rgba(255,255,255,.04) !important;
}
[data-testid="stMetricLabel"] > div { color:rgba(167,139,250,.65) !important; font-size:.68rem !important; font-weight:700 !important; letter-spacing:.1em !important; text-transform:uppercase !important; }
[data-testid="stMetricValue"] > div { color:#ddd6fe !important; font-weight:800 !important; font-size:1.65rem !important; }

/* expander */
[data-testid="stExpander"] {
    background:rgba(255,255,255,.025) !important; border:1px solid rgba(130,80,255,.15) !important; border-radius:12px !important;
}
[data-testid="stExpander"] summary { color:#a78bfa !important; font-weight:600 !important; }

/* alerts */
[data-testid="stAlert"] {
    background:rgba(90,50,220,.1) !important; border:1px solid rgba(130,80,255,.22) !important;
    border-radius:12px !important; color:#c4b5fd !important;
}

hr { border-color:rgba(130,80,255,.12) !important; }
::-webkit-scrollbar { width:5px; height:5px; }
::-webkit-scrollbar-track { background:rgba(0,0,0,.15); }
::-webkit-scrollbar-thumb { background:rgba(124,58,237,.4); border-radius:3px; }
::-webkit-scrollbar-thumb:hover { background:rgba(139,92,246,.65); }

/* ── custom components ── */
.hero-sub { color:rgba(196,181,255,.55); font-size:.98rem; margin-top:.2rem; margin-bottom:2rem; }
.lbl { font-size:.66rem; font-weight:800; letter-spacing:.12em; text-transform:uppercase; color:rgba(167,139,250,.55); margin-bottom:.35rem; }

.pipeline { background:rgba(255,255,255,.025); border:1px solid rgba(130,80,255,.14); border-radius:14px; padding:1.1rem 1.4rem; margin:.75rem 0 1.25rem; }
.step { display:flex; align-items:center; gap:.7rem; padding:.4rem 0; font-size:.88rem; color:rgba(196,181,255,.7); border-bottom:1px solid rgba(130,80,255,.07); }
.step:last-child { border-bottom:none; }
.pill { display:inline-flex; align-items:center; justify-content:center; padding:.12rem .6rem; border-radius:999px; font-size:.67rem; font-weight:800; letter-spacing:.04em; min-width:68px; flex-shrink:0; }
.pill-done { background:rgba(52,211,153,.12); color:#6ee7b7; border:1px solid rgba(52,211,153,.22); }
.pill-run  { background:rgba(251,191,36,.12); color:#fde68a; border:1px solid rgba(251,191,36,.22); animation:blink 1.4s ease-in-out infinite; }
.pill-wait { background:rgba(109,79,200,.1); color:rgba(167,139,250,.4); border:1px solid rgba(109,79,200,.14); }
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:.45} }

.concept { background:linear-gradient(135deg,rgba(124,58,237,.09) 0%,rgba(79,40,200,.06) 100%); border:1px solid rgba(167,139,250,.2); border-radius:14px; padding:1.2rem 1.4rem; font-size:1.02rem; color:rgba(221,214,254,.88); line-height:1.72; font-style:italic; box-shadow:inset 0 1px 0 rgba(255,255,255,.04); margin-bottom:1.4rem; }
.tags { display:flex; flex-wrap:wrap; gap:.38rem; margin-top:.45rem; margin-bottom:1rem; }
.tag { background:rgba(109,40,217,.16); border:1px solid rgba(139,92,246,.24); color:rgba(216,180,254,.85); padding:.2rem .72rem; border-radius:999px; font-size:.76rem; font-weight:500; }
.srow { display:flex; align-items:center; gap:.7rem; padding:.42rem .5rem; border-radius:8px; border-bottom:1px solid rgba(130,80,255,.07); transition:background .15s; }
.srow:hover { background:rgba(124,58,237,.07); }
.sname { font-weight:600; color:rgba(221,214,254,.9); min-width:170px; font-size:.88rem; }
.stime { color:rgba(148,112,255,.6); font-family:'SF Mono',monospace; font-size:.78rem; }
.sdur  { margin-left:auto; font-size:.7rem; color:rgba(130,100,220,.5); background:rgba(124,58,237,.1); padding:2px 8px; border-radius:999px; }

/* shot card */
.shot { background:linear-gradient(135deg,rgba(255,255,255,.038) 0%,rgba(109,40,217,.04) 100%); border:1px solid rgba(148,112,255,.15); border-radius:14px; padding:1rem 1.2rem; margin-bottom:.8rem; transition:border-color .2s,box-shadow .2s,transform .2s; box-shadow:0 3px 14px rgba(0,0,0,.28); }
.shot:hover { border-color:rgba(167,139,250,.3); box-shadow:0 6px 22px rgba(109,40,217,.2); transform:translateY(-1px); }
.shot-hdr { display:flex; align-items:center; gap:.45rem; margin-bottom:.42rem; }
.sid { font-size:.66rem; font-weight:800; letter-spacing:.1em; text-transform:uppercase; color:rgba(148,112,255,.6); }
.stag { background:rgba(109,40,217,.2); border:1px solid rgba(139,92,246,.22); color:rgba(216,180,254,.85); font-size:.63rem; font-weight:700; letter-spacing:.06em; padding:2px 9px; border-radius:999px; }
.sdesc { font-weight:600; font-size:.93rem; color:rgba(233,213,255,.9); margin-bottom:.28rem; }
.scue  { color:rgba(148,130,200,.55); font-size:.8rem; font-style:italic; margin-bottom:.6rem; }
.prompt-box { background:rgba(0,0,0,.32); border:1px solid rgba(109,40,217,.2); border-left:3px solid rgba(139,92,246,.65); border-radius:0 8px 8px 0; padding:.65rem .85rem; font-family:'SF Mono','Fira Code',monospace; font-size:.8rem; color:rgba(221,214,254,.82); white-space:pre-wrap; word-break:break-word; line-height:1.52; }
.img-box { background:rgba(0,0,0,.25); border:1px solid rgba(180,120,255,.18); border-left:3px solid rgba(200,150,255,.5); border-radius:0 8px 8px 0; padding:.65rem .85rem; font-family:'SF Mono','Fira Code',monospace; font-size:.8rem; color:rgba(230,210,255,.78); white-space:pre-wrap; word-break:break-word; line-height:1.52; margin-top:.5rem; }
.box-lbl { font-size:.6rem; font-weight:800; letter-spacing:.1em; text-transform:uppercase; color:rgba(148,112,255,.45); margin-bottom:.25rem; }

/* image prompts tab */
.img-prompt-block { background:rgba(255,255,255,.025); border:1px solid rgba(180,120,255,.16); border-radius:12px; padding:1rem 1.1rem; margin-bottom:.75rem; }
.img-prompt-num { font-size:.65rem; font-weight:800; letter-spacing:.1em; text-transform:uppercase; color:rgba(200,150,255,.5); margin-bottom:.35rem; }
.img-prompt-text { font-family:'SF Mono','Fira Code',monospace; font-size:.83rem; color:rgba(230,210,255,.82); line-height:1.58; white-space:pre-wrap; word-break:break-word; }

/* timeline */
.tlhdr { font-size:.68rem; font-weight:800; letter-spacing:.1em; text-transform:uppercase; color:rgba(148,112,255,.62); padding:1rem 0 .35rem; border-top:1px solid rgba(130,80,255,.1); margin-top:.4rem; }
.tlhdr:first-child { border-top:none; padding-top:0; }
.tlrow { display:flex; align-items:baseline; gap:.65rem; font-family:'SF Mono','Fira Code',monospace; font-size:.78rem; padding:.32rem .5rem; border-radius:6px; margin-bottom:1px; transition:background .14s; }
.tlrow:hover { background:rgba(124,58,237,.07); }
.tltime { color:rgba(139,92,246,.65); min-width:125px; flex-shrink:0; }
.tlshot { color:rgba(167,139,250,.65); font-weight:700; min-width:58px; flex-shrink:0; }
.tldesc { color:rgba(196,181,255,.72); }
.tlcue  { color:rgba(130,110,190,.45); font-style:italic; }

/* export cards */
.dlcard { background:rgba(255,255,255,.03); border:1px solid rgba(130,80,255,.18); border-radius:14px; padding:1.1rem 1rem .85rem; text-align:center; }
.dlico { font-size:1.8rem; line-height:1; margin-bottom:.35rem; }
.dltitle { font-weight:700; font-size:.88rem; color:rgba(221,214,254,.9); margin-bottom:.15rem; }
.dlsub { font-size:.73rem; color:rgba(148,130,200,.5); margin-bottom:.7rem; }

/* save banner */
.save-banner { background:linear-gradient(135deg,rgba(52,211,153,.08) 0%,rgba(16,185,129,.06) 100%); border:1px solid rgba(52,211,153,.2); border-radius:12px; padding:.75rem 1.1rem; color:rgba(110,231,183,.85); font-size:.85rem; font-weight:500; margin-bottom:.75rem; }

/* story arc card */
.arc-card { background:rgba(255,255,255,.025); border:1px solid rgba(130,80,255,.15); border-radius:14px; overflow:hidden; margin-bottom:.5rem; }
.arc-row { display:flex; gap:.75rem; padding:.55rem 1rem; border-bottom:1px solid rgba(130,80,255,.08); align-items:baseline; }
.arc-row:last-child { border-bottom:none; }
.arc-label { font-size:.67rem; font-weight:800; letter-spacing:.09em; text-transform:uppercase; color:rgba(148,112,255,.55); min-width:130px; flex-shrink:0; padding-top:.05rem; }
.arc-val { font-size:.88rem; color:rgba(210,195,255,.82); line-height:1.55; }

/* story beat on shot card */
.story-beat { font-size:.78rem; color:rgba(167,139,250,.55); font-style:italic; margin-bottom:.35rem; line-height:1.45; }

/* scene card (Story Studio) */
.scene-card { background:linear-gradient(135deg,rgba(255,255,255,.038) 0%,rgba(109,40,217,.04) 100%); border:1px solid rgba(148,112,255,.15); border-radius:14px; padding:1rem 1.2rem; margin-bottom:.8rem; transition:border-color .2s,box-shadow .2s,transform .2s; box-shadow:0 3px 14px rgba(0,0,0,.28); }
.scene-card:hover { border-color:rgba(167,139,250,.3); box-shadow:0 6px 22px rgba(109,40,217,.2); transform:translateY(-1px); }
.scene-hdr { display:flex; align-items:center; gap:.45rem; margin-bottom:.42rem; }
.scene-id { font-size:.66rem; font-weight:800; letter-spacing:.1em; text-transform:uppercase; color:rgba(148,112,255,.6); }
.scene-act { background:rgba(109,40,217,.2); border:1px solid rgba(139,92,246,.22); color:rgba(216,180,254,.85); font-size:.63rem; font-weight:700; letter-spacing:.06em; padding:2px 9px; border-radius:999px; }
.scene-desc { font-weight:600; font-size:.93rem; color:rgba(233,213,255,.9); margin-bottom:.28rem; }
.scene-beat { font-size:.78rem; color:rgba(167,139,250,.55); font-style:italic; margin-bottom:.5rem; line-height:1.45; }

/* chat iteration panel */
.chat-box { background:rgba(255,255,255,.02); border:1px solid rgba(130,80,255,.14); border-radius:14px; padding:1rem 1.2rem; margin-top:1rem; }
.chat-msg-user { background:rgba(124,58,237,.12); border:1px solid rgba(139,92,246,.2); border-radius:10px; padding:.55rem .85rem; margin-bottom:.45rem; font-size:.88rem; color:rgba(221,214,254,.9); }
.chat-msg-ai { background:rgba(52,211,153,.06); border:1px solid rgba(52,211,153,.15); border-radius:10px; padding:.55rem .85rem; margin-bottom:.45rem; font-size:.88rem; color:rgba(180,240,210,.85); }

/* mode switcher */
.mode-badge { display:inline-block; padding:.18rem .75rem; border-radius:999px; font-size:.72rem; font-weight:800; letter-spacing:.06em; text-transform:uppercase; }
.mode-mv { background:rgba(124,58,237,.18); border:1px solid rgba(139,92,246,.3); color:rgba(216,180,254,.9); }
.mode-ss { background:rgba(251,191,36,.1); border:1px solid rgba(251,191,36,.25); color:rgba(254,240,138,.85); }
</style>
""", unsafe_allow_html=True)


# ── helpers ───────────────────────────────────────────────────────────────────
def fmt_time(t):
    m = int(t // 60); s = t % 60
    return f"{m}:{s:05.2f}"


def save_project(name, mode, data):
    """Save any project (music video or story studio) as JSON."""
    slug = "".join(c if c.isalnum() or c in "-_ " else "_" for c in name).strip().replace(" ", "_")
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    fname = PROJECTS_DIR / f"{slug}_{ts}.json"
    payload = {"name": name, "mode": mode, "saved_at": datetime.datetime.now().isoformat()}
    payload.update(data)
    fname.write_text(json.dumps(payload, indent=2))
    return fname


def list_projects():
    files = sorted(PROJECTS_DIR.glob("*.json"), key=lambda f: f.stat().st_mtime, reverse=True)
    projects = []
    for f in files:
        try:
            d = json.loads(f.read_text())
            projects.append({
                "file": f,
                "name": d.get("name", f.stem),
                "mode": d.get("mode", "music_video"),
                "saved_at": d.get("saved_at", ""),
                "audio": d.get("audio_name", ""),
            })
        except Exception:
            pass
    return projects


def load_project(path):
    return json.loads(Path(path).read_text())


def delete_project(path):
    Path(path).unlink(missing_ok=True)


# ── sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🎬 Music Video Gen")
    st.divider()

    # ── Provider + API key ─────────────────────────────────────────────────
    st.markdown('<p class="lbl">AI Provider</p>', unsafe_allow_html=True)
    provider = st.selectbox(
        "provider_sel",
        ["anthropic", "openrouter"],
        format_func=lambda x: "🟣 Anthropic (Claude)" if x == "anthropic" else "🔀 OpenRouter",
        label_visibility="collapsed",
        key="provider_select",
    )

    if provider == "anthropic":
        st.markdown('<p class="lbl">Anthropic API Key</p>', unsafe_allow_html=True)
        api_key = st.text_input(
            "api_key_ant",
            value=os.environ.get("ANTHROPIC_API_KEY", ""),
            type="password",
            label_visibility="collapsed",
            placeholder="sk-ant-api03-...",
        )
        if api_key and api_key != os.environ.get("ANTHROPIC_API_KEY", ""):
            _save_api_key(api_key)
        elif api_key:
            os.environ["ANTHROPIC_API_KEY"] = api_key
    else:
        st.markdown('<p class="lbl">OpenRouter API Key</p>', unsafe_allow_html=True)
        or_key_saved = os.environ.get("OPENROUTER_API_KEY", "")
        api_key = st.text_input(
            "api_key_or",
            value=or_key_saved,
            type="password",
            label_visibility="collapsed",
            placeholder="sk-or-...",
        )
        if api_key and api_key != or_key_saved:
            # persist to .env
            lines = []
            if ENV_PATH.exists():
                for line in ENV_PATH.read_text().splitlines():
                    if not line.startswith("OPENROUTER_API_KEY="):
                        lines.append(line)
            lines.append(f"OPENROUTER_API_KEY={api_key}")
            ENV_PATH.write_text("\n".join(lines) + "\n")
            os.environ["OPENROUTER_API_KEY"] = api_key
        elif api_key:
            os.environ["OPENROUTER_API_KEY"] = api_key

    st.divider()

    # ── shared settings ────────────────────────────────────────────────────
    from src import llm_client as _llmc
    from src.llm_client import OPENROUTER_FREE_VISION_MODELS

    def _vision_describe(img_file, prompt_text, spinner_label, cache_key, max_tokens=300):
        """Describe an image via the active provider; cache result by content hash."""
        if not api_key:
            st.warning("Enter your API key in the sidebar before uploading images.")
            return ""
        img_bytes = img_file.read()
        if not img_bytes:
            st.warning("Image file appears empty — try re-uploading.")
            return ""
        img_hash = hash(img_bytes)
        if st.session_state.get(cache_key + "_hash") == img_hash:
            return st.session_state.get(cache_key + "_desc", "")
        with st.spinner(spinner_label):
            ext = img_file.name.rsplit(".", 1)[-1].lower()
            vision_model = (
                "claude-haiku-4-5-20251001" if provider == "anthropic"
                else OPENROUTER_FREE_VISION_MODELS[0]
            )
            try:
                desc = _llmc.vision_describe(
                    provider, api_key, vision_model,
                    img_bytes, ext, prompt_text, max_tokens,
                )
                if desc:
                    st.session_state[cache_key + "_hash"] = img_hash
                    st.session_state[cache_key + "_desc"] = desc
                    return desc
                else:
                    st.warning("Model returned empty description. Try re-uploading.")
                    return ""
            except Exception as e:
                st.error(f"Could not describe image: {e}")
                return ""

    # ── Characters (up to 4) ───────────────────────────────────────────────
    st.markdown('<p class="lbl">🎭 Characters</p>', unsafe_allow_html=True)
    st.markdown('<p style="color:rgba(148,112,255,.4);font-size:.72rem;margin-bottom:.5rem;line-height:1.45">Upload up to 4 character photos — Claude auto-describes each. Leave all blank and Claude invents them.</p>', unsafe_allow_html=True)

    # Toggle to show/hide characters 2-4
    if "show_extra_chars" not in st.session_state:
        st.session_state["show_extra_chars"] = False

    char_labels = ["Protagonist", "Character 2", "Character 3", "Character 4"]
    char_descriptions = []

    def _render_char_slot(ci):
        ck = f"char_{ci}"
        st.markdown(f'<p class="lbl" style="margin-top:.6rem;margin-bottom:.3rem">{char_labels[ci]}</p>', unsafe_allow_html=True)
        uploaded = st.file_uploader(
            " ",
            type=["jpg","jpeg","png","webp"],
            label_visibility="collapsed",
            key=f"{ck}_upload",
        )
        if uploaded is not None:
            img_col, name_col = st.columns([1, 3])
            with img_col:
                uploaded.seek(0)
                st.image(uploaded, use_container_width=True)
            with name_col:
                st.markdown(f'<p style="color:rgba(185,165,255,.7);font-size:.72rem;word-break:break-all;margin:0;padding-top:.25rem">{uploaded.name}</p>', unsafe_allow_html=True)
            uploaded.seek(0)
            _vision_describe(
                uploaded,
                "Describe this person for use as a consistent character in an AI visual project. "
                "Cover: approximate age, build/physique, hair (color, length, style), skin tone, "
                "facial features, clothing visible in the photo, and overall vibe/presence. "
                "Write 2-3 sentences, purely descriptive, no names. Start with 'A [age] [gender]…'",
                f"Describing {char_labels[ci]}…",
                ck,
            )
        saved_desc = st.session_state.get(f"{ck}_desc", "")
        # Keep widget state in sync with the underlying description value
        if saved_desc and st.session_state.get(f"{ck}_desc_box", "") != saved_desc:
            st.session_state[f"{ck}_desc_box"] = saved_desc
        desc_val = st.text_area(
            f"{ck}_desc_area",
            placeholder="Auto-filled after upload, or type manually…",
            height=75,
            label_visibility="collapsed",
            key=f"{ck}_desc_box",
        )
        st.session_state[f"{ck}_desc"] = desc_val
        if desc_val.strip():
            char_descriptions.append((char_labels[ci], desc_val.strip()))

    _render_char_slot(0)

    toggle_label = "﹢ Add more characters" if not st.session_state["show_extra_chars"] else "﹣ Hide extra characters"
    if st.button(toggle_label, key="toggle_extra_chars", use_container_width=True):
        st.session_state["show_extra_chars"] = not st.session_state["show_extra_chars"]
        st.rerun()

    if st.session_state["show_extra_chars"]:
        for ci in range(1, 4):
            _render_char_slot(ci)

    # Build the combined character string fed into prompts
    if char_descriptions:
        character = "\n".join(f"{label}: {desc}" for label, desc in char_descriptions)
    else:
        character = ""

    # ── Style Reference Image ──────────────────────────────────────────────
    st.divider()
    st.markdown('<p class="lbl">🎨 Style Reference Image</p>', unsafe_allow_html=True)
    st.markdown('<p style="color:rgba(148,112,255,.4);font-size:.72rem;margin-bottom:.4rem;line-height:1.45">Upload a mood board, film still, or artwork — Claude extracts the visual style.</p>', unsafe_allow_html=True)
    style_ref_img = st.file_uploader(" ", type=["jpg","jpeg","png","webp"],
                                     label_visibility="collapsed", key="style_ref_upload")
    if style_ref_img is not None:
        img_col, name_col = st.columns([1, 3])
        with img_col:
            style_ref_img.seek(0)
            st.image(style_ref_img, use_container_width=True)
        with name_col:
            st.markdown(f'<p style="color:rgba(185,165,255,.7);font-size:.72rem;word-break:break-all;margin:0;padding-top:.25rem">{style_ref_img.name}</p>', unsafe_allow_html=True)
        style_ref_img.seek(0)
        _vision_describe(
            style_ref_img,
            "Describe the visual style of this image for use as a style reference in an AI video/image generation project. "
            "Cover: color palette, lighting mood, texture/grain, art direction, era/period feel, and overall aesthetic. "
            "Write 2-3 sentences focused on visual qualities only, no story. "
            "Start with the dominant aesthetic (e.g. 'Dark neo-noir…', 'Warm golden-hour…').",
            "Extracting style…",
            "style_ref",
            max_tokens=250,
        )
    _srd = st.session_state.get("style_ref_desc", "")
    if _srd and st.session_state.get("style_ref_desc_box", "") != _srd:
        st.session_state["style_ref_desc_box"] = _srd
    style_ref_text = st.text_area(
        "style_ref_desc_box",
        placeholder="Auto-filled after upload, or type manually…",
        height=75,
        label_visibility="collapsed",
        key="style_ref_desc_box",
    )
    st.session_state["style_ref_desc"] = style_ref_text

    # ── Location / Environment Reference ──────────────────────────────────
    st.markdown('<p class="lbl" style="margin-top:.75rem">📍 Location / Environment</p>', unsafe_allow_html=True)
    st.markdown('<p style="color:rgba(148,112,255,.4);font-size:.72rem;margin-bottom:.4rem;line-height:1.45">Upload a photo of a place or environment — Claude describes it for use as the world setting.</p>', unsafe_allow_html=True)
    location_img = st.file_uploader(" ", type=["jpg","jpeg","png","webp"],
                                    label_visibility="collapsed", key="location_upload")
    if location_img is not None:
        img_col, name_col = st.columns([1, 3])
        with img_col:
            location_img.seek(0)
            st.image(location_img, use_container_width=True)
        with name_col:
            st.markdown(f'<p style="color:rgba(185,165,255,.7);font-size:.72rem;word-break:break-all;margin:0;padding-top:.25rem">{location_img.name}</p>', unsafe_allow_html=True)
        location_img.seek(0)
        _vision_describe(
            location_img,
            "Describe this location or environment for use as a setting in an AI visual project. "
            "Cover: type of place, key architectural or natural features, time of day if apparent, "
            "atmosphere, scale, and any distinctive details. "
            "Write 2-3 sentences, purely descriptive. Start with the location type (e.g. 'A rooftop terrace…', 'An abandoned warehouse…').",
            "Describing location…",
            "location_ref",
            max_tokens=250,
        )
    _ld = st.session_state.get("location_desc", "")
    if _ld and st.session_state.get("location_desc_box", "") != _ld:
        st.session_state["location_desc_box"] = _ld
    location_text = st.text_area(
        "location_desc_box",
        placeholder="Auto-filled after upload, or type manually…",
        height=75,
        label_visibility="collapsed",
        key="location_desc_box",
    )
    st.session_state["location_desc"] = location_text

    st.divider()
    st.markdown('<p class="lbl">Video Tool</p>', unsafe_allow_html=True)
    video_tool = st.selectbox("vtool", ["grok", "runway", "seedance"], label_visibility="collapsed")

    st.markdown('<p class="lbl">Model</p>', unsafe_allow_html=True)
    from src.llm_client import ANTHROPIC_MODELS, OPENROUTER_FREE_TEXT_MODELS
    if provider == "anthropic":
        model_opts = ANTHROPIC_MODELS
    else:
        model_opts = OPENROUTER_FREE_TEXT_MODELS
    shot_model = st.selectbox("model", model_opts, label_visibility="collapsed")

    # ── saved projects ──────────────────────────────────────────────────────
    st.divider()
    sp_col, new_col = st.columns([3, 2])
    with sp_col:
        st.markdown('<p class="lbl">Saved Projects</p>', unsafe_allow_html=True)
    with new_col:
        if st.button("＋ New", key="new_project_btn", use_container_width=True):
            clear_keys = [
                "results", "audio_name", "project_name", "saved_lyrics", "just_loaded",
                "story_treatment", "story_project_name", "story_chat_history", "story_style_input",
                "story_script", "story_script_type",
                "style_ref_desc", "style_ref_hash", "style_ref_desc_hash",
                "location_desc", "location_ref_hash", "location_ref_desc_hash",
            ]
            for ci in range(4):
                clear_keys += [f"char_{ci}_desc", f"char_{ci}_hash", f"char_{ci}_desc_hash"]
            for key in clear_keys:
                st.session_state.pop(key, None)
            st.rerun()

    projects = list_projects()
    if not projects:
        st.markdown('<p style="color:rgba(148,112,255,.35);font-size:.78rem">No saved projects yet.</p>', unsafe_allow_html=True)
    else:
        for p in projects[:8]:
            saved_dt = ""
            try:
                saved_dt = datetime.datetime.fromisoformat(p["saved_at"]).strftime("%b %d, %H:%M")
            except Exception:
                pass
            is_mv = p["mode"] == "music_video"
            active_mv = is_mv and st.session_state.get("project_name") == p["name"]
            active_ss = (not is_mv) and st.session_state.get("story_project_name") == p["name"]
            active = active_mv or active_ss
            mode_ico = "🎬" if is_mv else "✨"
            label = f"{'▶ ' if active else f'{mode_ico} '}{p['name']}"

            load_col, del_col = st.columns([4, 1])
            with load_col:
                if st.button(label, key=f"load_{p['file']}", use_container_width=True,
                             type="primary" if active else "secondary"):
                    try:
                        d = load_project(p["file"])
                        def _restore_ref_descriptions(d):
                            refs = d.get("ref_descriptions", {})
                            for ci in range(4):
                                v = refs.get("chars", {}).get(f"char_{ci}", "")
                                if v:
                                    st.session_state[f"char_{ci}_desc"] = v
                            if refs.get("style_ref"):
                                st.session_state["style_ref_desc"] = refs["style_ref"]
                            if refs.get("location"):
                                st.session_state["location_desc"] = refs["location"]

                        if d.get("mode", "music_video") == "music_video":
                            audio_data_full = {
                                "duration": d["audio_analysis"]["duration"],
                                "tempo": d["audio_analysis"]["tempo"],
                                "bar_length": d["audio_analysis"]["bar_length"],
                                "boundaries": d["audio_analysis"]["boundaries"],
                                "beats": [], "downbeats": [], "energy_profile": [],
                                "sec_per_beat": 60.0 / d["audio_analysis"]["tempo"],
                            }
                            st.session_state["results"] = (
                                audio_data_full, d["sections"], d["treatment"], d["timeline"])
                            st.session_state["audio_name"] = d.get("audio_name", "project")
                            st.session_state["saved_lyrics"] = d.get("lyrics", "")
                            st.session_state["project_name"] = d["name"]
                            st.session_state["just_loaded"] = d["name"]
                            st.session_state["app_mode"] = "music_video"
                            _restore_ref_descriptions(d)
                        else:
                            st.session_state["story_treatment"] = d.get("treatment", {})
                            st.session_state["story_project_name"] = d["name"]
                            st.session_state["story_chat_history"] = d.get("chat_history", [])
                            st.session_state["story_style_input"] = d.get("style_input", {})
                            st.session_state["story_script"] = d.get("script")
                            st.session_state["story_script_type"] = d.get("style_input", {}).get("script_type", "Voiceover + Dialogue")
                            st.session_state["just_loaded"] = d["name"]
                            st.session_state["app_mode"] = "story_studio"
                            _restore_ref_descriptions(d)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to load: {e}")
            with del_col:
                if st.button("🗑", key=f"del_{p['file']}", use_container_width=True,
                             help="Delete project"):
                    delete_project(p["file"])
                    # Clear session if the deleted project was active
                    if active_mv:
                        for k in ["results", "audio_name", "project_name", "saved_lyrics"]:
                            st.session_state.pop(k, None)
                    if active_ss:
                        for k in ["story_treatment", "story_project_name",
                                  "story_chat_history", "story_style_input"]:
                            st.session_state.pop(k, None)
                    st.rerun()


# ── mode switcher ─────────────────────────────────────────────────────────────
if "app_mode" not in st.session_state:
    st.session_state["app_mode"] = "music_video"

mode_col_l, mode_col_r, _ = st.columns([1, 1, 4], gap="small")
with mode_col_l:
    if st.button("🎬  Music Video", use_container_width=True,
                 type="primary" if st.session_state["app_mode"] == "music_video" else "secondary"):
        st.session_state["app_mode"] = "music_video"
        st.rerun()
with mode_col_r:
    if st.button("✨  Story Studio", use_container_width=True,
                 type="primary" if st.session_state["app_mode"] == "story_studio" else "secondary"):
        st.session_state["app_mode"] = "story_studio"
        st.rerun()

st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

if st.session_state.get("just_loaded"):
    st.markdown(f'<div class="save-banner">✓ Loaded project: <strong>{st.session_state["just_loaded"]}</strong></div>', unsafe_allow_html=True)
    del st.session_state["just_loaded"]


# ══════════════════════════════════════════════════════════════════════════════
# MUSIC VIDEO MODE
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state["app_mode"] == "music_video":

    st.markdown("# 🎬 Music Video Generator")
    st.markdown('<p class="hero-sub">Drop your audio &amp; lyrics — get a full shot list, visual treatment, image prompts and timeline powered by Claude.</p>', unsafe_allow_html=True)

    # ── music video sidebar extras ────────────────────────────────────────────
    # These need to live in the sidebar but depend on mode, so inject via expander trick
    with st.sidebar:
        st.divider()
        st.markdown('<p class="lbl">Visual Style</p>', unsafe_allow_html=True)
        style = st.text_area("style", value="anthemic pop rock, cinematic golden hour, OneRepublic energy",
                             height=78, label_visibility="collapsed")
        st.markdown('<p class="lbl">Mood</p>', unsafe_allow_html=True)
        mood = st.text_input("mood", placeholder="e.g. hopeful, triumphant", label_visibility="collapsed")
        st.markdown('<p class="lbl">Reference Artist</p>', unsafe_allow_html=True)
        reference = st.text_input("ref", placeholder="e.g. OneRepublic Counting Stars", label_visibility="collapsed")
        st.markdown('<p class="lbl">Transcription</p>', unsafe_allow_html=True)
        whisper_mode = st.selectbox("wmode", ["skip", "local", "api"], label_visibility="collapsed")
        whisper_model_size = "medium"
        if whisper_mode == "local":
            st.markdown('<p class="lbl">Whisper Size</p>', unsafe_allow_html=True)
            whisper_model_size = st.selectbox("wsize", ["tiny","base","small","medium","large"],
                                              index=3, label_visibility="collapsed")

    # ── upload / paste row ────────────────────────────────────────────────────
    col_audio, col_lyrics = st.columns(2, gap="large")

    with col_audio:
        st.markdown('<p class="lbl">🎵 Audio File</p>', unsafe_allow_html=True)
        audio_file = st.file_uploader("audio", type=["wav","mp3","m4a","flac","ogg"],
                                      label_visibility="collapsed")

    with col_lyrics:
        if "lyrics_mode" not in st.session_state:
            st.session_state.lyrics_mode = "paste"
        mc1, mc2 = st.columns(2)
        with mc1:
            if st.button("✏️ Paste Lyrics",
                         type="primary" if st.session_state.lyrics_mode == "paste" else "secondary",
                         use_container_width=True):
                st.session_state.lyrics_mode = "paste"
        with mc2:
            if st.button("📂 Upload File",
                         type="primary" if st.session_state.lyrics_mode == "upload" else "secondary",
                         use_container_width=True):
                st.session_state.lyrics_mode = "upload"

        if st.session_state.lyrics_mode == "paste":
            lyrics_text_raw = st.text_area(
                "lyrics_paste",
                value=st.session_state.get("saved_lyrics", ""),
                placeholder="Paste your lyrics here…\n\nUse [Section] markers:\n[Intro]\n[Verse 1]\n[Chorus]",
                height=160, label_visibility="collapsed",
            )
            st.session_state["saved_lyrics"] = lyrics_text_raw
        else:
            lyrics_file = st.file_uploader("lyrics", type=["txt"], label_visibility="collapsed")
            lyrics_text_raw = st.session_state.get("saved_lyrics", "")
            if lyrics_file:
                lyrics_text_raw = lyrics_file.read().decode("utf-8")
                st.session_state["saved_lyrics"] = lyrics_text_raw
                lyrics_file.seek(0)
                with st.expander("Preview"):
                    st.text(lyrics_text_raw[:600] + ("…" if len(lyrics_text_raw) > 600 else ""))

    lyrics_ready = bool(lyrics_text_raw.strip())

    # ── generate + save row ───────────────────────────────────────────────────
    st.markdown("<div style='height:.6rem'></div>", unsafe_allow_html=True)
    can_run = bool(audio_file and lyrics_ready and api_key and style)

    btn_col, save_col = st.columns([3, 1], gap="medium")
    with btn_col:
        run_btn = st.button("✦  Generate Music Video Plan", disabled=not can_run,
                            use_container_width=True, type="primary")
    with save_col:
        has_results = "results" in st.session_state
        save_btn = st.button("💾  Save Project", disabled=not has_results,
                             use_container_width=True, type="secondary")

    if not can_run and not run_btn:
        missing = []
        if not api_key:      missing.append("API key (sidebar)")
        if not audio_file:   missing.append("audio file")
        if not lyrics_ready: missing.append("lyrics")
        if missing:
            st.markdown(
                f'<div style="text-align:center;color:rgba(148,112,255,.45);font-size:.8rem;padding:.5rem 0">'
                f'Still needed: {" · ".join(missing)}</div>', unsafe_allow_html=True)

    # ── save modal ────────────────────────────────────────────────────────────
    if save_btn and has_results:
        st.session_state["show_save_dialog"] = True

    if st.session_state.get("show_save_dialog"):
        with st.form("save_form"):
            st.markdown('<p class="lbl">Project Name</p>', unsafe_allow_html=True)
            default_name = st.session_state.get("audio_name", "My Project").rsplit(".", 1)[0]
            proj_name = st.text_input("proj_name", value=default_name, label_visibility="collapsed")
            sc1, sc2 = st.columns(2)
            with sc1:
                submitted = st.form_submit_button("💾 Save", use_container_width=True, type="primary")
            with sc2:
                cancelled = st.form_submit_button("Cancel", use_container_width=True)
        if submitted and proj_name:
            ad, sec, tr, tl = st.session_state["results"]
            an = st.session_state.get("audio_name", "project")
            fpath = save_project(proj_name, "music_video", {
                "audio_name": an,
                "lyrics": st.session_state.get("saved_lyrics", ""),
                "treatment": tr,
                "timeline": tl,
                "audio_analysis": {
                    "duration": ad["duration"], "tempo": ad["tempo"],
                    "bar_length": ad["bar_length"], "boundaries": ad["boundaries"],
                },
                "sections": sec,
                "ref_descriptions": {
                    "chars": {f"char_{ci}": st.session_state.get(f"char_{ci}_desc", "") for ci in range(4)},
                    "style_ref": st.session_state.get("style_ref_desc", ""),
                    "location": st.session_state.get("location_desc", ""),
                },
            })
            st.session_state["project_name"] = proj_name
            del st.session_state["show_save_dialog"]
            st.markdown(f'<div class="save-banner">✓ Saved as <strong>{proj_name}</strong> → {fpath.name}</div>', unsafe_allow_html=True)
            st.rerun()
        if cancelled:
            del st.session_state["show_save_dialog"]
            st.rerun()

    # ── pipeline runner ───────────────────────────────────────────────────────
    def run_pipeline(audio_path, lyrics_text, style, mood, reference,
                     video_tool, shot_model, whisper_mode, whisper_model_size):
        from src.audio_analyzer import analyze_audio
        from src.transcriber import transcribe
        from src.lyric_aligner import align_lyrics
        from src.shot_generator import generate_shots
        from src.timeline_builder import build_timeline

        STEPS = [
            "Analyzing audio — BPM, beats, sections",
            "Transcribing audio",
            "Aligning lyrics to sections",
            "Generating visual treatment + prompts via Claude",
            "Building timeline",
        ]
        ph = st.empty()

        def render(done, msg=None):
            rows = ""
            for i, label in enumerate(STEPS):
                if i < done:
                    pill = '<span class="pill pill-done">✓ done</span>'
                elif i == done:
                    pill = f'<span class="pill pill-run">⟳ {msg or "running"}</span>'
                else:
                    pill = '<span class="pill pill-wait">waiting</span>'
                rows += f'<div class="step">{pill}{label}</div>'
            ph.markdown(f'<div class="pipeline">{rows}</div>', unsafe_allow_html=True)

        render(0)
        audio_data = analyze_audio(audio_path)
        render(1)
        word_timestamps = None
        if whisper_mode != "skip":
            try:
                word_timestamps = transcribe(audio_path, method=whisper_mode, model=whisper_model_size)
            except Exception as e:
                st.warning(f"Transcription failed ({e}) — using proportional alignment.")
        render(2)
        sections = align_lyrics(lyrics_text, audio_data, word_timestamps)
        render(3, "Claude API")
        treatment = generate_shots(sections, audio_data, {
            "style": style, "mood": mood, "reference": reference,
            "video_tool": video_tool, "character": character,
            "style_ref": st.session_state.get("style_ref_desc", ""),
            "location": st.session_state.get("location_desc", ""),
            "provider": provider,
            "api_key": api_key,
        }, model=shot_model)
        render(4)
        timeline = build_timeline(sections, audio_data, treatment)
        rows = "".join(f'<div class="step"><span class="pill pill-done">✓ done</span>{label}</div>' for label in STEPS)
        ph.markdown(f'<div class="pipeline">{rows}</div>', unsafe_allow_html=True)
        return audio_data, sections, treatment, timeline

    # ── run pipeline ──────────────────────────────────────────────────────────
    if run_btn:
        suffix = Path(audio_file.name).suffix
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        tmp.write(audio_file.read())
        tmp.flush()
        try:
            audio_data, sections, treatment, timeline = run_pipeline(
                tmp.name, lyrics_text_raw,
                style, mood, reference, video_tool, shot_model, whisper_mode, whisper_model_size,
            )
            st.session_state["results"] = (audio_data, sections, treatment, timeline)
            st.session_state["audio_name"] = audio_file.name
            st.session_state.pop("project_name", None)
        except Exception as e:
            st.error(f"Pipeline failed: {e}")
            st.exception(e)
        finally:
            try: os.unlink(tmp.name)
            except Exception: pass

    # ── results ───────────────────────────────────────────────────────────────
    if "results" in st.session_state:
        audio_data, sections, treatment, timeline = st.session_state["results"]
        audio_name = st.session_state.get("audio_name", "song")

        if st.session_state.get("project_name"):
            st.markdown(
                f'<div style="color:rgba(167,139,250,.5);font-size:.78rem;margin-bottom:.5rem">📂 {st.session_state["project_name"]}</div>',
                unsafe_allow_html=True)

        st.markdown("<div style='height:.75rem'></div>", unsafe_allow_html=True)
        c1,c2,c3,c4 = st.columns(4, gap="medium")
        c1.metric("Duration", fmt_time(audio_data["duration"]))
        c2.metric("BPM",      f"{audio_data['tempo']:.1f}")
        c3.metric("Sections", len(sections))
        c4.metric("Shots",    len(treatment.get("shots", [])))

        st.markdown("<div style='height:1.25rem'></div>", unsafe_allow_html=True)

        t1, t2, t3, t4, t5, t6 = st.tabs([
            "🎨  Treatment", "🎞  Shot List", "🎬  Video Prompts", "🖼  Image Prompts", "⏱  Timeline", "💾  Export"
        ])

        # ── Treatment ─────────────────────────────────────────────────────────
        with t1:
            vd = treatment.get("visual_direction", {})
            arc = treatment.get("story_arc", {})

            st.markdown(f'<div class="concept">{treatment.get("concept","")}</div>', unsafe_allow_html=True)

            if arc:
                st.markdown('<p class="lbl" style="margin-bottom:.6rem">📖 Story Arc</p>', unsafe_allow_html=True)
                arc_items = [
                    ("Opening State",      arc.get("opening","")),
                    ("Inciting Moment",    arc.get("inciting_moment","")),
                    ("Escalation",         arc.get("escalation","")),
                    ("Chorus Identity",    arc.get("chorus_identity","")),
                    ("Bridge Turn",        arc.get("bridge_turn","")),
                    ("Climax",             arc.get("climax","")),
                    ("Resolution",         arc.get("resolution","")),
                ]
                arc_html = ""
                for label, val in arc_items:
                    if val:
                        arc_html += (
                            f'<div class="arc-row">'
                            f'<span class="arc-label">{label}</span>'
                            f'<span class="arc-val">{val}</span>'
                            f'</div>'
                        )
                st.markdown(f'<div class="arc-card">{arc_html}</div>', unsafe_allow_html=True)

            st.markdown("<div style='height:.75rem'></div>", unsafe_allow_html=True)
            cl, cr = st.columns(2, gap="large")
            with cl:
                st.markdown('<p class="lbl">Palette</p>', unsafe_allow_html=True)
                st.markdown(f'<p style="color:rgba(196,181,255,.78);font-size:.9rem;line-height:1.6">{vd.get("palette","")}</p>', unsafe_allow_html=True)
                st.markdown('<p class="lbl">Recurring Motifs</p>', unsafe_allow_html=True)
                st.markdown(f'<div class="tags">{"".join(f"<span class=tag>{m}</span>" for m in vd.get("recurring_motifs",[]))}</div>', unsafe_allow_html=True)
            with cr:
                st.markdown('<p class="lbl">Style Modifiers</p>', unsafe_allow_html=True)
                st.markdown(f'<div class="tags">{"".join(f"<span class=tag>{m}</span>" for m in vd.get("style_modifiers",[]))}</div>', unsafe_allow_html=True)
            st.markdown('<p class="lbl" style="margin-top:1rem">Continuity Notes</p>', unsafe_allow_html=True)
            st.markdown(f'<p style="color:rgba(196,181,255,.72);font-size:.9rem;line-height:1.65">{treatment.get("continuity_notes","")}</p>', unsafe_allow_html=True)
            st.markdown('<p class="lbl" style="margin-top:1.2rem">Section Map</p>', unsafe_allow_html=True)
            rows_html = "".join(
                f'<div class="srow"><span class="sname">{s["name"]}</span>'
                f'<span class="stime">{fmt_time(s["start"])} → {fmt_time(s["end"])}</span>'
                f'<span class="sdur">{s["end"]-s["start"]:.1f}s</span></div>'
                for s in sections
            )
            st.markdown(rows_html, unsafe_allow_html=True)

        # ── Shot List ─────────────────────────────────────────────────────────
        with t2:
            shots = treatment.get("shots", [])
            hc, fc = st.columns([3,1])
            with hc:
                st.markdown(f'<p style="color:rgba(148,112,255,.55);font-size:.82rem">{len(shots)} shots — paste any prompt into Grok / Runway / Seedance</p>', unsafe_allow_html=True)
            with fc:
                fsec = st.selectbox("filter", ["All"] + sorted({s["section"] for s in shots}),
                                    key="shot_filter", label_visibility="collapsed")

            for idx, shot in enumerate(shots):
                if fsec != "All" and shot["section"] != fsec:
                    continue
                cue_html = f'<div class="scue">"{shot.get("lyric_cue","")}"</div>' if shot.get("lyric_cue") else ""
                beat_html = f'<div class="story-beat">📖 {shot["story_beat"]}</div>' if shot.get("story_beat") else ""
                img_html = ""
                if shot.get("image_prompt"):
                    img_html = f'<div class="box-lbl" style="margin-top:.6rem">🖼 Image Prompt</div><div class="img-box">{shot["image_prompt"]}</div>'
                st.markdown(f"""<div class="shot">
  <div class="shot-hdr"><span class="sid">Shot {shot['id']}</span><span class="stag">{shot['section']}</span></div>
  <div class="sdesc">{shot.get('description','')}</div>
  {beat_html}
  {cue_html}
  <div class="box-lbl">🎬 Video Prompt</div>
  <div class="prompt-box">{shot['prompt']}</div>
  {img_html}
</div>""", unsafe_allow_html=True)

                if st.button(f"🎲 Reroll Shot {shot['id']}", key=f"reroll_{idx}_{shot['id']}",
                             use_container_width=False):
                    with st.spinner(f"Rerolling shot {shot['id']}…"):
                        try:
                            from src.shot_generator import reroll_shot
                            new_shot = reroll_shot(shot, treatment, {"style": style, "mood": mood,
                                                                      "reference": reference, "character": character,
                                                                      "provider": provider, "api_key": api_key}, model=shot_model)
                            ad, sec, tr, tl = st.session_state["results"]
                            tr["shots"][idx] = new_shot
                            st.session_state["results"] = (ad, sec, tr, tl)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Reroll failed: {e}")

        # ── Video Prompts ─────────────────────────────────────────────────────
        with t3:
            vid_shots = [s for s in treatment.get("shots", []) if s.get("prompt")]
            st.markdown(
                f'<p style="color:rgba(148,112,255,.55);font-size:.82rem;margin-bottom:.75rem">'
                f'{len(vid_shots)} video prompts — paste the full block into Grok / Runway / Seedance</p>',
                unsafe_allow_html=True,
            )
            all_video_text = "\n\n".join(s["prompt"] for s in vid_shots)
            st.text_area("all_video_prompts", value=all_video_text, height=220,
                         label_visibility="collapsed", key="vid_prompts_copy_box")
            st.markdown("<div style='height:.75rem'></div>", unsafe_allow_html=True)
            st.markdown('<p class="lbl">Individual Video Prompts</p>', unsafe_allow_html=True)
            for shot in vid_shots:
                beat_line = f'<div class="img-prompt-num" style="margin-top:.15rem;color:rgba(180,150,255,.45);font-weight:500;font-size:.7rem;letter-spacing:0;text-transform:none">📖 {shot["story_beat"]}</div>' if shot.get("story_beat") else ""
                st.markdown(
                    f'<div class="img-prompt-block">'
                    f'<div class="img-prompt-num">Shot {shot["id"]} · {shot["section"]}</div>'
                    f'{beat_line}'
                    f'<div class="img-prompt-text">{shot["prompt"]}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

        # ── Image Prompts ─────────────────────────────────────────────────────
        with t4:
            shots = treatment.get("shots", [])
            img_shots = [s for s in shots if s.get("image_prompt")]
            st.markdown(
                f'<p style="color:rgba(148,112,255,.55);font-size:.82rem;margin-bottom:.75rem">'
                f'{len(img_shots)} image prompts — paste the full block into your ChatGPT extension</p>',
                unsafe_allow_html=True,
            )
            all_prompts_text = "\n\n".join(s["image_prompt"] for s in img_shots)
            st.text_area("all_image_prompts", value=all_prompts_text, height=220,
                         label_visibility="collapsed", key="img_prompts_copy_box")
            st.markdown("<div style='height:.75rem'></div>", unsafe_allow_html=True)
            st.markdown('<p class="lbl">Individual Prompts</p>', unsafe_allow_html=True)
            for i, shot in enumerate(img_shots):
                st.markdown(
                    f'<div class="img-prompt-block">'
                    f'<div class="img-prompt-num">Shot {shot["id"]} · {shot["section"]}</div>'
                    f'<div class="img-prompt-text">{shot["image_prompt"]}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

        # ── Timeline ──────────────────────────────────────────────────────────
        with t5:
            by_sec = {}
            for entry in timeline:
                by_sec.setdefault(entry["section"], []).append(entry)
            tl_html = ""
            for section in sections:
                entries = by_sec.get(section["name"], [])
                if not entries: continue
                tl_html += (f'<div class="tlhdr">{section["name"]} '
                            f'<span style="font-weight:400;opacity:.55">{fmt_time(section["start"])} → {fmt_time(section["end"])}</span></div>')
                for e in entries:
                    cue_part = f'<span class="tlcue"> · {e["lyric_cue"]}</span>' if e.get("lyric_cue") else ""
                    tl_html += (f'<div class="tlrow">'
                                f'<span class="tltime">[{fmt_time(e["start"])} – {fmt_time(e["end"])}]</span>'
                                f'<span class="tlshot">SHOT {e["shot_id"]}</span>'
                                f'<span class="tldesc">{e["description"]}</span>{cue_part}</div>')
            st.markdown(tl_html, unsafe_allow_html=True)

        # ── Export ────────────────────────────────────────────────────────────
        with t6:
            def build_treatment_md():
                vd = treatment.get("visual_direction", {})
                lines = ["# Music Video Treatment","",
                         f"**Duration:** {fmt_time(audio_data['duration'])} | **BPM:** {audio_data['tempo']:.1f} | **Bar:** {audio_data['bar_length']:.2f}s",
                         "","## Concept","",treatment.get("concept",""),"","## Visual Direction","",
                         f"**Palette:** {vd.get('palette','')}","","**Recurring motifs:**"]
                for m in vd.get("recurring_motifs",[]): lines.append(f"- {m}")
                lines += ["","**Style modifiers:**"]
                for m in vd.get("style_modifiers",[]): lines.append(f"- {m}")
                lines += ["","## Continuity Notes","",treatment.get("continuity_notes",""),"","## Section Map",""]
                for s in sections: lines.append(f"- **{s['name']}** — {fmt_time(s['start'])} to {fmt_time(s['end'])} ({s['end']-s['start']:.1f}s)")
                return "\n".join(lines)+"\n"

            def build_prompts_md():
                lines = ["# Shot Prompts","",f"Total: {len(treatment['shots'])} unique shots",""]
                cur = None
                for shot in treatment["shots"]:
                    if shot["section"] != cur:
                        cur = shot["section"]; lines += ["",f"## {cur}",""]
                    lines.append(f"### SHOT {shot['id']}")
                    if shot.get("lyric_cue"): lines.append(f'*Cue: "{shot["lyric_cue"]}"*')
                    lines += ["","**Video prompt:**","```",shot["prompt"],"```"]
                    if shot.get("image_prompt"):
                        lines += ["","**Image prompt:**","```",shot["image_prompt"],"```"]
                    lines.append("")
                return "\n".join(lines)+"\n"

            def build_video_prompts_txt():
                return "\n\n".join(s["prompt"] for s in treatment["shots"] if s.get("prompt")) + "\n"

            def build_image_prompts_txt():
                return "\n\n".join(s["image_prompt"] for s in treatment["shots"] if s.get("image_prompt")) + "\n"

            def build_timeline_md():
                lines = ["# Music Video Timeline","",
                         f"**Duration:** {fmt_time(audio_data['duration'])} | **BPM:** {audio_data['tempo']:.1f} | **Bar length:** {audio_data['bar_length']:.2f}s",""]
                bs = {}
                for entry in timeline: bs.setdefault(entry["section"],[]).append(entry)
                for section in sections:
                    entries = bs.get(section["name"],[])
                    if not entries: continue
                    lines += ["",f"## {section['name']} — {fmt_time(section['start'])} to {fmt_time(section['end'])}","","```"]
                    for e in entries:
                        cue = f"  ({e['lyric_cue']})" if e.get("lyric_cue") else ""
                        lines.append(f"[{fmt_time(e['start'])} - {fmt_time(e['end'])}]  SHOT {e['shot_id']}  {e['description']}{cue}")
                    lines.append("```")
                return "\n".join(lines)+"\n"

            project_json = json.dumps({
                "name": st.session_state.get("project_name",""),
                "treatment": treatment, "timeline": timeline,
                "audio_analysis": {"duration":audio_data["duration"],"tempo":audio_data["tempo"],
                                   "bar_length":audio_data["bar_length"],"boundaries":audio_data["boundaries"]},
                "sections": sections,
            }, indent=2)

            stem = Path(audio_name).stem
            st.markdown('<p class="lbl">Download Files</p>', unsafe_allow_html=True)
            lyrics_export = st.session_state.get("saved_lyrics", "")

            d1,d2,d3,d4,d5,d6,d7 = st.columns(7, gap="small")
            for col,ico,title,sub,data,fname,mime in [
                (d1,"📋","treatment.md","Story arc & direction",build_treatment_md(),f"{stem}-treatment.md","text/markdown"),
                (d2,"🎞","prompts.md","All prompts combined",build_prompts_md(),f"{stem}-prompts.md","text/markdown"),
                (d3,"🎬","video-prompts.txt","Paste-ready video prompts",build_video_prompts_txt(),f"{stem}-video-prompts.txt","text/plain"),
                (d4,"🖼","image-prompts.txt","Paste-ready image prompts",build_image_prompts_txt(),f"{stem}-image-prompts.txt","text/plain"),
                (d5,"🎵","lyrics.txt","Song lyrics",lyrics_export,f"{stem}-lyrics.txt","text/plain"),
                (d6,"⏱","timeline.md","Bar-snapped layout",build_timeline_md(),f"{stem}-timeline.md","text/markdown"),
                (d7,"🗂","project.json","Full raw data",project_json,f"{stem}-project.json","application/json"),
            ]:
                with col:
                    st.markdown(f'<div class="dlcard"><div class="dlico">{ico}</div><div class="dltitle">{title}</div><div class="dlsub">{sub}</div></div>', unsafe_allow_html=True)
                    st.download_button("Download", data, fname, mime, use_container_width=True, key=f"dl_{fname}")

            st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)
            with st.expander("Raw project.json"):
                st.json(json.loads(project_json))


# ══════════════════════════════════════════════════════════════════════════════
# STORY STUDIO MODE
# ══════════════════════════════════════════════════════════════════════════════
else:
    from src.story_generator import (PROJECT_TYPES, SCRIPT_TYPES, generate_scenes,
                                      iterate_scenes, reroll_scene, generate_script,
                                      reroll_script_line)

    st.markdown("# ✨ Story Studio")
    st.markdown('<p class="hero-sub">Write any story — anime, short film, ad, rap battle — and iterate scene by scene with Claude.</p>', unsafe_allow_html=True)

    # ── Story Studio sidebar extras ───────────────────────────────────────────
    with st.sidebar:
        st.divider()
        st.markdown('<p class="lbl">Project Type</p>', unsafe_allow_html=True)
        project_type = st.selectbox("proj_type", PROJECT_TYPES, label_visibility="collapsed")
        st.markdown('<p class="lbl">Tone</p>', unsafe_allow_html=True)
        tone = st.text_input("tone_ss", placeholder="e.g. dark, comedic, heartwarming", label_visibility="collapsed")
        st.markdown('<p class="lbl">Reference / Inspiration</p>', unsafe_allow_html=True)
        ss_reference = st.text_input("ref_ss", placeholder="e.g. Studio Ghibli, Breaking Bad", label_visibility="collapsed")

        st.divider()
        st.markdown('<p class="lbl">🎬 Video Duration</p>', unsafe_allow_html=True)

        # Clip length depends on video tool
        if video_tool == "seedance":
            clip_opts = [5, 10, 15]
            clip_default = 10
        else:  # grok, runway, etc.
            clip_opts = [6, 10]
            clip_default = 10
        st.markdown('<p style="color:rgba(148,112,255,.4);font-size:.72rem;margin-bottom:.3rem">Clip length per scene</p>', unsafe_allow_html=True)
        clip_duration = st.selectbox(
            "clip_dur",
            clip_opts,
            index=clip_opts.index(clip_default),
            format_func=lambda x: f"{x}s per clip",
            label_visibility="collapsed",
        )

        st.markdown('<p style="color:rgba(148,112,255,.4);font-size:.72rem;margin-top:.5rem;margin-bottom:.3rem">Total video length</p>', unsafe_allow_html=True)
        dur_col1, dur_col2 = st.columns(2)
        with dur_col1:
            total_min = st.number_input("tot_min", min_value=0, max_value=59, value=1,
                                        label_visibility="collapsed", step=1)
        with dur_col2:
            total_sec_inp = st.number_input("tot_sec", min_value=0, max_value=59, value=30,
                                            label_visibility="collapsed", step=5)
        total_duration_sec = total_min * 60 + total_sec_inp
        n_scenes = max(1, round(total_duration_sec / clip_duration))
        st.markdown(
            f'<p style="color:rgba(167,139,250,.55);font-size:.75rem;margin-top:.3rem">'
            f'→ {n_scenes} scenes × {clip_duration}s = {total_duration_sec}s total</p>',
            unsafe_allow_html=True,
        )

    treatment = st.session_state.get("story_treatment")

    # ── input form ────────────────────────────────────────────────────────────
    if not treatment:
        st.markdown('<p class="lbl">📝 Your Story / Idea</p>', unsafe_allow_html=True)
        brief = st.text_area(
            "brief",
            placeholder=(
                "Describe your story, concept, or idea in as much or as little detail as you want.\n\n"
                "Example: A teenage girl discovers she has the power to rewind time. "
                "She uses it selfishly at first, but when she accidentally erases someone she loves, "
                "she must decide what to sacrifice to bring them back."
            ),
            height=200,
            label_visibility="collapsed",
        )

        gen_col, _ = st.columns([2, 3])
        with gen_col:
            can_gen = bool(brief.strip() and api_key)
            gen_btn = st.button("✦  Generate Scenes", disabled=not can_gen,
                                use_container_width=True, type="primary")

        if not can_gen:
            missing = []
            if not api_key: missing.append("API key (sidebar)")
            if not brief.strip(): missing.append("story idea")
            if missing:
                st.markdown(
                    f'<div style="color:rgba(148,112,255,.45);font-size:.8rem;padding:.5rem 0">'
                    f'Still needed: {" · ".join(missing)}</div>', unsafe_allow_html=True)

        if gen_btn:
            style_input = {
                "project_type": project_type,
                "tone": tone,
                "reference": ss_reference,
                "video_tool": video_tool,
                "character": character,
                "n_scenes": n_scenes,
                "clip_duration": clip_duration,
                "style_ref": st.session_state.get("style_ref_desc", ""),
                "location": st.session_state.get("location_desc", ""),
                "provider": provider,
                "api_key": api_key,
            }
            with st.spinner("Claude is building your story arc and scenes…"):
                try:
                    result = generate_scenes(brief, style_input, model=shot_model)
                    st.session_state["story_treatment"] = result
                    st.session_state["story_chat_history"] = []
                    st.session_state["story_style_input"] = style_input
                    st.session_state.pop("story_project_name", None)
                    st.rerun()
                except Exception as e:
                    st.error(f"Generation failed: {e}")
                    st.exception(e)

    # ── results ───────────────────────────────────────────────────────────────
    if treatment:
        style_input = st.session_state.get("story_style_input", {
            "project_type": project_type, "tone": tone,
            "reference": ss_reference, "video_tool": video_tool,
            "character": character, "n_scenes": n_scenes,
            "clip_duration": clip_duration,
            "style_ref": st.session_state.get("style_ref_desc", ""),
            "location": st.session_state.get("location_desc", ""),
            "provider": provider,
            "api_key": api_key,
        })
        # Always keep provider/api_key fresh (user may switch mid-session)
        style_input["provider"] = provider
        style_input["api_key"] = api_key

        if st.session_state.get("story_project_name"):
            st.markdown(
                f'<div style="color:rgba(167,139,250,.5);font-size:.78rem;margin-bottom:.5rem">📂 {st.session_state["story_project_name"]}</div>',
                unsafe_allow_html=True)

        # metrics row
        scenes = treatment.get("scenes", [])
        total_dur = sum(s.get("duration_sec", 8) for s in scenes)
        c1, c2, c3 = st.columns(3, gap="medium")
        c1.metric("Scenes", len(scenes))
        c2.metric("Est. Duration", f"{total_dur}s")
        c3.metric("Type", treatment.get("project_type", style_input.get("project_type", "—")))

        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

        # save / reset row
        sv_col, reset_col = st.columns([3, 1], gap="medium")
        with sv_col:
            pass
        with reset_col:
            if st.button("🔄 Start Over", use_container_width=True, type="secondary"):
                for k in ["story_treatment", "story_project_name", "story_chat_history", "story_style_input"]:
                    st.session_state.pop(k, None)
                st.rerun()

        # save project button in main area
        save_story_col, _ = st.columns([2, 4])
        with save_story_col:
            save_story_btn = st.button("💾  Save Project", use_container_width=True, type="secondary", key="save_story")

        if save_story_btn:
            st.session_state["show_story_save_dialog"] = True

        if st.session_state.get("show_story_save_dialog"):
            with st.form("story_save_form"):
                st.markdown('<p class="lbl">Project Name</p>', unsafe_allow_html=True)
                default_ss_name = treatment.get("project_type", "Story") + " Project"
                ss_proj_name = st.text_input("ss_proj_name", value=default_ss_name, label_visibility="collapsed")
                sc1, sc2 = st.columns(2)
                with sc1:
                    ss_submitted = st.form_submit_button("💾 Save", use_container_width=True, type="primary")
                with sc2:
                    ss_cancelled = st.form_submit_button("Cancel", use_container_width=True)
            if ss_submitted and ss_proj_name:
                fpath = save_project(ss_proj_name, "story_studio", {
                    "treatment": treatment,
                    "script": st.session_state.get("story_script"),
                    "chat_history": st.session_state.get("story_chat_history", []),
                    "style_input": style_input,
                    "ref_descriptions": {
                        "chars": {f"char_{ci}": st.session_state.get(f"char_{ci}_desc", "") for ci in range(4)},
                        "style_ref": st.session_state.get("style_ref_desc", ""),
                        "location": st.session_state.get("location_desc", ""),
                    },
                })
                st.session_state["story_project_name"] = ss_proj_name
                del st.session_state["show_story_save_dialog"]
                st.markdown(f'<div class="save-banner">✓ Saved as <strong>{ss_proj_name}</strong> → {fpath.name}</div>', unsafe_allow_html=True)
                st.rerun()
            if ss_cancelled:
                del st.session_state["show_story_save_dialog"]
                st.rerun()

        st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

        tab_treatment, tab_scenes, tab_script, tab_video, tab_images, tab_export = st.tabs([
            "🎨  Treatment", "🎬  Scenes", "📝  Script", "🎥  Video Prompts", "🖼  Image Prompts", "💾  Export"
        ])

        # ── Treatment tab ─────────────────────────────────────────────────────
        with tab_treatment:
            vd = treatment.get("visual_direction", {})
            arc = treatment.get("story_arc", {})

            st.markdown(f'<div class="concept">{treatment.get("concept","")}</div>', unsafe_allow_html=True)

            if arc:
                st.markdown('<p class="lbl" style="margin-bottom:.6rem">📖 Story Arc</p>', unsafe_allow_html=True)
                arc_items = [
                    ("Opening",         arc.get("opening","")),
                    ("Inciting Moment", arc.get("inciting_moment","")),
                    ("Rising Action",   arc.get("rising_action","")),
                    ("Midpoint",        arc.get("midpoint","")),
                    ("Climax",          arc.get("climax","")),
                    ("Resolution",      arc.get("resolution","")),
                ]
                arc_html = ""
                for label, val in arc_items:
                    if val:
                        arc_html += (
                            f'<div class="arc-row">'
                            f'<span class="arc-label">{label}</span>'
                            f'<span class="arc-val">{val}</span>'
                            f'</div>'
                        )
                st.markdown(f'<div class="arc-card">{arc_html}</div>', unsafe_allow_html=True)

            st.markdown("<div style='height:.75rem'></div>", unsafe_allow_html=True)
            cl, cr = st.columns(2, gap="large")
            with cl:
                st.markdown('<p class="lbl">Palette</p>', unsafe_allow_html=True)
                st.markdown(f'<p style="color:rgba(196,181,255,.78);font-size:.9rem;line-height:1.6">{vd.get("palette","")}</p>', unsafe_allow_html=True)
                st.markdown('<p class="lbl">Recurring Motifs</p>', unsafe_allow_html=True)
                st.markdown(f'<div class="tags">{"".join(f"<span class=tag>{m}</span>" for m in vd.get("recurring_motifs",[]))}</div>', unsafe_allow_html=True)
            with cr:
                st.markdown('<p class="lbl">Style Modifiers</p>', unsafe_allow_html=True)
                st.markdown(f'<div class="tags">{"".join(f"<span class=tag>{m}</span>" for m in vd.get("style_modifiers",[]))}</div>', unsafe_allow_html=True)
            st.markdown('<p class="lbl" style="margin-top:1rem">Continuity Notes</p>', unsafe_allow_html=True)
            st.markdown(f'<p style="color:rgba(196,181,255,.72);font-size:.9rem;line-height:1.65">{treatment.get("continuity_notes","")}</p>', unsafe_allow_html=True)

        # ── Scenes tab ────────────────────────────────────────────────────────
        with tab_scenes:
            scenes = treatment.get("scenes", [])

            # Filter by act
            acts = list(dict.fromkeys(s.get("act", "—") for s in scenes))
            fc_col, _ = st.columns([2, 4])
            with fc_col:
                filter_act = st.selectbox("filter_act", ["All Acts"] + acts,
                                          label_visibility="collapsed", key="scene_act_filter")

            for idx, scene in enumerate(scenes):
                if filter_act != "All Acts" and scene.get("act") != filter_act:
                    continue

                img_html = ""
                if scene.get("image_prompt"):
                    img_html = f'<div class="box-lbl" style="margin-top:.6rem">🖼 Image Prompt</div><div class="img-box">{scene["image_prompt"]}</div>'

                st.markdown(f"""<div class="scene-card">
  <div class="scene-hdr">
    <span class="scene-id">Scene {scene['id']}</span>
    <span class="scene-act">{scene.get('act','')}</span>
  </div>
  <div class="scene-desc">{scene.get('description','')}</div>
  <div class="scene-beat">📖 {scene.get('story_beat','')}</div>
  <div class="box-lbl">🎬 Video Prompt</div>
  <div class="prompt-box">{scene.get('prompt','')}</div>
  {img_html}
</div>""", unsafe_allow_html=True)

                if st.button(f"🎲 Reroll Scene {scene['id']}", key=f"ss_reroll_{idx}_{scene['id']}"):
                    with st.spinner(f"Rerolling scene {scene['id']}…"):
                        try:
                            new_scene = reroll_scene(scene, treatment, style_input, model=shot_model)
                            tr = st.session_state["story_treatment"]
                            tr["scenes"][idx] = new_scene
                            st.session_state["story_treatment"] = tr
                            st.rerun()
                        except Exception as e:
                            st.error(f"Reroll failed: {e}")

            # ── Chat iteration panel ──────────────────────────────────────────
            st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)
            st.markdown('<p class="lbl">💬 Iterate with Claude</p>', unsafe_allow_html=True)
            st.markdown('<p style="color:rgba(148,112,255,.45);font-size:.78rem;margin-bottom:.6rem">Tell Claude what to change — specific scenes, global tone shifts, new characters, anything.</p>', unsafe_allow_html=True)

            chat_history = st.session_state.get("story_chat_history", [])
            if chat_history:
                chat_html = ""
                for msg in chat_history[-6:]:
                    if msg["role"] == "user":
                        chat_html += f'<div class="chat-msg-user">You: {msg["content"]}</div>'
                    else:
                        chat_html += f'<div class="chat-msg-ai">Claude: {msg["content"]}</div>'
                st.markdown(f'<div class="chat-box">{chat_html}</div>', unsafe_allow_html=True)

            with st.form("iterate_form", clear_on_submit=True):
                instruction = st.text_input(
                    "instruction",
                    placeholder='e.g. "Make scene 3 darker and add rain" or "Give the protagonist a red jacket in every scene"',
                    label_visibility="collapsed",
                )
                iter_btn = st.form_submit_button("Send →", type="primary", use_container_width=False)

            if iter_btn and instruction.strip():
                with st.spinner("Claude is updating your scenes…"):
                    try:
                        updated = iterate_scenes(
                            st.session_state["story_treatment"],
                            instruction,
                            style_input,
                            model=shot_model,
                        )
                        st.session_state["story_treatment"] = updated
                        history = st.session_state.get("story_chat_history", [])
                        history.append({"role": "user", "content": instruction})
                        history.append({"role": "assistant", "content": f"Updated {len(updated.get('scenes',[]))} scenes."})
                        st.session_state["story_chat_history"] = history
                        st.rerun()
                    except Exception as e:
                        st.error(f"Iteration failed: {e}")

        # ── Script tab ────────────────────────────────────────────────────────
        with tab_script:
            script = st.session_state.get("story_script")
            cd = style_input.get("clip_duration", 10)

            # Header controls
            sc_type_col, sc_gen_col = st.columns([2, 2], gap="medium")
            with sc_type_col:
                st.markdown('<p class="lbl">Script Type</p>', unsafe_allow_html=True)
                script_type_sel = st.selectbox(
                    "script_type",
                    SCRIPT_TYPES,
                    index=0,
                    label_visibility="collapsed",
                    key="script_type_select",
                )
            with sc_gen_col:
                st.markdown('<p class="lbl" style="opacity:0">.</p>', unsafe_allow_html=True)
                if st.button("✦  Generate Script", type="primary", use_container_width=True, key="gen_script_btn"):
                    with st.spinner("Claude is writing your script…"):
                        try:
                            result_script = generate_script(
                                treatment, style_input,
                                script_type=script_type_sel,
                                model=shot_model,
                            )
                            st.session_state["story_script"] = result_script
                            st.session_state["story_script_type"] = script_type_sel
                            st.rerun()
                        except Exception as e:
                            st.error(f"Script generation failed: {e}")

            if not script:
                st.markdown(
                    '<p style="color:rgba(148,112,255,.4);font-size:.85rem;margin-top:1rem">'
                    'Choose a script type above and click Generate Script. Claude will write '
                    'timestamped voiceover and/or dialogue for every scene.</p>',
                    unsafe_allow_html=True,
                )
            else:
                scenes_by_id = {s["id"]: s for s in treatment.get("scenes", [])}
                lines = script.get("lines", [])
                total_s = script.get("total_duration_sec", 0)
                sc_type = st.session_state.get("story_script_type", script_type_sel)

                st.markdown(
                    f'<p style="color:rgba(148,112,255,.55);font-size:.82rem;margin-bottom:.75rem">'
                    f'{len(lines)} scenes · {total_s}s total · {sc_type}</p>',
                    unsafe_allow_html=True,
                )

                want_vo = sc_type in ("Voiceover + Dialogue", "Voiceover only")
                want_dlg = sc_type in ("Voiceover + Dialogue", "Dialogue only")

                for li, line in enumerate(lines):
                    sid = line.get("scene_id", "?")
                    scene_ctx = scenes_by_id.get(sid, {})
                    ts = f'{line.get("timestamp_start","?")} – {line.get("timestamp_end","?")}'

                    st.markdown(
                        f'<div class="scene-card">'
                        f'<div class="scene-hdr">'
                        f'<span class="scene-id">Scene {sid}</span>'
                        f'<span class="scene-act">{scene_ctx.get("act","")}</span>'
                        f'<span style="margin-left:auto;font-family:monospace;font-size:.75rem;color:rgba(148,112,255,.5)">{ts}</span>'
                        f'</div>'
                        f'<div class="scene-beat">📖 {scene_ctx.get("story_beat","")}</div>',
                        unsafe_allow_html=True,
                    )

                    if want_vo:
                        vo_val = st.text_area(
                            f"vo_{li}",
                            value=line.get("voiceover") or "",
                            placeholder="(no voiceover for this scene)",
                            height=70,
                            label_visibility="collapsed",
                            key=f"vo_edit_{li}",
                        )
                        # write edits back into session state immediately
                        lines[li]["voiceover"] = vo_val if vo_val.strip() else None

                    if want_dlg:
                        dlg = line.get("dialogue", [])
                        if dlg:
                            for di, d_line in enumerate(dlg):
                                dcol1, dcol2 = st.columns([1, 3], gap="small")
                                with dcol1:
                                    char_edit = st.text_input(
                                        f"char_{li}_{di}",
                                        value=d_line.get("character", ""),
                                        label_visibility="collapsed",
                                        key=f"dlg_char_{li}_{di}",
                                        placeholder="Character",
                                    )
                                with dcol2:
                                    line_edit = st.text_input(
                                        f"line_{li}_{di}",
                                        value=d_line.get("line", ""),
                                        label_visibility="collapsed",
                                        key=f"dlg_line_{li}_{di}",
                                        placeholder="Dialogue line…",
                                    )
                                lines[li]["dialogue"][di] = {"character": char_edit, "line": line_edit}
                        else:
                            st.markdown(
                                '<p style="color:rgba(148,112,255,.3);font-size:.78rem;font-style:italic">No dialogue for this scene.</p>',
                                unsafe_allow_html=True,
                            )

                    st.markdown('</div>', unsafe_allow_html=True)

                    if st.button(f"🎲 Reroll Scene {sid} Script", key=f"reroll_script_{li}_{sid}"):
                        with st.spinner(f"Rewriting scene {sid} script…"):
                            try:
                                new_line = reroll_script_line(
                                    sid, scene_ctx, line, sc_type, style_input, model=shot_model
                                )
                                st.session_state["story_script"]["lines"][li] = new_line
                                st.rerun()
                            except Exception as e:
                                st.error(f"Reroll failed: {e}")

                # Persist edits back
                if script:
                    st.session_state["story_script"]["lines"] = lines

        # ── Video Prompts tab ─────────────────────────────────────────────────
        with tab_video:
            scenes = treatment.get("scenes", [])
            vid_scenes = [s for s in scenes if s.get("prompt")]
            st.markdown(
                f'<p style="color:rgba(148,112,255,.55);font-size:.82rem;margin-bottom:.75rem">'
                f'{len(vid_scenes)} video prompts — paste into Grok / Runway / Seedance</p>',
                unsafe_allow_html=True,
            )
            all_vid = "\n\n".join(s["prompt"] for s in vid_scenes)
            st.text_area("ss_all_video", value=all_vid, height=220,
                         label_visibility="collapsed", key="ss_vid_copy_box")
            st.markdown("<div style='height:.75rem'></div>", unsafe_allow_html=True)
            st.markdown('<p class="lbl">Individual Video Prompts</p>', unsafe_allow_html=True)
            for scene in vid_scenes:
                beat_line = f'<div class="img-prompt-num" style="margin-top:.15rem;color:rgba(180,150,255,.45);font-weight:500;font-size:.7rem;letter-spacing:0;text-transform:none">📖 {scene["story_beat"]}</div>' if scene.get("story_beat") else ""
                st.markdown(
                    f'<div class="img-prompt-block">'
                    f'<div class="img-prompt-num">Scene {scene["id"]} · {scene.get("act","")}</div>'
                    f'{beat_line}'
                    f'<div class="img-prompt-text">{scene["prompt"]}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

        # ── Image Prompts tab ─────────────────────────────────────────────────
        with tab_images:
            scenes = treatment.get("scenes", [])
            img_scenes = [s for s in scenes if s.get("image_prompt")]
            st.markdown(
                f'<p style="color:rgba(148,112,255,.55);font-size:.82rem;margin-bottom:.75rem">'
                f'{len(img_scenes)} image prompts — paste into ChatGPT / Midjourney / DALL-E</p>',
                unsafe_allow_html=True,
            )
            all_img = "\n\n".join(s["image_prompt"] for s in img_scenes)
            st.text_area("ss_all_images", value=all_img, height=220,
                         label_visibility="collapsed", key="ss_img_copy_box")
            st.markdown("<div style='height:.75rem'></div>", unsafe_allow_html=True)
            st.markdown('<p class="lbl">Individual Image Prompts</p>', unsafe_allow_html=True)
            for scene in img_scenes:
                st.markdown(
                    f'<div class="img-prompt-block">'
                    f'<div class="img-prompt-num">Scene {scene["id"]} · {scene.get("act","")}</div>'
                    f'<div class="img-prompt-text">{scene["image_prompt"]}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

        # ── Export tab ────────────────────────────────────────────────────────
        with tab_export:
            scenes = treatment.get("scenes", [])
            proj_slug = st.session_state.get("story_project_name", treatment.get("project_type", "story")).lower().replace(" ", "-")

            def ss_build_treatment_md():
                vd = treatment.get("visual_direction", {})
                arc = treatment.get("story_arc", {})
                lines = [f"# {treatment.get('project_type','Story')} Treatment","",
                         "## Concept","", treatment.get("concept",""),""]
                if arc:
                    lines += ["## Story Arc",""]
                    for k, v in arc.items():
                        if v: lines.append(f"**{k.replace('_',' ').title()}:** {v}")
                    lines.append("")
                lines += ["## Visual Direction","",
                          f"**Palette:** {vd.get('palette','')}","","**Recurring motifs:**"]
                for m in vd.get("recurring_motifs",[]): lines.append(f"- {m}")
                lines += ["","**Style modifiers:**"]
                for m in vd.get("style_modifiers",[]): lines.append(f"- {m}")
                lines += ["","## Continuity Notes","", treatment.get("continuity_notes","")]
                return "\n".join(lines)+"\n"

            def ss_build_prompts_md():
                lines = [f"# Scene Prompts","",f"Total: {len(scenes)} scenes",""]
                cur_act = None
                for scene in scenes:
                    if scene.get("act") != cur_act:
                        cur_act = scene.get("act","")
                        lines += ["",f"## {cur_act}",""]
                    lines.append(f"### Scene {scene['id']} — {scene.get('description','')}")
                    lines.append(f"*{scene.get('story_beat','')}*")
                    lines += ["","**Video prompt:**","```",scene.get("prompt",""),"```"]
                    if scene.get("image_prompt"):
                        lines += ["","**Image prompt:**","```",scene["image_prompt"],"```"]
                    lines.append("")
                return "\n".join(lines)+"\n"

            def ss_build_video_prompts_txt():
                return "\n\n".join(s["prompt"] for s in scenes if s.get("prompt")) + "\n"

            def ss_build_image_prompts_txt():
                return "\n\n".join(s["image_prompt"] for s in scenes if s.get("image_prompt")) + "\n"

            def ss_build_script_txt():
                sc = st.session_state.get("story_script")
                if not sc:
                    return "(No script generated yet — go to the Script tab and click Generate Script)"
                sc_type = st.session_state.get("story_script_type", "Script")
                scenes_by_id = {s["id"]: s for s in scenes}
                lines_out = [
                    f"# {treatment.get('project_type','Story')} — {sc_type}",
                    f"Total duration: {sc.get('total_duration_sec',0)}s",
                    "",
                ]
                for line in sc.get("lines", []):
                    sid = line.get("scene_id","?")
                    sc_ctx = scenes_by_id.get(sid, {})
                    lines_out.append(f"[{line.get('timestamp_start','?')} – {line.get('timestamp_end','?')}]  SCENE {sid}  {sc_ctx.get('description','')}")
                    vo = line.get("voiceover")
                    if vo:
                        lines_out.append(f"  VO: {vo}")
                    for d in line.get("dialogue", []):
                        lines_out.append(f"  {d.get('character','?').upper()}: {d.get('line','')}")
                    lines_out.append("")
                return "\n".join(lines_out)

            ss_project_json = json.dumps({
                "name": st.session_state.get("story_project_name",""),
                "mode": "story_studio",
                "treatment": treatment,
                "script": st.session_state.get("story_script"),
                "style_input": style_input,
                "chat_history": st.session_state.get("story_chat_history", []),
            }, indent=2)

            st.markdown('<p class="lbl">Download Files</p>', unsafe_allow_html=True)

            e1, e2, e3, e4, e5, e6 = st.columns(6, gap="small")
            for col, ico, title, sub, data, fname, mime in [
                (e1,"📋","treatment.md","Story arc & direction",ss_build_treatment_md(),f"{proj_slug}-treatment.md","text/markdown"),
                (e2,"🎞","prompts.md","All scene prompts",ss_build_prompts_md(),f"{proj_slug}-prompts.md","text/markdown"),
                (e3,"📝","script.txt","Timestamped script",ss_build_script_txt(),f"{proj_slug}-script.txt","text/plain"),
                (e4,"🎬","video-prompts.txt","Paste-ready video prompts",ss_build_video_prompts_txt(),f"{proj_slug}-video-prompts.txt","text/plain"),
                (e5,"🖼","image-prompts.txt","Paste-ready image prompts",ss_build_image_prompts_txt(),f"{proj_slug}-image-prompts.txt","text/plain"),
                (e6,"🗂","project.json","Full raw data",ss_project_json,f"{proj_slug}-project.json","application/json"),
            ]:
                with col:
                    st.markdown(f'<div class="dlcard"><div class="dlico">{ico}</div><div class="dltitle">{title}</div><div class="dlsub">{sub}</div></div>', unsafe_allow_html=True)
                    st.download_button("Download", data, fname, mime, use_container_width=True, key=f"ss_dl_{fname}")

            st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)
            with st.expander("Raw project.json"):
                st.json(json.loads(ss_project_json))
