import pandas as pd
import yfinance as yf
import ta
import streamlit as st
import logging
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load tickers from CSV
@st.cache_data
def load_tickers(csv_path: str) -> dict:
    try:
        df = pd.read_csv(csv_path)
        tickers = {row['NAME OF COMPANY']: f"{row['SYMBOL']}.NS" for _, row in df.iterrows()}
        logger.info(f"Loaded {len(tickers)} tickers from CSV")
        return tickers
    except Exception as e:
        logger.error(f"Error loading tickers from CSV: {str(e)}")
        return {}

# Fetch market data with retry mechanism
@st.cache_data
def fetch_market_data(ticker: str, period: str = '1mo', interval: str = '1d') -> pd.DataFrame:
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period=period, interval=interval)
        
        if df.empty:
            logger.warning(f"No data fetched for {ticker}")
            return None
            
        # Ensure we have enough data points
        if len(df) < 50:
            logger.warning(f"Insufficient data points ({len(df)}) for {ticker}")
            return None
            
        logger.info(f"Successfully fetched data for {ticker}")
        return df
    except Exception as e:
        logger.error(f"Error fetching data for {ticker}: {str(e)}")
        return None

# Calculate indicators with error handling
def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return None

    df_indicators = df.copy()

    try:
        # Ensure we have required columns
        required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        if not all(col in df.columns for col in required_cols):
            logger.error("Missing required columns in DataFrame")
            return None

        # Moving Averages
        df_indicators['EMA9'] = ta.trend.ema_indicator(close=df['Close'], window=9)
        df_indicators['EMA21'] = ta.trend.ema_indicator(close=df['Close'], window=21)
        df_indicators['SMA50'] = ta.trend.sma_indicator(close=df['Close'], window=50)
        df_indicators['SMA200'] = ta.trend.sma_indicator(close=df['Close'], window=200)

        # Momentum Indicators
        df_indicators['RSI'] = ta.momentum.rsi(close=df['Close'], window=14)
        
        # MACD
        macd = ta.trend.MACD(close=df['Close'])
        df_indicators['MACD'] = macd.macd()
        df_indicators['MACD_Signal'] = macd.macd_signal()
        df_indicators['MACD_Hist'] = macd.macd_diff()

        # Bollinger Bands
        bb = ta.volatility.BollingerBands(close=df['Close'])
        df_indicators['BB_Upper'] = bb.bollinger_hband()
        df_indicators['BB_Lower'] = bb.bollinger_lband()

        # Volume Indicators
        df_indicators['OBV'] = ta.volume.on_balance_volume(close=df['Close'], volume=df['Volume'])
        df_indicators['Volume_MA'] = df['Volume'].rolling(window=20).mean()
        df_indicators['Volume_Spike'] = df['Volume'] > (df_indicators['Volume_MA'] * 2)

        logger.info("Successfully calculated indicators")
        return df_indicators

    except Exception as e:
        logger.error(f"Error calculating indicators: {str(e)}")
        return None

# Generate trading signals
def generate_signals(df: pd.DataFrame, ticker: str) -> tuple:
    if df is None or df.empty:
        return "No Data", []

    latest = df.iloc[-1]
    signals = []

    try:
        # Moving Average Signals
        if latest['EMA9'] > latest['EMA21']:
            signals.append("Bullish EMA Crossover")
        elif latest['EMA9'] < latest['EMA21']:
            signals.append("Bearish EMA Crossover")

        # RSI Signals
        if latest['RSI'] < 30:
            signals.append("Oversold RSI")
        elif latest['RSI'] > 70:
            signals.append("Overbought RSI")

        # MACD Signals
        if latest['MACD'] > latest['MACD_Signal']:
            signals.append("Bullish MACD Crossover")
        elif latest['MACD'] < latest['MACD_Signal']:
            signals.append("Bearish MACD Crossover")

        # Price Position Signals
        if latest['Close'] > latest['SMA200']:
            signals.append("Price Above 200MA")
        else:
            signals.append("Price Below 200MA")

        if latest['Close'] < latest['BB_Lower']:
            signals.append("Below Bollinger Lower Band")
        elif latest['Close'] > latest['BB_Upper']:
            signals.append("Above Bollinger Upper Band")

        # Volume Signals
        if latest['Volume_Spike']:
            signals.append("Volume Spike Detected")

        # Generate final signal
        bullish_count = sum(1 for s in signals if "Bullish" in s or "Oversold" in s or "Below" in s)
        bearish_count = sum(1 for s in signals if "Bearish" in s or "Overbought" in s or "Above" in s)

        if bullish_count > bearish_count:
            return "Buy", signals
        elif bearish_count > bullish_count:
            return "Sell", signals
        else:
            return "Hold", signals

    except Exception as e:
        logger.error(f"Error generating signals for {ticker}: {str(e)}")
        return "Signal Generation Failed", []

