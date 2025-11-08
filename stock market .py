import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import date, datetime, timedelta
import io

# optional sentiment
try:
    from textblob import TextBlob
    TEXTBLOB_AVAILABLE = True
except Exception:
    TEXTBLOB_AVAILABLE = False

# -------------------- Page config --------------------
st.set_page_config(page_title='MarketMate — Dark Dashboard', layout='wide', initial_sidebar_state='expanded')

# -------------------- Custom dark CSS --------------------
DARK_CSS = r"""
<style>
/* Backgrounds */
[data-testid="stAppViewContainer"] {
  background-color: #0b0c10;
  color: #e6eef8;
}
[data-testid="stHeader"]{visibility:hidden}
[data-testid="stToolbar"]{visibility:hidden}
.stApp, .block-container {
  background-color: #0b0c10;
}
/* Sidebar */
.css-1d391kg {background-color: #070708 !important;}
/* Card backgrounds */
.css-1v3fvcr {background-color: #0b0c10 !important;}
/* Widget labels */
.st-bf {color: #c9d1d9}
/* Buttons */
.stButton>button{
  background-color:#1e293b;
  color:#e6eef8;
  border-radius: 8px;
}
.stDownloadButton>button{background-color:#0b64a0}
/* Metrics */
.card-title, .card-value{color:#e6eef8}
/* Small print */
.small {color:#9aa4b2}

/* Make tables have dark background */
.stDataFrame, .stTable td, .stTable th {background-color: #071018; color: #e6eef8}

/* Improve spacing */
.css-1lcbmhc {padding: 1rem 1rem 1rem 1rem}
</style>
"""

st.markdown(DARK_CSS, unsafe_allow_html=True)

# -------------------- Helpers --------------------
@st.cache_data(ttl=60*60)
def fetch_ticker_data(ticker: str, start: str, end: str, interval: str):
    t = yf.Ticker(ticker)
    df = t.history(start=start, end=end, interval=interval, actions=False)
    if df is None or df.empty:
        return pd.DataFrame()
    df = df.reset_index()
    df.columns = [c.lower().replace(' ', '_') for c in df.columns]
    return df

@st.cache_data(ttl=60*60)
def get_info(ticker: str):
    t = yf.Ticker(ticker)
    try:
        return t.info
    except Exception:
        return {}


def sma(series, window):
    return series.rolling(window=window).mean()

def ema(series, span):
    return series.ewm(span=span, adjust=False).mean()


def plot_price(df, ticker, indicators, template='plotly_dark'):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['date'], y=df['close'], name=f'{ticker} Close', mode='lines', line={'width':2}))
    if indicators.get('SMA'):
        for w in indicators['SMA']:
            fig.add_trace(go.Scatter(x=df['date'], y=sma(df['close'], w), name=f'SMA {w}', line={'dash':'dot'}))
    if indicators.get('EMA'):
        for w in indicators['EMA']:
            fig.add_trace(go.Scatter(x=df['date'], y=ema(df['close'], w), name=f'EMA {w}', line={'dash':'dash'}))
    fig.update_layout(margin=dict(l=10,r=10,t=40,b=10), height=420, xaxis_title='Date', yaxis_title='Price', template=template, legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))
    return fig


def plot_volume(df, ticker, template='plotly_dark'):
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df['date'], y=df['volume'], name='Volume'))
    fig.update_layout(margin=dict(l=10,r=10,t=10,b=10), height=220, xaxis_title='Date', yaxis_title='Volume', template=template)
    return fig


def plot_candlestick(df, ticker, template='plotly_dark'):
    fig = go.Figure(data=[go.Candlestick(x=df['date'], open=df['open'], high=df['high'], low=df['low'], close=df['close'], name='Candlestick')])
    fig.update_layout(margin=dict(l=10,r=10,t=40,b=10), height=520, template=template)
    return fig


def sentiment_text(text: str):
    if not TEXTBLOB_AVAILABLE:
        return None
    tb = TextBlob(text)
    return tb.sentiment.polarity

# -------------------- Layout / Controls --------------------
st.sidebar.markdown('# ⚫ MarketMate — Dark')
st.sidebar.write('Professional dashboard — black theme')

default_ticker = st.sidebar.text_input('Ticker symbol (e.g. AAPL, INFY.NS)', value='AAPL')
compare_ticker = st.sidebar.text_input('Compare with (optional)', value='')

