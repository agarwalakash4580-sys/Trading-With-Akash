import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from alpha_vantage.timeseries import TimeSeries

# -----------------------------------------------------------------------------
# PAGE & BRAND CONFIGURATION
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="ALPHA QUANT | Trading Terminal",
    page_icon="⚡",
    layout="wide"
)

# -----------------------------------------------------------------------------
# CUSTOM STYLING & ANIMATIONS (CSS)
# -----------------------------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Gradient Hero Text */
    .brand-header {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(90deg, #00F2FE 0%, #4FACFE 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: fadeIn 1.2s ease-in-out;
    }

    .brand-sub {
        color: #A0AEC0;
        font-size: 1rem;
        margin-bottom: 25px;
    }

    /* Glassmorphism Cards */
    .metric-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 18px;
        text-align: center;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
        transition: transform 0.3s ease, border-color 0.3s ease;
    }
    .metric-card:hover {
        transform: translateY(-3px);
        border-color: #00F2FE;
    }

    .metric-label {
        font-size: 0.85rem;
        color: #A0AEC0;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    .metric-value {
        font-size: 1.6rem;
        font-weight: 700;
        color: #FFFFFF;
        margin-top: 5px;
    }

    /* Pulsing Badge Animations */
    .badge-buy {
        background-color: rgba(0, 230, 118, 0.15);
        color: #00E676;
        border: 1px solid #00E676;
        padding: 6px 14px;
        border-radius: 20px;
        font-weight: 700;
        display: inline-block;
        animation: pulse-green 2s infinite;
    }

    .badge-sell {
        background-color: rgba(255, 23, 68, 0.15);
        color: #FF1744;
        border: 1px solid #FF1744;
        padding: 6px 14px;
        border-radius: 20px;
        font-weight: 700;
        display: inline-block;
        animation: pulse-red 2s infinite;
    }

    .badge-neutral {
        background-color: rgba(255, 255, 255, 0.1);
        color: #B0BEC5;
        border: 1px solid #B0BEC5;
        padding: 6px 14px;
        border-radius: 20px;
        font-weight: 700;
        display: inline-block;
    }

    @keyframes pulse-green {
        0% { box-shadow: 0 0 0 0 rgba(0, 230, 118, 0.4); }
        70% { box-shadow: 0 0 0 10px rgba(0, 230, 118, 0); }
        100% { box-shadow: 0 0 0 0 rgba(0, 230, 118, 0); }
    }

    @keyframes pulse-red {
        0% { box-shadow: 0 0 0 0 rgba(255, 23, 68, 0.4); }
        70% { box-shadow: 0 0 0 10px rgba(255, 23, 68, 0); }
        100% { box-shadow: 0 0 0 0 rgba(255, 23, 68, 0); }
    }

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(-10px); }
        to { opacity: 1; transform: translateY(0); }
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# HEADER & BRANDING
# -----------------------------------------------------------------------------
st.markdown('<div class="brand-header">⚡ ALPHA QUANT TERMINAL</div>', unsafe_allow_html=True)
st.markdown('<div class="brand-sub">Algorithmic Engine & Quantitative Analytics for Indian Equities & Indices</div>', unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# SIDEBAR CONTROLS
# -----------------------------------------------------------------------------
st.sidebar.header("🕹️ Terminal Controls")
api_key = st.sidebar.text_input("Alpha Vantage API Key", type="password", help="Enter your free API key from Alpha Vantage.")

# Combined Indices and Stocks Asset Directory
asset_directory = {
    "Indices": {
        "Nifty 50 Index": "NSEI",
        "Bank Nifty Index": "NSEBANK",
        "Nifty IT Index": "CNXIT"
    },
    "Equities (BSE/NSE)": {
        "HDFC Bank": "HDFCBANK.BSE",
        "Reliance Industries": "RELIANCE.BSE",
        "Tata Consultancy Services": "TCS.BSE",
        "Infosys": "INFY.BSE",
        "State Bank of India": "SBIN.BSE",
        "ICICI Bank": "ICICIBANK.BSE",
        "Custom Asset...": "CUSTOM"
    }
}

category = st.sidebar.radio("Asset Category", list(asset_directory.keys()))
selected_label = st.sidebar.selectbox("Select Asset", list(asset_directory[category].keys()))

if asset_directory[category][selected_label] == "CUSTOM":
    ticker_symbol = st.sidebar.text_input("Enter Ticker Code (e.g., WIPRO.BSE):", value="WIPRO.BSE").upper()
else:
    ticker_symbol = asset_directory[category][selected_label]

selected_strategy = st.sidebar.selectbox(
    "Select Quantitative Model", 
    ["EMA + RSI Mean Reversion", "Bollinger Bands Volatility Squeeze"]
)

st.sidebar.markdown("---")
st.sidebar.caption("Powered by Alpha Vantage Engine")

if not api_key:
    st.warning("⚠️ Please enter your Alpha Vantage API Key in the sidebar to activate the terminal.")
    st.stop()

# -----------------------------------------------------------------------------
# DATA RETRIEVAL ENGINE
# -----------------------------------------------------------------------------
@st.cache_data(ttl=600)
def fetch_market_data(symbol, key):
    ts = TimeSeries(key=key, output_format='pandas')
    data, _ = ts.get_daily(symbol=symbol, outputsize='compact')
    data.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
    data.index = pd.to_datetime(data.index)
    return data.sort_index()

with st.spinner(f"Processing algorithmic feeds for {ticker_symbol}..."):
    try:
        df = fetch_market_data(ticker_symbol, api_key)
    except Exception as e:
        st.error(f"Execution Error: {e}")
        st.stop()

# -----------------------------------------------------------------------------
# QUANTITATIVE STRATEGIES EVALUATOR
# -----------------------------------------------------------------------------
def apply_quant_strategies(data, strategy):
    df = data.copy()
    
    # Base Indicators
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['SMA50'] = df['Close'].rolling(window=50).mean()
    
    # RSI (14)
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    # Bollinger Bands
    df['BB_Middle'] = df['Close'].rolling(20).mean()
    std = df['Close'].rolling(20).std()
    df['BB_Upper'] = df['BB_Middle'] + (std * 2)
    df['BB_Lower'] = df['BB_Middle'] - (std * 2)

    if strategy == "EMA + RSI Mean Reversion":
        conditions = [
            (df['RSI'] < 35) & (df['Close'] > df['EMA20']),
            (df['RSI'] > 65) & (df['Close'] < df['EMA20'])
        ]
        choices = ['BUY', 'SELL']
        df['Signal'] = np.select(conditions, choices, default='NEUTRAL')
    
    elif strategy == "Bollinger Bands Volatility Squeeze":
        conditions = [
            (df['Close'] <= df['BB_Lower']),
            (df['Close'] >= df['BB_Upper'])
        ]
        choices = ['BUY', 'SELL']
        df['Signal'] = np.select(conditions, choices, default='NEUTRAL')

    return df

df = apply_quant_strategies(df, selected_strategy)
latest = df.iloc[-1]

# -----------------------------------------------------------------------------
# METRICS DASHBOARD
# -----------------------------------------------------------------------------
m1, m2, m3, m4 = st.columns(4)

with m1:
    st.markdown(f'''
        <div class="metric-card">
            <div class="metric-label">Close Price</div>
            <div class="metric-value">₹{latest['Close']:,.2f}</div>
        </div>
    ''', unsafe_allow_html=True)

with m2:
    st.markdown(f'''
        <div class="metric-card">
            <div class="metric-label">20-Day EMA</div>
            <div class="metric-value">₹{latest['EMA20']:,.2f}</div>
        </div>
    ''', unsafe_allow_html=True)

with m3:
    st.markdown(f'''
        <div class="metric-card">
            <div class="metric-label">RSI (14) Index</div>
            <div class="metric-value">{latest['RSI']:.2f}</div>
        </div>
    ''', unsafe_allow_html=True)

with m4:
    sig = latest['Signal']
    badge_class = "badge-buy" if sig == "BUY" else ("badge-sell" if sig == "SELL" else "badge-neutral")
    st.markdown(f'''
        <div class="metric-card">
            <div class="metric-label">Quant Signal</div>
            <div style="margin-top: 8px;"><span class="{badge_class}">{sig}</span></div>
        </div>
    ''', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# SUBPLOT CHARTS (CANDLESTICK + RSI)
# -----------------------------------------------------------------------------
fig = make_subplots(
    rows=2, cols=1, 
    shared_xaxes=True, 
    vertical_spacing=0.08, 
    row_heights=[0.75, 0.25]
)

# Candlesticks
fig.add_trace(go.Candlestick(
    x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
    name="Price"
), row=1, col=1)

# Overlays
fig.add_trace(go.Scatter(x=df.index, y=df['EMA20'], name="20 EMA", line=dict(color='#FF9F43', width=1.5)), row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df['SMA50'], name="50 SMA", line=dict(color='#00D2D3', width=1.5)), row=1, col=1)

if selected_strategy == "Bollinger Bands Volatility Squeeze":
    fig.add_trace(go.Scatter(x=df.index, y=df['BB_Upper'], name="Upper BB", line=dict(color='#54a0ff', width=1, dash='dash')), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['BB_Lower'], name="Lower BB", line=dict(color='#54a0ff', width=1, dash='dash')), row=1, col=1)

