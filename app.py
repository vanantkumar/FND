import streamlit as st
import requests
import sqlite3
import hashlib
import google.generativeai as genai
from datetime import datetime
import urllib.parse
from xml.etree import ElementTree as ET
import re
 
# ══════════════════════════════════════════════════════════
# PAGE CONFIG  — must be the very first Streamlit call
# ══════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Veridect · Fake News Detector",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="collapsed",
)
 
# ══════════════════════════════════════════════════════════
# GLOBAL CSS
# ══════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:wght@300;400;500&family=DM+Mono:wght@400;500&display=swap');
 
/* ── Hard reset ── */
*, *::before, *::after { box-sizing: border-box; }
 
/* ── Hide Streamlit chrome ── */
#MainMenu, header[data-testid="stHeader"], footer,
section[data-testid="stSidebar"] { display: none !important; }
 
/* ── App background ── */
[data-testid="stAppViewContainer"] {
    background: #0e0e10 !important;
    padding: 0 !important;
}
[data-testid="block-container"] {
    padding: 0 !important;
    max-width: 100% !important;
}
[data-testid="stVerticalBlock"]  { gap: 0 !important; }
[data-testid="stHorizontalBlock"]{ gap: 0 !important; }
 
/* ── Column borders for login ── */
.login-left-col  > div:first-child { padding: 0 !important; }
.login-right-col > div:first-child { padding: 0 !important; }
 
/* ── All text inputs dark ── */
div[data-testid="stTextInput"]  input,
div[data-testid="stTextArea"]   textarea {
    background   : #1c1c20 !important;
    color        : #f0ece4 !important;
    border       : 1px solid rgba(240,236,228,.14) !important;
    border-radius: 8px !important;
    font-family  : 'DM Sans', sans-serif !important;
    font-size    : 14px !important;
    padding      : 10px 14px !important;
}
div[data-testid="stTextInput"]  input:focus,
div[data-testid="stTextArea"]   textarea:focus {
    border-color : rgba(240,236,228,.42) !important;
    box-shadow   : none !important;
}
div[data-testid="stTextInput"]  label,
div[data-testid="stTextArea"]   label { display: none !important; }
 
/* ── All buttons base ── */
div.stButton > button {
    font-family  : 'DM Sans', sans-serif !important;
    font-weight  : 500 !important;
    border-radius: 8px !important;
    transition   : all .18s ease !important;
    cursor       : pointer !important;
}
 
/* ── Login RIGHT column wrapper ── */
.vd-right-wrap {
    background  : #0e0e10;
    min-height  : 100vh;
    padding     : 64px 52px;
    display     : flex;
    flex-direction: column;
    justify-content: center;
    border-left : 1px solid rgba(240,236,228,.07);
}
 
/* ── Form titles inside right panel ── */
.vd-form-title {
    font-family : 'Bebas Neue', cursive;
    font-size   : 30px;
    letter-spacing: 2.5px;
    color       : #f0ece4;
    margin-bottom: 4px;
}
.vd-form-sub {
    font-size   : 12px;
    color       : rgba(240,236,228,.35);
    margin-bottom: 28px;
    font-family : 'DM Sans', sans-serif;
}
.vd-field-label {
    display     : block;
    font-size   : 10px;
    text-transform: uppercase;
    letter-spacing: 1.3px;
    color       : rgba(240,236,228,.38);
    margin-bottom: 5px;
    font-weight : 500;
    font-family : 'DM Sans', sans-serif;
}
.vd-divider {
    height      : 1px;
    background  : rgba(240,236,228,.08);
    margin      : 20px 0;
    position    : relative;
}
.vd-divider-label {
    position    : absolute;
    top         : -9px;
    left        : 50%;
    transform   : translateX(-50%);
    background  : #0e0e10;
    padding     : 0 12px;
    font-size   : 11px;
    color       : rgba(240,236,228,.22);
    font-family : 'DM Sans', sans-serif;
}
.vd-switch {
    text-align  : center;
    margin-top  : 14px;
    font-size   : 12px;
    color       : rgba(240,236,228,.3);
    font-family : 'DM Sans', sans-serif;
}
 
