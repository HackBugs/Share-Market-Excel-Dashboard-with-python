import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objs as go
from plotly.subplots import make_subplots
from ta.trend import SMAIndicator, EMAIndicator, MACD, IchimokuIndicator, ADXIndicator, PSARIndicator
from ta.momentum import RSIIndicator, StochasticOscillator, WilliamsRIndicator
from ta.volatility import BollingerBands, AverageTrueRange
from ta.volume import OnBalanceVolumeIndicator, ChaikinMoneyFlowIndicator
from datetime import datetime, timedelta
import io
import re
from typing import Union, List, Tuple
import seaborn as sns
import matplotlib.pyplot as plt
from functools import lru_cache
import logging
import asyncio
import concurrent.futures
from dateutil.relativedelta import relativedelta

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Ensure set_page_config is called only once
if not st.session_state.get("page_config_set", False):
    st.set_page_config(layout="wide", page_title="Expert Stock Technical Analysis")
    st.session_state.page_config_set = True

# Expanded ticker database
TICKER_DB = {
    "Reliance Industries": "RELIANCE.NS",
    "Tata Steel": "TATASTEEL.NS",
    "State Bank of India": "SBIN.NS",
    "Infosys": "INFY.NS",
    "HDFC Bank": "HDFCBANK.NS",
    "Adani Enterprises": "ADANIENT.NS",
    "Tata Motors": "TATAMOTORS.NS",
    "Bajaj Finance": "BAJFINANCE.NS",
    "ICICI Bank": "ICICIBANK.NS",
    "Hindustan Unilever": "HINDUNILVR.NS",
    "Bharti Airtel": "BHARTIARTL.NS",
    "Maruti Suzuki": "MARUTI.NS",
    "Larsen & Toubro": "LT.NS",
    "Axis Bank": "AXISBANK.NS",
    "Sun Pharmaceutical": "SUNPHARMA.NS",
    "Apple": "AAPL",
    "Microsoft": "MSFT",
    "Amazon": "AMZN",
    "Tesla": "TSLA",
    "Alphabet (Google)": "GOOGL",
    "Nvidia": "NVDA",
    "Vodafone": "VOD.L",
    "Toyota": "7203.T",
    "BP PLC": "BP.L",
    "Samsung Electronics": "005930.KS",
    "Tencent Holdings": "0700.HK",
    "Kweichow Moutai": "600519.SS"
}

# Cache stock data fetching
@lru_cache(maxsize=100)
def fetch_stock_data(ticker: str, period: str, interval: str) -> Tuple[pd.DataFrame, dict]:
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period=period, interval=interval)
        logger.debug(f"Fetched data for {ticker}: {len(df)} rows")
        if df.empty:
            logger.warning(f"No data returned for {ticker}")
            return pd.DataFrame(), {}
        return df, stock.info
    except Exception as e:
        logger.error(f"Error fetching data for {ticker}: {str(e)}")
        return pd.DataFrame(), {}

# Function to search tickers
def search_ticker(query: str) -> List[tuple]:
    query = query.lower().strip()
    return [(company, ticker) for company, ticker in TICKER_DB.items() if re.search(query, company.lower(), re.IGNORECASE)]

# Function to get currency
def get_currency_and_symbol(ticker_info: dict) -> tuple:
    exchange = ticker_info.get('exchange', '')
    country = ticker_info.get('country', '')
    currency_map = {
        'India': ('INR', '₹'), 'United States': ('USD', '$'), 'United Kingdom': ('GBP', '£'),
        'European Union': ('EUR', '€'), 'Japan': ('JPY', '¥'), 'China': ('CNY', '¥'),
        'Australia': ('AUD', 'A$'), 'South Korea': ('KRW', '₩'), 'Hong Kong': ('HKD', 'HK$')
    }
    if country in currency_map:
        return currency_map[country]
    elif 'NSE' in exchange or 'BSE' in exchange:
        return ('INR', '₹')
    elif 'KRX' in exchange:
        return ('KRW', '₩')
    elif 'HKG' in exchange:
        return ('HKD', 'HK$')
    return ('USD', '$')

# Function to calculate Fibonacci levels
def calculate_fibonacci_levels(df: pd.DataFrame) -> dict:
    if df.empty:
        return {}
    high = df['High'].max()
    low = df['Low'].min()
    diff = high - low
    return {
        '0.0%': high, '23.6%': high - 0.236 * diff, '38.2%': high - 0.382 * diff,
        '50.0%': high - 0.5 * diff, '61.8%': high - 0.618 * diff, '100.0%': low
    }

# Function to calculate pivot points
def calculate_pivot_points(df: pd.DataFrame) -> tuple:
    if df.empty or len(df) < 1:
        return 0, 0, 0
    pivot = (df['High'][-1] + df['Low'][-1] + df['Close'][-1]) / 3
    support1 = (2 * pivot) - df['High'][-1]
    resistance1 = (2 * pivot) - df['Low'][-1]
    return pivot, support1, resistance1

# Function to calculate VWAP
def calculate_vwap(df: pd.DataFrame) -> pd.Series:
    if df.empty:
        return pd.Series()
    typical_price = (df['High'] + df['Low'] + df['Close']) / 3
    return (typical_price * df['Volume']).cumsum() / df['Volume'].cumsum()

# Function to calculate advanced indicators
def calculate_indicators(df: pd.DataFrame, sma1_window: int, sma2_window: int, rsi_window: int, macd_fast: int, macd_slow: int, macd_signal: int, bb_window: int, bb_dev: float) -> pd.DataFrame:
    if df.empty:
        logger.warning("Empty DataFrame passed to calculate_indicators")
        return pd.DataFrame()
    
    sma1 = SMAIndicator(close=df['Close'], window=sma1_window).sma_indicator()
    sma2 = SMAIndicator(close=df['Close'], window=sma2_window).sma_indicator()
    ema20 = EMAIndicator(close=df['Close'], window=20).ema_indicator()
    rsi = RSIIndicator(close=df['Close'], window=rsi_window).rsi()
    macd = MACD(close=df['Close'], window_fast=macd_fast, window_slow=macd_slow, window_sign=macd_signal)
    bb = BollingerBands(close=df['Close'], window=bb_window, window_dev=bb_dev)
    atr = AverageTrueRange(high=df['High'], low=df['Low'], close=df['Close'], window=14).average_true_range()
    stoch = StochasticOscillator(high=df['High'], low=df['Low'], close=df['Close'], window=14, smooth_window=3)
    ichimoku = IchimokuIndicator(high=df['High'], low=df['Low'], window1=9, window2=26, window3=52)
    obv = OnBalanceVolumeIndicator(close=df['Close'], volume=df['Volume']).on_balance_volume()
    cmf = ChaikinMoneyFlowIndicator(high=df['High'], low=df['Low'], close=df['Close'], volume=df['Volume'], window=20).chaikin_money_flow()
    vwap = calculate_vwap(df)
    adx = ADXIndicator(high=df['High'], low=df['Low'], close=df['Close'], window=14).adx()
    psar = PSARIndicator(high=df['High'], low=df['Low'], close=df['Close']).psar()
    willr = WilliamsRIndicator(high=df['High'], low=df['Low'], close=df['Close'], lbp=14).williams_r()
    
    indicators = pd.DataFrame({
        'SMA1': sma1, 'SMA2': sma2, 'EMA20': ema20, 'RSI': rsi, 'MACD': macd.macd(),
        'Signal': macd.macd_signal(), 'Histogram': macd.macd_diff(), 'BB_High': bb.bollinger_hband(),
        'BB_Low': bb.bollinger_lband(), 'BB_Mid': bb.bollinger_mavg(), 'ATR': atr,
        'Stoch_K': stoch.stoch(), 'Stoch_D': stoch.stoch_signal(), 'Tenkan_Sen': ichimoku.ichimoku_conversion_line(),
        'Kijun_Sen': ichimoku.ichimoku_base_line(), 'Senkou_Span_A': ichimoku.ichimoku_a(),
        'Senkou_Span_B': ichimoku.ichimoku_b(), 'OBV': obv, 'CMF': cmf, 'VWAP': vwap,
        'ADX': adx, 'PSAR': psar, 'WilliamsR': willr
    }, index=df.index)
    
    if indicators.empty:
        logger.warning("Indicators DataFrame is empty")
    return indicators

