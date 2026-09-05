import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# -----------------------------------------------------------------------------
# PAGE CONFIGURATION
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Quantitative Trading Dashboard",
    page_icon="📈",
    layout="wide"
)

st.title("📈 Quantitative Trading Dashboard")
st.markdown("Real-time technical analysis, interactive charting, and automated signal detection for Indian markets.")

# -----------------------------------------------------------------------------
# SIDEBAR CONTROL PANEL
# -----------------------------------------------------------------------------
st.sidebar.header("Configuration Panel")

ticker_options = {
    "Nifty 50 Index": "^NSEI",
    "Bank Nifty Index": "^NSEBANK",
    "Reliance Industries": "RELIANCE.NS",
    "Tata Consultancy Services": "TCS.NS",
    "HDFC Bank": "HDFCBANK.NS",
    "Infosys": "INFY.NS",
    "ICICI Bank": "ICICIBANK.NS",
    "Tata Steel": "TATASTEEL.NS",
    "State Bank of India": "SBIN.NS",
    "Custom Ticker...": "CUSTOM"
}

selected_label = st.sidebar.selectbox("Select Asset / Ticker", list(ticker_options.keys()))

if ticker_options[selected_label] == "CUSTOM":
    ticker_symbol = st.sidebar.text_input("Enter NSE Ticker (e.g., WIPRO.NS):", value="WIPRO.NS").upper()
else:
    ticker_symbol = ticker_options[selected_label]

st.sidebar.markdown("---")
st.sidebar.info("Data fetched dynamically via Yahoo Finance (`yfinance`). Ensure Yahoo ticker suffixes are included (`.NS` for NSE).")

# -----------------------------------------------------------------------------
# TECHNICAL INDICATORS CALCULATIONS
# -----------------------------------------------------------------------------
def calculate_indicators(df):
    """Calculates 20 EMA, Approximate Daily VWAP, and 14-period RSI."""
    # 1. Exponential Moving Average (20-period)
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()

    # 2. Approximate Daily VWAP (Typical Price * Volume / Cumulative Volume)
    typical_price = (df['High'] + df['Low'] + df['Close']) / 3
    df['VWAP'] = (typical_price * df['Volume']).cumsum() / df['Volume'].cumsum()

    # 3. Relative Strength Index (RSI - 14 period)
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    # 4. Generate Signal Logic
    # BUY: RSI < 30 and Price > 20 EMA
    # SELL: RSI > 70
    # NEUTRAL: Otherwise
    conditions = [
        (df['RSI'] < 30) & (df['Close'] > df['EMA20']),
        (df['RSI'] > 70)
    ]
    choices = ['BUY', 'SELL']
    df['Signal'] = np.select(conditions, choices, default='NEUTRAL')

    return df

# -----------------------------------------------------------------------------
# DATA RETRIEVAL
# -----------------------------------------------------------------------------
with st.spinner(f"Fetching data for {ticker_symbol}..."):
    try:
        data = yf.download(ticker_symbol, period="6m", interval="1d", progress=False)

        # Clean MultiIndex columns if returned by yfinance
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)

        if data.empty:
            st.error(f"No data returned for ticker '{ticker_symbol}'. Please verify the symbol.")
            st.stop()

        df = calculate_indicators(data.copy())

    except Exception as e:
        st.error(f"Error fetching data: {e}")
        st.stop()

# Get recent metrics
latest_row = df.iloc[-1]
latest_price = float(latest_row['Close'])
latest_rsi = float(latest_row['RSI'])
latest_signal = str(latest_row['Signal'])
latest_ema = float(latest_row['EMA20'])

# -----------------------------------------------------------------------------
# SIGNAL BOX & SUMMARY METRICS
# -----------------------------------------------------------------------------
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(label="Latest Close Price", value=f"₹{latest_price:,.2f}")

with col2:
    st.metric(label="20-Day EMA", value=f"₹{latest_ema:,.2f}")

with col3:
    st.metric(label="Current RSI (14)", value=f"{latest_rsi:.2f}")

with col4:
    if latest_signal == "BUY":
        st.markdown("<h3 style='color: green; text-align: center; margin-top: 10px;'>🟢 BUY</h3>", unsafe_allow_html=True)
    elif latest_signal == "SELL":
        st.markdown("<h3 style='color: red; text-align: center; margin-top: 10px;'>🔴 SELL</h3>", unsafe_allow_html=True)
    else:
        st.markdown("<h3 style='color: gray; text-align: center; margin-top: 10px;'>⚪ NEUTRAL</h3>", unsafe_allow_html=True)

st.markdown("---")

# -----------------------------------------------------------------------------
# INTERACTIVE CHART (PLOTLY)
# -----------------------------------------------------------------------------
st.subheader(f"Price Action & Indicators: {ticker_symbol}")

fig = go.Figure()

# Candlestick
fig.add_trace(go.Candlestick(
    x=df.index,
    open=df['Open'],
    high=df['High'],
    low=df['Low'],
    close=df['Close'],
    name='Price'
))

# 20 EMA
fig.add_trace(go.Scatter(
    x=df.index,
    y=df['EMA20'],
    mode='lines',
    name='20 EMA',
    line=dict(color='orange', width=1.5)
))

# VWAP
fig.add_trace(go.Scatter(
    x=df.index,
    y=df['VWAP'],
    mode='lines',
    name='Cumulative VWAP',
    line=dict(color='purple', width=1.5, dash='dash')
))

fig.update_layout(
    xaxis_rangeslider_visible=False,
    height=550,
    margin=dict(l=20, r=20, t=30, b=20),
    template="plotly_dark",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)

st.plotly_chart(fig, use_container_width=True)

# -----------------------------------------------------------------------------
# RECENT TRADING SIGNALS TABLE
# -----------------------------------------------------------------------------
st.subheader("10 Most Recent Trading Signals")

recent_signals_df = df[['Close', 'EMA20', 'VWAP', 'RSI', 'Signal']].tail(10).sort_index(ascending=False)
recent_signals_df.index = recent_signals_df.index.strftime('%Y-%m-%d')

# Highlight signals for better visibility
def highlight_signal(val):
    if val == 'BUY':
        return 'background-color: rgba(0, 255, 0, 0.2); color: green; font-weight: bold;'
    elif val == 'SELL':
        return 'background-color: rgba(255, 0, 0, 0.2); color: red; font-weight: bold;'
    return 'color: gray;'

styled_df = recent_signals_df.style.applymap(highlight_signal, subset=['Signal'])\
    .format({'Close': '₹{:.2f}', 'EMA20': '₹{:.2f}', 'VWAP': '₹{:.2f}', 'RSI': '{:.2f}'})

st.dataframe(styled_df, use_container_width=True)