# RSI Oscillator
fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], name="RSI", line=dict(color='#5f27cd', width=1.5)), row=2, col=1)
fig.add_hline(y=70, line_dash="dash", line_color="#FF1744", row=2, col=1)
fig.add_hline(y=30, line_dash="dash", line_color="#00E676", row=2, col=1)

fig.update_layout(
    template="plotly_dark",
    height=600,
    margin=dict(l=20, r=20, t=30, b=20),
    xaxis_rangeslider_visible=False,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)

st.plotly_chart(fig, use_container_width=True)

# -----------------------------------------------------------------------------
# RECENT TRADING SIGNALS LOG
# -----------------------------------------------------------------------------
st.subheader("📜 Recent Signal Execution Logs")

log_df = df[['Close', 'EMA20', 'RSI', 'Signal']].tail(10).sort_index(ascending=False)
log_df.index = log_df.index.strftime('%Y-%m-%d')

def style_signal_table(val):
    if val == 'BUY':
        return 'background-color: rgba(0, 230, 118, 0.2); color: #00E676; font-weight: bold;'
    elif val == 'SELL':
        return 'background-color: rgba(255, 23, 68, 0.2); color: #FF1744; font-weight: bold;'
    return 'color: #B0BEC5;'

formatted_table = log_df.style.applymap(style_signal_table, subset=['Signal'])\
    .format({'Close': '₹{:.2f}', 'EMA20': '₹{:.2f}', 'RSI': '{:.2f}'})

st.dataframe(formatted_table, use_container_width=True)