today = date.today()
default_start = today - timedelta(days=365)
start_date = st.sidebar.date_input('Start date', default_start)
end_date = st.sidebar.date_input('End date', today)
interval = st.sidebar.selectbox('Interval', options=['1d','1wk','1mo','60m','30m','15m'], index=0)

show_sma = st.sidebar.checkbox('Show SMA', value=True)
show_ema = st.sidebar.checkbox('Show EMA', value=False)
sma_windows = st.sidebar.text_input('SMA windows (comma separated)', value='20,50')
ema_windows = st.sidebar.text_input('EMA windows (comma separated)', value='12,26')

st.sidebar.markdown('---')
# Watchlist
if 'watchlist' not in st.session_state:
    st.session_state['watchlist'] = ['AAPL','MSFT','GOOGL']

st.sidebar.write('### Watchlist')
new_w = st.sidebar.text_input('Add symbol to watchlist', '')
if st.sidebar.button('Add') and new_w:
    sym = new_w.strip().upper()
    if sym not in st.session_state['watchlist']:
        st.session_state['watchlist'].append(sym)

for s in st.session_state['watchlist']:
    st.sidebar.write(f'- {s}')

st.sidebar.markdown('---')
# Alerts
if 'alerts' not in st.session_state:
    st.session_state['alerts'] = []
alert_symbol = st.sidebar.text_input('Alert symbol', '')
alert_price = st.sidebar.number_input('Alert price', value=0.0, format='%f')
if st.sidebar.button('Set alert') and alert_symbol and alert_price>0:
    st.session_state['alerts'].append({'symbol': alert_symbol.upper(), 'price': alert_price})
    st.sidebar.success('Alert set (session only)')

st.sidebar.markdown('---')
# Quick examples
st.sidebar.write('Quick examples')
if st.sidebar.button('Load: INFY.NS'):
    default_ticker = 'INFY.NS'
if st.sidebar.button('Load: NIFTY50 ETF'):
    default_ticker = '^NSEI'

st.sidebar.markdown('---')
st.sidebar.write('Theme: Dark • Professional • Minimal')

# -------------------- Header --------------------
col1, col2 = st.columns([3,1])
with col1:
    st.markdown("# <span style='color:#e6eef8'>MarketMate — Dark Dashboard</span>", unsafe_allow_html=True)
    st.markdown("<div class='small'>Interactive stock explorer with charts, indicators, watchlist and portfolio tools.</div>", unsafe_allow_html=True)
with col2:
    st.image('https://raw.githubusercontent.com/plotly/datasets/master/logo.png', width=80)

st.markdown('---')

# -------------------- Main functionality --------------------
query_col, action_col = st.columns([3,1])
with query_col:
    ticker = st.text_input('Ticker to analyze', value=default_ticker).strip().upper()
with action_col:
    if st.button('Search'):
        pass

