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
import logging
import requests
from packaging import version
from functools import lru_cache
from typing import Union, List, Tuple, Dict

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Ensure set_page_config is called only once
if not st.session_state.get("page_config_set", False):
    st.set_page_config(layout="wide", page_title="Expert Stock Technical Analysis")
    st.session_state.page_config_set = True

# Function to load tickers from CSV
def load_tickers(csv_path: str = "EQUITY_L.csv") -> dict:
    """Load ticker symbols from a CSV file."""
    try:
        df = pd.read_csv(csv_path)
        tickers = {row['NAME OF COMPANY']: f"{row['SYMBOL']}.NS" for _, row in df.iterrows()}
        logger.debug(f"Loaded {len(tickers)} tickers from CSV")
        return tickers
    except Exception as e:
        logger.error(f"Error loading tickers from CSV: {str(e)}")
        return {}

# Cache stock data fetching
@lru_cache(maxsize=100)
def fetch_yfinance_data(ticker: str, start: str, end: str, interval: str, retries: int = 3, proxies: Dict = None) -> Tuple[pd.DataFrame, dict]:
    """Fetch data using yfinance with version-aware proxy handling."""
    try:
        yf_version = getattr(yf, '__version__', '0.1.0')
        use_proxies = proxies and version.parse(yf_version) >= version.parse('0.2.0')
        
        stock = yf.Ticker(ticker)
        for attempt in range(retries):
            try:
                if use_proxies:
                    df = stock.history(start=start, end=end, interval=interval, proxies=proxies)
                else:
                    df = stock.history(start=start, end=end, interval=interval)
                if not df.empty:
                    logger.debug(f"Fetched data for {ticker}: {len(df)} rows")
                    return df, stock.info
                logger.warning(f"Empty data for {ticker}, attempt {attempt + 1}")
            except Exception as e:
                logger.error(f"yfinance attempt {attempt + 1} failed for {ticker}: {str(e)}")
                if "429" in str(e).lower():
                    return pd.DataFrame(), {}
            time.sleep(5 * (attempt + 1))
        logger.error(f"All {retries} yfinance attempts failed for {ticker}")
        return pd.DataFrame(), {}
    except Exception as e:
        logger.error(f"Error fetching data for {ticker}: {str(e)}")
        return pd.DataFrame(), {}

def fetch_stock_data(ticker_name: str, ticker_symbol: str, start_date: str, end_date: str, interval: str, proxies: Dict = None) -> Tuple[pd.DataFrame, dict]:
    """Fetch stock data using yfinance."""
    df, info = fetch_yfinance_data(ticker_symbol, start_date, end_date, interval, proxies=proxies)
    if df.empty:
        logger.error(f"No data for {ticker_name} ({ticker_symbol})")
    return df, info

def generate_mock_data(start_date: datetime, end_date: datetime) -> pd.DataFrame:
    """Generate mock stock data for testing."""
    dates = pd.date_range(start=start_date, end=end_date, freq='B')
    data = {
        'Open': np.random.uniform(100, 200, len(dates)),
        'High': np.random.uniform(110, 210, len(dates)),
        'Low': np.random.uniform(90, 190, len(dates)),
        'Close': np.random.uniform(100, 200, len(dates)),
        'Volume': np.random.randint(1000, 100000, len(dates))
    }
    df = pd.DataFrame(data, index=dates)
    return df

def test_yahoo_finance_connectivity() -> str:
    """Test connectivity to Yahoo Finance."""
    try:
        response = requests.get("https://finance.yahoo.com", timeout=10)
        return f"Yahoo Finance accessible: HTTP {response.status_code}"
    except Exception as e:
        return f"Failed to reach Yahoo Finance: {str(e)}"

def get_currency_and_symbol(ticker_info: dict) -> tuple:
    """Determine currency and symbol based on exchange and country."""
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
    return ('USD', '$')

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

def calculate_pivot_points(df: pd.DataFrame) -> tuple:
    if df.empty or len(df) < 1:
        return 0, 0, 0
    pivot = (df['High'][-1] + df['Low'][-1] + df['Close'][-1]) / 3
    support1 = (2 * pivot) - df['High'][-1]
    resistance1 = (2 * pivot) - df['Low'][-1]
    return pivot, support1, resistance1

def calculate_vwap(df: pd.DataFrame) -> pd.Series:
    if df.empty:
        return pd.Series()
    typical_price = (df['High'] + df['Low'] + df['Close']) / 3
    return (typical_price * df['Volume']).cumsum() / df['Volume'].cumsum()

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

