import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objs as go
from plotly.subplots import make_subplots
from ta.trend import SMAIndicator, EMAIndicator, MACD, IchimokuIndicator
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.volatility import BollingerBands, AverageTrueRange
from datetime import datetime, timedelta

# Set page config for responsive design
st.set_page_config(layout="wide", page_title="Advanced Stock Technical Analysis")

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
        return ('USD', '$')

# Function to fetch stock data
def fetch_stock_data(ticker, period='1y', interval='1d'):
    stock = yf.Ticker(ticker)
    df = stock.history(period=period, interval=interval)
    return df, stock.info

# Function to calculate advanced technical indicators
def calculate_indicators(df):
    # Moving Averages
    sma20 = SMAIndicator(close=df['Close'], window=20).sma_indicator()
    sma50 = SMAIndicator(close=df['Close'], window=50).sma_indicator()
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
    
    # Average True Range
    atr = AverageTrueRange(high=df['High'], low=df['Low'], close=df['Close'], window=14).average_true_range()
    
    # Stochastic Oscillator
    stoch = StochasticOscillator(high=df['High'], low=df['Low'], close=df['Close'], window=14, smooth_window=3)
    stoch_k = stoch.stoch()
    stoch_d = stoch.stoch_signal()
    
    # Ichimoku Cloud
    ichimoku = IchimokuIndicator(high=df['High'], low=df['Low'], window1=9, window2=26, window3=52)
    tenkan_sen = ichimoku.ichimoku_conversion_line()
    kijun_sen = ichimoku.ichimoku_base_line()
    senkou_span_a = ichimoku.ichimoku_a()
    senkou_span_b = ichimoku.ichimoku_b()
    
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
        'BB_Mid': bb_mid,
        'ATR': atr,
        'Stoch_K': stoch_k,
        'Stoch_D': stoch_d,
        'Tenkan_Sen': tenkan_sen,
        'Kijun_Sen': kijun_sen,
        'Senkou_Span_A': senkou_span_a,
        'Senkou_Span_B': senkou_span_b
    }, index=df.index)

# Function to generate buy/sell recommendation
def generate_recommendation(df, indicators):
    score = 0
    signals = []
    
    # RSI Signal
    latest_rsi = indicators['RSI'][-1]
    if latest_rsi < 30:
        score += 2
        signals.append("RSI Oversold (Buy)")
    elif latest_rsi > 70:
        score -= 2
        signals.append("RSI Overbought (Sell)")
    
    # MACD Signal
    if indicators['MACD'][-1] > indicators['Signal'][-1] and indicators['MACD'][-2] <= indicators['Signal'][-2]:
        score += 2
        signals.append("MACD Bullish Crossover (Buy)")
    elif indicators['MACD'][-1] < indicators['Signal'][-1] and indicators['MACD'][-2] >= indicators['Signal'][-2]:
        score -= 2
        signals.append("MACD Bearish Crossover (Sell)")
    
    # SMA Crossover
    if indicators['SMA20'][-1] > indicators['SMA50'][-1] and indicators['SMA20'][-2] <= indicators['SMA50'][-2]:
        score += 2
        signals.append("SMA Bullish Crossover (Buy)")
    elif indicators['SMA20'][-1] < indicators['SMA50'][-1] and indicators['SMA20'][-2] >= indicators['SMA50'][-2]:
        score -= 2
        signals.append("SMA Bearish Crossover (Sell)")
    
    # Stochastic Oscillator
    if indicators['Stoch_K'][-1] < 20 and indicators['Stoch_K'][-1] > indicators['Stoch_D'][-1]:
        score += 2
        signals.append("Stochastic Oversold (Buy)")
    elif indicators['Stoch_K'][-1] > 80 and indicators['Stoch_K'][-1] < indicators['Stoch_D'][-1]:
        score -= 2
        signals.append("Stochastic Overbought (Sell)")
    
    # Ichimoku Cloud
    if (df['Close'][-1] > indicators['Senkou_Span_A'][-1] and 
        df['Close'][-1] > indicators['Senkou_Span_B'][-1] and
        indicators['Tenkan_Sen'][-1] > indicators['Kijun_Sen'][-1]):
        score += 2
        signals.append("Ichimoku Bullish (Buy)")
    elif (df['Close'][-1] < indicators['Senkou_Span_A'][-1] and 
          df['Close'][-1] < indicators['Senkou_Span_B'][-1]):
        score -= 2
        signals.append("Ichimoku Bearish (Sell)")
    
    recommendation = "Buy" if score >= 4 else "Sell" if score <= -4 else "Hold"
    return recommendation, signals, score

