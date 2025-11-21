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
# Theme: Green + Blue (Professional)
# ==============================
st.markdown("""
    <style>
        /* Background */
        [data-testid="stAppViewContainer"] {
            background: linear-gradient(135deg, #0f2b1d 0%, #0b3f60 100%);
            color: #EAF6F4;
        }
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0a2c1e 0%, #0c3c54 100%);
            color: #EAF6F4;
        }
        h1, h2, h3, h4 {
            color: #3cd28c !important;
            font-weight: 700;
        }
        .stButton>button {
            background-color: #3cd28c !important;
            color: #0f2b1d !important;
            border-radius: 8px;
            font-weight: 700;
            transition: 0.3s;
        }
        .stButton>button:hover {
            background-color: #5decab !important;
            transform: scale(1.03);
        }
        .card {
            background: rgba(255,255,255,0.05);
            border-radius: 12px;
            padding: 18px;
            margin-bottom: 16px;
            box-shadow: 0 8px 24px rgba(0,0,0,0.35);
        }
        [data-testid="stMetricValue"] { color: #3cd28c !important; font-weight: 700; }
        [data-testid="stMetricLabel"] { color: #EAF6F4 !important; }
        .scroll-box {
            max-height: 320px;
            overflow-y: auto;
            padding-right: 10px;
        }
        .scroll-box::-webkit-scrollbar {
            width: 6px;
        }
        .scroll-box::-webkit-scrollbar-thumb {
            background-color: #3cd28c;
            border-radius: 3px;
        }
    </style>
""", unsafe_allow_html=True)

# ==============================
# Header
# ==============================
st.title("📈 Indian Market Dashboard")
st.write("Live Market Overview • Stock Analysis • Top Movers • Business News • Sentiment Insights")

# ==============================
# Primary & Backup News API Keys
# ==============================
PRIMARY_NEWS_API_KEY = "a9b91dc9740c491ab00c7b79d40486e4"
BACKUP_NEWS_API_KEY = "YOUR_NEWDATA_IO_KEY"  # replace with your NewsData.io key or another backup

# ==============================
# Helper functions
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
    # Try primary key
    url1 = f"https://newsapi.org/v2/top-headlines?country=in&category={category}&apiKey={PRIMARY_NEWS_API_KEY}&pageSize={num_articles}"
    try:
        r1 = requests.get(url1, timeout=10)
        if r1.status_code == 200:
            return r1.json().get("articles", [])
    except Exception:
        pass
    # Try backup key
    if BACKUP_NEWS_API_KEY:
        url2 = f"https://newsdata.io/api/1/news?country=in&category={category}&apikey={BACKUP_NEWS_API_KEY}&page_size={num_articles}"
        try:
            r2 = requests.get(url2, timeout=10)
            if r2.status_code == 200:
                result = r2.json().get("results", [])
                # Normalize to our structure
                articles = []
                for item in result:
                    articles.append({
                        "title": item.get("title"),
                        "url": item.get("link"),
                        "urlToImage": item.get("image_url"),
                        "source": {"name": item.get("source_id")},
                        "publishedAt": item.get("pubDate"),
                        "description": item.get("description")
                    })
                return articles
        except Exception:
            pass
    return []

def get_stock_data(symbol, period="1mo"):
    try:
        df = yf.Ticker(symbol).history(period=period)
        return df
    except Exception:
        return pd.DataFrame()

def sentiment_label(text):
    try:
        score = TextBlob(text).sentiment.polarity
        if score > 0.1:
            return "🟢 Positive"
        elif score < -0.1:
            return "🔴 Negative"
        else:
            return "⚪ Neutral"
    except Exception:
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
    )
)

