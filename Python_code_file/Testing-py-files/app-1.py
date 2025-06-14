import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objs as go
from plotly.subplots import make_subplots
from ta.trend import SMAIndicator, EMAIndicator, MACD
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands
import requests
from datetime import datetime, timedelta

# Set page config for responsive design
st.set_page_config(layout="wide", page_title="Stock Technical Analysis")

# Function to get currency based on stock exchange
def get_currency_and_symbol(ticker_info):
    exchange = ticker_info.get('exchange', '')
    country = ticker_info.get('country', '')
    
    currency_map = {
        'India': ('INR', '₹'),
        'United States': ('USD', '$'),
        'United Kingdom': ('GBP', '£'),
        'European Union': ('EUR', '€'),
        'Japan': ('JPY', '¥'),
        'China': ('CNY', '¥'),
        'Australia': ('AUD', 'A$')
    }
    
    if country in currency_map:
        return currency_map[country]
    elif 'NSE' in exchange or 'BSE' in exchange:
        return ('INR', '₹')
    else:
        return ('USD', '$')  # Default to USD

# Function to fetch stock data
def fetch_stock_data(ticker, period='1y'):
    stock = yf.Ticker(ticker)
    df = stock.history(period=period)
    return df, stock.info

# Function to calculate technical indicators
def calculate_indicators(df):
    # Simple Moving Average
    sma20 = SMAIndicator(close=df['Close'], window=20).sma_indicator()
    sma50 = SMAIndicator(close=df['Close'], window=50).sma_indicator()
    
    # Exponential Moving Average
    ema20 = EMAIndicator(close=df['Close'], window=20).ema_indicator()
    
    # RSI
    rsi = RSIIndicator(close=df['Close'], window=14).rsi()
    
    # MACD
    macd = MACD(close=df['Close'])
    macd_line = macd.macd()
    signal_line = macd.macd_signal()
    histogram = macd.macd_diff()
    
    # Bollinger Bands
    bb = BollingerBands(close=df['Close'], window=20, window_dev=2)
    bb_high = bb.bollinger_hband()
    bb_low = bb.bollinger_lband()
    bb_mid = bb.bollinger_mavg()
    
    return pd.DataFrame({
        'SMA20': sma20,
        'SMA50': sma50,
        'EMA20': ema20,
        'RSI': rsi,
        'MACD': macd_line,
        'Signal': signal_line,
        'Histogram': histogram,
        'BB_High': bb_high,
        'BB_Low': bb_low,
        'BB_Mid': bb_mid
    }, index=df.index)

# Function to create plotly chart
def create_chart(df, indicators, ticker, currency_symbol):
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, 
                       vertical_spacing=0.05, 
                       subplot_titles=(f'{ticker} Price and Indicators', 'RSI', 'MACD'),
                       row_heights=[0.5, 0.2, 0.3])
    
    # Candlestick
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name='Price'
    ), row=1, col=1)
    
    # Moving Averages
    fig.add_trace(go.Scatter(x=df.index, y=indicators['SMA20'], name='SMA20', line=dict(color='blue')), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=indicators['SMA50'], name='SMA50', line=dict(color='orange')), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=indicators['EMA20'], name='EMA20', line=dict(color='purple')), row=1, col=1)
    
    # Bollinger Bands
    fig.add_trace(go.Scatter(x=df.index, y=indicators['BB_High'], name='BB High', line=dict(color='gray', dash='dash')), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=indicators['BB_Low'], name='BB Low', line=dict(color='gray', dash='dash')), row=1, col=1)
    
    # RSI
    fig.add_trace(go.Scatter(x=df.index, y=indicators['RSI'], name='RSI', line=dict(color='green')), row=2, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="red", row=2, col=1)
    
    # MACD
    fig.add_trace(go.Scatter(x=df.index, y=indicators['MACD'], name='MACD', line=dict(color='blue')), row=3, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=indicators['Signal'], name='Signal', line=dict(color='orange')), row=3, col=1)
    fig.add_trace(go.Bar(x=df.index, y=indicators['Histogram'], name='Histogram', marker_color='gray'), row=3, col=1)
    
    # Update layout
    fig.update_layout(
        height=800,
        showlegend=True,
        template='plotly_dark',
        xaxis_rangeslider_visible=False,
        yaxis_title=f'Price ({currency_symbol})',
        yaxis2_title='RSI',
        yaxis3_title='MACD'
    )
    
    return fig

# Streamlit app
def main():
    st.title("Stock Technical Analysis")
    
    # Sidebar for inputs
    with st.sidebar:
        st.header("Stock Selection")
        ticker = st.text_input("Enter Stock Ticker (e.g., RELIANCE.NS for Reliance Industries)", value="RELIANCE.NS")
        period = st.selectbox("Select Time Period", ['1mo', '3mo', '6mo', '1y', '2y', '5y'], index=3)
        analyze = st.button("Analyze")
    
    if analyze and ticker:
        try:
            with st.spinner("Fetching data..."):
                # Fetch data
                df, info = fetch_stock_data(ticker, period)
                
                if df.empty:
                    st.error("No data found for the given ticker.")
                    return
                
                # Get currency
                currency, currency_symbol = get_currency_and_symbol(info)
                
                # Calculate indicators
                indicators = calculate_indicators(df)
                
                # Create two columns for responsive layout
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    # Display chart
                    fig = create_chart(df, indicators, ticker, currency_symbol)
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    # Display stock info
                    st.subheader("Stock Information")
                    st.write(f"**Company**: {info.get('longName', 'N/A')}")
                    st.write(f"**Exchange**: {info.get('exchange', 'N/A')}")
                    st.write(f"**Currency**: {currency} ({currency_symbol})")
                    st.write(f"**Current Price**: {currency_symbol}{df['Close'][-1]:.2f}")
                    st.write(f"**52 Week High**: {currency_symbol}{info.get('fiftyTwoWeekHigh', 'N/A')}")
                    st.write(f"**52 Week Low**: {currency_symbol}{info.get('fiftyTwoWeekLow', 'N/A')}")
                    
                    # Summary statistics
                    st.subheader("Summary Statistics")
                    st.write(f"**Average Price**: {currency_symbol}{df['Close'].mean():.2f}")
                    st.write(f"**Volatility**: {currency_symbol}{df['Close'].std():.2f}")
                    st.write(f"**Latest RSI**: {indicators['RSI'][-1]:.2f}")
        
        except Exception as e:
            st.error(f"Error: {str(e)}")
    
    # Instructions
    st.markdown("""
    ### Instructions
    - Enter a stock ticker (e.g., RELIANCE.NS for Indian stocks, AAPL for US stocks)
    - Select a time period for analysis
    - Click 'Analyze' to view technical indicators
    - The app automatically detects the currency based on the stock's exchange
    """)

if __name__ == "__main__":
    main()
