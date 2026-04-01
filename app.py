import streamlit as st
import requests
import sqlite3
import hashlib
import google.generativeai as genai
from datetime import datetime
import urllib.parse
from xml.etree import ElementTree as ET
import pandas as pd
import re
import time
 
# ─────────────────────────────────────────────
# PAGE CONFIG  (must be first Streamlit call)
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Veridect · Fake News Detector",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="collapsed",
)
 
# ─────────────────────────────────────────────
# GLOBAL CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:wght@300;400;500&family=DM+Mono:wght@400;500&display=swap');
 
/* ── Reset & base ── */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html, body, [data-testid="stAppViewContainer"] { height: 100%; }
 
section[data-testid="stSidebar"] { display: none !important; }
header[data-testid="stHeader"]   { display: none !important; }
footer                            { display: none !important; }
#MainMenu                         { display: none !important; }
 
[data-testid="stAppViewContainer"] {
    background: #0e0e10 !important;
    padding: 0 !important;
}
[data-testid="block-container"] {
    padding: 0 !important;
    max-width: 100% !important;
}
[data-testid="stVerticalBlock"] { gap: 0 !important; }
 
/* ── Streamlit widget resets ── */
div[data-testid="stTextArea"] textarea,
div[data-testid="stTextInput"] input {
    background: #1a1a1e !important;
    color: #f0ece4 !important;
    border: 1px solid rgba(240,236,228,0.15) !important;
    border-radius: 10px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 14px !important;
}
div[data-testid="stTextArea"] textarea:focus,
div[data-testid="stTextInput"] input:focus {
    border-color: rgba(240,236,228,0.45) !important;
    box-shadow: none !important;
}
 
div.stButton > button {
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    border-radius: 8px !important;
    transition: all .18s ease !important;
    border: none !important;
}
 
div[data-testid="stProgress"] > div {
    border-radius: 10px !important;
    height: 5px !important;
    background: rgba(240,236,228,0.1) !important;
}
div[data-testid="stProgress"] > div > div {
    border-radius: 10px !important;
}
 
/* ── Layout shell ── */
.vd-shell {
    display: grid;
    grid-template-columns: 230px 1fr;
    grid-template-rows: 52px 1fr;
    min-height: 100vh;
    background: #0e0e10;
    color: #f0ece4;
    font-family: 'DM Sans', sans-serif;
}
 