# ==============================
# Dashboard Page
# ==============================
if page == "🏠 Dashboard":
    st.header("📊 Indian Market Overview")

    col1, col2, col3 = st.columns([1.2,1.2,1.6])

    nifty = get_stock_data("^NSEI", "1mo")
    sensex = get_stock_data("^BSESN", "1mo")

    # NIFTY card
    with col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("📊 NIFTY 50")
        if not nifty.empty:
            start = nifty["Close"].iloc[0]
            end = nifty["Close"].iloc[-1]
            growth = ((end-start)/start)*100
            st.metric("Value", f"₹{end:,.2f}", delta=f"{growth:.2f}%")
            st.line_chart(nifty["Close"], height=160)
        else:
            st.warning("NIFTY data unavailable.")
        st.markdown('</div>', unsafe_allow_html=True)

    # SENSEX card
    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("📈 SENSEX")
        if not sensex.empty:
            start = sensex["Close"].iloc[0]
            end = sensex["Close"].iloc[-1]
            growth = ((end-start)/start)*100
            st.metric("Value", f"₹{end:,.2f}", delta=f"{growth:.2f}%")
            st.line_chart(sensex["Close"], height=160)
        else:
            st.warning("SENSEX data unavailable.")
        st.markdown('</div>', unsafe_allow_html=True)

    # News panel
    with col3:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("📰 Latest Business Headlines")
        news = fetch_news("business", 10)
        if news:
            st.markdown('<div class="scroll-box">', unsafe_allow_html=True)
            for n in news:
                title = n.get("title", "")
                src = n.get("source", {}).get("name", "")
                st.markdown(f"• **{title}**  \n🗞️ {src}")
                st.markdown("---")
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("News currently unavailable.")
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
# Stock Search Page
# ==============================
elif page == "🔎 Stock Search":
    st.header("🔍 Stock Search & Chart")
    symbol = st.text_input("Enter NSE symbol (e.g., RELIANCE.NS)", "RELIANCE.NS")
    period = st.selectbox("Select timeframe", ["5d","1mo","3mo","6mo","1y"], index=1)

    if st.button("Show Data"):
        data = get_stock_data(symbol, period)
        if data.empty:
            st.error("Data not found. Try another stock symbol.")
        else:
            start = data["Close"].iloc[0]
            end = data["Close"].iloc[-1]
            growth = ((end-start)/start)*100
            st.metric("Growth", f"{growth:.2f}%")
            st.line_chart(data["Close"], height=350)
            st.dataframe(data.tail(), use_container_width=True)

# ==============================
# Top Movers Page
# ==============================
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

# ==============================
# Latest News Page
# ==============================
elif page == "📰 Latest News":
    st.header("📰 Latest Business News")
    num = st.slider("Number of Articles", 3, 12, 6)
    if st.button("Load News"):
        articles = fetch_news("business", num)
        if not articles:
            st.warning("News unavailable (API might be blocked).")
        else:
            for i, art in enumerate(articles, start=1):
                title = art.get("title", "No title")
                url = art.get("url", "#")
                img = art.get("urlToImage")
                src = art.get("source", {}).get("name", "")
                date = art.get("publishedAt", "")[:19].replace("T", " ")
                desc = art.get("description", "")
                st.markdown(f"### {i}. [{title}]({url})")
                if img:
                    st.image(img, use_column_width=True)
                st.caption(f"{src} | {date}")
                st.write(desc)
                st.write("---")

# ==============================
# Sentiment Page
# ==============================
elif page == "💬 Sentiment":
    st.header("💬 Business News Sentiment")
    if st.button("Analyze"):
        arts = fetch_news("business", 8)
        if not arts:
            st.info("No headlines found.")
        else:
            for a in arts:
                title = a.get("title", "")
                lbl = sentiment_label(title)
                st.markdown(f"- {lbl}: {title}")

# ==============================
# About Page
# ==============================
else:
    st.header("ℹ️ About")
    st.markdown("""
    ### Indian Market Dashboard  
    Features:
    - Live NIFTY / SENSEX performance  
    - Stock search with growth tracking  
    - Top gainers & losers  
    - Business news with sentiment  
    - Professional green-blue theme  

    Notes:
    - Some NSE APIs may be blocked; if so, use manual symbol format (e.g., RELIANCE.NS).
    - Free news APIs often have request limits. Consider backup key for continuity.
    """)
