import streamlit as st
import requests
from bs4 import BeautifulSoup
import sqlite3

# -------------------- CONFIG --------------------
st.set_page_config(page_title="Fake News Detector", layout="centered")

# -------------------- DATABASE --------------------
conn = sqlite3.connect("history.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS history (
    news TEXT,
    result TEXT
)
""")
conn.commit()

# -------------------- LOGIN SYSTEM --------------------
def login():
    st.title("🔐 Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username == "admin" and password == "1234":
            st.session_state["logged_in"] = True
            st.success("Login Successful ✅")
        else:
            st.error("Invalid Credentials ❌")

# -------------------- CHECK LOGIN --------------------
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    login()
    st.stop()

# -------------------- LOAD API KEY --------------------
try:
    API_KEY = st.secrets["PPLX_API_KEY"]
except:
    st.error("API key missing in Streamlit secrets ❌")
    st.stop()

# -------------------- MAIN UI --------------------
st.title("📰 Fake News Detection System")

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
        return "Error in API"

# -------------------- ANALYZE BUTTON --------------------
if st.button("🔍 Analyze News"):
    if news_text.strip() == "":
        st.warning("Enter news first ⚠️")
    else:
        with st.spinner("Analyzing..."):
            result = analyze_news(news_text)

        # -------------------- COLOR RESULT --------------------
        if "fake" in result.lower():
            st.error("🚨 FAKE NEWS DETECTED")
        elif "real" in result.lower():
            st.success("✅ REAL NEWS")
        else:
            st.info("Result unclear")

        st.markdown(result)

        # Save history
        c.execute("INSERT INTO history VALUES (?, ?)", (news_text, result))
        conn.commit()

# -------------------- HISTORY --------------------
st.subheader("📜 Analysis History")

if st.button("Show History"):
    rows = c.execute("SELECT * FROM history").fetchall()

    for row in rows[::-1]:
        st.text(f"📰 {row[0][:100]}...")
        st.text(f"Result: {row[1]}")
        st.write("---")

# -------------------- LOGOUT --------------------
if st.button("Logout"):
    st.session_state["logged_in"] = False
    st.experimental_rerun()