def analyze_ticker(ticker_name: str, ticker_symbol: str, start_date: str, end_date: str, interval: str, proxies: Dict = None, use_mock: bool = False) -> Dict:
    """Analyze stock using advanced indicators and provide recommendation."""
    if use_mock:
        df = generate_mock_data(datetime.strptime(start_date, '%Y-%m-%d'), datetime.strptime(end_date, '%Y-%m-%d'))
        info = {}
    else:
        df, info = fetch_stock_data(ticker_name, ticker_symbol, start_date, end_date, interval, proxies)
        if df.empty:
            return {"recommendation": "Not Buy", "details": "Data unavailable", "score": 0, "current_price": None}
    
    if len(df) < 50:
        return {"recommendation": "Not Buy", "details": "Insufficient data (<50 days)", "score": 0, "current_price": None}
    
    try:
        indicators = calculate_indicators(df, 20, 50, 14, 12, 26, 9, 20, 2.0)
        recommendation, signals, score, contributions = generate_recommendation(df, indicators)
        current_price = df['Close'].iloc[-1] if not df.empty else None
        
        details = []
        for indicator, data in contributions.items():
            details.append(f"{indicator}: {data['signal']} (Score: {data['score']:+.2f}, Weight: {data['weight']:.1f})")
        details.append(f"Total Score: {score:.2f} (Threshold: ≥5 for Buy)")
        
        return {
            "recommendation": recommendation,
            "details": "\n".join(details),
            "score": score,
            "current_price": current_price
        }
    except Exception as e:
        logger.error(f"Error analyzing {ticker_name}: {str(e)}")
        return {"recommendation": "Not Buy", "details": f"Analysis failed: {str(e)}", "score": 0, "current_price": None}

def calculate_investment_returns(ticker_name: str, ticker_symbol: str, investment: float, start_date: datetime, end_date: datetime, proxies: Dict = None, use_mock: bool = False) -> Dict:
    start_str = start_date.strftime('%Y-%m-%d')
    end_str = end_date.strftime('%Y-%m-%d')
    interval = "1d"
    
    if use_mock:
        df = generate_mock_data(start_date, end_date)
    else:
        df, _ = fetch_stock_data(ticker_name, ticker_symbol, start_str, end_str, interval, proxies)
        if df.empty:
            return {"error": f"No valid data for {ticker_name}"}
    
    if len(df) < 2:
        return {"error": f"Insufficient data for {ticker_name}"}
    
    try:
        start_price = df['Close'].iloc[0]
        end_price = df['Close'].iloc[-1]
        
        if pd.isna(start_price) or pd.isna(end_price):
            return {"error": f"Invalid price data for {ticker_name}"}
        
        shares = investment / start_price
        final_value = shares * end_price
        profit_loss = final_value - investment
        profit_loss_pct = (profit_loss / investment) * 100
        
        return {
            "shares": shares,
            "final_value": final_value,
            "profit_loss": profit_loss,
            "profit_loss_pct": profit_loss_pct,
            "mock": use_mock
        }
    except Exception as e:
        logger.error(f"Error calculating returns for {ticker_name}: {str(e)}")
        return {"error": f"Calculation failed for {ticker_name}: {str(e)}"}

def calculate_profit_loss_dates(ticker_name: str, ticker_symbol: str, investment: float, start_date: datetime, end_date: datetime, proxies: Dict = None) -> str:
    start_str = start_date.strftime('%Y-%m-%d')
    end_str = end_date.strftime('%Y-%m-%d')
    interval = "1d"
    
    df, _ = fetch_stock_data(ticker_name, ticker_symbol, start_str, end_str, interval, proxies)
    if df.empty:
        return "Data unavailable"
    
    profit_dates = []
    loss_dates = []
    current_date = datetime.now().date()
    
    date_range = pd.date_range(start=start_date, end=end_date, freq='MS')
    
    for invest_date in date_range:
        if invest_date.date() >= current_date:
            continue
        invest_dt = datetime.combine(invest_date.date(), datetime.min.time())
        if invest_dt >= end_date:
            continue
        
        try:
            start_price = df['Close'].loc[invest_dt:invest_dt + timedelta(days=1)].iloc[0]
            end_price = df['Close'].iloc[-1]
            
            if pd.isna(start_price) or pd.isna(end_price):
                continue
            
            shares = investment / start_price
            final_value = shares * end_price
            profit_loss = final_value - investment
            
            if profit_loss > 0:
                profit_dates.append(invest_date.strftime("%Y-%m"))
            elif profit_loss < 0:
                loss_dates.append(invest_date.strftime("%Y-%m"))
        except Exception as e:
            logger.debug(f"Skipping date {invest_date} for {ticker_name}: {str(e)}")
            continue
    
    def summarize_dates(dates):
        if not dates:
            return "None"
        dates = sorted(dates)
        ranges = []
        start = dates[0]
        prev = dates[0]
        for d in dates[1:] + ["END"]:
            if d == "END" or d != prev:
                if start == prev:
                    ranges.append(start)
                else:
                    ranges.append(f"{start} to {prev}")
                start = d
            prev = d
        return "; ".join(ranges) if ranges else "None"
    
    return f"Profit: {summarize_dates(profit_dates)}\nLoss: {summarize_dates(loss_dates)}"

