import streamlit as st
import requests
from bs4 import BeautifulSoup
import sqlite3
from passlib.hash import pbkdf2_sha256
import google.generativeai as genai
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

    # Default admin
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
                st.warning("Enter all fields")

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

# -------------------- LOAD GEMINI --------------------
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel("gemini-pro")   # ✅ FIXED MODEL
except Exception as e:
    st.error(f"❌ Gemini setup error: {e}")
    st.stop()

# -------------------- MAIN UI --------------------
st.title("🧠 Fake News Detection System")
st.write(f"👤 Logged in as: {st.session_state['user']}")

option = st.radio("Choose Input Type:", ["Text", "URL"])
news_text = ""

# -------------------- URL INPUT --------------------
if option == "URL":
    url_input = st.text_input("Enter News URL")

    if st.button("Fetch News"):
        try:
            res = requests.get(url_input, timeout=10)
            soup = BeautifulSoup(res.text, "html.parser")
            paragraphs = soup.find_all("p")
            news_text = " ".join([p.text for p in paragraphs])

            st.success("News Extracted ✅")
            st.text_area("Extracted Content", news_text, height=200)

        except Exception as e:
            st.error(f"Failed to fetch URL ❌\n{e}")

# -------------------- TEXT INPUT --------------------
else:
    news_text = st.text_area("Enter News Content", height=200)

# -------------------- ANALYSIS FUNCTION --------------------
def analyze_news(text):
    prompt = f"""
    Analyze the following news and respond STRICTLY in this format:

    Verdict: Fake or Real
    Confidence: XX%
    Explanation: ...

    News:
    {text}
    """

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"API Error ❌\n{str(e)}"

# -------------------- ANALYZE --------------------
if st.button("🔍 Analyze News"):
    if news_text.strip() == "":
        st.warning("⚠️ Enter news first")
    else:
        with st.spinner("Analyzing..."):
            result = analyze_news(news_text)

        result_lower = result.lower()

        if any(word in result_lower for word in ["fake", "false", "misleading"]):
            st.error("🚨 FAKE NEWS DETECTED")
        elif any(word in result_lower for word in ["real", "true", "accurate"]):
            st.success("✅ REAL NEWS")
        else:
            st.warning("⚠️ Could not clearly classify")

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