/* ── Top bar ── */
.vd-topbar {
    grid-column: 1 / -1;
    background: #0a0a0c;
    border-bottom: 1px solid rgba(240,236,228,0.07);
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 28px;
}
.vd-brand {
    font-family: 'Bebas Neue', cursive;
    font-size: 22px;
    letter-spacing: 3px;
    color: #f0ece4;
    display: flex;
    align-items: center;
    gap: 10px;
}
.vd-brand-dot {
    width: 8px; height: 8px;
    border-radius: 50%;
    background: #c8291a;
    display: inline-block;
    animation: pulseDot 2s ease-in-out infinite;
}
@keyframes pulseDot {
    0%,100% { opacity:1; transform:scale(1); }
    50%      { opacity:.4; transform:scale(.65); }
}
.vd-topbar-right {
    display: flex;
    align-items: center;
    gap: 14px;
}
.vd-user-pill {
    background: rgba(240,236,228,.07);
    border: 1px solid rgba(240,236,228,.12);
    border-radius: 20px;
    padding: 4px 14px 4px 8px;
    font-size: 12px;
    color: rgba(240,236,228,.7);
    display: flex;
    align-items: center;
    gap: 7px;
}
.vd-avatar {
    width: 22px; height: 22px;
    border-radius: 50%;
    background: #c8291a;
    display: flex; align-items: center; justify-content: center;
    font-size: 10px; font-weight: 500; color: #fff;
}
.vd-logout-btn {
    background: transparent;
    border: 1px solid rgba(240,236,228,.18);
    border-radius: 6px;
    color: rgba(240,236,228,.5);
    font-family: 'DM Sans', sans-serif;
    font-size: 11px;
    padding: 4px 12px;
    cursor: pointer;
    transition: all .15s;
}
.vd-logout-btn:hover { color: #f0ece4; border-color: rgba(240,236,228,.4); }
 
/* ── Sidebar ── */
.vd-sidebar {
    background: #0a0a0c;
    border-right: 1px solid rgba(240,236,228,.06);
    padding: 24px 0;
    display: flex;
    flex-direction: column;
    gap: 2px;
}
.vd-nav-label {
    font-size: 10px;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: rgba(240,236,228,.25);
    padding: 8px 22px 4px;
    font-weight: 500;
}
.vd-nav-item {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 22px;
    cursor: pointer;
    font-size: 13px;
    color: rgba(240,236,228,.45);
    border-left: 2px solid transparent;
    transition: all .15s;
    user-select: none;
}
.vd-nav-item:hover {
    background: rgba(240,236,228,.04);
    color: rgba(240,236,228,.8);
}
.vd-nav-item.active {
    color: #f0ece4;
    background: rgba(240,236,228,.06);
    border-left-color: #c8291a;
}
.vd-nav-icon { font-size: 14px; width: 18px; text-align: center; }
.vd-nav-badge {
    margin-left: auto;
    background: #c8291a;
    color: #fff;
    font-size: 10px; font-weight: 500;
    padding: 1px 7px; border-radius: 10px;
}
.vd-sidebar-footer {
    margin-top: auto;
    padding: 16px 22px;
    border-top: 1px solid rgba(240,236,228,.05);
    font-size: 10px;
    color: rgba(240,236,228,.18);
    line-height: 1.6;
}
 
/* ── Main content ── */
.vd-main {
    background: #111114;
    padding: 32px 36px;
    overflow-y: auto;
}
.vd-panel-title {
    font-family: 'Bebas Neue', cursive;
    font-size: 34px;
    letter-spacing: 2px;
    color: #f0ece4;
    margin-bottom: 4px;
}
.vd-panel-sub {
    font-size: 12px;
    color: rgba(240,236,228,.38);
    margin-bottom: 28px;
}
 
/* ── Analyze ── */
.vd-textarea-hint {
    font-size: 11px;
    color: rgba(240,236,228,.3);
    text-align: right;
    margin-top: -8px;
    margin-bottom: 16px;
    font-family: 'DM Mono', monospace;
}
 
/* ── Result card ── */
.vd-result {
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid rgba(240,236,228,.12);
    margin-top: 8px;
    animation: slideUp .35s ease;
}
@keyframes slideUp {
    from { opacity:0; transform:translateY(12px); }
    to   { opacity:1; transform:translateY(0); }
}
.vd-result-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 18px 22px;
}
.vd-result-header.fake     { background: rgba(200,41,26,.15); border-bottom:1px solid rgba(200,41,26,.2); }
.vd-result-header.real     { background: rgba(26,110,60,.15);  border-bottom:1px solid rgba(26,110,60,.2); }
.vd-result-header.unverified { background: rgba(181,107,0,.12); border-bottom:1px solid rgba(181,107,0,.2); }
 
