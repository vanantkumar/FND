import streamlit as st
import requests
from bs4 import BeautifulSoup
import sqlite3
from passlib.hash import pbkdf2_sha256
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

# -------------------- CONFIG --------------------
st.set_page_config(page_title="AI Fake News Detector", layout="centered")

# -------------------- DATABASE --------------------
conn = sqlite3.connect("app.db", check_same_thread=False)
c = conn.cursor()

def init_db():
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        username TEXT,
        password TEXT,
        role TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS history (
        username TEXT,
        news TEXT,
        result TEXT
    )
    """)

    # Default admin user
    user = c.execute("SELECT * FROM users WHERE username='admin'").fetchone()
    if not user:
        hashed = pbkdf2_sha256.hash("admin123")
        c.execute("INSERT INTO users VALUES (?, ?, ?)", ("admin", hashed, "admin"))
        conn.commit()

init_db()

# -------------------- SESSION --------------------
if "user" not in st.session_state:
    st.session_state["user"] = None

# -------------------- AUTH --------------------
def login_ui():
    st.title("🔐 Login / Signup")

    st.info("Default Login → admin / admin123")

    option = st.radio("Choose:", ["Login", "Signup"])

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if option == "Signup":
        if st.button("Create Account"):
            if username and password:
                hashed = pbkdf2_sha256.hash(password)
                c.execute("INSERT INTO users VALUES (?, ?, ?)", (username, hashed, "user"))
                conn.commit()
                st.success("Account created ✅")
            else:
                st.warning("Enter details")

    else:
        if st.button("Login"):
            user = c.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()

            if user and pbkdf2_sha256.verify(password, user[1]):
                st.session_state["user"] = username
                st.success("Login successful ✅")
                st.rerun()
            else:
                st.error("Invalid credentials ❌")

# -------------------- CHECK LOGIN --------------------
if not st.session_state["user"]:
    login_ui()
    st.stop()

# -------------------- LOAD API KEY --------------------
try:
    API_KEY = st.secrets["PPLX_API_KEY"]
except:
    st.error("API key missing in Streamlit secrets ❌")
    st.stop()

# -------------------- MAIN APP --------------------
st.title("🧠 Fake News Detection System")

st.write(f"👤 Logged in as: {st.session_state['user']}")

option = st.radio("Choose Input Type:", ["Text", "URL"])

news_text = ""

# -------------------- URL INPUT --------------------
if option == "URL":
    url = st.text_input("Enter News URL")

    if st.button("Fetch News"):
        try:
            res = requests.get(url)
            soup = BeautifulSoup(res.text, "html.parser")
            paragraphs = soup.find_all("p")
            news_text = " ".join([p.text for p in paragraphs])

            st.success("News Extracted ✅")
            st.text_area("Extracted Content", news_text, height=200)

        except:
            st.error("Failed to fetch URL ❌")

# -------------------- TEXT INPUT --------------------
else:
    news_text = st.text_area("Enter News Content", height=200)

# -------------------- ANALYSIS FUNCTION --------------------
def analyze_news(text):
    url = "https://api.perplexity.ai/chat/completions"

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    prompt = f"""
    Analyze the following news and determine if it is FAKE or REAL.

    Provide:
    - Verdict (Fake/Real)
    - Confidence (%)
    - Explanation

    News:
    {text}
    """

    data = {
        "model": "sonar-medium-online",
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        return "API Error ❌"

# -------------------- ANALYZE --------------------
if st.button("🔍 Analyze News"):
    if news_text.strip() == "":
        st.warning("Enter news first ⚠️")
    else:
        with st.spinner("Analyzing..."):
            result = analyze_news(news_text)

        # Color result
        if "fake" in result.lower():
            st.error("🚨 FAKE NEWS DETECTED")
        elif "real" in result.lower():
            st.success("✅ REAL NEWS")
        else:
            st.info("Result unclear")

        st.markdown(result)

        # Save history
        c.execute("INSERT INTO history VALUES (?, ?, ?)",
                  (st.session_state["user"], news_text, result))
        conn.commit()

        # PDF Export
        doc = SimpleDocTemplate("report.pdf")
        styles = getSampleStyleSheet()
        story = [Paragraph(result, styles["Normal"])]
        doc.build(story)

        with open("report.pdf", "rb") as f:
            st.download_button("📄 Download Report", f, "report.pdf")

# -------------------- HISTORY --------------------
st.subheader("📜 History")

rows = c.execute("SELECT * FROM history WHERE username=?",
                 (st.session_state["user"],)).fetchall()

for r in rows[::-1]:
    st.write("📰 " + r[1][:100] + "...")
    st.write(r[2])
    st.write("---")

# -------------------- LOGOUT --------------------
if st.button("Logout"):
    st.session_state["user"] = None
    st.rerun()