# We allow Search by either pressing Search or if ticker is prefilled
if ticker:
    df = fetch_ticker_data(ticker, start_date.isoformat(), (end_date + timedelta(days=1)).isoformat(), interval)
    if df.empty:
        st.error(f'No data found for {ticker}. Check the symbol and interval.')
    else:
        info = get_info(ticker)
        # Top metrics
        last_close = df['close'].iloc[-1]
        prev_close = info.get('previousClose', None)
        market_cap = info.get('marketCap', 'N/A')
        high_52 = info.get('fiftyTwoWeekHigh', 'N/A')
        low_52 = info.get('fiftyTwoWeekLow', 'N/A')

        mcol1, mcol2, mcol3, mcol4 = st.columns(4)
        mcol1.metric('Last Price', f"{last_close:.2f}")
        try:
            change = last_close - prev_close if prev_close else 0
            pct = (change/prev_close*100) if prev_close else 0
            mcol2.metric('Change', f"{change:.2f}", f"{pct:.2f}%")
        except Exception:
            mcol2.metric('Change', 'N/A')
        mcol3.metric('Market Cap', market_cap)
        mcol4.metric('52W H / L', f"{high_52} / {low_52}")

        # Indicators parse
        indicators = {'SMA': [], 'EMA': []}
        try:
            if show_sma:
                indicators['SMA'] = [int(x) for x in sma_windows.split(',') if x.strip().isdigit()]
            if show_ema:
                indicators['EMA'] = [int(x) for x in ema_windows.split(',') if x.strip().isdigit()]
        except Exception:
            indicators = {'SMA': [], 'EMA': []}

        # Charts
        st.markdown('### Price chart')
        st.plotly_chart(plot_price(df, ticker, indicators), use_container_width=True)

        st.markdown('### Volume')
        st.plotly_chart(plot_volume(df, ticker), use_container_width=True)

        if st.checkbox('Show candlestick chart'):
            st.plotly_chart(plot_candlestick(df, ticker), use_container_width=True)

        # Compare
        if compare_ticker.strip():
            compare = compare_ticker.strip().upper()
            df2 = fetch_ticker_data(compare, start_date.isoformat(), (end_date + timedelta(days=1)).isoformat(), interval)
            if df2.empty:
                st.warning('No data for compare ticker')
            else:
                merged = pd.merge(df[['date','close']].rename(columns={'close':ticker}), df2[['date','close']].rename(columns={'close':compare}), on='date', how='inner')
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=merged['date'], y=merged[ticker], name=ticker))
                fig.add_trace(go.Scatter(x=merged['date'], y=merged[compare], name=compare))
                fig.update_layout(title='Comparison: Close prices', template='plotly_dark', height=420)
                st.plotly_chart(fig, use_container_width=True)

        # Quick analytics
        st.markdown('### Quick analytics')
        returns = df['close'].pct_change().dropna()
        c1, c2, c3 = st.columns(3)
        period_return = (df['close'].iloc[-1]/df['close'].iloc[0]-1)*100 if len(df)>1 else 0
        c1.metric('Period Return', f"{period_return:.2f}%")
        c2.metric('Volatility (Ann.)', f"{returns.std()*np.sqrt(252)*100:.2f}%")
        c3.metric('Avg Volume', f"{int(df['volume'].mean())}")

        # News & sentiment
        st.markdown('---')
        st.subheader('News & Sentiment')
        t = yf.Ticker(ticker)
        news_items = []
        try:
            news_items = t.news
        except Exception:
            news_items = []
        if news_items:
            for n in news_items[:8]:
                title = n.get('title') or n.get('headline') or str(n)
                if TEXTBLOB_AVAILABLE:
                    score = sentiment_text(title)
                    st.write(f"- {title} — sentiment: {score:.2f}")
                else:
                    st.write(f"- {title}")
        else:
            st.write('No news fetched. To enable richer news, integrate NewsAPI / Finnhub.')

        # Portfolio Simulator
        st.markdown('---')
        st.subheader('Portfolio Simulator (session-only)')
        if 'trades' not in st.session_state:
            st.session_state['trades'] = []
        with st.form('trade_form'):
            col_a, col_b, col_c = st.columns([1,1,2])
            with col_a:
                buy_sell = st.selectbox('Type', ['Buy','Sell'])
                qty = st.number_input('Quantity', min_value=1, value=1)
            with col_b:
                price = st.number_input('Price per share (0 = last close)', value=0.0)
            with col_c:
                notes = st.text_input('Notes')
            submitted = st.form_submit_button('Add trade')
            if submitted:
                trade_price = price if price>0 else float(df['close'].iloc[-1])
                st.session_state['trades'].append({'symbol':ticker, 'type':buy_sell, 'qty':int(qty), 'price':float(trade_price), 'notes':notes, 'date':datetime.now().isoformat()})
                st.success('Trade added (session only)')
        if st.session_state['trades']:
            trades_df = pd.DataFrame(st.session_state['trades'])
            st.dataframe(trades_df)

        # Data download
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button('Download historical data (CSV)', csv, file_name=f'{ticker}_{start_date}_{end_date}.csv')

        # Alerts check
        if st.session_state['alerts']:
            for a in st.session_state['alerts']:
                if a['symbol'] == ticker and df['close'].iloc[-1] >= a['price']:
                    st.balloons()
                    st.warning(f"Alert: {ticker} >= {a['price']} (now {df['close'].iloc[-1]:.2f})")

# -------------------- Footer / Feature ideas --------------------
st.markdown('---')
st.header('Next steps & Pro features')
st.write('- Add user authentication + persistent DB (Supabase, Firebase, PostgreSQL)')
st.write('- Real-time quotes & websockets for streaming prices')
st.write('- Backtester & strategy builder (SMA crossover, RSI, MACD)')
st.write('- Options chain viewer and Greeks')
st.write('- Export printable PDF reports and chart snapshots')

st.info('To deploy: push this file and a requirements.txt to GitHub, then connect the repo to Streamlit Community Cloud.')

# End of file
