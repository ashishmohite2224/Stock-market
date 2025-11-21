import streamlit as st
import requests
import yfinance as yf
import pandas as pd
from textblob import TextBlob
from datetime import datetime

# ==============================
# Page Config
# ==============================
st.set_page_config(
    page_title="📊 Indian Market Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ==============================
# Professional Theme (Blue + Dark Mode)
# ==============================
st.markdown("""
    <style>
        /* Main background */
        [data-testid="stAppViewContainer"] {
            background: linear-gradient(135deg, #031a35 0%, #07305b 100%);
            color: #EAF6F4;
        }

        /* Sidebar styling */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #061b33 0%, #082c54 100%);
            color: #EAF6F4;
        }

        /* Header text color fix */
        h1, h2, h3, h4 {
            color: #5cc9ff !important;
            font-weight: 700;
        }

        /* Metric styling */
        [data-testid="stMetricValue"] {
            color: #5cc9ff !important;
            font-weight: 800;
        }
        [data-testid="stMetricLabel"] {
            color: #cce7ff !important;
        }

        /* Buttons */
        .stButton>button {
            background-color: #58d1f5 !important;
            color: #041427 !important;
            border-radius: 8px;
            font-weight: 700;
            transition: 0.3s;
        }
        .stButton>button:hover {
            background-color: #89e0ff !important;
            transform: scale(1.05);
        }

        /* Card style */
        .card {
            background: rgba(255,255,255,0.07);
            border-radius: 12px;
            padding: 18px;
            margin-bottom: 16px;
            box-shadow: 0 8px 20px rgba(0,0,0,0.4);
        }

        /* Scrollable news box */
        .scroll-box {
            max-height: 320px;
            overflow-y: auto;
            padding-right: 10px;
        }
        .scroll-box::-webkit-scrollbar {
            width: 6px;
        }
        .scroll-box::-webkit-scrollbar-thumb {
            background-color: #58d1f5;
            border-radius: 3px;
        }
    </style>
""", unsafe_allow_html=True)

# ==============================
# App Header
# ==============================
st.title("📈 Indian Market Dashboard")
st.write("Live Market Overview • Stock Analysis • Top Movers • Business News • Sentiment Insights")

# ==============================
# NewsAPI Key
# ==============================
API_KEY = "a9b91dc9740c491ab00c7b79d40486e4"

# ==============================
# Data Fetch Functions
# ==============================
@st.cache_data(ttl=1800)
def fetch_nse_data():
    url = "https://www.nseindia.com/api/equity-stockIndices?index=NIFTY%20500"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        res.raise_for_status()
        data = res.json().get("data", [])
        df = pd.DataFrame(data)
        if "symbol" in df.columns and "lastPrice" in df.columns:
            return df[["symbol", "lastPrice", "pChange"]]
        return df
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=300)
def fetch_news(category="business", num_articles=8):
    url = f"https://newsapi.org/v2/top-headlines?country=in&category={category}&apiKey={API_KEY}&pageSize={num_articles}"
    try:
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        return res.json().get("articles", [])
    except Exception:
        return []

def get_stock_data(symbol, period="1mo"):
    try:
        df = yf.Ticker(symbol).history(period=period)
        return df
    except Exception:
        return pd.DataFrame()

def sentiment_label(text):
    score = TextBlob(text).sentiment.polarity
    if score > 0.1:
        return "🟢 Positive"
    elif score < -0.1:
        return "🔴 Negative"
    else:
        return "⚪ Neutral"

# ==============================
# Sidebar Navigation
# ==============================
st.sidebar.title("📍 Navigation")
page = st.sidebar.radio(
    "Go to",
    (
        "🏠 Dashboard",
        "🔎 Stock Search",
        "🚀 Top Movers",
        "📰 Latest News",
        "💬 Sentiment",
        "ℹ️ About"
    ),
)