/* ── Primary button (white) ── */
.btn-primary > div > button {
    background   : #f0ece4 !important;
    color        : #0e0e10 !important;
    border       : none !important;
    width        : 100% !important;
    padding      : 12px 20px !important;
    font-size    : 13.5px !important;
}
.btn-primary > div > button:hover { background: #fff !important; }
 
/* ── Ghost button ── */
.btn-ghost > div > button {
    background   : transparent !important;
    color        : rgba(240,236,228,.45) !important;
    border       : 1px solid rgba(240,236,228,.16) !important;
    width        : 100% !important;
    padding      : 11px 20px !important;
    font-size    : 13px !important;
}
.btn-ghost > div > button:hover {
    color        : #f0ece4 !important;
    border-color : rgba(240,236,228,.38) !important;
    background   : rgba(240,236,228,.04) !important;
}
 
/* ══════════════════════
   APP SHELL (post-login)
   ══════════════════════ */
 
/* Top bar */
.vd-topbar {
    position    : sticky;
    top         : 0;
    z-index     : 100;
    background  : #0a0a0c;
    border-bottom: 1px solid rgba(240,236,228,.07);
    display     : flex;
    align-items : center;
    justify-content: space-between;
    padding     : 0 28px;
    height      : 52px;
    width       : 100%;
}
.vd-brand {
    font-family : 'Bebas Neue', cursive;
    font-size   : 22px;
    letter-spacing: 3.5px;
    color       : #f0ece4;
    display     : flex;
    align-items : center;
    gap         : 10px;
}
.vd-brand-dot {
    width       : 8px; height: 8px;
    border-radius: 50%;
    background  : #c8291a;
    display     : inline-block;
    animation   : pulseDot 2s ease-in-out infinite;
}
@keyframes pulseDot {
    0%,100% { opacity:1; transform:scale(1); }
    50%     { opacity:.35; transform:scale(.6); }
}
.vd-topbar-right {
    display     : flex;
    align-items : center;
    gap         : 14px;
}
.vd-user-pill {
    background  : rgba(240,236,228,.07);
    border      : 1px solid rgba(240,236,228,.12);
    border-radius: 20px;
    padding     : 4px 14px 4px 8px;
    font-size   : 12px;
    color       : rgba(240,236,228,.7);
    display     : flex;
    align-items : center;
    gap         : 7px;
    font-family : 'DM Sans', sans-serif;
}
.vd-avatar {
    width       : 24px; height: 24px;
    border-radius: 50%;
    background  : #c8291a;
    display     : flex; align-items: center; justify-content: center;
    font-size   : 10px; font-weight: 500; color: #fff;
    font-family : 'DM Sans', sans-serif;
}
 
/* Sidebar column */
.vd-sidebar-wrap {
    background  : #0a0a0c;
    border-right: 1px solid rgba(240,236,228,.06);
    min-height  : calc(100vh - 52px);
    padding     : 24px 0 0 0;
    display     : flex;
    flex-direction: column;
}
.vd-nav-section-label {
    font-size   : 10px;
    letter-spacing: 1.8px;
    text-transform: uppercase;
    color       : rgba(240,236,228,.22);
    padding     : 6px 22px 4px;
    font-weight : 500;
    font-family : 'DM Sans', sans-serif;
}
 
/* Nav buttons */
div.stButton.nav-btn > button {
    background   : transparent !important;
    color        : rgba(240,236,228,.45) !important;
    border       : none !important;
    border-left  : 2px solid transparent !important;
    border-radius: 0 !important;
    text-align   : left !important;
    width        : 100% !important;
    padding      : 10px 22px !important;
    font-size    : 13px !important;
    justify-content: flex-start !important;
}
div.stButton.nav-btn > button:hover {
    background   : rgba(240,236,228,.04) !important;
    color        : rgba(240,236,228,.8) !important;
}
div.stButton.nav-active > button {
    background   : rgba(240,236,228,.06) !important;
    color        : #f0ece4 !important;
    border       : none !important;
    border-left  : 2px solid #c8291a !important;
    border-radius: 0 !important;
    text-align   : left !important;
    width        : 100% !important;
    padding      : 10px 22px !important;
    font-size    : 13px !important;
    justify-content: flex-start !important;
}
 
.vd-sidebar-footer {
    margin-top  : auto;
    padding     : 16px 22px;
    border-top  : 1px solid rgba(240,236,228,.05);
    font-size   : 10px;
    color       : rgba(240,236,228,.16);
    line-height : 1.7;
    font-family : 'DM Sans', sans-serif;
}
 
/* Logout button */
div.stButton.logout-btn > button {
    background   : transparent !important;
    color        : rgba(240,236,228,.35) !important;
    border       : 1px solid rgba(240,236,228,.12) !important;
    width        : calc(100% - 44px) !important;
    margin       : 0 22px 22px !important;
    font-size    : 12px !important;
    padding      : 8px !important;
}
div.stButton.logout-btn > button:hover {
    color        : #f0ece4 !important;
    border-color : rgba(240,236,228,.3) !important;
}
 
/* Main panel */
.vd-main-wrap {
    background  : #111114;
    min-height  : calc(100vh - 52px);
    padding     : 36px 40px 60px;
    font-family : 'DM Sans', sans-serif;
    color       : #f0ece4;
}
.vd-panel-title {
    font-family : 'Bebas Neue', cursive;
    font-size   : 34px;
    letter-spacing: 2px;
    color       : #f0ece4;
    margin-bottom: 4px;
}
.vd-panel-sub {
    font-size   : 12px;
    color       : rgba(240,236,228,.35);
    margin-bottom: 28px;
    line-height : 1.6;
}
 
/* Analyze buttons */
div.stButton.run-btn > button {
    background   : #f0ece4 !important;
    color        : #0e0e10 !important;
    border       : none !important;
    padding      : 11px 24px !important;
    font-size    : 13px !important;
    width        : 100% !important;
}
div.stButton.run-btn > button:hover { background: #fff !important; transform: translateY(-1px); }
 
div.stButton.sec-btn > button {
    background   : transparent !important;
    color        : rgba(240,236,228,.5) !important;
    border       : 1px solid rgba(240,236,228,.16) !important;
    padding      : 11px 20px !important;
    font-size    : 13px !important;
    width        : 100% !important;
}
div.stButton.sec-btn > button:hover {
    color        : #f0ece4 !important;
    border-color : rgba(240,236,228,.35) !important;
}
 
/* char hint */
.vd-char-hint {
    font-size   : 11px;
    color       : rgba(240,236,228,.25);
    text-align  : right;
    margin-top  : -10px;
    margin-bottom: 14px;
    font-family : 'DM Mono', monospace;
}
 
/* Result card */
.vd-result {
    border-radius: 12px;
    overflow    : hidden;
    border      : 1px solid rgba(240,236,228,.1);
    margin-top  : 12px;
    animation   : slideUp .35s ease;
}
@keyframes slideUp {
    from { opacity:0; transform:translateY(10px); }
    to   { opacity:1; transform:translateY(0); }
}
.vd-result-hdr {
    display     : flex;
    align-items : center;
    justify-content: space-between;
    padding     : 18px 22px;
}
.vd-result-hdr.fake        { background: rgba(200,41,26,.16); border-bottom:1px solid rgba(200,41,26,.22); }
.vd-result-hdr.real        { background: rgba(26,110,60,.16);  border-bottom:1px solid rgba(26,110,60,.22); }
.vd-result-hdr.unverified  { background: rgba(181,107,0,.13);  border-bottom:1px solid rgba(181,107,0,.2); }
 
.vd-verdict {
    font-family : 'Bebas Neue', cursive;
    font-size   : 22px;
    letter-spacing: 2.5px;
}
.vd-verdict.fake        { color:#e85d4a; }
.vd-verdict.real        { color:#4caf7d; }
.vd-verdict.unverified  { color:#e5a835; }
 
.vd-conf-pill {
    font-family : 'DM Mono', monospace;
    font-size   : 13px;
    padding     : 4px 13px;
    border-radius: 20px;
    font-weight : 500;
}
.fake .vd-conf-pill        { background:rgba(200,41,26,.18); color:#e85d4a; }
.real .vd-conf-pill        { background:rgba(26,110,60,.18);  color:#4caf7d; }
.unverified .vd-conf-pill  { background:rgba(181,107,0,.18);  color:#e5a835; }
 
.vd-result-body { background:#1a1a1e; padding:20px 22px; }
 
.vd-bar-label {
    font-size   : 10px;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    color       : rgba(240,236,228,.28);
    margin-bottom: 7px;
    font-weight : 500;
}
.vd-bar-track {
    height      : 5px;
    background  : rgba(240,236,228,.09);
    border-radius: 10px;
    overflow    : hidden;
    margin-bottom: 18px;
}
.vd-bar-fill { height:100%; border-radius:10px; }
.fake .vd-bar-fill        { background:#c8291a; }
.real .vd-bar-fill        { background:#1a6e3c; }
.unverified .vd-bar-fill  { background:#b56b00; }
 
.vd-explanation {
    font-size   : 13.5px;
    color       : rgba(240,236,228,.68);
    line-height : 1.78;
    border-top  : 1px solid rgba(240,236,228,.07);
    padding-top : 16px;
}
.vd-headlines-box {
    margin-top  : 18px;
    background  : #111114;
    border-radius: 8px;
    padding     : 14px 16px;
    border      : 1px solid rgba(240,236,228,.06);
}
.vd-hl-label {
    font-size   : 10px;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    color       : rgba(240,236,228,.27);
    margin-bottom: 10px;
    font-weight : 500;
}
.vd-hl-item {
    font-size   : 12px;
    color       : rgba(240,236,228,.5);
    padding     : 5px 0;
    border-bottom: 1px solid rgba(240,236,228,.05);
    display     : flex; gap: 8px; align-items: baseline;
    line-height : 1.45;
}
.vd-hl-item:last-child { border-bottom:none; }
.vd-hl-item::before { content:"—"; color:rgba(240,236,228,.18); font-size:11px; flex-shrink:0; }
 
/* Scanning */
.vd-scanning {
    display     : flex;
    flex-direction: column;
    align-items : center;
    gap         : 14px;
    padding     : 48px 0;
}
.vd-scan-bar { width:220px; height:3px; background:rgba(240,236,228,.09); border-radius:10px; overflow:hidden; }
.vd-scan-fill { height:100%; width:28%; background:#f0ece4; border-radius:10px; animation:scanAnim 1.1s ease-in-out infinite; }
@keyframes scanAnim { 0%{transform:translateX(-100%)} 100%{transform:translateX(420%)} }
.vd-scan-text { font-size:12px; color:rgba(240,236,228,.32); font-family:'DM Mono',monospace; }
 
/* Dashboard stats */
.vd-stats-grid {
    display     : grid;
    grid-template-columns: repeat(3,1fr);
    gap         : 14px;
    margin-bottom: 30px;
}
.vd-stat-card {
    background  : #1a1a1e;
    border      : 1px solid rgba(240,236,228,.07);
    border-radius: 10px;
    padding     : 20px 22px;
    position    : relative;
    overflow    : hidden;
}
.vd-stat-card::before {
    content     : "";
    position    : absolute; left:0; top:0; bottom:0;
    width       : 3px;
}
.vd-stat-card.s-fake::before { background:#c8291a; }
.vd-stat-card.s-real::before { background:#1a6e3c; }
.vd-stat-card.s-unv::before  { background:#b56b00; }
.vd-stat-label {
    font-size   : 10px;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    color       : rgba(240,236,228,.28);
    margin-bottom: 8px;
    font-weight : 500;
}
.vd-stat-num {
    font-family : 'Bebas Neue', cursive;
    font-size   : 44px;
    letter-spacing: 1px;
    line-height : 1;
}
.vd-stat-card.s-fake .vd-stat-num { color:#e85d4a; }
.vd-stat-card.s-real .vd-stat-num { color:#4caf7d; }
.vd-stat-card.s-unv  .vd-stat-num { color:#e5a835; }
 
/* Table */
.vd-table {
    width       : 100%;
    border-collapse: collapse;
    font-size   : 12.5px;
    font-family : 'DM Sans', sans-serif;
}
.vd-table th {
    text-align  : left;
    font-size   : 10px;
    text-transform: uppercase;
    letter-spacing: 1px;
    color       : rgba(240,236,228,.27);
    padding     : 0 14px 10px;
    font-weight : 500;
}
.vd-table td {
    padding     : 11px 14px;
    border-top  : 1px solid rgba(240,236,228,.05);
    color       : rgba(240,236,228,.7);
    vertical-align: middle;
}
.vd-table tr:hover td { background: rgba(240,236,228,.025); }
.mono { font-family:'DM Mono',monospace; font-size:11px; }
 
/* Pills */
.pill { display:inline-block; padding:2px 9px; border-radius:10px; font-size:10px; font-weight:500; text-transform:uppercase; letter-spacing:.5px; }
.pill-fake { background:rgba(200,41,26,.18); color:#e85d4a; }
.pill-real { background:rgba(26,110,60,.18);  color:#4caf7d; }
.pill-unv  { background:rgba(181,107,0,.18);  color:#e5a835; }
 
/* History items */
.vd-history-item {
    background  : #1a1a1e;
    border      : 1px solid rgba(240,236,228,.07);
    border-radius: 10px;
    padding     : 16px 20px;
    margin-bottom: 12px;
    display     : grid;
    grid-template-columns: 1fr auto;
    gap         : 14px;
    align-items : start;
    transition  : border-color .15s;
}
.vd-history-item:hover { border-color:rgba(240,236,228,.22); }
.vd-history-news { font-size:13px; color:rgba(240,236,228,.78); line-height:1.5; margin-bottom:5px; }
.vd-history-ts   { font-size:11px; color:rgba(240,236,228,.27); font-family:'DM Mono',monospace; }
.vd-history-conf { font-size:11px; color:rgba(240,236,228,.27); font-family:'DM Mono',monospace; margin-top:4px; }
 
/* Section divider */
.vd-section-label {
    font-size   : 10px;
    text-transform: uppercase;
    letter-spacing: 1.4px;
    color       : rgba(240,236,228,.28);
    margin      : 24px 0 14px;
    font-weight : 500;
    padding-bottom: 8px;
    border-bottom: 1px solid rgba(240,236,228,.06);
}
</style>
""", unsafe_allow_html=True)
 
# ══════════════════════════════════════════════════════════
# DATABASE
# ══════════════════════════════════════════════════════════
conn = sqlite3.connect("veridect.db", check_same_thread=False)
cur  = conn.cursor()
 
cur.execute("""CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY, password TEXT, role TEXT)""")
cur.execute("""CREATE TABLE IF NOT EXISTS history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username  TEXT, news TEXT, result TEXT,
    verdict   TEXT, confidence INTEGER, created_at TEXT)""")
 
if not cur.execute("SELECT 1 FROM users WHERE username='admin'").fetchone():
    cur.execute("INSERT INTO users VALUES (?,?,?)",
                ("admin", hashlib.sha256("admin123".encode()).hexdigest(), "admin"))
    conn.commit()
 
# ══════════════════════════════════════════════════════════
# SESSION STATE DEFAULTS
# ══════════════════════════════════════════════════════════
for k, v in {
    "user": None, "page": "Analyze",
    "auth_mode": "login", "result_html": "",
}.items():
    if k not in st.session_state:
        st.session_state[k] = v
 
# ══════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ══════════════════════════════════════════════════════════
def hp(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()
 
def initials(name: str) -> str:
    return name[:2].upper()
 
def fetch_headlines(query: str) -> list[str]:
    try:
        url  = (f"https://news.google.com/rss/search?"
                f"q={urllib.parse.quote(query)}&hl=en-IN&gl=IN&ceid=IN:en")
        root = ET.fromstring(requests.get(url, timeout=5).content)
        return [i.find("title").text for i in root.findall(".//item")[:5]]
    except Exception:
        return []
 
def analyze_news(text: str) -> dict:
    lines = fetch_headlines(text)
    hl    = "\n".join(lines) if lines else "No matching headlines found."
    prompt = f"""You are a professional fact-checker.
Today: {datetime.now().strftime('%B %d, %Y')}
 
News to analyze:
\"\"\"{text}\"\"\"
 
Related headlines from Google News:
{hl}
 
Respond STRICTLY in this format:
VERDICT: Real|Fake|Unverified
CONFIDENCE: <1-99>
EXPLANATION: <2-3 sentences>"""
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        mdl = genai.GenerativeModel(
            next(m.name for m in genai.list_models()
                 if "generateContent" in m.supported_generation_methods))
        raw = mdl.generate_content(prompt).text.strip()
        vm  = re.search(r"VERDICT:\s*(Real|Fake|Unverified)", raw, re.I)
        cm  = re.search(r"CONFIDENCE:\s*(\d+)", raw)
        em  = re.search(r"EXPLANATION:\s*(.+)", raw, re.S)
        verdict    = vm.group(1).capitalize() if vm else "Unverified"
        confidence = max(1, min(99, int(cm.group(1)))) if cm else 50
        explanation= em.group(1).strip() if em else raw
    except Exception as e:
        verdict, confidence, explanation = "Unverified", 50, f"Analysis failed: {e}"
    return {"verdict": verdict, "confidence": confidence,
            "explanation": explanation, "headlines": lines}
 
def result_card(res: dict) -> str:
    v   = res["verdict"].lower()
    c   = res["confidence"]
    lbl = {"fake":"✕ FAKE NEWS","real":"✓ VERIFIED REAL","unverified":"? UNVERIFIED"}.get(v,"? UNVERIFIED")
    hl  = "".join(f'<div class="vd-hl-item">{h}</div>' for h in res["headlines"]) \
          or '<div class="vd-hl-item">No matching headlines found.</div>'
    return f"""
<div class="vd-result">
  <div class="vd-result-hdr {v}">
    <div class="vd-verdict {v}">{lbl}</div>
    <span class="vd-conf-pill">{c}%</span>
  </div>
  <div class="vd-result-body {v}">
    <div class="vd-bar-label">Confidence Score</div>
    <div class="vd-bar-track"><div class="vd-bar-fill" style="width:{c}%;"></div></div>
    <div class="vd-explanation">{res['explanation']}</div>
    <div class="vd-headlines-box">
      <div class="vd-hl-label">Cross-referenced headlines</div>
      {hl}
    </div>
  </div>
</div>"""
 
def db_stats():
    rows = cur.execute("SELECT verdict FROM history").fetchall()
    f = sum(1 for r in rows if r[0] and r[0].lower()=="fake")
    r = sum(1 for r in rows if r[0] and r[0].lower()=="real")
    u = sum(1 for r in rows if r[0] and r[0].lower()=="unverified")
    return f, r, u
 
# ══════════════════════════════════════════════════════════
#  LOGIN / SIGNUP SCREEN
# ══════════════════════════════════════════════════════════
if not st.session_state["user"]:
 
    # ── Left decorative panel (pure HTML, full viewport height) ──
    # ── Right form panel (Streamlit widgets inside styled column) ──
    left_col, right_col = st.columns([1, 1], gap="small")
 
    # LEFT — completely pure HTML, no Streamlit widgets
    with left_col:
        st.markdown("""
        <div style="
            background:#0a0a0c;
            min-height:100vh;
            padding:56px 52px;
            display:flex;
            flex-direction:column;
            justify-content:space-between;
            border-right:1px solid rgba(240,236,228,.07);
            font-family:'DM Sans',sans-serif;
        ">
          <!-- logo -->
          <div style="font-family:'Bebas Neue',cursive;font-size:22px;letter-spacing:4px;color:#f0ece4;display:flex;align-items:center;gap:10px;">
            <span style="width:8px;height:8px;border-radius:50%;background:#c8291a;display:inline-block;animation:pulseDot 2s ease-in-out infinite;"></span>
            VERIDECT
          </div>
 
          <!-- hero -->
          <div>
            <div style="font-family:'Bebas Neue',cursive;font-size:68px;line-height:1.0;color:#f0ece4;margin-bottom:20px;letter-spacing:1px;">
              TRUTH<br>STARTS<br>HERE.
            </div>
            <p style="font-size:13px;color:rgba(240,236,228,.38);line-height:1.8;max-width:290px;margin-bottom:28px;">
              AI-powered misinformation detection with real-time
              Google News cross-referencing and confidence scoring.
            </p>
            <div style="display:flex;flex-direction:column;gap:9px;">
              <div style="display:flex;align-items:center;gap:9px;font-size:11px;color:rgba(240,236,228,.3);">
                <span style="width:5px;height:5px;border-radius:50%;background:#c8291a;flex-shrink:0;"></span>
                Detects fake news with Gemini AI reasoning
              </div>
              <div style="display:flex;align-items:center;gap:9px;font-size:11px;color:rgba(240,236,228,.3);">
                <span style="width:5px;height:5px;border-radius:50%;background:#1a6e3c;flex-shrink:0;"></span>
                Cross-references 5 real-time Google News headlines
              </div>
              <div style="display:flex;align-items:center;gap:9px;font-size:11px;color:rgba(240,236,228,.3);">
                <span style="width:5px;height:5px;border-radius:50%;background:#b56b00;flex-shrink:0;"></span>
                Full history &amp; analytics dashboard included
              </div>
            </div>
          </div>
 
          <!-- footer -->
          <p style="font-size:10px;color:rgba(240,236,228,.14);">
            © 2025 Veridect · Powered by Google Gemini
          </p>
        </div>
        """, unsafe_allow_html=True)
 
    # RIGHT — Streamlit widgets, styled to look part of the dark layout
    with right_col:
        # Outer wrapper gives the dark background and centering
        st.markdown("""
        <div style="
            background:#0e0e10;
            min-height:100vh;
            padding:64px 52px 48px;
            display:flex;
            flex-direction:column;
            justify-content:center;
            font-family:'DM Sans',sans-serif;
        ">
        """, unsafe_allow_html=True)
 
        if st.session_state["auth_mode"] == "login":
            st.markdown('<div class="vd-form-title">SIGN IN</div>', unsafe_allow_html=True)
            st.markdown('<p class="vd-form-sub">Enter your credentials to continue</p>', unsafe_allow_html=True)
 
            st.markdown('<label class="vd-field-label">Username</label>', unsafe_allow_html=True)
            username = st.text_input("__u", key="login_u", label_visibility="collapsed",
                                     placeholder="e.g. admin")
 
            st.markdown('<label class="vd-field-label">Password</label>', unsafe_allow_html=True)
            password = st.text_input("__p", key="login_p", label_visibility="collapsed",
                                     type="password", placeholder="••••••••")
 
            st.markdown('<div class="btn-primary">', unsafe_allow_html=True)
            if st.button("Sign In  →", key="login_btn", use_container_width=True):
                row = cur.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
                if row and hp(password) == row[1]:
                    st.session_state["user"] = username
                    st.rerun()
                else:
                    st.error("Invalid username or password.")
            st.markdown('</div>', unsafe_allow_html=True)
 
            st.markdown('<div class="vd-divider"><span class="vd-divider-label">or</span></div>',
                        unsafe_allow_html=True)
 
            st.markdown('<div class="btn-ghost">', unsafe_allow_html=True)
            if st.button("Create a new account", key="goto_signup", use_container_width=True):
                st.session_state["auth_mode"] = "signup"
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
 
        else:  # signup
            st.markdown('<div class="vd-form-title">CREATE ACCOUNT</div>', unsafe_allow_html=True)
            st.markdown('<p class="vd-form-sub">Join Veridect to start detecting misinformation</p>',
                        unsafe_allow_html=True)
 
            st.markdown('<label class="vd-field-label">Username</label>', unsafe_allow_html=True)
            new_u = st.text_input("__nu", key="signup_u", label_visibility="collapsed",
                                  placeholder="Choose a username")
 
            st.markdown('<label class="vd-field-label">Password</label>', unsafe_allow_html=True)
            new_p = st.text_input("__np", key="signup_p", label_visibility="collapsed",
                                  type="password", placeholder="Create a strong password")
 
            st.markdown('<div class="btn-primary">', unsafe_allow_html=True)
            if st.button("Create Account  →", key="signup_btn", use_container_width=True):
                if new_u and new_p:
                    if cur.execute("SELECT 1 FROM users WHERE username=?", (new_u,)).fetchone():
                        st.error("Username already exists.")
                    else:
                        cur.execute("INSERT INTO users VALUES (?,?,?)",
                                    (new_u, hp(new_p), "user"))
                        conn.commit()
                        st.session_state["user"] = new_u
                        st.rerun()
                else:
                    st.warning("Please fill in both fields.")
            st.markdown('</div>', unsafe_allow_html=True)
 
            st.markdown('<div class="vd-divider"><span class="vd-divider-label">or</span></div>',
                        unsafe_allow_html=True)
 
            st.markdown('<div class="btn-ghost">', unsafe_allow_html=True)
            if st.button("← Back to Sign In", key="back_login", use_container_width=True):
                st.session_state["auth_mode"] = "login"
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
 
        st.markdown('</div>', unsafe_allow_html=True)
 
    st.stop()
 
# ══════════════════════════════════════════════════════════
# APP SHELL  (authenticated)
# ══════════════════════════════════════════════════════════
user = st.session_state["user"]
 
# ── Top bar ──────────────────────────────────────────────
st.markdown(f"""
<div class="vd-topbar">
  <div class="vd-brand">
    <span class="vd-brand-dot"></span>
    VERIDECT
  </div>
  <div class="vd-topbar-right">
    <div class="vd-user-pill">
      <div class="vd-avatar">{initials(user)}</div>
      {user}
    </div>
  </div>
</div>
""", unsafe_allow_html=True)
 
# ── Body: sidebar + main ─────────────────────────────────
sb_col, main_col = st.columns([1, 4], gap="small")
 
# ────────────────────────────────────────────
# SIDEBAR
# ────────────────────────────────────────────
with sb_col:
    st.markdown('<div class="vd-sidebar-wrap">', unsafe_allow_html=True)
    st.markdown('<div class="vd-nav-section-label">Navigation</div>', unsafe_allow_html=True)
 
    icons = {"Analyze": "◈  Analyze", "Dashboard": "◻  Dashboard", "History": "◷  History"}
 
    for pname, label in icons.items():
        css = "nav-active" if st.session_state["page"] == pname else "nav-btn"
        st.markdown(f'<div class="{css}">', unsafe_allow_html=True)
        if st.button(label, key=f"nav_{pname}", use_container_width=True):
            st.session_state["page"] = pname
            st.session_state["result_html"] = ""
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
 
    history_count = cur.execute(
        "SELECT COUNT(*) FROM history WHERE username=?", (user,)).fetchone()[0]
 
    st.markdown(f"""
    <div class="vd-sidebar-footer">
      {history_count} analyses in your history<br>
      Gemini AI · Google News RSS<br>
      SQLite · Streamlit
    </div>
    """, unsafe_allow_html=True)
 
    st.markdown('<div class="logout-btn">', unsafe_allow_html=True)
    if st.button("Logout", key="logout_btn", use_container_width=True):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()
    st.markdown('</div></div>', unsafe_allow_html=True)
 
# ────────────────────────────────────────────
# MAIN CONTENT
# ────────────────────────────────────────────
with main_col:
    st.markdown('<div class="vd-main-wrap">', unsafe_allow_html=True)
    page = st.session_state["page"]
 
    # ════════════════════════════════════════
    # ANALYZE
    # ════════════════════════════════════════
    if page == "Analyze":
        st.markdown('<div class="vd-panel-title">ANALYZE NEWS</div>', unsafe_allow_html=True)
        st.markdown('<p class="vd-panel-sub">Paste any news headline or article excerpt — Gemini AI cross-references it against live Google News headlines</p>', unsafe_allow_html=True)
 
        # Handle example pre-fill
        default_val = st.session_state.pop("_example_text", "")
 
        news_text = st.text_area(
            "news_area", label_visibility="collapsed",
            placeholder="Paste your news headline or article text here…",
            height=148, key="news_textarea",
            value=default_val,
        )
 
        if news_text:
            st.markdown(f'<div class="vd-char-hint">{len(news_text)} characters</div>',
                        unsafe_allow_html=True)
 
        c1, c2, c3 = st.columns([2.2, 1, 1])
        with c1:
            st.markdown('<div class="run-btn">', unsafe_allow_html=True)
            run = st.button("▷  Run Analysis", key="run_btn", use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        with c2:
            st.markdown('<div class="sec-btn">', unsafe_allow_html=True)
            if st.button("Clear", key="clear_btn", use_container_width=True):
                st.session_state["result_html"] = ""
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        with c3:
            st.markdown('<div class="sec-btn">', unsafe_allow_html=True)
            if st.button("Try example", key="ex_btn", use_container_width=True):
                EXAMPLES = [
                    "Scientists discover new species of deep-sea creature that survives without oxygen near hydrothermal vents.",
                    "Government secretly plans to ban all social media platforms by end of 2025 according to anonymous leaked documents.",
                    "NASA confirms strong evidence of liquid water beneath the Martian surface in a major new study.",
                ]
                idx = st.session_state.get("_ex_idx", 0) % len(EXAMPLES)
                st.session_state["_ex_idx"] = idx + 1
                st.session_state["_example_text"] = EXAMPLES[idx]
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
 
        if run and news_text.strip():
            ph = st.empty()
            ph.markdown("""
            <div class="vd-scanning">
              <div class="vd-scan-text">scanning google news…</div>
              <div class="vd-scan-bar"><div class="vd-scan-fill"></div></div>
              <div class="vd-scan-text" style="opacity:.45;font-size:11px;">cross-referencing with gemini ai</div>
            </div>""", unsafe_allow_html=True)
 
            res  = analyze_news(news_text.strip())
            html = result_card(res)
 
            cur.execute(
                "INSERT INTO history (username,news,result,verdict,confidence,created_at) VALUES (?,?,?,?,?,?)",
                (user, news_text.strip(), res["explanation"],
                 res["verdict"], res["confidence"],
                 datetime.now().strftime("%Y-%m-%d %H:%M")))
            conn.commit()
 
            ph.empty()
            st.session_state["result_html"] = html
 
        if st.session_state.get("result_html"):
            st.markdown(st.session_state["result_html"], unsafe_allow_html=True)
 
    # ════════════════════════════════════════
    # DASHBOARD
    # ════════════════════════════════════════
    elif page == "Dashboard":
        st.markdown('<div class="vd-panel-title">DASHBOARD</div>', unsafe_allow_html=True)
        st.markdown('<p class="vd-panel-sub">Analytics across all users and submissions</p>',
                    unsafe_allow_html=True)
 
        f, r, u = db_stats()
        st.markdown(f"""
        <div class="vd-stats-grid">
          <div class="vd-stat-card s-fake">
            <div class="vd-stat-label">Fake Detected</div>
            <div class="vd-stat-num">{f}</div>
          </div>
          <div class="vd-stat-card s-real">
            <div class="vd-stat-label">Verified Real</div>
            <div class="vd-stat-num">{r}</div>
          </div>
          <div class="vd-stat-card s-unv">
            <div class="vd-stat-label">Unverified</div>
            <div class="vd-stat-num">{u}</div>
          </div>
        </div>
        """, unsafe_allow_html=True)
 
        rows = cur.execute(
            "SELECT username,news,verdict,confidence,created_at FROM history ORDER BY id DESC LIMIT 12"
        ).fetchall()
 
        if rows:
            st.markdown('<div class="vd-section-label">Recent submissions</div>', unsafe_allow_html=True)
            trs = ""
            for uname, news, verdict, conf, ts in rows:
                v   = (verdict or "unverified").lower()
                pc  = {"fake":"pill-fake","real":"pill-real","unverified":"pill-unv"}.get(v,"pill-unv")
                pl  = {"fake":"Fake","real":"Real","unverified":"Unverified"}.get(v,"?")
                prv = (news or "")[:78] + ("…" if len(news or "") > 78 else "")
                trs += f"""<tr>
                  <td>{uname}</td><td>{prv}</td>
                  <td><span class="pill {pc}">{pl}</span></td>
                  <td class="mono">{conf or "—"}%</td>
                  <td class="mono" style="opacity:.45;">{ts or ""}</td>
                </tr>"""
            st.markdown(f"""
            <table class="vd-table">
              <thead><tr><th>User</th><th>News preview</th><th>Verdict</th><th>Conf.</th><th>Time</th></tr></thead>
              <tbody>{trs}</tbody>
            </table>""", unsafe_allow_html=True)
        else:
            st.markdown('<p style="color:rgba(240,236,228,.28);font-size:13px;margin-top:40px;text-align:center;">No analyses yet — head to Analyze to get started.</p>',
                        unsafe_allow_html=True)
 
    # ════════════════════════════════════════
    # HISTORY
    # ════════════════════════════════════════
    elif page == "History":
        st.markdown('<div class="vd-panel-title">HISTORY</div>', unsafe_allow_html=True)
        st.markdown(f'<p class="vd-panel-sub">Your personal analysis history · {user}</p>',
                    unsafe_allow_html=True)
 
        rows = cur.execute(
            "SELECT news,result,verdict,confidence,created_at FROM history WHERE username=? ORDER BY id DESC",
            (user,)).fetchall()
 
        if not rows:
            st.markdown('<p style="color:rgba(240,236,228,.28);font-size:13px;margin-top:40px;text-align:center;">No history yet — analyze some news to see it here.</p>',
                        unsafe_allow_html=True)
        else:
            items = ""
            for news, _, verdict, conf, ts in rows:
                v   = (verdict or "unverified").lower()
                pc  = {"fake":"pill-fake","real":"pill-real","unverified":"pill-unv"}.get(v,"pill-unv")
                pl  = {"fake":"Fake","real":"Real","unverified":"Unverified"}.get(v,"?")
                prv = (news or "")[:130] + ("…" if len(news or "") > 130 else "")
                items += f"""
                <div class="vd-history-item">
                  <div>
                    <div class="vd-history-news">{prv}</div>
                    <div class="vd-history-ts">{ts or "—"}</div>
                  </div>
                  <div style="text-align:right;flex-shrink:0;">
                    <span class="pill {pc}">{pl}</span>
                    <div class="vd-history-conf">{conf or "—"}% confidence</div>
                  </div>
                </div>"""
            st.markdown(items, unsafe_allow_html=True)
 
    st.markdown('</div>', unsafe_allow_html=True)