# Function to generate recommendation
def generate_recommendation(df: pd.DataFrame, indicators: pd.DataFrame) -> tuple:
    if df.empty or indicators.empty:
        logger.warning("Empty data in generate_recommendation")
        return "Not Buy", [], 0.0, {}
    
    score = 0
    signals = []
    contributions = {}
    weights = {
        'RSI': 1.0, 'MACD': 1.5, 'SMA': 1.2, 'Stochastic': 1.0, 'Ichimoku': 1.5,
        'CMF': 0.8, 'OBV': 0.8, 'VWAP': 1.0, 'ADX': 1.0, 'PSAR': 1.0, 'WilliamsR': 0.8
    }
    
    try:
        if indicators['RSI'][-1] < 30:
            score += 2 * weights['RSI']
            signals.append("RSI Oversold (Buy)")
            contributions['RSI'] = {'signal': 'Oversold (Buy)', 'score': 2 * weights['RSI'], 'weight': weights['RSI']}
        elif indicators['RSI'][-1] > 70:
            score -= 2 * weights['RSI']
            signals.append("RSI Overbought (Sell)")
            contributions['RSI'] = {'signal': 'Overbought (Sell)', 'score': -2 * weights['RSI'], 'weight': weights['RSI']}
        else:
            contributions['RSI'] = {'signal': 'Neutral', 'score': 0, 'weight': weights['RSI']}
        
        if indicators['MACD'][-1] > indicators['Signal'][-1] and indicators['MACD'][-2] <= indicators['Signal'][-2]:
            score += 2 * weights['MACD']
            signals.append("MACD Bullish Crossover (Buy)")
            contributions['MACD'] = {'signal': 'Bullish Crossover (Buy)', 'score': 2 * weights['MACD'], 'weight': weights['MACD']}
        elif indicators['MACD'][-1] < indicators['Signal'][-1] and indicators['MACD'][-2] >= indicators['Signal'][-2]:
            score -= 2 * weights['MACD']
            signals.append("MACD Bearish Crossover (Sell)")
            contributions['MACD'] = {'signal': 'Bearish Crossover (Sell)', 'score': -2 * weights['MACD'], 'weight': weights['MACD']}
        else:
            contributions['MACD'] = {'signal': 'Neutral', 'score': 0, 'weight': weights['MACD']}
        
        if indicators['SMA1'][-1] > indicators['SMA2'][-1] and indicators['SMA1'][-2] <= indicators['SMA2'][-2]:
            score += 2 * weights['SMA']
            signals.append("SMA Bullish Crossover (Buy)")
            contributions['SMA'] = {'signal': 'Bullish Crossover (Buy)', 'score': 2 * weights['SMA'], 'weight': weights['SMA']}
        elif indicators['SMA1'][-1] < indicators['SMA2'][-1] and indicators['SMA1'][-2] >= indicators['SMA2'][-2]:
            score -= 2 * weights['SMA']
            signals.append("SMA Bearish Crossover (Sell)")
            contributions['SMA'] = {'signal': 'Bearish Crossover (Sell)', 'score': -2 * weights['SMA'], 'weight': weights['SMA']}
        else:
            contributions['SMA'] = {'signal': 'Neutral', 'score': 0, 'weight': weights['SMA']}
        
        if indicators['Stoch_K'][-1] < 20 and indicators['Stoch_K'][-1] > indicators['Stoch_D'][-1]:
            score += 2 * weights['Stochastic']
            signals.append("Stochastic Oversold (Buy)")
            contributions['Stochastic'] = {'signal': 'Oversold (Buy)', 'score': 2 * weights['Stochastic'], 'weight': weights['Stochastic']}
        elif indicators['Stoch_K'][-1] > 80 and indicators['Stoch_K'][-1] < indicators['Stoch_D'][-1]:
            score -= 2 * weights['Stochastic']
            signals.append("Stochastic Overbought (Sell)")
            contributions['Stochastic'] = {'signal': 'Overbought (Sell)', 'score': -2 * weights['Stochastic'], 'weight': weights['Stochastic']}
        else:
            contributions['Stochastic'] = {'signal': 'Neutral', 'score': 0, 'weight': weights['Stochastic']}
        
        if (df['Close'][-1] > indicators['Senkou_Span_A'][-1] and 
            df['Close'][-1] > indicators['Senkou_Span_B'][-1] and
            indicators['Tenkan_Sen'][-1] > indicators['Kijun_Sen'][-1]):
            score += 2 * weights['Ichimoku']
            signals.append("Ichimoku Bullish (Buy)")
            contributions['Ichimoku'] = {'signal': 'Bullish (Buy)', 'score': 2 * weights['Ichimoku'], 'weight': weights['Ichimoku']}
        elif (df['Close'][-1] < indicators['Senkou_Span_A'][-1] and 
              df['Close'][-1] < indicators['Senkou_Span_B'][-1]):
            score -= 2 * weights['Ichimoku']
            signals.append("Ichimoku Bearish (Sell)")
            contributions['Ichimoku'] = {'signal': 'Bearish (Sell)', 'score': -2 * weights['Ichimoku'], 'weight': weights['Ichimoku']}
        else:
            contributions['Ichimoku'] = {'signal': 'Neutral', 'score': 0, 'weight': weights['Ichimoku']}
        
        if indicators['CMF'][-1] > 0:
            score += 1 * weights['CMF']
            signals.append("CMF Positive (Buy)")
            contributions['CMF'] = {'signal': 'Positive (Buy)', 'score': 1 * weights['CMF'], 'weight': weights['CMF']}
        elif indicators['CMF'][-1] < 0:
            score -= 1 * weights['CMF']
            signals.append("CMF Negative (Sell)")
            contributions['CMF'] = {'signal': 'Negative (Sell)', 'score': -1 * weights['CMF'], 'weight': weights['CMF']}
        else:
            contributions['CMF'] = {'signal': 'Neutral', 'score': 0, 'weight': weights['CMF']}
        
        if indicators['OBV'][-1] > indicators['OBV'][-2]:
            score += 1 * weights['OBV']
            signals.append("OBV Increasing (Buy)")
            contributions['OBV'] = {'signal': 'Increasing (Buy)', 'score': 1 * weights['OBV'], 'weight': weights['OBV']}
        elif indicators['OBV'][-1] < indicators['OBV'][-2]:
            score -= 1 * weights['OBV']
            signals.append("OBV Decreasing (Sell)")
            contributions['OBV'] = {'signal': 'Decreasing (Sell)', 'score': -1 * weights['OBV'], 'weight': weights['OBV']}
        else:
            contributions['OBV'] = {'signal': 'Neutral', 'score': 0, 'weight': weights['OBV']}
        
        if df['Close'][-1] > indicators['VWAP'][-1]:
            score += 1 * weights['VWAP']
            signals.append("Price Above VWAP (Buy)")
            contributions['VWAP'] = {'signal': 'Above VWAP (Buy)', 'score': 1 * weights['VWAP'], 'weight': weights['VWAP']}
        elif df['Close'][-1] < indicators['VWAP'][-1]:
            score -= 1 * weights['VWAP']
            signals.append("Price Below VWAP (Sell)")
            contributions['VWAP'] = {'signal': 'Below VWAP (Sell)', 'score': -1 * weights['VWAP'], 'weight': weights['VWAP']}
        else:
            contributions['VWAP'] = {'signal': 'Neutral', 'score': 0, 'weight': weights['VWAP']}
        
        if indicators['ADX'][-1] > 25 and df['Close'][-1] > df['Close'][-2]:
            score += 1 * weights['ADX']
            signals.append("Strong Uptrend (Buy)")
            contributions['ADX'] = {'signal': 'Strong Uptrend (Buy)', 'score': 1 * weights['ADX'], 'weight': weights['ADX']}
        elif indicators['ADX'][-1] > 25 and df['Close'][-1] < df['Close'][-2]:
            score -= 1 * weights['ADX']
            signals.append("Strong Downtrend (Sell)")
            contributions['ADX'] = {'signal': 'Strong Downtrend (Sell)', 'score': -1 * weights['ADX'], 'weight': weights['ADX']}
        else:
            contributions['ADX'] = {'signal': 'Neutral', 'score': 0, 'weight': weights['ADX']}
        
        if df['Close'][-1] > indicators['PSAR'][-1] and df['Close'][-2] <= indicators['PSAR'][-2]:
            score += 1 * weights['PSAR']
            signals.append("PSAR Bullish Reversal (Buy)")
            contributions['PSAR'] = {'signal': 'Bullish Reversal (Buy)', 'score': 1 * weights['PSAR'], 'weight': weights['PSAR']}
        elif df['Close'][-1] < indicators['PSAR'][-1] and df['Close'][-2] >= indicators['PSAR'][-2]:
            score -= 1 * weights['PSAR']
            signals.append("PSAR Bearish Reversal (Sell)")
            contributions['PSAR'] = {'signal': 'Bearish Reversal (Sell)', 'score': -1 * weights['PSAR'], 'weight': weights['PSAR']}
        else:
            contributions['PSAR'] = {'signal': 'Neutral', 'score': 0, 'weight': weights['PSAR']}
        
        if indicators['WilliamsR'][-1] < -80:
            score += 1 * weights['WilliamsR']
            signals.append("Williams %R Oversold (Buy)")
            contributions['WilliamsR'] = {'signal': 'Oversold (Buy)', 'score': 1 * weights['WilliamsR'], 'weight': weights['WilliamsR']}
        elif indicators['WilliamsR'][-1] > -20:
            score -= 1 * weights['WilliamsR']
            signals.append("Williams %R Overbought (Sell)")
            contributions['WilliamsR'] = {'signal': 'Overbought (Sell)', 'score': -1 * weights['WilliamsR'], 'weight': weights['WilliamsR']}
        else:
            contributions['WilliamsR'] = {'signal': 'Neutral', 'score': 0, 'weight': weights['WilliamsR']}
    except IndexError as e:
        logger.error(f"IndexError in generate_recommendation: {str(e)}")
        return "Not Buy", [], 0.0, {}
    
    recommendation = "Buy" if score >= 5 else "Not Buy"
    return recommendation, signals, score, contributions

