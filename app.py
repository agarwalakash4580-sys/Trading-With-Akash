import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from alpha_vantage.timeseries import TimeSeries

st.set_page_config(page_title="Quantitative Trading Dashboard", page_icon="📈", layout="wide")
st.title("📈 Quantitative Trading Dashboard")

st.sidebar.header("Configuration Panel")
api_key = st.sidebar.text_input("Enter Alpha Vantage API Key:", type="password")

ticker_options = {
    "Reliance Industries": "RELIANCE.BSE",
    "Tata Consultancy Services": "TCS.BSE",
    "HDFC Bank": "HDFCBANK.BSE",
    "Infosys": "INFY.BSE"
}

selected_label = st.sidebar.selectbox("Select Asset", list(ticker_options.keys()))
ticker_symbol = ticker_options[selected_label]

if not api_key:
    st.info("Please enter your free Alpha Vantage API Key in the sidebar to load chart data.")
    st.stop()

@st.cache_data(ttl=600)
def fetch_data(symbol, key):
    ts = TimeSeries(key=key, output_format='pandas')
    data, _ = ts.get_daily(symbol=symbol, outputsize='compact')
    data.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
    data.index = pd.to_datetime(data.index)
    return data.sort_index()

try:
    df = fetch_data(ticker_symbol, api_key)
    
    # Calculations
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    df['RSI'] = 100 - (100 / (1 + (gain / loss)))

    # Metrics Display
    latest = df.iloc[-1]
    c1, c2, c3 = st.columns(3)
    c1.metric("Close Price", f"₹{latest['Close']:.2f}")
    c2.metric("20 EMA", f"₹{latest['EMA20']:.2f}")
    c3.metric("RSI (14)", f"{latest['RSI']:.2f}")

    # Chart
    fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA20'], name="20 EMA", line=dict(color='orange')))
    fig.update_layout(template="plotly_dark", xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"Error fetching data: {e}")