# Plot candlestick chart
def plot_chart(df: pd.DataFrame, ticker: str):
    if df is None or df.empty:
        return None

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                       vertical_spacing=0.1, subplot_titles=(f'{ticker} Price', 'Volume'),
                       row_heights=[0.7, 0.3])

    # Candlestick
    fig.add_trace(go.Candlestick(x=df.index,
                               open=df['Open'],
                               high=df['High'],
                               low=df['Low'],
                               close=df['Close'],
                               name='Price'), row=1, col=1)

    # Moving Averages
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA9'], line=dict(color='blue', width=1), name='EMA9'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA21'], line=dict(color='orange', width=1), name='EMA21'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['SMA200'], line=dict(color='red', width=1), name='SMA200'), row=1, col=1)

    # Bollinger Bands
    fig.add_trace(go.Scatter(x=df.index, y=df['BB_Upper'], line=dict(color='gray', width=1, dash='dash'), 
                 name='BB Upper', fill=None), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['BB_Lower'], line=dict(color='gray', width=1, dash='dash'), 
                 name='BB Lower', fill='tonexty'), row=1, col=1)

    # Volume
    colors = ['green' if row['Close'] >= row['Open'] else 'red' for _, row in df.iterrows()]
    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name='Volume', marker_color=colors), row=2, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['Volume_MA'], line=dict(color='black', width=1), name='Vol MA(20)'), row=2, col=1)

    fig.update_layout(title=f'{ticker} Technical Analysis',
                     yaxis_title='Price',
                     xaxis_title='Date',
                     xaxis_rangeslider_visible=False,
                     height=700)
    
    return fig

# Streamlit App
def main():
    st.title("Stock Technical Analysis Dashboard")
    
    # File uploader for ticker CSV
    uploaded_file = st.file_uploader("Upload Ticker CSV", type=['csv'])
    
    if uploaded_file is not None:
        try:
            tickers = load_tickers(uploaded_file)
        except Exception as e:
            st.error(f"Error loading tickers: {str(e)}")
            return
    else:
        st.warning("Please upload a CSV file with ticker data")
        return

    if not tickers:
        st.error("No tickers loaded. Check your CSV format.")
        return

    company_names = sorted(tickers.keys())
    selected_company = st.selectbox("Select Company", company_names)
    selected_ticker = tickers[selected_company]

    period = st.selectbox("Select Time Period", ['1mo', '3mo', '6mo', '1y', '2y'], index=2)
    
    if st.button("Analyze"):
        with st.spinner(f"Fetching data for {selected_company}..."):
            data = fetch_market_data(selected_ticker, period=period)
            
            if data is None:
                st.error(f"Failed to fetch data for {selected_ticker}")
                return
                
            with st.spinner("Calculating indicators..."):
                data_with_indicators = calculate_indicators(data)
                
                if data_with_indicators is None:
                    st.error(f"Failed to calculate indicators for {selected_ticker}")
                    return
                    
                with st.spinner("Generating signals..."):
                    signal, signal_details = generate_signals(data_with_indicators, selected_ticker)
                
                # Display results
                st.subheader(f"Analysis for {selected_company} ({selected_ticker})")
                
                # Signal display
                if signal == "Buy":
                    st.success(f"**Signal**: {signal}")
                elif signal == "Sell":
                    st.error(f"**Signal**: {signal}")
                else:
                    st.warning(f"**Signal**: {signal}")
                
                # Indicators
                st.write("**Active Signals**:")
                if signal_details:
                    for detail in signal_details:
                        if "Bullish" in detail or "Buy" in detail:
                            st.success(f"✓ {detail}")
                        elif "Bearish" in detail or "Sell" in detail:
                            st.error(f"✗ {detail}")
                        else:
                            st.info(f"• {detail}")
                else:
                    st.info("No strong signals detected")
                
                # Key metrics
                latest = data_with_indicators.iloc[-1]
                cols = st.columns(3)
                with cols[0]:
                    st.metric("Price", f"₹{latest['Close']:.2f}")
                    st.metric("RSI", f"{latest['RSI']:.2f}", 
                              "Oversold" if latest['RSI'] < 30 else "Overbought" if latest['RSI'] > 70 else "Neutral")
                with cols[1]:
                    st.metric("Volume", f"{latest['Volume']/1e6:.2f}M")
                    st.metric("Volume MA", f"{latest['Volume_MA']/1e6:.2f}M")
                with cols[2]:
                    st.metric("200MA", f"₹{latest['SMA200']:.2f}")
                    st.metric("Trend", 
                              "Bullish" if latest['Close'] > latest['SMA200'] else "Bearish")
                
                # Chart
                st.subheader("Price Chart with Indicators")
                fig = plot_chart(data_with_indicators, selected_ticker)
                st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()