# Function to perform advanced backtest
def backtest_strategy(df: pd.DataFrame, indicators: pd.DataFrame, bt_sma1: int, bt_sma2: int, bt_macd: bool) -> tuple:
    if df.empty or indicators.empty or len(df) < 2 or len(indicators) < 2:
        logger.warning("Insufficient data for backtest_strategy")
        return 0.0, 0.0, [], 0.0, 0.0
    
    signals = []
    position = 0
    returns = []
    equity = [100000]
    max_drawdown = 0
    peak = equity[0]
    
    try:
        for i in range(1, len(df)):
            if i >= len(indicators) or i-1 >= len(indicators):
                logger.warning(f"Index out of bounds in backtest_strategy at i={i}")
                continue
                
            buy_signal = (indicators['SMA1'][i] > indicators['SMA2'][i] and 
                          indicators['SMA1'][i-1] <= indicators['SMA2'][i-1])
            if bt_macd:
                buy_signal = buy_signal and (indicators['MACD'][i] > indicators['Signal'][i])
            sell_signal = (indicators['SMA1'][i] < indicators['SMA2'][i] and 
                           indicators['SMA1'][i-1] >= indicators['SMA2'][i-1])
            
            if buy_signal and position == 0:
                position = 1
                signals.append(('Buy', df.index[i], df['Close'][i]))
                logger.debug(f"Buy signal at {df.index[i]}: {df['Close'][i]}")
            elif sell_signal and position == 1:
                position = 0
                signals.append(('Sell', df.index[i], df['Close'][i]))
                logger.debug(f"Sell signal at {df.index[i]}: {df['Close'][i]}")
                if len(signals) >= 2:
                    ret = (signals[-1][2] - signals[-2][2]) / signals[-2][2]
                    returns.append(ret)
                    equity.append(equity[-1] * (1 + ret))
                    peak = max(peak, equity[-1])
                    drawdown = (peak - equity[-1]) / peak
                    max_drawdown = max(max_drawdown, drawdown)
    except Exception as e:
        logger.error(f"Error in backtest_strategy: {str(e)}")
        return 0.0, 0.0, [], 0.0, 0.0
    
    total_return = ((equity[-1] - equity[0]) / equity[0] * 100) if equity else 0
    win_rate = sum(1 for r in returns if r > 0) / len(returns) * 100 if returns else 0
    sharpe_ratio = (np.mean(returns) / np.std(returns) * np.sqrt(252)) if returns else 0
    return total_return, win_rate, signals, sharpe_ratio, max_drawdown * 100

# Function to calculate position size
def calculate_position_size(capital: float, risk_pct: float, atr: float, current_price: float) -> float:
    if atr <= 0 or current_price <= 0:
        logger.warning("Invalid ATR or price for position sizing")
        return 0
    risk_per_share = 2 * atr
    shares = (capital * risk_pct) / risk_per_share
    return min(shares, capital / current_price)

# Function to fetch sentiment (mock)
def fetch_sentiment(ticker: str) -> str:
    logger.debug(f"Fetching sentiment for {ticker}")
    return "Neutral (No real-time X data)"

# Function to create correlation heatmap
def create_correlation_heatmap(tickers: List[str], period: str) -> go.Figure:
    data = {}
    for ticker in tickers[:5]:
        df, _ = fetch_stock_data(ticker, period, '1d')
        if not df.empty:
            data[ticker] = df['Close']
        else:
            logger.warning(f"No data for {ticker} in correlation heatmap")
    if not data:
        logger.warning("No valid data for correlation heatmap")
        return go.Figure()
    
    df = pd.DataFrame(data)
    corr = df.pct_change().corr()
    
    fig = go.Figure(data=go.Heatmap(
        z=corr.values, x=corr.columns, y=corr.columns,
        colorscale='RdBu', zmin=-1, zmax=1,
        text=corr.values.round(2), texttemplate="%{text}",
        showscale=True
    ))
    fig.update_layout(title="Correlation Heatmap", height=400)
    return fig