def create_correlation_heatmap(tickers: List[str], start_date: str, end_date: str, interval: str) -> go.Figure:
    data = {}
    for ticker in tickers[:5]:
        df, _ = fetch_yfinance_data(ticker, start_date, end_date, interval)
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

def calculate_position_size(capital: float, risk_pct: float, atr: float, current_price: float) -> float:
    if atr <= 0 or current_price <= 0:
        logger.warning("Invalid ATR or price for position sizing")
        return 0
    risk_per_share = 2 * atr
    shares = (capital * risk_pct) / risk_per_share
    return min(shares, capital / current_price)

def generate_report(ticker: str, info: dict, df: pd.DataFrame, indicators: pd.DataFrame, recommendation: str, signals: list, score: float, fib_levels: dict, pivot: float, support1: float, resistance1: float, backtest_results: tuple, currency_symbol: str, position_size: float, take_profit: float) -> str:
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
This analysis suggests a **{recommendation}** position based on advanced technical indicators. Use the risk management parameters and backtest results to inform your trading decisions.
"""
    return report

def main():
    st.title("Expert Stock Technical Analysis Dashboard")
    
    # Initialize session state
    if 'watchlist' not in st.session_state:
        st.session_state.watchlist = []
    for key, default in [('sma1_window', 20), ('sma2_window', 50), ('total_return', 0), ('win_rate', 0), ('sharpe_ratio', 0), ('max_drawdown', 0)]:
        if key not in st.session_state:
            st.session_state[key] = default
    
    # Load tickers from CSV
    TICKER_DB = load_tickers()
    if not TICKER_DB:
        st.error("Failed to load tickers from CSV. Please ensure 'EQUITY_L.csv' is available.")
        return
    
    # Sidebar for settings
    with st.sidebar:
        st.header("Settings")
        debug_mode = st.checkbox("Enable Debug Mode")
        use_mock_data = st.checkbox("Use Mock Data")
        
        use_proxy = st.checkbox("Use Proxy")
        proxies = None
        if use_proxy:
            proxy_url = st.text_input("Proxy URL (e.g., http://proxy:port)")
            if proxy_url:
                proxies = {"http": proxy_url, "https": proxy_url}
        
        st.header("Analysis Parameters")
        period_options = {'1mo': 30, '3mo': 90, '6mo': 180, '1y': 365, '2y': 730, '5y': 1825}
        period = st.selectbox("Time Period", list(period_options.keys()), index=3)
        interval = st.selectbox("Data Interval", ['1d', '1wk', '1mo'], index=0)
        
        sma1_window = st.slider("SMA1 Window", 5, 50, 20)
        sma2_window = st.slider("SMA2 Window", 10, 100, 50)
        rsi_window = st.slider("RSI Window", 5, 30, 14)
        macd_fast = st.slider("MACD Fast EMA", 5, 20, 12)
        macd_slow = st.slider("MACD Slow EMA", 10, 50, 26)
        macd_signal = st.slider("MACD Signal", 5, 20, 9)
        bb_window = st.slider("Bollinger Bands Window", 10, 50, 20)
        bb_dev = st.slider("Bollinger Bands Std Dev", 1.0, 3.0, 2.0, step=0.1)
        
        st.header("Backtest Parameters")
        bt_sma1 = st.slider("Backtest SMA1", 5, 50, 20)
        bt_sma2 = st.slider("Backtest SMA2", 10, 100, 50)
        bt_macd = st.checkbox("Include MACD in Backtest", value=True)
        
        st.header("Risk Management")
        capital = st.number_input("Trading Capital (INR)", min_value=1000.0, value=100000.0, step=1000.0)
        risk_pct = st.slider("Risk per Trade (%)", 0.1, 5.0, 1.0, step=0.1)
        
        if st.button("Clear Cache"):
            st.cache_data.clear()
            st.success("Cache cleared successfully!")
        
        # Ticker selection
        st.header("Stock Selection")
        ticker_search = st.text_input("Search Stock")
        filtered_tickers = {name: ticker for name, ticker in TICKER_DB.items() if ticker_search.lower() in name.lower()}
        selected_ticker_name = st.selectbox("Select Stock", options=list(filtered_tickers.keys()), index=0 if filtered_tickers else None)
        selected_ticker_symbol = filtered_tickers.get(selected_ticker_name, "")

    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=period_options[period])
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')

    # Section 1: Manual Investment Calculator
    st.header("Investment Profit/Loss Calculator")
    col1, col2, col3 = st.columns(3)
    with col1:
        ticker_calc_name = st.selectbox("Select Stock for Calculator", list(TICKER_DB.keys()))
        ticker_calc_symbol = TICKER_DB.get(ticker_calc_name, "")
    with col2:
        investment = st.number_input("Investment Amount (INR)", min_value=1000.0, value=10000.0)
    with col3:
        invest_date = st.date_input("Investment Date", value=datetime.now() - timedelta(days=30), max_value=datetime.now().date())
    
    if st.button("Calculate Returns"):
        invest_dt = datetime.combine(invest_date, datetime.min.time())
        
        with st.spinner(f"Fetching data for {ticker_calc_name}..."):
            results = calculate_investment_returns(ticker_calc_name, ticker_calc_symbol, investment, invest_dt, end_date, proxies, use_mock_data)
        
        if "error" not in results:
            st.subheader(f"Results for {ticker_calc_name}")
            if results.get("mock"):
                st.warning("Using mock data")
            st.write(f"Shares Purchased: {results['shares']:.2f}")
            st.write(f"Initial Investment: ₹{investment:,.2f}")
            st.write(f"Current Value: ₹{results['final_value']:,.2f}")
            st.write(f"Profit/Loss: ₹{results['profit_loss']:,.2f}")
            st.write(f"Return Percentage: {results['profit_loss_pct']:.2f}%")
        else:
            st.error(results["error"])
            if debug_mode:
                st.text_area("Debug Log", logger.handlers[0].stream.getvalue(), height=200)
    
    # Section 2: Watchlist Dashboard
    st.header("Watchlist Dashboard")
    if st.session_state.watchlist:
        watchlist_data = []
        for wt in st.session_state.watchlist:
            try:
                df, info = fetch_yfinance_data(wt, start_date_str, end_date_str, interval)
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
        heatmap_fig = create_correlation_heatmap(st.session_state.watchlist, start_date_str, end_date_str, interval)
        st.plotly_chart(heatmap_fig, use_container_width=True)
    
    st.subheader("Add to Watchlist")
    watchlist_ticker = st.text_input("Enter Stock Ticker for Watchlist")
    if watchlist_ticker and watchlist_ticker not in st.session_state.watchlist:
        if st.button("Add to Watchlist"):
            st.session_state.watchlist.append(watchlist_ticker)
    
    # Section 3: AnalyzeDB
    st.header("Database Analysis")
    if st.button("AnalyzeDB"):
        analysis_results = []
        progress_bar = st.progress(0)
        total_tickers = len(TICKER_DB)
        
        for idx, (ticker_name, ticker_symbol) in enumerate(TICKER_DB.items()):
            with st.spinner(f"Analyzing {ticker_name}..."):
                result = analyze_ticker(ticker_name, ticker_symbol, start_date_str, end_date_str, interval, proxies, use_mock_data)
                analysis_results.append({
                    "Stock": ticker_name,
                    "Current Price": result["current_price"],
                    "Recommendation": result["recommendation"],
                    "Analysis Details": result["details"],
                    "Score": result["score"]
                })
            progress_bar.progress((idx + 1) / total_tickers)
        
        if analysis_results:
            results_df = pd.DataFrame(analysis_results)
            results_df["Current Price"] = results_df["Current Price"].apply(lambda x: f"₹{x:,.2f}" if pd.notna(x) else "N/A")
            st.subheader("Analysis Results")
            st.write("Recommendations based on advanced technical indicators (RSI, MACD, SMA, Stochastic, Ichimoku, CMF, OBV, VWAP, ADX, PSAR, Williams %R):")
            st.dataframe(results_df[["Stock", "Current Price", "Recommendation", "Score"]], use_container_width=True)
            
            for result in analysis_results:
                with st.expander(f"Details for {result['Stock']} (Current Price: {result['Current Price']})"):
                    st.text(result["Analysis Details"])
        else:
            st.error("No analysis results available")
            if debug_mode:
                st.text_area("Debug Log", logger.handlers[0].stream.getvalue(), height=200)
    
    # Section 4: Historical Investment Analysis
    st.header("Historical Investment Analysis")
    col1, col2 = st.columns(2)
    with col1:
        hist_investment = st.number_input("Historical Investment Amount (INR)", min_value=1000.0, value=10000.0)
    with col2:
        hist_date = st.date_input("Historical Investment Date", value=datetime.now() - timedelta(days=365*3), max_value=datetime.now().date())
    
    if st.button("Calculate Historical Returns"):
        hist_start_date = datetime.combine(hist_date, datetime.min.time())
        
        hist_results = []
        progress_bar = st.progress(0)
        total_tickers = len(TICKER_DB)
        failed_tickers = []
        
        for idx, (ticker_name, ticker_symbol) in enumerate(TICKER_DB.items()):
            with st.spinner(f"Calculating returns for {ticker_name}..."):
                results = calculate_investment_returns(ticker_name, ticker_symbol, hist_investment, hist_start_date, end_date, proxies, use_mock_data)
                if "error" not in results:
                    profit_loss_dates = calculate_profit_loss_dates(
                        ticker_name, ticker_symbol, hist_investment,
                        hist_start_date, end_date, proxies
                    )
                    hist_results.append({
                        "Stock": ticker_name,
                        "Shares": results['shares'],
                        "Final Value": results['final_value'],
                        "Profit/Loss": results['profit_loss'],
                        "Return %": results['profit_loss_pct'],
                        "Profit/Loss Dates": profit_loss_dates,
                        "Mock Data": "Yes" if results.get("mock") else "No"
                    })
                else:
                    failed_tickers.append(f"{ticker_name}: {results['error']}")
            progress_bar.progress((idx + 1) / total_tickers)
        
        if hist_results:
            results_df = pd.DataFrame(hist_results)
            results_df["Shares"] = results_df["Shares"].map("{:.2f}".format)
            results_df["Final Value"] = results_df["Final Value"].map("₹{:,.2f}".format)
            results_df["Profit/Loss"] = results_df["Profit/Loss"].map("₹{:,.2f}".format)
            results_df["Return %"] = results_df["Return %"].map("{:.2f}%".format)
            
            def style_profit_loss(val):
                color = "color: green" if float(val.replace("₹", "").replace(",", "")) > 0 else "color: red"
                return f"{color}; font-weight: bold"
            
            styled_df = results_df.style.applymap(style_profit_loss, subset=["Profit/Loss"])
            
            st.subheader("Historical Investment Results")
            st.write("Profit (green) and Loss (red) for selected date, with dates when investment would yield profit/loss:")
            st.dataframe(styled_df, use_container_width=True)
        else:
            st.error("No data available for the selected period")
        
        if failed_tickers:
            st.warning(f"Failed to fetch data for: {', '.join(failed_tickers)}")
            if debug_mode:
                st.text_area("Debug Log", logger.handlers[0].stream.getvalue(), height=200)
    
    # Section 5: Single Stock Analysis
    st.header("Single Stock Analysis")
    if st.button("Analyze Single Stock") and selected_ticker_symbol:
        try:
            with st.spinner("Analyzing..."):
                df, info = fetch_stock_data(selected_ticker_name, selected_ticker_symbol, start_date_str, end_date_str, interval, proxies)
                if df.empty or len(df) < 2:
                    st.error("No data found or insufficient data for the ticker.")
                    return
                
                currency, currency_symbol = get_currency_and_symbol(info)
                indicators = calculate_indicators(df, sma1_window, sma2_window, rsi_window, macd_fast, macd_slow, macd_signal, bb_window, bb_dev)
                if indicators.empty or len(indicators) < 2:
                    st.error("Failed to calculate indicators.")
                    return
                
                fib_levels = calculate_fibonacci_levels(df)
                pivot, support1, resistance1 = calculate_pivot_points(df)
                recommendation, signals, score, contributions = generate_recommendation(df, indicators)
                total_return, win_rate, backtest_signals, sharpe_ratio, max_drawdown = backtest_strategy(df, indicators, bt_sma1, bt_sma2, bt_macd)
                position_size = calculate_position_size(capital, risk_pct / 100, indicators['ATR'][-1] if not indicators.empty else 0, df['Close'][-1])
                take_profit = df['Close'][-1] + 3 * indicators['ATR'][-1] if not indicators.empty else 0
                
                def format_value(value, fmt=".2f", default="N/A"):
                    try:
                        return f"{value:{fmt}}" if pd.notnull(value) else default
                    except (ValueError, TypeError):
                        return default
                
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    fig = create_chart(df, indicators, selected_ticker_symbol, currency_symbol, fib_levels, pivot, support1, resistance1, backtest_signals)
                    if fig.data:
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.warning("No chart data available.")
                
                with col2:
                    st.subheader("Recommendation")
                    if recommendation == "Buy":
                        st.button("Buy", key="buy", disabled=True, type="primary", use_container_width=True)
                    else:
                        st.button("Not Buy", key="sell", disabled=True, type="primary", use_container_width=True)
                    
                    st.write(f"**Signal Score**: {score:.2f}")
                    st.write("**Signals**:")
                    for signal in signals:
                        st.write(f"- {signal}")
                    
                    st.subheader("Recommendation Reasoning")
                    if contributions:
                        for indicator, data in contributions.items():
                            st.write(f"- **{indicator}**: {data['signal']}, Score: {data['score']:+.2f}, Weight: {data['weight']:.1f}")
                        st.write(f"**Total Score**: {score:.2f} ({'Buy' if score >= 5 else 'Not Buy'})")
                    
                    st.subheader("Stock Information")
                    st.write(f"**Company**: {info.get('longName', 'N/A')}")
                    st.write(f"**Exchange**: {info.get('exchange', 'N/A')}")
                    st.write(f"**Currency**: {currency} ({currency_symbol})")
                    st.write(f"**Current Price**: {currency_symbol}{format_value(df['Close'][-1])}")
                    
                    st.subheader("Key Levels")
                    st.write(f"**Pivot Point**: {currency_symbol}{format_value(pivot)}")
                    st.write(f"**Support 1**: {currency_symbol}{format_value(support1)}")
                    st.write(f"**Resistance 1**: {currency_symbol}{format_value(resistance1)}")
                    st.write("**Fibonacci Levels**:")
                    for level, price in fib_levels.items():
                        st.write(f"- {level}: {currency_symbol}{format_value(price)}")
                    
                    st.subheader("Risk Management")
                    st.write(f"**Stop Loss**: {currency_symbol}{format_value(df['Close'][-1] - 2 * indicators['ATR'][-1] if not indicators.empty else 0)}")
                    st.write(f"**Take Profit**: {currency_symbol}{format_value(take_profit)}")
                    st.write(f"**Position Size**: {format_value(position_size, '.0f')} shares")
                    
                    st.subheader("Backtest Results")
                    st.write(f"**Total Return**: {total_return:.2f}%")
                    st.write(f"**Win Rate**: {win_rate:.2f}%")
                    st.write(f"**Sharpe Ratio**: {sharpe_ratio:.2f}")
                    st.write(f"**Max Drawdown**: {max_drawdown:.2f}%")
                
                st.subheader("Analysis Report")
                report = generate_report(selected_ticker_symbol, info, df, indicators, recommendation, signals, score, 
                                       fib_levels, pivot, support1, resistance1, 
                                       (total_return, win_rate, sharpe_ratio, max_drawdown), 
                                       currency_symbol, position_size, take_profit)
                st.markdown(report)
                
                buffer = io.StringIO()
                buffer.write(report)
                st.download_button(
                    label="Download Analysis Report",
                    data=buffer.getvalue(),
                    file_name=f"{selected_ticker_symbol}_expert_report.txt",
                    mime="text/plain"
                )
                
                valid_signals = [s for s in backtest_signals if isinstance(s, (list, tuple)) and len(s) >= 3]
                signals_df = pd.DataFrame(valid_signals, columns=['Type', 'Date', 'Price']) if valid_signals else pd.DataFrame()
                if not signals_df.empty:
                    signals_csv = signals_df.to_csv(index=False)
                    st.download_button(
                        label="Download Backtest Signals",
                        data=signals_csv,
                        file_name=f"{selected_ticker_symbol}_backtest_signals.csv",
                        mime="text/csv"
                    )
    
        except Exception as e:
            st.error(f"Error: {str(e)}")
            if debug_mode:
                st.text_area("Debug Log", logger.handlers[0].stream.getvalue(), height=200)

if __name__ == "__main__":
    main()
