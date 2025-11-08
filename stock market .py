import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import date, timedelta
from textblob import TextBlob

st.set_page_config(page_title='MarketMate – Dark Dashboard', layout='wide', initial_sidebar_state='expanded')

st.markdown("""
<style>
[data-testid="stAppViewContainer"] {background-color:#0b0c10;color:#e6eef8;}
[data-testid="stHeader"]{visibility:hidden}
[data-testid="stToolbar"]{visibility:hidden}
.block-container{background-color:#0b0c10;}
.stButton>button{background-color:#1e293b;color:#e6eef8;border-radius:8px;}
.stDownloadButton>button{background-color:#0b64a0;}
.stDataFrame, .stTable td, .stTable th{background-color:#071018;color:#e6eef8}
.small{color:#9aa4b2}
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=3600)
def get_data(ticker, start, end, interval):
    df = yf.download(ticker, start=start, end=end, interval=interval)
    df.reset_index(inplace=True)
    return df

def sma(series, window):
    return series.rolling(window=window).mean()

def ema(series, span):
    return series.ewm(span=span, adjust=False).mean()

def plot_price(df, ticker, sma_windows, ema_windows):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['Date'], y=df['Close'], name=f'{ticker} Close', line=dict(width=2)))
    for w in sma_windows:
        fig.add_trace(go.Scatter(x=df['Date'], y=sma(df['Close'], w), name=f'SMA {w}', line=dict(dash='dot')))
    for w in ema_windows:
        fig.add_trace(go.Scatter(x=df['Date'], y=ema(df['Close'], w), name=f'EMA {w}', line=dict(dash='dash')))
    fig.update_layout(template='plotly_dark', margin=dict(l=10, r=10, t=40, b=10), height=420)
    return fig

def plot_volume(df):
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df['Date'], y=df['Volume'], name='Volume'))
    fig.update_layout(template='plotly_dark', margin=dict(l=10, r=10, t=10, b=10), height=200)
    return fig

def plot_candlestick(df):
    fig = go.Figure(data=[go.Candlestick(x=df['Date'], open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
    fig.update_layout(template='plotly_dark', margin=dict(l=10, r=10, t=40, b=10), height=520)
    return fig

st.sidebar.markdown('## ⚫ MarketMate – Dark Dashboard')
ticker = st.sidebar.text_input('Enter Ticker', 'AAPL').upper()
compare_ticker = st.sidebar.text_input('Compare With (Optional)', '').upper()
start_date = st.sidebar.date_input('Start Date', date.today() - timedelta(days=365))
end_date = st.sidebar.date_input('End Date', date.today())
interval = st.sidebar.selectbox('Interval', ['1d','1wk','1mo','60m','30m','15m'])
sma_list = st.sidebar.text_input('SMA (comma separated)', '20,50')
ema_list = st.sidebar.text_input('EMA (comma separated)', '12,26')

st.markdown("<h1 style='color:#e6eef8'>MarketMate – Dark Stock Dashboard</h1>", unsafe_allow_html=True)
st.markdown("<p class='small'>Interactive charts, analytics, and sentiment tracking</p>", unsafe_allow_html=True)

if ticker:
    df = get_data(ticker, start_date, end_date + timedelta(days=1), interval)
    if df.empty:
        st.error('No data found for this symbol.')
    else:
        st.subheader(f'{ticker} Stock Overview')
        last_price = df['Close'].iloc[-1]
        first_price = df['Close'].iloc[0]
        change = last_price - first_price
        pct = (change / first_price) * 100
        col1, col2, col3 = st.columns