# Function to create plotly chart
def create_chart(df: pd.DataFrame, indicators: pd.DataFrame, ticker: str, currency_symbol: str, fib_levels: dict, pivot: float, support1: float, resistance1: float, backtest_signals: list) -> go.Figure:
    if df.empty or indicators.empty:
        logger.warning("Empty data in create_chart")
        return go.Figure()
    
    fig = make_subplots(rows=6, cols=1, shared_xaxes=True, 
                       vertical_spacing=0.05, 
                       subplot_titles=(f'{ticker} Price and Indicators', 'RSI', 'MACD', 'Stochastic', 'Volume & CMF', 'ADX & Williams %R'),
                       row_heights=[0.4, 0.1, 0.1, 0.1, 0.1, 0.2])
    
    try:
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Price'), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=indicators['SMA1'], name='SMA1', line=dict(color='blue')), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=indicators['SMA2'], name='SMA2', line=dict(color='orange')), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=indicators['EMA20'], name='EMA20', line=dict(color='purple')), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=indicators['BB_High'], name='BB High', line=dict(color='gray', dash='dash')), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=indicators['BB_Low'], name='BB Low', line=dict(color='gray', dash='dash')), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=indicators['Senkou_Span_A'], name='Senkou A', line=dict(color='green')), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=indicators['Senkou_Span_B'], name='Senkou B', line=dict(color='red')), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=indicators['Tenkan_Sen'], name='Tenkan Sen', line=dict(color='blue', dash='dot')), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=indicators['Kijun_Sen'], name='Kijun Sen', line=dict(color='red', dash='dot')), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=indicators['VWAP'], name='VWAP', line=dict(color='cyan')), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=indicators['PSAR'], name='PSAR', mode='markers', marker=dict(size=5, color='yellow')), row=1, col=1)
        
        for level, price in fib_levels.items():
            fig.add_hline(y=price, line_dash="dash", line_color="yellow", annotation_text=f"Fib {level}", row=1, col=1)
        
        fig.add_hline(y=support1, line_dash="dot", line_color="green", annotation_text="S1", row=1, col=1)
        fig.add_hline(y=resistance1, line_dash="dot", line_color="red", annotation_text="R1", row=1, col=1)
        
        valid_signals = [s for s in backtest_signals if isinstance(s, (list, tuple)) and len(s) >= 3]
        buy_signals = [(s[1], s[2]) for s in valid_signals if s[0] == 'Buy']
        sell_signals = [(s[1], s[2]) for s in valid_signals if s[0] == 'Sell']
        if buy_signals:
            buy_x, buy_y = zip(*buy_signals)
            fig.add_trace(go.Scatter(x=buy_x, y=buy_y, mode='markers', name='Buy Signals', marker=dict(symbol='triangle-up', size=10, color='green')), row=1, col=1)
        if sell_signals:
            sell_x, sell_y = zip(*sell_signals)
            fig.add_trace(go.Scatter(x=sell_x, y=sell_y, mode='markers', name='Sell Signals', marker=dict(symbol='triangle-down', size=10, color='red')), row=1, col=1)
        
        fig.add_trace(go.Scatter(x=df.index, y=indicators['RSI'], name='RSI', line=dict(color='green')), row=2, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="red", row=2, col=1)
        
        fig.add_trace(go.Scatter(x=df.index, y=indicators['MACD'], name='MACD', line=dict(color='blue')), row=3, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=indicators['Signal'], name='Signal', line=dict(color='orange')), row=3, col=1)
        fig.add_trace(go.Bar(x=df.index, y=indicators['Histogram'], name='Histogram', marker_color='gray'), row=3, col=1)
        
        fig.add_trace(go.Scatter(x=df.index, y=indicators['Stoch_K'], name='Stoch %K', line=dict(color='blue')), row=4, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=indicators['Stoch_D'], name='Stoch %D', line=dict(color='orange')), row=4, col=1)
        fig.add_hline(y=80, line_dash="dash", line_color="red", row=4, col=1)
        fig.add_hline(y=20, line_dash="dash", line_color="red", row=4, col=1)
        
        fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name='Volume', marker_color='gray'), row=5, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=indicators['CMF'], name='CMF', line=dict(color='purple')), row=5, col=1)
        fig.add_hline(y=0, line_dash="dash", line_color="white", row=5, col=1)
        
        fig.add_trace(go.Scatter(x=df.index, y=indicators['ADX'], name='ADX', line=dict(color='blue')), row=6, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=indicators['WilliamsR'], name='Williams %R', line=dict(color='red')), row=6, col=1)
        fig.add_hline(y=25, line_dash="dash", line_color="green", annotation_text="ADX Strong Trend", row=6, col=1)
        fig.add_hline(y=-20, line_dash="dash", line_color="red", annotation_text="W%R Overbought", row=6, col=1)
        fig.add_hline(y=-80, line_dash="dash", line_color="green", annotation_text="W%R Oversold", row=6, col=1)
        
        fig.update_layout(
            height=1400, showlegend=True, template='plotly_dark', xaxis_rangeslider_visible=False,
            yaxis_title=f'Price ({currency_symbol})', yaxis2_title='RSI', yaxis3_title='MACD',
            yaxis4_title='Stochastic', yaxis5_title='Volume/CMF', yaxis6_title='ADX/W%R'
        )
    except Exception as e:
        logger.error(f"Error in create_chart: {str(e)}")
        return go.Figure()
    
    return fig

# Function to calculate profit/loss
def calculate_profit_loss(df: pd.DataFrame, investment: float, start_date: datetime, end_date: datetime, currency_symbol: str) -> dict:
    if df.empty or investment <= 0:
        return {
            'shares': 0, 'initial_price': 0, 'final_price': 0, 'initial_value': 0,
            'final_value': 0, 'profit_loss': 0, 'return_pct': 0, 'sharpe_ratio': 0,
            'tax': 0, 'net_profit_loss': 0
        }
    
    try:
        start_price = df['Close'].loc[df.index >= start_date].iloc[0] if not df['Close'].loc[df.index >= start_date].empty else 0
        end_price = df['Close'].loc[df.index <= end_date].iloc[-1] if not df['Close'].loc[df.index <= end_date].empty else 0
        
        if start_price <= 0 or end_price <= 0:
            logger.warning("Invalid prices for profit/loss calculation")
            return {
                'shares': 0, 'initial_price': 0, 'final_price': 0, 'initial_value': 0,
                'final_value': 0, 'profit_loss': 0, 'return_pct': 0, 'sharpe_ratio': 0,
                'tax': 0, 'net_profit_loss': 0
            }
        
        shares = investment / start_price
        initial_value = shares * start_price
        final_value = shares * end_price
        profit_loss = final_value - initial_value
        return_pct = (profit_loss / initial_value * 100) if initial_value > 0 else 0
        
        # Calculate Sharpe Ratio
        returns = df['Close'].pct_change().loc[(df.index >= start_date) & (df.index <= end_date)]
        sharpe_ratio = (returns.mean() / returns.std() * np.sqrt(252)) if returns.std() != 0 else 0
        
        # Mock capital gains tax (15% short-term if <1 year, 10% long-term if >=1 year)
        holding_period = (end_date - start_date).days / 365
        tax_rate = 0.15 if holding_period < 1 else 0.10
        tax = max(0, profit_loss * tax_rate)
        net_profit_loss = profit_loss - tax
        
        return {
            'shares': shares, 'initial_price': start_price, 'final_price': end_price,
            'initial_value': initial_value, 'final_value': final_value, 'profit_loss': profit_loss,
            'return_pct': return_pct, 'sharpe_ratio': sharpe_ratio, 'tax': tax,
            'net_profit_loss': net_profit_loss
        }
    except Exception as e:
        logger.error(f"Error in calculate_profit_loss: {str(e)}")
        return {
            'shares': 0, 'initial_price': 0, 'final_price': 0, 'initial_value': 0,
            'final_value': 0, 'profit_loss': 0, 'return_pct': 0, 'sharpe_ratio': 0,
            'tax': 0, 'net_profit_loss': 0
        }