.vd-verdict {
    font-family: 'Bebas Neue', cursive;
    font-size: 22px;
    letter-spacing: 2px;
    display: flex; align-items: center; gap: 8px;
}
.vd-verdict.fake        { color: #e85d4a; }
.vd-verdict.real        { color: #4caf7d; }
.vd-verdict.unverified  { color: #e5a835; }
 
.vd-conf-badge {
    font-family: 'DM Mono', monospace;
    font-size: 13px;
    padding: 4px 12px;
    border-radius: 20px;
    font-weight: 500;
}
.fake .vd-conf-badge        { background:rgba(200,41,26,.18); color:#e85d4a; }
.real .vd-conf-badge        { background:rgba(26,110,60,.18);  color:#4caf7d; }
.unverified .vd-conf-badge  { background:rgba(181,107,0,.18);  color:#e5a835; }
 
.vd-result-body {
    background: #1a1a1e;
    padding: 20px 22px;
}
.vd-conf-label {
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    color: rgba(240,236,228,.3);
    margin-bottom: 8px;
    font-weight: 500;
}
.vd-conf-track {
    height: 5px;
    background: rgba(240,236,228,.1);
    border-radius: 10px;
    overflow: hidden;
    margin-bottom: 18px;
}
.vd-conf-fill { height:100%; border-radius:10px; }
.fake .vd-conf-fill        { background:#c8291a; }
.real .vd-conf-fill        { background:#1a6e3c; }
.unverified .vd-conf-fill  { background:#b56b00; }
 
.vd-explanation {
    font-size: 13.5px;
    color: rgba(240,236,228,.7);
    line-height: 1.75;
    border-top: 1px solid rgba(240,236,228,.08);
    padding-top: 16px;
}
 
.vd-headlines {
    margin-top: 18px;
    background: #111114;
    border-radius: 8px;
    padding: 14px 16px;
    border: 1px solid rgba(240,236,228,.07);
}
.vd-headlines-label {
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    color: rgba(240,236,228,.3);
    margin-bottom: 10px;
    font-weight: 500;
}
.vd-headline-item {
    font-size: 12px;
    color: rgba(240,236,228,.55);
    padding: 5px 0;
    border-bottom: 1px solid rgba(240,236,228,.06);
    display: flex; gap: 8px; align-items: baseline;
    line-height: 1.45;
}
.vd-headline-item:last-child { border-bottom: none; }
.vd-headline-item::before { content:"—"; color:rgba(240,236,228,.2); font-size:11px; flex-shrink:0; }
 
/* ── Dashboard ── */
.vd-stats-row {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 14px;
    margin-bottom: 28px;
}
.vd-stat-card {
    background: #1a1a1e;
    border: 1px solid rgba(240,236,228,.08);
    border-radius: 10px;
    padding: 20px 22px;
    position: relative;
    overflow: hidden;
}
.vd-stat-card::before {
    content:"";
    position:absolute; left:0; top:0; bottom:0;
    width:3px;
}
.vd-stat-card.s-fake::before  { background:#c8291a; }
.vd-stat-card.s-real::before  { background:#1a6e3c; }
.vd-stat-card.s-unv::before   { background:#b56b00; }
.vd-stat-label {
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    color: rgba(240,236,228,.3);
    margin-bottom: 8px;
    font-weight: 500;
}
.vd-stat-num {
    font-family: 'Bebas Neue', cursive;
    font-size: 42px;
    letter-spacing: 1px;
    line-height: 1;
}
.vd-stat-card.s-fake .vd-stat-num { color:#e85d4a; }
.vd-stat-card.s-real .vd-stat-num { color:#4caf7d; }
.vd-stat-card.s-unv  .vd-stat-num { color:#e5a835; }
 
/* ── Table ── */
.vd-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 12.5px;
    margin-top: 20px;
}
.vd-table th {
    text-align: left;
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: rgba(240,236,228,.3);
    padding: 0 14px 10px;
    font-weight: 500;
}
.vd-table td {
    padding: 11px 14px;
    border-top: 1px solid rgba(240,236,228,.06);
    color: rgba(240,236,228,.75);
    vertical-align: middle;
}
.vd-table tr:hover td { background: rgba(240,236,228,.03); }
.vd-mono { font-family: 'DM Mono', monospace; font-size:11px; }
 
/* ── Pills ── */
.pill {
    display:inline-block; padding:2px 9px;
    border-radius:10px; font-size:10px;
    font-weight:500; text-transform:uppercase; letter-spacing:.5px;
}
.pill-fake { background:rgba(200,41,26,.18); color:#e85d4a; }
.pill-real { background:rgba(26,110,60,.18);  color:#4caf7d; }
.pill-unv  { background:rgba(181,107,0,.18);  color:#e5a835; }
 
/* ── History ── */
.vd-history-item {
    background: #1a1a1e;
    border: 1px solid rgba(240,236,228,.08);
    border-radius: 10px;
    padding: 16px 20px;
    margin-bottom: 12px;
    display: grid;
    grid-template-columns: 1fr auto;
    gap: 14px; align-items: start;
    transition: border-color .15s;
}
.vd-history-item:hover { border-color: rgba(240,236,228,.25); }
.vd-history-news { font-size:13px; color:rgba(240,236,228,.8); line-height:1.5; margin-bottom:5px; }
.vd-history-meta { font-size:11px; color:rgba(240,236,228,.3); font-family:'DM Mono',monospace; }
.vd-history-conf { font-size:11px; color:rgba(240,236,228,.3); font-family:'DM Mono',monospace; margin-top:4px; }
 
/* ── Login ── */
.vd-login-wrap {
    min-height: 100vh;
    display: grid;
    grid-template-columns: 1fr 1fr;
    background: #0e0e10;
    font-family: 'DM Sans', sans-serif;
}
.vd-login-left {
    background: #0a0a0c;
    border-right: 1px solid rgba(240,236,228,.07);
    padding: 52px 52px;
    display: flex; flex-direction: column; justify-content: space-between;
}
.vd-login-logo {
    font-family: 'Bebas Neue', cursive;
    font-size: 24px; letter-spacing: 4px;
    color: #f0ece4;
    display: flex; align-items: center; gap: 10px;
}
.vd-login-tagline {
    font-family: 'Bebas Neue', cursive;
    font-size: 64px; line-height: 1.0;
    color: #f0ece4; margin-bottom: 20px; letter-spacing: 1px;
}
.vd-login-desc {
    font-size: 13px;
    color: rgba(240,236,228,.38);
    line-height: 1.75; max-width: 300px;
}
.vd-ticker { display:flex; flex-direction:column; gap:8px; margin-top:28px; }
.vd-ticker-item {
    display:flex; align-items:center; gap:9px;
    font-size:11px; color:rgba(240,236,228,.28);
}
.vd-ticker-dot { width:5px; height:5px; border-radius:50%; flex-shrink:0; }
.vd-login-right {
    padding: 52px 52px;
    display: flex; flex-direction: column; justify-content: center;
    color: #f0ece4;
}
.vd-form-title {
    font-family: 'Bebas Neue', cursive;
    font-size: 30px; letter-spacing: 2px;
    color: #f0ece4; margin-bottom: 4px;
}
.vd-form-sub { font-size: 12px; color: rgba(240,236,228,.35); margin-bottom: 28px; }
.vd-field-label {
    font-size: 10px; text-transform: uppercase;
    letter-spacing: 1.2px; color: rgba(240,236,228,.4);
    margin-bottom: 6px; font-weight: 500; display: block;
}
.vd-divider {
    height: 1px; background: rgba(240,236,228,.08);
    margin: 22px 0; position: relative;
}
.vd-divider-label {
    position:absolute; top:-9px; left:50%;
    transform:translateX(-50%);
    background:#0e0e10; padding:0 12px;
    font-size:11px; color:rgba(240,236,228,.25);
}
.vd-login-footer { font-size:10px; color:rgba(240,236,228,.15); }
 
/* ── Analyzing animation ── */
.vd-scanning {
    display:flex; flex-direction:column; align-items:center; gap:16px;
    padding: 48px 0;
}
.vd-scan-bar { width:200px; height:3px; background:rgba(240,236,228,.1); border-radius:10px; overflow:hidden; }
.vd-scan-fill { height:100%; width:30%; background:#f0ece4; border-radius:10px; animation:scan 1.1s ease-in-out infinite; }
@keyframes scan { 0%{transform:translateX(-100%)} 100%{transform:translateX(400%)} }
.vd-scan-text { font-size:12px; color:rgba(240,236,228,.35); font-family:'DM Mono',monospace; }
 
/* ── Button overrides ── */
.stButton[data-vd="primary"] > button {
    background: #f0ece4 !important; color: #0e0e10 !important;
    padding: 11px 28px !important; font-size: 13px !important;
    width: 100% !important;
}
.stButton[data-vd="primary"] > button:hover { background: #fff !important; }
 
.stButton[data-vd="ghost"] > button {
    background: transparent !important;
    color: rgba(240,236,228,.55) !important;
    border: 1px solid rgba(240,236,228,.18) !important;
    padding: 11px 20px !important; font-size: 13px !important;
}
.stButton[data-vd="ghost"] > button:hover {
    color: #f0ece4 !important;
    border-color: rgba(240,236,228,.4) !important;
}
 
.stButton[data-vd="nav"] > button {
    background: transparent !important;
    color: rgba(240,236,228,.55) !important;
    border: none !important;
    text-align: left !important;
    width: 100% !important;
    justify-content: flex-start !important;
    padding: 10px 22px !important;
    font-size: 13px !important;
    border-radius: 0 !important;
    border-left: 2px solid transparent !important;
}
.stButton[data-vd="nav"] > button:hover { background: rgba(240,236,228,.04) !important; color:#f0ece4 !important; }
.stButton[data-vd="nav-active"] > button {
    background: rgba(240,236,228,.06) !important;
    color: #f0ece4 !important;
    border: none !important;
    border-left: 2px solid #c8291a !important;
    text-align: left !important;
    width: 100% !important;
    justify-content: flex-start !important;
    padding: 10px 22px !important;
    font-size: 13px !important;
    border-radius: 0 !important;
}
</style>
""", unsafe_allow_html=True)
 
# ─────────────────────────────────────────────
# DATABASE
# ─────────────────────────────────────────────
conn = sqlite3.connect("veridect.db", check_same_thread=False)
c = conn.cursor()
 
c.execute("""CREATE TABLE IF NOT EXISTS users
             (username TEXT PRIMARY KEY, password TEXT, role TEXT)""")
c.execute("""CREATE TABLE IF NOT EXISTS history
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              username TEXT, news TEXT, result TEXT,
              verdict TEXT, confidence INTEGER,
              created_at TEXT)""")
 
if not c.execute("SELECT * FROM users WHERE username='admin'").fetchone():
    c.execute("INSERT INTO users VALUES (?,?,?)",
              ("admin", hashlib.sha256("admin123".encode()).hexdigest(), "admin"))
    conn.commit()
 
# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────
defaults = {
    "user": None,
    "page": "Analyze",
    "auth_mode": "login",
    "result_html": "",
    "analyzing": False,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v
 
# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()
 
def get_initials(username: str) -> str:
    return username[:2].upper()
 
def fetch_real_news(query: str) -> list[str]:
    try:
        url = (f"https://news.google.com/rss/search?"
               f"q={urllib.parse.quote(query)}&hl=en-IN&gl=IN&ceid=IN:en")
        root = ET.fromstring(requests.get(url, timeout=5).content)
        return [i.find("title").text for i in root.findall(".//item")[:5]]
    except Exception:
        return []
 
def analyze_news(text: str) -> dict:
    """Returns dict with keys: verdict, confidence, explanation, headlines"""
    headlines = fetch_real_news(text)
    headlines_str = "\n".join(headlines) if headlines else "No matching headlines found."
 
    prompt = f"""You are a professional fact-checker and misinformation analyst.
 
Today's date: {datetime.now().strftime("%B %d, %Y")}
 
News to analyze:
\"\"\"{text}\"\"\"
 
Related real headlines from Google News:
{headlines_str}
 
Analyze the news carefully. Respond STRICTLY in this exact format (no extra text):
VERDICT: Real|Fake|Unverified
CONFIDENCE: <number between 1-99>
EXPLANATION: <2-3 sentence explanation of your reasoning>
"""
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        model = genai.GenerativeModel(
            next(m.name for m in genai.list_models()
                 if "generateContent" in m.supported_generation_methods)
        )
        raw = model.generate_content(prompt).text.strip()
 
        verdict_match     = re.search(r"VERDICT:\s*(Real|Fake|Unverified)", raw, re.I)
        confidence_match  = re.search(r"CONFIDENCE:\s*(\d+)", raw)
        explanation_match = re.search(r"EXPLANATION:\s*(.+)", raw, re.S)
 
        verdict     = verdict_match.group(1).capitalize()    if verdict_match     else "Unverified"
        confidence  = int(confidence_match.group(1))         if confidence_match  else 50
        explanation = explanation_match.group(1).strip()     if explanation_match else raw
 
        confidence = max(1, min(99, confidence))
    except Exception as e:
        verdict, confidence, explanation = "Unverified", 50, f"Analysis failed: {e}"
 
    return {
        "verdict":     verdict,
        "confidence":  confidence,
        "explanation": explanation,
        "headlines":   headlines,
    }
 
def result_to_html(res: dict, news_text: str) -> str:
    verdict    = res["verdict"].lower()
    conf       = res["confidence"]
    label_map  = {"fake": "✕ FAKE NEWS", "real": "✓ VERIFIED REAL", "unverified": "? UNVERIFIED"}
    label      = label_map.get(verdict, "? UNVERIFIED")
    headlines  = res["headlines"]
    explanation = res["explanation"]
 
    hl_html = "".join(f'<div class="vd-headline-item">{h}</div>' for h in headlines) \
              if headlines else '<div class="vd-headline-item">No matching headlines found.</div>'
 
    return f"""
<div class="vd-result">
  <div class="vd-result-header {verdict}">
    <div class="vd-verdict {verdict}">{label}</div>
    <div class="vd-conf-badge">{conf}%</div>
  </div>
  <div class="vd-result-body {verdict}">
    <div class="vd-conf-label">Confidence Score</div>
    <div class="vd-conf-track">
      <div class="vd-conf-fill" style="width:{conf}%;"></div>
    </div>
    <div class="vd-explanation">{explanation}</div>
    <div class="vd-headlines">
      <div class="vd-headlines-label">Related headlines cross-referenced</div>
      {hl_html}
    </div>
  </div>
</div>
"""
 
def dashboard_stats() -> tuple:
    rows = c.execute("SELECT verdict FROM history").fetchall()
    fake = sum(1 for r in rows if r[0] and r[0].lower() == "fake")
    real = sum(1 for r in rows if r[0] and r[0].lower() == "real")
    unv  = sum(1 for r in rows if r[0] and r[0].lower() == "unverified")
    return fake, real, unv
 
# ─────────────────────────────────────────────
# LOGIN SCREEN
# ─────────────────────────────────────────────
if not st.session_state["user"]:
    st.markdown("""
    <div class="vd-login-wrap">
      <div class="vd-login-left">
        <div class="vd-login-logo">
          <span class="vd-brand-dot"></span> VERIDECT
        </div>
        <div class="vd-login-hero">
          <div class="vd-login-tagline">TRUTH<br>STARTS<br>HERE.</div>
          <p class="vd-login-desc">
            AI-powered misinformation detection with real-time
            Google News cross-referencing and confidence scoring.
          </p>
          <div class="vd-ticker">
            <div class="vd-ticker-item">
              <span class="vd-ticker-dot" style="background:#c8291a;"></span>
              Detects fake news with Gemini AI reasoning
            </div>
            <div class="vd-ticker-item">
              <span class="vd-ticker-dot" style="background:#1a6e3c;"></span>
              Cross-references 5 real-time Google News headlines
            </div>
            <div class="vd-ticker-item">
              <span class="vd-ticker-dot" style="background:#b56b00;"></span>
              Full history & analytics dashboard included
            </div>
          </div>
        </div>
        <p class="vd-login-footer">© 2025 Veridect · Powered by Google Gemini</p>
      </div>
      <div class="vd-login-right">
    """, unsafe_allow_html=True)
 
    if st.session_state["auth_mode"] == "login":
        st.markdown('<div class="vd-form-title">SIGN IN</div>', unsafe_allow_html=True)
        st.markdown('<p class="vd-form-sub">Enter your credentials to continue</p>', unsafe_allow_html=True)
        st.markdown('<label class="vd-field-label">Username</label>', unsafe_allow_html=True)
        username = st.text_input("username_", label_visibility="collapsed", placeholder="e.g. admin")
        st.markdown('<label class="vd-field-label">Password</label>', unsafe_allow_html=True)
        password = st.text_input("password_", label_visibility="collapsed", type="password", placeholder="••••••••")
 
        if st.button("Sign In →", use_container_width=True, key="login_btn"):
            user = c.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
            if user and hash_pw(password) == user[1]:
                st.session_state["user"] = username
                st.rerun()
            else:
                st.error("Invalid username or password.")
 
        st.markdown('<div class="vd-divider"><span class="vd-divider-label">or</span></div>', unsafe_allow_html=True)
 
        if st.button("Create new account", use_container_width=True, key="goto_signup"):
            st.session_state["auth_mode"] = "signup"
            st.rerun()
 
    else:
        st.markdown('<div class="vd-form-title">CREATE ACCOUNT</div>', unsafe_allow_html=True)
        st.markdown('<p class="vd-form-sub">Join Veridect to start detecting misinformation</p>', unsafe_allow_html=True)
        st.markdown('<label class="vd-field-label">Username</label>', unsafe_allow_html=True)
        new_user = st.text_input("new_username_", label_visibility="collapsed", placeholder="Choose a username")
        st.markdown('<label class="vd-field-label">Password</label>', unsafe_allow_html=True)
        new_pass = st.text_input("new_password_", label_visibility="collapsed", type="password", placeholder="Create a strong password")
 
        if st.button("Create Account & Sign In →", use_container_width=True, key="signup_btn"):
            if new_user and new_pass:
                existing = c.execute("SELECT * FROM users WHERE username=?", (new_user,)).fetchone()
                if existing:
                    st.error("Username already taken.")
                else:
                    c.execute("INSERT INTO users VALUES (?,?,?)",
                              (new_user, hash_pw(new_pass), "user"))
                    conn.commit()
                    st.session_state["user"] = new_user
                    st.rerun()
            else:
                st.warning("Please fill in both fields.")
 
        st.markdown('<div class="vd-divider"><span class="vd-divider-label">or</span></div>', unsafe_allow_html=True)
 
        if st.button("← Back to Sign In", use_container_width=True, key="goto_login"):
            st.session_state["auth_mode"] = "login"
            st.rerun()
 
    st.markdown("</div></div>", unsafe_allow_html=True)
    st.stop()
 
# ─────────────────────────────────────────────
# APP SHELL  (logged in)
# ─────────────────────────────────────────────
initials = get_initials(st.session_state["user"])
 
# Top bar
st.markdown(f"""
<div class="vd-shell" style="display:grid;grid-template-columns:230px 1fr;grid-template-rows:52px auto;min-height:100vh;">
  <div class="vd-topbar" style="grid-column:1/-1;">
    <div class="vd-brand"><span class="vd-brand-dot"></span> VERIDECT</div>
    <div class="vd-topbar-right">
      <div class="vd-user-pill">
        <div class="vd-avatar">{initials}</div>
        {st.session_state["user"]}
      </div>
    </div>
  </div>
""", unsafe_allow_html=True)
 
# Close outer shell div later — use columns for sidebar + main
st.markdown('</div>', unsafe_allow_html=True)
 
sidebar_col, main_col = st.columns([230, 770], gap="small")
 
# ── SIDEBAR ──────────────────────────────────
with sidebar_col:
    st.markdown('<div class="vd-sidebar">', unsafe_allow_html=True)
    st.markdown('<div class="vd-nav-label">Navigation</div>', unsafe_allow_html=True)
 
    pages = ["Analyze", "Dashboard", "History"]
    icons = {"Analyze": "◈", "Dashboard": "◻", "History": "◷"}
 
    for p in pages:
        is_active = st.session_state["page"] == p
        key_attr  = "nav-active" if is_active else "nav"
        badge     = ""
        if p == "History":
            count = c.execute("SELECT COUNT(*) FROM history WHERE username=?",
                              (st.session_state["user"],)).fetchone()[0]
            if count:
                badge = f'<span class="vd-nav-badge">{count}</span>'
        label = f"{icons[p]}  {p}"
        if st.button(label, key=f"nav_{p}", use_container_width=True):
            st.session_state["page"] = p
            st.session_state["result_html"] = ""
            st.rerun()
 
    st.markdown("""
    <div class="vd-sidebar-footer">
      Gemini AI · Google News RSS<br>
      SQLite · Python 3.11+
    </div>
    </div>
    """, unsafe_allow_html=True)
 
    if st.button("Logout", key="logout_btn", use_container_width=True):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()
 
# ── MAIN ─────────────────────────────────────
with main_col:
    st.markdown('<div class="vd-main">', unsafe_allow_html=True)
    page = st.session_state["page"]
 
    # ════════════════════════════════════════
    # ANALYZE PAGE
    # ════════════════════════════════════════
    if page == "Analyze":
        st.markdown('<div class="vd-panel-title">ANALYZE NEWS</div>', unsafe_allow_html=True)
        st.markdown('<p class="vd-panel-sub">Paste any news headline or article excerpt to verify its authenticity using Gemini AI</p>', unsafe_allow_html=True)
 
        news_text = st.text_area(
            "news_input",
            label_visibility="collapsed",
            placeholder="Paste your news headline or article text here…",
            height=140,
            key="news_textarea",
        )
 
        if news_text:
            st.markdown(f'<div class="vd-textarea-hint">{len(news_text)} characters</div>',
                        unsafe_allow_html=True)
 
        col_a, col_b, col_c = st.columns([2, 1.2, 1.2])
 
        with col_a:
            run_clicked = st.button("▷  Run Analysis", key="run_btn", use_container_width=True)
        with col_b:
            if st.button("Clear", key="clear_btn", use_container_width=True):
                st.session_state["result_html"] = ""
                st.rerun()
        with col_c:
            example_btn = st.button("Try example", key="ex_btn", use_container_width=True)
 
        if example_btn:
            examples = [
                "Scientists discover new species of deep-sea creature that survives without oxygen near hydrothermal vents.",
                "Government secretly plans to ban all social media platforms by end of 2025 according to anonymous leaked documents.",
                "NASA confirms strong evidence of liquid water beneath the Martian surface in a major new study.",
            ]
            idx = st.session_state.get("_ex_idx", 0) % len(examples)
            st.session_state["_ex_idx"] = idx + 1
            st.session_state["_example_text"] = examples[idx]
            st.rerun()
 
        # Pre-fill example
        if "_example_text" in st.session_state and not news_text:
            news_text = st.session_state.pop("_example_text")
 
        if run_clicked and news_text.strip():
            # Show scanning animation
            scan_placeholder = st.empty()
            scan_placeholder.markdown("""
            <div class="vd-scanning">
              <div class="vd-scan-text">scanning google news…</div>
              <div class="vd-scan-bar"><div class="vd-scan-fill"></div></div>
              <div class="vd-scan-text" style="opacity:.5;font-size:11px;">cross-referencing with gemini ai</div>
            </div>
            """, unsafe_allow_html=True)
 
            result = analyze_news(news_text.strip())
            html   = result_to_html(result, news_text.strip())
 
            # Save to history
            c.execute(
                "INSERT INTO history (username,news,result,verdict,confidence,created_at) VALUES (?,?,?,?,?,?)",
                (
                    st.session_state["user"],
                    news_text.strip(),
                    result["explanation"],
                    result["verdict"],
                    result["confidence"],
                    datetime.now().strftime("%Y-%m-%d %H:%M"),
                )
            )
            conn.commit()
 
            scan_placeholder.empty()
            st.session_state["result_html"] = html
 
        if st.session_state.get("result_html"):
            st.markdown(st.session_state["result_html"], unsafe_allow_html=True)
 
    # ════════════════════════════════════════
    # DASHBOARD PAGE
    # ════════════════════════════════════════
    elif page == "Dashboard":
        st.markdown('<div class="vd-panel-title">DASHBOARD</div>', unsafe_allow_html=True)
        st.markdown('<p class="vd-panel-sub">Analytics across all users and submissions</p>', unsafe_allow_html=True)
 
        fake_n, real_n, unv_n = dashboard_stats()
        total = fake_n + real_n + unv_n
 
        st.markdown(f"""
        <div class="vd-stats-row">
          <div class="vd-stat-card s-fake">
            <div class="vd-stat-label">Fake Detected</div>
            <div class="vd-stat-num">{fake_n}</div>
          </div>
          <div class="vd-stat-card s-real">
            <div class="vd-stat-label">Verified Real</div>
            <div class="vd-stat-num">{real_n}</div>
          </div>
          <div class="vd-stat-card s-unv">
            <div class="vd-stat-label">Unverified</div>
            <div class="vd-stat-num">{unv_n}</div>
          </div>
        </div>
        """, unsafe_allow_html=True)
 
        # Recent submissions table
        rows = c.execute(
            "SELECT username, news, verdict, confidence, created_at FROM history ORDER BY id DESC LIMIT 10"
        ).fetchall()
 
        if rows:
            st.markdown('<div class="vd-panel-sub" style="margin-top:20px;">Recent submissions</div>',
                        unsafe_allow_html=True)
            rows_html = ""
            for r in rows:
                uname, news, verdict, conf, ts = r
                v = (verdict or "unverified").lower()
                pill_cls = {"fake":"pill-fake","real":"pill-real","unverified":"pill-unv"}.get(v,"pill-unv")
                pill_lbl = {"fake":"Fake","real":"Real","unverified":"Unverified"}.get(v,"?")
                preview  = (news or "")[:80] + ("…" if len(news or "") > 80 else "")
                rows_html += f"""
                <tr>
                  <td>{uname}</td>
                  <td>{preview}</td>
                  <td><span class="pill {pill_cls}">{pill_lbl}</span></td>
                  <td class="vd-mono">{conf or "—"}%</td>
                  <td class="vd-mono" style="opacity:.5;">{ts or ""}</td>
                </tr>"""
            st.markdown(f"""
            <table class="vd-table">
              <thead>
                <tr><th>User</th><th>News preview</th><th>Verdict</th><th>Conf.</th><th>Time</th></tr>
              </thead>
              <tbody>{rows_html}</tbody>
            </table>
            """, unsafe_allow_html=True)
        else:
            st.markdown('<p style="color:rgba(240,236,228,.3);font-size:13px;margin-top:40px;text-align:center;">No analyses yet. Go to Analyze to get started.</p>', unsafe_allow_html=True)
 
    # ════════════════════════════════════════
    # HISTORY PAGE
    # ════════════════════════════════════════
    elif page == "History":
        st.markdown('<div class="vd-panel-title">HISTORY</div>', unsafe_allow_html=True)
        st.markdown(f'<p class="vd-panel-sub">Your recent analysis sessions · logged in as <strong>{st.session_state["user"]}</strong></p>', unsafe_allow_html=True)
 
        rows = c.execute(
            "SELECT news, result, verdict, confidence, created_at FROM history WHERE username=? ORDER BY id DESC",
            (st.session_state["user"],)
        ).fetchall()
 
        if not rows:
            st.markdown('<p style="color:rgba(240,236,228,.3);font-size:13px;margin-top:40px;text-align:center;">No history yet. Analyze some news to see it here.</p>', unsafe_allow_html=True)
        else:
            items_html = ""
            for news, result_text, verdict, conf, ts in rows:
                v = (verdict or "unverified").lower()
                pill_cls = {"fake":"pill-fake","real":"pill-real","unverified":"pill-unv"}.get(v,"pill-unv")
                pill_lbl = {"fake":"Fake","real":"Real","unverified":"Unverified"}.get(v,"?")
                preview  = (news or "")[:120] + ("…" if len(news or "") > 120 else "")
                items_html += f"""
                <div class="vd-history-item">
                  <div>
                    <div class="vd-history-news">{preview}</div>
                    <div class="vd-history-meta">{ts or "—"}</div>
                  </div>
                  <div style="text-align:right;">
                    <span class="pill {pill_cls}">{pill_lbl}</span>
                    <div class="vd-history-conf">{conf or "—"}% confidence</div>
                  </div>
                </div>"""
            st.markdown(items_html, unsafe_allow_html=True)
 
    st.markdown('</div>', unsafe_allow_html=True)
 