# ==============================
# Dashboard Page
# ==============================
if page == "🏠 Dashboard":
    st.header("📊 Indian Market Overview")

    col1, col2, col3 = st.columns([1.2, 1.2, 1.6])

    nifty = get_stock_data("^NSEI", "1mo")
    sensex = get_stock_data("^BSESN", "1mo")

    # NIFTY
    with col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("📊 NIFTY 50")
        if not nifty.empty:
            start, end = nifty["Close"].iloc[0], nifty["Close"].iloc[-1]
            growth = ((end - start) / start) * 100
            st.metric("Value", f"₹{end:,.2f}", delta=f"{growth:.2f}%")
            st.line_chart(nifty["Close"], height=160)
        else:
            st.warning("NIFTY data unavailable.")
        st.markdown('</div>', unsafe_allow_html=True)

    # SENSEX
    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("📈 SENSEX")
        if not sensex.empty:
            start, end = sensex["Close"].iloc[0], sensex["Close"].iloc[-1]
            growth = ((end - start) / start) * 100
            st.metric("Value", f"₹{end:,.2f}", delta=f"{growth:.2f}%")
            st.line_chart(sensex["Close"], height=160)
        else:
            st.warning("SENSEX data unavailable.")
        st.markdown('</div>', unsafe_allow_html=True)

    # Latest News Scrollable
    with col3:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("📰 Latest Business Headlines")
        news = fetch_news("business", 10)
        if news:
            st.markdown('<div class="scroll-box">', unsafe_allow_html=True)
            for n in news:
                title = n.get("title", "")
                source = n.get("source", {}).get("name", "")
                st.markdown(f"• **{title}**  \n🗞️ {source}")
                st.markdown("---")
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("No latest news found.")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("📄 NSE Snapshot (Sample)")
    df = fetch_nse_data()
    if not df.empty:
        df["pChange"] = pd.to_numeric(df["pChange"], errors="coerce").round(2)
        st.dataframe(df.head(30), use_container_width=True)
    else:
        st.info("NSE data currently unavailable.")

# ==============================
# Other Pages stay the same
# ==============================

elif page == "🔎 Stock Search":
    st.header("🔍 Stock Search & Chart")
    symbol = st.text_input("Enter NSE symbol (e.g., RELIANCE.NS, TCS.NS)", "RELIANCE.NS")
    period = st.selectbox("Select timeframe", ["5d", "1mo", "3mo", "6mo", "1y"], index=1)

    if st.button("Show Data"):
        data = get_stock_data(symbol, period)
        if data.empty:
            st.error("Data not found. Try another stock symbol.")
        else:
            start, end = data["Close"].iloc[0], data["Close"].iloc[-1]
            growth = ((end - start) / start) * 100
            st.metric("Growth", f"{growth:.2f}%")
            st.line_chart(data["Close"], height=350)
            st.dataframe(data.tail(), use_container_width=True)

elif page == "🚀 Top Movers":
    st.header("🚀 Top Gainers & Losers (NSE)")
    df = fetch_nse_data()
    if df.empty:
        st.info("NSE data not available.")
    else:
        df["pChange"] = pd.to_numeric(df["pChange"], errors="coerce")
        gainers = df.sort_values("pChange", ascending=False).head(10)
        losers = df.sort_values("pChange", ascending=True).head(10)

        c1, c2 = st.columns(2)
        with c1:
            st.subheader("🏆 Top Gainers")
            st.dataframe(gainers.reset_index(drop=True), use_container_width=True)
        with c2:
            st.subheader("📉 Top Losers")
            st.dataframe(losers.reset_index(drop=True), use_container_width=True)

elif page == "📰 Latest News":
    st.header("📰 Latest Business News")
    num = st.slider("Number of Articles", 3, 12, 6)
    if st.button("Load News"):
        articles = fetch_news("business", num)
        if not articles:
            st.warning("No news available (API limit).")
        for i, art in enumerate(articles, start=1):
            st.markdown(f"### {i}. [{art.get('title')}]({art.get('url')})")
            if art.get("urlToImage"):
                st.image(art["urlToImage"], use_column_width=True)
            st.caption(f"{art.get('source',{}).get('name','')} | {art.get('publishedAt','')[:19].replace('T',' ')}")
            st.write(art.get("description", ""))
            st.write("---")

elif page == "💬 Sentiment":
    st.header("💬 Business News Sentiment")
    if st.button("Analyze"):
        articles = fetch_news("business", 8)
        if not articles:
            st.info("No headlines found.")
        else:
            for a in articles:
                title = a.get("title", "")
                sentiment = sentiment_label(title)
                st.markdown(f"- {sentiment}: {title}")

else:
    st.header("ℹ️ About")
    st.markdown("""
    ### Indian Market Dashboard  
    **Features:**  
    - Live NIFTY / SENSEX charts  
    - Stock search & growth tracking  
    - Top gainers/losers  
    - Business news with sentiment analysis  
    - Professional blue-dark interface  

    *Powered by Streamlit · Data from Yahoo Finance & NewsAPI*
    """)