# Function to analyze all tickers in TICKER_DB
async def analyze_db_tickers(period: str, interval: str, sma1_window: int, sma2_window: int, rsi_window: int, macd_fast: int, macd_slow: int, macd_signal: int, bb_window: int, bb_dev: float) -> List[dict]:
    results = []
    
    async def analyze_single_ticker(ticker: str, company: str) -> dict:
        try:
            df, _ = fetch_stock_data(ticker, period, interval)
            if df.empty or len(df) < 2:
                return {'company': company, 'ticker': ticker, 'recommendation': 'Not Buy', 'score': 0.0}
            
            indicators = calculate_indicators(df, sma1_window, sma2_window, rsi_window, macd_fast, macd_slow, macd_signal, bb_window, bb_dev)
            if indicators.empty or len(indicators) < 2:
                return {'company': company, 'ticker': ticker, 'recommendation': 'Not Buy', 'score': 0.0}
            
            recommendation, _, score, _ = generate_recommendation(df, indicators)
            return {'company': company, 'ticker': ticker, 'recommendation': recommendation, 'score': score}
        except Exception as e:
            logger.error(f"Error analyzing {ticker}: {str(e)}")
            return {'company': company, 'ticker': ticker, 'recommendation': 'Not Buy', 'score': 0.0}
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        loop = asyncio.get_event_loop()
        tasks = [
            loop.run_in_executor(executor, lambda t, c: analyze_single_ticker(t, c), ticker, company)
            for company, ticker in TICKER_DB.items()
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
    
    return [r for r in results if isinstance(r, dict)]

# Function to calculate historical investment for all tickers
def calculate_historical_investment(tickers: List[str], investment: float, start_date: datetime, end_date: datetime) -> Tuple[List[dict], go.Figure]:
    results = []
    fig = go.Figure()
    
    for company, ticker in tickers:
        try:
            df, _ = fetch_stock_data(ticker, 'max', '1d')
            if df.empty:
                results.append({
                    'company': company, 'ticker': ticker, 'shares': 0, 'initial_value': 0,
                    'final_value': 0, 'profit_loss': 0, 'return_pct': 0, 'sharpe_ratio': 0,
                    'tax': 0, 'net_profit_loss': 0
                })
                continue
            
            pl_data = calculate_profit_loss(df, investment, start_date, end_date, '')
            results.append({
                'company': company, 'ticker': ticker, 'shares': pl_data['shares'],
                'initial_value': pl_data['initial_value'], 'final_value': pl_data['final_value'],
                'profit_loss': pl_data['profit_loss'], 'return_pct': pl_data['return_pct'],
                'sharpe_ratio': pl_data['sharpe_ratio'], 'tax': pl_data['tax'],
                'net_profit_loss': pl_data['net_profit_loss']
            })
            
            # Add to comparison chart
            if not df.empty:
                df_period = df.loc[(df.index >= start_date) & (df.index <= end_date)]
                if not df_period.empty:
                    equity = (investment / df_period['Close'].iloc[0]) * df_period['Close']
                    fig.add_trace(go.Scatter(x=df_period.index, y=equity, name=f"{company} ({ticker})"))
        except Exception as e:
            logger.error(f"Error in historical investment for {ticker}: {str(e)}")
            results.append({
                'company': company, 'ticker': ticker, 'shares': 0, 'initial_value': 0,
                'final_value': 0, 'profit_loss': 0, 'return_pct': 0, 'sharpe_ratio': 0,
                'tax': 0, 'net_profit_loss': 0
            })
    
    fig.update_layout(
        title="Investment Value Over Time", xaxis_title="Date", yaxis_title="Value",
        height=400, template='plotly_dark'
    )
    return results, fig

# Function to generate analysis report
def generate_report(ticker: str, info: dict, df: pd.DataFrame, indicators: pd.DataFrame, recommendation: str, signals: list, score: float, fib_levels: dict, pivot: float, support1: float, resistance1: float, backtest_results: tuple, currency_symbol: str, position_size: float, take_profit: float, sentiment: str) -> str:
    if df.empty:
        logger.warning("Empty DataFrame in generate_report")
        return "No data available for analysis."
    
    def format_value(value, fmt=".2f", default="N/A"):
        try:
            return f"{value:{fmt}}" if pd.notnull(value) else default
        except (ValueError, TypeError) as e:
            logger.error(f"Formatting error: {str(e)}")
            return default

    rsi_value = format_value(indicators['RSI'][-1] if not indicators.empty else None)
    rsi_status = "Oversold" if not indicators.empty and pd.notnull(indicators['RSI'][-1]) and indicators['RSI'][-1] < 30 else \
                "Overbought" if not indicators.empty and pd.notnull(indicators['RSI'][-1]) and indicators['RSI'][-1] > 70 else "Neutral"
    
    macd_value = format_value(indicators['MACD'][-1] if not indicators.empty else None)
    signal_value = format_value(indicators['Signal'][-1] if not indicators.empty else None)
    
    sma1_value = format_value(indicators['SMA1'][-1] if not indicators.empty else None)
    sma2_value = format_value(indicators['SMA2'][-1] if not indicators.empty else None)
    
    atr_value = format_value(indicators['ATR'][-1] if not indicators.empty else None)
    stoch_k_value = format_value(indicators['Stoch_K'][-1] if not indicators.empty else None)
    stoch_d_value = format_value(indicators['Stoch_D'][-1] if not indicators.empty else None)
    
    ichimoku_status = "Above" if not indicators.empty and pd.notnull(df['Close'][-1]) and \
        pd.notnull(indicators['Senkou_Span_A'][-1]) and pd.notnull(indicators['Senkou_Span_B'][-1]) and \
        df['Close'][-1] > max(indicators['Senkou_Span_A'][-1], indicators['Senkou_Span_B'][-1]) else "Below"
    
    cmf_value = format_value(indicators['CMF'][-1] if not indicators.empty else None)
    cmf_status = "Positive" if not indicators.empty and pd.notnull(indicators['CMF'][-1]) and indicators['CMF'][-1] > 0 else "Negative"
    
    obv_value = format_value(indicators['OBV'][-1] if not indicators.empty else None, fmt=".0f")
    vwap_value = format_value(indicators['VWAP'][-1] if not indicators.empty else None)
    
    adx_value = format_value(indicators['ADX'][-1] if not indicators.empty else None)
    adx_status = "Strong Trend" if not indicators.empty and pd.notnull(indicators['ADX'][-1]) and indicators['ADX'][-1] > 25 else "Weak Trend"
    
    psar_value = format_value(indicators['PSAR'][-1] if not indicators.empty else None)
    
    willr_value = format_value(indicators['WilliamsR'][-1] if not indicators.empty else None)
    willr_status = "Oversold" if not indicators.empty and pd.notnull(indicators['WilliamsR'][-1]) and indicators['WilliamsR'][-1] < -80 else \
                  "Overbought" if not indicators.empty and pd.notnull(indicators['WilliamsR'][-1]) and indicators['WilliamsR'][-1] > -20 else "Neutral"
    
    stop_loss = format_value((df['Close'][-1] - 2 * indicators['ATR'][-1]) if not indicators.empty and pd.notnull(indicators['ATR'][-1]) else None)

    report = f"""
# Expert Technical Analysis Report for {ticker}
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Stock Information
- **Company**: {info.get('longName', 'N/A')}
- **Exchange**: {info.get('exchange', 'N/A')}
- **Currency**: {currency_symbol}
- **Current Price**: {currency_symbol}{format_value(df['Close'][-1])}
- **52 Week High**: {currency_symbol}{format_value(info.get('fiftyTwoWeekHigh', 'N/A'))}
- **52 Week Low**: {currency_symbol}{format_value(info.get('fiftyTwoWeekLow', 'N/A'))}
- **Market Sentiment (X)**: {sentiment}

## Recommendation
- **Recommendation**: {recommendation}
- **Signal Score**: {score:.2f}
- **Signals**:
{chr(10).join([f'  - {s}' for s in signals])}

## Technical Indicators
- **RSI**: {rsi_value} ({rsi_status})
- **MACD**: {macd_value} (Signal: {signal_value})
- **SMA1**: {sma1_value}
- **SMA2**: {sma2_value}
- **ATR**: {currency_symbol}{atr_value}
- **Stochastic %K**: {stoch_k_value}
- **Stochastic %D**: {stoch_d_value}
- **Ichimoku Cloud**: {ichimoku_status}
- **CMF**: {cmf_value} ({cmf_status})
- **OBV**: {obv_value}
- **VWAP**: {currency_symbol}{vwap_value}
- **ADX**: {adx_value} ({adx_status})
- **Parabolic SAR**: {currency_symbol}{psar_value}
- **Williams %R**: {willr_value} ({willr_status})

## Key Levels
- **Pivot Point**: {currency_symbol}{format_value(pivot)}
- **Support 1**: {currency_symbol}{format_value(support1)}
- **Resistance 1**: {currency_symbol}{format_value(resistance1)}
- **Fibonacci Levels**:
{chr(10).join([f'  - {level}: {currency_symbol}{format_value(price)}' for level, price in fib_levels.items()])}

## Risk Management
- **Volatility (ATR)**: {currency_symbol}{atr_value}
- **Suggested Stop Loss**: {currency_symbol}{stop_loss}
- **Suggested Take Profit**: {currency_symbol}{format_value(take_profit)}
- **Position Size**: {format_value(position_size, '.0f')} shares (based on 1% risk)

## Backtest Results
- **Total Return**: {backtest_results[0]:.2f}%
- **Win Rate**: {backtest_results[1]:.2f}%
- **Sharpe Ratio**: {backtest_results[2]:.2f}
- **Max Drawdown**: {backtest_results[3]:.2f}%

## Conclusion
This analysis suggests a **{recommendation}** position based on advanced technical indicators and sentiment analysis. Use the risk management parameters and backtest results to inform your trading decisions. Always combine with fundamental analysis.
"""
    return report

# Function to generate analysis details
def generate_analysis_details(ticker: str, recommendation: str, signals: list, score: float) -> str:
    details = f"""
### Expert Analysis Details for {ticker}

The **{recommendation}** recommendation is derived from a multi-indicator system with weighted scoring:

#### Indicators Used
- **RSI**: Contributes {'RSI Oversold (Buy)' in signals and '2.0' or 'RSI Overbought (Sell)' in signals and '-2.0' or '0'}.
- **MACD**: Contributes {'MACD Bullish Crossover (Buy)' in signals and '3.0' or 'MACD Bearish Crossover (Sell)' in signals and '-3.0' or '0'}.
- **SMA**: Contributes {'SMA Bullish Crossover (Buy)' in signals and '2.4' or 'SMA Bearish Crossover (Sell)' in signals and '-2.4' or '0'}.
- **Stochastic**: Contributes {'Stochastic Oversold (Buy)' in signals and '2.0' or 'Stochastic Overbought (Sell)' in signals and '-2.0' or '0'}.
- **Ichimoku**: Contributes {'Ichimoku Bullish (Buy)' in signals and '3.0' or 'Ichimoku Bearish (Sell)' in signals and '-3.0' or '0'}.
- **CMF**: Contributes {'CMF Positive (Buy)' in signals and '0.8' or 'CMF Negative (Sell)' in signals and '-0.8' or '0'}.
- **OBV**: Contributes {'OBV Increasing (Buy)' in signals and '0.8' or 'OBV Decreasing (Sell)' in signals and '-0.8' or '0'}.
- **VWAP**: Contributes {'Price Above VWAP (Buy)' in signals and '1.0' or 'Price Below VWAP (Sell)' in signals and '-1.0' or '0'}.
- **ADX**: Contributes {'Strong Uptrend (Buy)' in signals and '1.0' or 'Strong Downtrend (Sell)' in signals and '-1.0' or '0'}.
- **PSAR**: Contributes {'PSAR Bullish Reversal (Buy)' in signals and '1.0' or 'PSAR Bearish Reversal (Sell)' in signals and '-1.0' or '0'}.
- **Williams %R**: Contributes {'Williams %R Oversold (Buy)' in signals and '0.8' or 'Williams %R Overbought (Sell)' in signals and '-0.8' or '0'}.

#### Weighted Scoring
- **Weights**: MACD (1.5), Ichimoku (1.5), SMA (1.2), RSI (1.0), Stochastic (1.0), VWAP (1.0), ADX (1.0), PSAR (1.0), CMF (0.8), OBV (0.8), Williams %R (0.8).
- **Total Score**: {score:.2f}
- **Signals**:
{chr(10).join([f'  - {s}' for s in signals])}

#### Logic
- Score ≥ 5.0: **Buy**
- Score < 5.0: **Not Buy**

#### Additional Analysis
- **Backtest**: {st.session_state.get('total_return', 0):.2f}% return, {st.session_state.get('win_rate', 0):.2f}% win rate, {st.session_state.get('sharpe_ratio', 0):.2f} Sharpe Ratio.
- **Risk**: Stop-loss at 2x ATR, take-profit at 3x ATR.
- **Sentiment**: Incorporated X-based market sentiment.
"""
    return details

# Streamlit app
def main():
    st.title("Expert Stock Technical Analysis")
    
    # Watchlist management
    if 'watchlist' not in st.session_state:
        st.session_state.watchlist = []
    if 'db_analysis_results' not in st.session_state:
        st.session_state.db_analysis_results = []
    
    # Sidebar for inputs
    with st.sidebar:
        st.header("Stock Selection")
        search_query = st.text_input("Search Company Name", "")
        selected_ticker = None
        matches = []
        
        if search_query:
            matches = search_ticker(search_query)
            if matches:
                options = [f"{company} ({ticker})" for company, ticker in matches]
                selected_option = st.selectbox("Select a stock", options)
                if selected_option:
                    selected_ticker = matches[options.index(selected_option)][1]
            else:
                st.warning("No matching stocks found.")
        
        ticker = st.text_input("Enter Stock Ticker", value=selected_ticker if selected_ticker else "")
        if ticker and ticker not in st.session_state.watchlist:
            if st.button("Add to Watchlist"):
                st.session_state.watchlist.append(ticker)
        
        st.header("Analysis Settings")
        period = st.selectbox("Time Period", ['1mo', '3mo', '6mo', '1y', '2y', '5y'], index=3)
        interval = st.selectbox("Data Interval", ['1d', '1wk', '1mo'], index=0)
        
        st.subheader("Indicator Parameters")
        sma1_window = st.slider("SMA1 Window", 5, 50, 20)
        sma2_window = st.slider("SMA2 Window", 10, 100, 50)
        rsi_window = st.slider("RSI Window", 5, 30, 14)
        macd_fast = st.slider("MACD Fast EMA", 5, 20, 12)
        macd_slow = st.slider("MACD Slow EMA", 10, 50, 26)
        macd_signal = st.slider("MACD Signal", 5, 20, 9)
        bb_window = st.slider("Bollinger Bands Window", 10, 50, 20)
        bb_dev = st.slider("Bollinger Bands Std Dev", 1.0, 3.0, 2.0, step=0.1)
        
        st.subheader("Backtest Parameters")
        bt_sma1 = st.slider("Backtest SMA1", 5, 50, 20)
        bt_sma2 = st.slider("Backtest SMA2", 10, 100, 50)
        bt_macd = st.checkbox("Include MACD in Backtest", value=True)
        
        st.subheader("Risk Management")
        capital = st.number_input("Trading Capital", min_value=1000.0, value=100000.0, step=1000.0)
        risk_pct = st.slider("Risk per Trade (%)", 0.1, 5.0, 1.0, step=0.1)
        
        analyze = st.button("Analyze")
        st.button("Analysis Details", on_click=lambda: st.session_state.update({'show_details': True}))
        analyze_db = st.button("Analyze DB")
    
    # Initialize session state
    for key, default in [('sma1_window', 20), ('sma2_window', 50), ('total_return', 0), ('win_rate', 0), ('sharpe_ratio', 0), ('max_drawdown', 0)]:
        if key not in st.session_state:
            st.session_state[key] = default
    
    # Watchlist dashboard
    if st.session_state.watchlist:
        st.subheader("Watchlist Dashboard")
        watchlist_data = []
        for wt in st.session_state.watchlist:
            try:
                df, info = fetch_stock_data(wt, '1mo', '1d')
                if df.empty:
                    watchlist_data.append([wt, 'No Data', 0, 0])
                    continue
                latest_price = df['Close'][-1]
                change = ((df['Close'][-1] - df['Close'][-2]) / df['Close'][-2] * 100) if len(df) > 1 else 0
                watchlist_data.append([wt, info.get('longName', 'N/A'), latest_price, change])
            except Exception as e:
                logger.error(f"Error processing watchlist ticker {wt}: {str(e)}")
                watchlist_data.append([wt, 'Error', 0, 0])
        watchlist_df = pd.DataFrame(watchlist_data, columns=['Ticker', 'Company', 'Price', 'Daily Change (%)'])
        st.dataframe(watchlist_df, use_container_width=True)
        
        if st.button("Remove Selected from Watchlist"):
            selected = st.session_state.get('watchlist_selection', [])
            st.session_state.watchlist = [t for t in st.session_state.watchlist if t not in selected]
        
        st.subheader("Watchlist Correlation")
        heatmap_fig = create_correlation_heatmap(st.session_state.watchlist, period)
        st.plotly_chart(heatmap_fig, use_container_width=True)
    
    # Analyze DB button
    if analyze_db:
        with st.spinner("Analyzing all tickers in database..."):
            progress_bar = st.progress(0)
            results = asyncio.run(analyze_db_tickers(period, interval, sma1_window, sma2_window, rsi_window, macd_fast, macd_slow, macd_signal, bb_window, bb_dev))
            st.session_state.db_analysis_results = results
            progress_bar.progress(100)
        
        if st.session_state.db_analysis_results:
            with st.expander("Database Analysis Results", expanded=True):
                db_data = [[r['company'], r['ticker'], r['recommendation'], r['score']] for r in st.session_state.db_analysis_results]
                db_df = pd.DataFrame(db_data, columns=['Company', 'Ticker', 'Recommendation', 'Score'])
                st.dataframe(db_df.sort_values(by='Score', ascending=False), use_container_width=True)
                if st.button("Close DB Results"):
                    st.session_state.db_analysis_results = []
    
    # Historical Investment Calculator
    st.subheader("Historical Investment Calculator")
    with st.form("historical_investment_form"):
        hist_investment = st.number_input("Investment Amount", min_value=100.0, value=10000.0, step=100.0)
        hist_date = st.date_input("Investment Date", value=datetime.now() - timedelta(days=3*365), min_value=datetime(2000, 1, 1), max_value=datetime.now())
        hist_submit = st.form_submit_button("Calculate Historical Returns")
    
    if hist_submit:
        with st.spinner("Calculating historical returns..."):
            results, fig = calculate_historical_investment(list(TICKER_DB.items()), hist_investment, hist_date, datetime.now())
            if results:
                hist_data = [
                    [r['company'], r['ticker'], r['shares'], r['initial_value'], r['final_value'],
                     r['profit_loss'], r['return_pct'], r['sharpe_ratio'], r['tax'], r['net_profit_loss']]
                    for r in results
                ]
                hist_df = pd.DataFrame(hist_data, columns=[
                    'Company', 'Ticker', 'Shares', 'Initial Value', 'Final Value',
                    'Profit/Loss', 'Return (%)', 'Sharpe Ratio', 'Tax', 'Net Profit/Loss'
                ])
                st.dataframe(hist_df.sort_values(by='Return (%)', ascending=False), use_container_width=True)
                st.plotly_chart(fig, use_container_width=True)
    
    if analyze and ticker:
        try:
            with st.spinner("Analyzing..."):
                df, info = fetch_stock_data(ticker, period, interval)
                if df.empty or len(df) < 2:
                    st.error("No data found or insufficient data for the ticker.")
                    logger.error(f"No data for ticker {ticker}")
                    return
                
                currency, currency_symbol = get_currency_and_symbol(info)
                indicators = calculate_indicators(df, sma1_window, sma2_window, rsi_window, macd_fast, macd_slow, macd_signal, bb_window, bb_dev)
                if indicators.empty or len(indicators) < 2:
                    st.error("Failed to calculate indicators or insufficient indicator data.")
                    logger.error(f"Empty indicators for {ticker}")
                    return
                
                fib_levels = calculate_fibonacci_levels(df)
                pivot, support1, resistance1 = calculate_pivot_points(df)
                recommendation, signals, score, contributions = generate_recommendation(df, indicators)
                total_return, win_rate, backtest_signals, sharpe_ratio, max_drawdown = backtest_strategy(df, indicators, bt_sma1, bt_sma2, bt_macd)
                sentiment = fetch_sentiment(ticker)
                position_size = calculate_position_size(capital, risk_pct / 100, indicators['ATR'][-1] if not indicators.empty else 0, df['Close'][-1])
                take_profit = df['Close'][-1] + 3 * indicators['ATR'][-1] if not indicators.empty else 0
                
                def format_value(value, fmt=".2f", default="N/A"):
                    try:
                        return f"{value:{fmt}}" if pd.notnull(value) else default
                    except (ValueError, TypeError) as e:
                        logger.error(f"Formatting error: {str(e)}")
                        return default
                
                rsi_value = format_value(indicators['RSI'][-1] if not indicators.empty else None)
                atr_value = format_value(indicators['ATR'][-1] if not indicators.empty else None)
                stoch_k_value = format_value(indicators['Stoch_K'][-1] if not indicators.empty else None)
                stoch_d_value = format_value(indicators['Stoch_D'][-1] if not indicators.empty else None)
                cmf_value = format_value(indicators['CMF'][-1] if not indicators.empty else None)
                obv_value = format_value(indicators['OBV'][-1] if not indicators.empty else None, fmt=".0f")
                vwap_value = format_value(indicators['VWAP'][-1] if not indicators.empty else None)
                adx_value = format_value(indicators['ADX'][-1] if not indicators.empty else None)
                psar_value = format_value(indicators['PSAR'][-1] if not indicators.empty else None)
                willr_value = format_value(indicators['WilliamsR'][-1] if not indicators.empty else None)
                stop_loss = format_value((df['Close'][-1] - 2 * indicators['ATR'][-1]) if not indicators.empty and pd.notnull(indicators['ATR'][-1]) else None)
                
                st.session_state.update({
                    'sma1_window': sma1_window, 'sma2_window': sma2_window, 'total_return': total_return,
                    'win_rate': win_rate, 'sharpe_ratio': sharpe_ratio, 'max_drawdown': max_drawdown
                })
                
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    fig = create_chart(df, indicators, ticker, currency_symbol, fib_levels, pivot, support1, resistance1, backtest_signals)
                    if fig.data:
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.warning("No chart data available.")
                
                with col2:
                    st.subheader("Recommendation")
                    if recommendation == "Buy":
                        st.button("Buy", key="buy", help="Bullish Signal", disabled=True, type="primary", use_container_width=True)
                    else:
                        st.button("Not Buy", key="sell", help="Bearish/Neutral Signal", disabled=True, type="primary", use_container_width=True)
                    
                    st.write(f"**Signal Score**: {score:.2f}")
                    st.write(f"**Market Sentiment (X)**: {sentiment}")
                    st.write("**Signals**:")
                    for signal in signals:
                        st.write(f"- {signal}")
                    
                    st.subheader("Recommendation Reasoning")
                    if contributions:
                        st.write("The recommendation is based on the following indicator signals and their weighted scores:")
                        for indicator, data in contributions.items():
                            st.write(f"- **{indicator}**: {data['signal']}, Score: {data['score']:+.2f}, Weight: {data['weight']:.1f}")
                        st.write(f"**Total Score**: {score:.2f} ({'Buy' if score >= 5 else 'Not Buy'} because score {'≥' if score >= 5 else '<'} 5.0)")
                    else:
                        st.write("No indicator signals available.")
                    
                    st.subheader("Stock Information")
                    st.write(f"**Company**: {info.get('longName', 'N/A')}")
                    st.write(f"**Exchange**: {info.get('exchange', 'N/A')}")
                    st.write(f"**Currency**: {currency} ({currency_symbol})")
                    st.write(f"**Current Price**: {currency_symbol}{format_value(df['Close'][-1])}")
                    st.write(f"**52 Week High**: {currency_symbol}{format_value(info.get('fiftyTwoWeekHigh', 'N/A'))}")
                    st.write(f"**52 Week Low**: {currency_symbol}{format_value(info.get('fiftyTwoWeekLow', 'N/A'))}")
                    
                    st.subheader("Key Levels")
                    st.write(f"**Pivot Point**: {currency_symbol}{format_value(pivot)}")
                    st.write(f"**Support 1**: {currency_symbol}{format_value(support1)}")
                    st.write(f"**Resistance 1**: {currency_symbol}{format_value(resistance1)}")
                    st.write("**Fibonacci Levels**:")
                    for level, price in fib_levels.items():
                        st.write(f"- {level}: {currency_symbol}{format_value(price)}")
                    
                    st.subheader("Advanced Indicators")
                    st.write(f"**RSI**: {rsi_value}")
                    st.write(f"**ATR**: {currency_symbol}{atr_value}")
                    st.write(f"**Stochastic %K**: {stoch_k_value}")
                    st.write(f"**Stochastic %D**: {stoch_d_value}")
                    st.write(f"**CMF**: {cmf_value}")
                    st.write(f"**OBV**: {obv_value}")
                    st.write(f"**VWAP**: {currency_symbol}{vwap_value}")
                    st.write(f"**ADX**: {adx_value}")
                    st.write(f"**Parabolic SAR**: {currency_symbol}{psar_value}")
                    st.write(f"**Williams %R**: {willr_value}")
                    
                    st.subheader("Risk Management")
                    st.write(f"**Stop Loss**: {currency_symbol}{stop_loss}")
                    st.write(f"**Take Profit**: {currency_symbol}{format_value(take_profit)}")
                    st.write(f"**Position Size**: {format_value(position_size, '.0f')} shares")
                    
                    st.subheader("Backtest Results")
                    st.write(f"**Total Return**: {total_return:.2f}%")
                    st.write(f"**Win Rate**: {win_rate:.2f}%")
                    st.write(f"**Sharpe Ratio**: {sharpe_ratio:.2f}")
                    st.write(f"**Max Drawdown**: {max_drawdown:.2f}%")
                    
                    # Manual Profit/Loss Calculator
                    st.subheader("Manual Profit/Loss Calculator")
                    with st.form("profit_loss_form"):
                        investment = st.number_input("Investment Amount", min_value=100.0, value=10000.0, step=100.0)
                        start_date = st.date_input("Start Date", value=datetime.now() - timedelta(days=365), min_value=df.index[0].date(), max_value=datetime.now())
                        end_date = st.date_input("End Date", value=datetime.now(), min_value=start_date, max_value=datetime.now())
                        pl_submit = st.form_submit_button("Calculate Profit/Loss")
                    
                    if pl_submit:
                        pl_data = calculate_profit_loss(df, investment, start_date, end_date, currency_symbol)
                        st.write("**Profit/Loss Calculation**:")
                        st.write(f"- **Shares Purchased**: {format_value(pl_data['shares'], '.2f')}")
                        st.write(f"- **Initial Price**: {currency_symbol}{format_value(pl_data['initial_price'])}")
                        st.write(f"- **Final Price**: {currency_symbol}{format_value(pl_data['final_price'])}")
                        st.write(f"- **Initial Value**: {currency_symbol}{format_value(pl_data['initial_value'])}")
                        st.write(f"- **Final Value**: {currency_symbol}{format_value(pl_data['final_value'])}")
                        st.write(f"- **Profit/Loss**: {currency_symbol}{format_value(pl_data['profit_loss'])}")
                        st.write(f"- **Return (%)**: {format_value(pl_data['return_pct'])}%")
                        st.write(f"- **Sharpe Ratio**: {format_value(pl_data['sharpe_ratio'])}")
                        st.write(f"- **Tax (Estimated)**: {currency_symbol}{format_value(pl_data['tax'])}")
                        st.write(f"- **Net Profit/Loss**: {currency_symbol}{format_value(pl_data['net_profit_loss'])}")
                
                st.subheader("Analysis Report")
                report = generate_report(ticker, info, df, indicators, recommendation, signals, score, 
                                       fib_levels, pivot, support1, resistance1, 
                                       (total_return, win_rate, sharpe_ratio, max_drawdown), 
                                       currency_symbol, position_size, take_profit, sentiment)
                st.markdown(report)
                
                buffer = io.StringIO()
                buffer.write(report)
                st.download_button(
                    label="Download Analysis Report",
                    data=buffer.getvalue(),
                    file_name=f"{ticker}_expert_report.txt",
                    mime="text/plain"
                )
                
                valid_signals = [s for s in backtest_signals if isinstance(s, (list, tuple)) and len(s) >= 3]
                signals_df = pd.DataFrame(valid_signals, columns=['Type', 'Date', 'Price']) if valid_signals else pd.DataFrame()
                if not signals_df.empty:
                    signals_csv = signals_df.to_csv(index=False)
                    st.download_button(
                        label="Download Backtest Signals",
                        data=signals_csv,
                        file_name=f"{ticker}_backtest_signals.csv",
                        mime="text/csv"
                    )
                
                if st.session_state.get('show_details', False):
                    with st.expander("Analysis Details", expanded=True):
                        details = generate_analysis_details(ticker, recommendation, signals, score)
                        st.markdown(details)
                        if st.button("Close Details"):
                            st.session_state.show_details = False
    
        except Exception as e:
            st.error(f"Error: {str(e)}")
            logger.error(f"Main loop error: {str(e)}")
    
    st.markdown("""
    ### Instructions
    - Search for a company (e.g., 'Reliance') or enter a ticker (e.g., RELIANCE.NS).
    - Add stocks to your watchlist for a summary dashboard and correlation analysis.
    - Customize indicator parameters (SMA, RSI, MACD, Bollinger Bands) and backtest settings.
    - Set trading capital and risk percentage for position sizing.
    - Click 'Analyze' to view charts, recommendations, and risk management.
    - Use 'Recommendation Reasoning' to understand why a Buy or Not Buy signal was generated.
    - Use 'Analysis Details' for deeper methodology insights.
    - Use 'Manual Profit/Loss Calculator' to calculate returns for a specific investment amount and date range.
    - Click 'Analyze DB' to run analysis on all tickers in the database and view recommendations.
    - Use 'Historical Investment Calculator' to see what an investment in each ticker would be worth today.
    - Download the report or backtest signals for offline review.
    - Recommendations incorporate ADX, PSAR, Williams %R, and X sentiment.
    - Always combine with fundamental analysis and proper risk management.
    """)

if __name__ == "__main__":
    main()