# Function to create plotly chart
def create_chart(df, indicators, ticker, currency_symbol):
    fig = make_subplots(rows=4, cols=1, shared_xaxes=True, 
                       vertical_spacing=0.05, 
                       subplot_titles=(f'{ticker} Price and Indicators', 'RSI', 'MACD', 'Stochastic'),
                       row_heights=[0.4, 0.2, 0.2, 0.2])
    
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
    
    # Ichimoku Cloud
    fig.add_trace(go.Scatter(x=df.index, y=indicators['Senkou_Span_A'], name='Senkou A', line=dict(color='green')), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=indicators['Senkou_Span_B'], name='Senkou B', line=dict(color='red')), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=indicators['Tenkan_Sen'], name='Tenkan Sen', line=dict(color='blue', dash='dot')), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=indicators['Kijun_Sen'], name='Kijun Sen', line=dict(color='red', dash='dot')), row=1, col=1)
    
    # RSI
    fig.add_trace(go.Scatter(x=df.index, y=indicators['RSI'], name='RSI', line=dict(color='green')), row=2, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="red", row=2, col=1)
    
    # MACD
    fig.add_trace(go.Scatter(x=df.index, y=indicators['MACD'], name='MACD', line=dict(color='blue')), row=3, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=indicators['Signal'], name='Signal', line=dict(color='orange')), row=3, col=1)
    fig.add_trace(go.Bar(x=df.index, y=indicators['Histogram'], name='Histogram', marker_color='gray'), row=3, col=1)
    
    # Stochastic Oscillator
    fig.add_trace(go.Scatter(x=df.index, y=indicators['Stoch_K'], name='Stoch %K', line=dict(color='blue')), row=4, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=indicators['Stoch_D'], name='Stoch %D', line=dict(color='orange')), row=4, col=1)
    fig.add_hline(y=80, line_dash="dash", line_color="red", row=4, col=1)
    fig.add_hline(y=20, line_dash="dash", line_color="red", row=4, col=1)
    
    # Update layout
    fig.update_layout(
        height=1000,
        showlegend=True,
        template='plotly_dark',
        xaxis_rangeslider_visible=False,
        yaxis_title=f'Price ({currency_symbol})',
        yaxis2_title='RSI',
        yaxis3_title='MACD',
        yaxis4_title='Stochastic'
    )
    
    return fig

# Streamlit app
def main():
    st.title("Advanced Stock Technical Analysis")
    
    # Sidebar for inputs
    with st.sidebar:
        st.header("Stock Selection")
        ticker = st.text_input("Enter Stock Ticker (e.g., RELIANCE.NS for Reliance Industries)", value="RELIANCE.NS")
        period = st.selectbox("Select Time Period", ['1mo', '3mo', '6mo', '1y', '2y', '5y'], index=3)
        interval = st.selectbox("Select Data Interval", ['1d', '1wk', '1mo'], index=0)
        analyze = st.button("Analyze")
    
    if analyze and ticker:
        try:
            with st.spinner("Fetching data..."):
                # Fetch data
                df, info = fetch_stock_data(ticker, period, interval)
                
                if df.empty:
                    st.error("No data found for the given ticker.")
                    return
                
                # Get currency
                currency, currency_symbol = get_currency_and_symbol(info)
                
                # Calculate indicators
                indicators = calculate_indicators(df)
                
                # Generate recommendation
                recommendation, signals, score = generate_recommendation(df, indicators)
                
                # Create two columns for responsive layout
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    # Display chart
                    fig = create_chart(df, indicators, ticker, currency_symbol)
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    # Display recommendation
                    st.subheader("Recommendation")
                    if recommendation == "Buy":
                        st.button("Buy", key="buy", help="Bullish Signal", disabled=True, 
                                 type="primary", use_container_width=True, 
                                 args={'styles': {'background-color': 'green'}})
                    elif recommendation == "Sell":
                        st.button("Sell", key="sell", help="Bearish Signal", disabled=True, 
                                 type="primary", use_container_width=True, 
                                 args={'styles': {'background-color': 'red'}})
                    else:
                        st.button("Hold", key="hold", help="Neutral Signal", disabled=True, 
                                 type="secondary", use_container_width=True)
                    
                    st.write(f"**Signal Score**: {score}")
                    st.write("**Signals**:")
                    for signal in signals:
                        st.write(f"- {signal}")
                    
                    # Display stock info
                    st.subheader("Stock Information")
                    st.write(f"**Company**: {info.get('longName', 'N/A')}")
                    st.write(f"**Exchange**: {info.get('exchange', 'N/A')}")
                    st.write(f"**Currency**: {currency} ({currency_symbol})")
                    st.write(f"**Current Price**: {currency_symbol}{df['Close'][-1]:.2f}")
                    st.write(f"**52 Week High**: {currency_symbol}{info.get('fiftyTwoWeekHigh', 'N/A')}")
                    st.write(f"**52 Week Low**: {currency_symbol}{info.get('fiftyTwoWeekLow', 'N/A')}")
                    
                    # Advanced indicators
                    st.subheader("Advanced Indicators")
                    st.write(f"**Latest RSI**: {indicators['RSI'][-1]:.2f}")
                    st.write(f"**Latest ATR**: {currency_symbol}{indicators['ATR'][-1]:.2f}")
                    st.write(f"**Stochastic %K**: {indicators['Stoch_K'][-1]:.2f}")
                    st.write(f"**Stochastic %D**: {indicators['Stoch_D'][-1]:.2f}")
                    st.write(f"**Ichimoku Cloud**: {'Above' if df['Close'][-1] > max(indicators['Senkou_Span_A'][-1], indicators['Senkou_Span_B'][-1]) else 'Below'}")
                    
                    # Daily change
                    st.subheader("Daily Performance")
                    latest_change = ((df['Close'][-1] - df['Close'][-2]) / df['Close'][-2] * 100) if len(df) > 1 else 0
                    st.write(f"**Daily Change**: {latest_change:.2f}%")
        
        except Exception as e:
            st.error(f"Error: {str(e)}")
    
    # Instructions
    st.markdown("""
    ### Instructions
    - Enter a stock ticker (e.g., RELIANCE.NS for Indian stocks, AAPL for US stocks)
    - Select a time period and data interval (daily, weekly, monthly)
    - Click 'Analyze' to view advanced technical indicators
    - The app automatically detects the currency based on the stock's exchange
    - Green 'Buy' or red 'Sell' buttons indicate trading recommendations
    - Recommendations are based on RSI, MACD, SMA, Stochastic, and Ichimoku signals
    """)

if __name__ == "__main__":
    main()
