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
import uuid
import time

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Ensure set_page_config is called only once
if not st.session_state.get("page_config_set", False):
    st.set_page_config(layout="wide", page_title="Expert Stock Technical Analysis")
    st.session_state.page_config_set = True

# Expanded ticker database
# Expanded ticker database
TICKER_DB = {
    # Existing Indian stocks
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
    
    # Additional Indian stocks - Large Caps
    "TCS": "TCS.NS",
    "Wipro": "WIPRO.NS",
    "HCL Technologies": "HCLTECH.NS",
    "ITC Limited": "ITC.NS",
    "Kotak Mahindra Bank": "KOTAKBANK.NS",
    "Mahindra & Mahindra": "M&M.NS",
    "Asian Paints": "ASIANPAINT.NS",
    "Bajaj Auto": "BAJAJ-AUTO.NS",
    "Tech Mahindra": "TECHM.NS",
    "Titan Company": "TITAN.NS",
    "UltraTech Cement": "ULTRACEMCO.NS",
    "Nestle India": "NESTLEIND.NS",
    "Power Grid Corporation": "POWERGRID.NS",
    "NTPC": "NTPC.NS",
    "ONGC": "ONGC.NS",
    "Coal India": "COALINDIA.NS",
    "IndusInd Bank": "INDUSINDBK.NS",
    "Grasim Industries": "GRASIM.NS",
    "Adani Ports": "ADANIPORTS.NS",
    "Hero MotoCorp": "HEROMOTOCO.NS",
    "Bajaj Finserv": "BAJAJFINSV.NS",
    "Tata Consumer Products": "TATACONSUM.NS",
    "JSW Steel": "JSWSTEEL.NS",
    "Britannia Industries": "BRITANNIA.NS",
    "Cipla": "CIPLA.NS",
    "Dr. Reddy's Laboratories": "DRREDDY.NS",
    "Eicher Motors": "EICHERMOT.NS",
    "Hindalco Industries": "HINDALCO.NS",
    "Bharat Petroleum": "BPCL.NS",
    "Divi's Laboratories": "DIVISLAB.NS",
    
    # More Indian Large Caps
    "HDFC Life Insurance": "HDFCLIFE.NS",
    "SBI Life Insurance": "SBILIFE.NS",
    "Adani Green Energy": "ADANIGREEN.NS",
    "Adani Transmission": "ADANITRANS.NS",
    "Adani Total Gas": "ATGL.NS",
    "Avenue Supermarts (DMart)": "DMART.NS",
    "Bajaj Holdings": "BAJAJHLDNG.NS",
    "Bandhan Bank": "BANDHANBNK.NS",
    "Bank of Baroda": "BANKBARODA.NS",
    "Berger Paints": "BERGEPAINT.NS",
    "Bharat Electronics": "BEL.NS",
    "Biocon": "BIOCON.NS",
    "Bosch": "BOSCHLTD.NS",
    "Canara Bank": "CANBK.NS",
    "Cholamandalam Investment": "CHOLAFIN.NS",
    "Colgate Palmolive": "COLPAL.NS",
    "Container Corporation": "CONCOR.NS",
    "Dabur India": "DABUR.NS",
    "DLF": "DLF.NS",
    "Federal Bank": "FEDERALBNK.NS",
    "Godrej Consumer Products": "GODREJCP.NS",
    "Godrej Properties": "GODREJPROP.NS",
    "Havells India": "HAVELLS.NS",
    "HDFC AMC": "HDFCAMC.NS",
    "Hindustan Aeronautics": "HAL.NS",
    "Hindustan Petroleum": "HINDPETRO.NS",
    "Hindustan Zinc": "HINDZINC.NS",
    "IDFC First Bank": "IDFCFIRSTB.NS",
    "Indian Oil Corporation": "IOC.NS",
    "Indus Towers": "INDUSTOWER.NS",
    
    # Indian Mid Caps
    "Abbott India": "ABBOTINDIA.NS",
    "ACC": "ACC.NS",
    "Aditya Birla Capital": "ABCAPITAL.NS",
    "Aditya Birla Fashion": "ABFRL.NS",
    "Ambuja Cements": "AMBUJACEM.NS",
    "Apollo Hospitals": "APOLLOHOSP.NS",
    "Ashok Leyland": "ASHOKLEY.NS",
    "Aurobindo Pharma": "AUROPHARMA.NS",
    "Balkrishna Industries": "BALKRISIND.NS",
    "Bata India": "BATAINDIA.NS",
    "Bharat Forge": "BHARATFORG.NS",
    "Bharti Infratel": "INFRATEL.NS",
    "Birla Corporation": "BIRLACORPN.NS",
    "Bombay Dyeing": "BOMDYEING.NS",
    "CESC": "CESC.NS",
    "Coforge": "COFORGE.NS",
    "Crompton Greaves Consumer": "CROMPTON.NS",
    "Cummins India": "CUMMINSIND.NS",
    "Dixon Technologies": "DIXON.NS",
    "Emami": "EMAMILTD.NS",
    "Exide Industries": "EXIDEIND.NS",
    "Future Retail": "FRETAIL.NS",
    "Glenmark Pharmaceuticals": "GLENMARK.NS",
    "GMR Infrastructure": "GMRINFRA.NS",
    "Godrej Industries": "GODREJIND.NS",
    "Granules India": "GRANULES.NS",
    "Gujarat Gas": "GUJGASLTD.NS",
    "Hindustan Copper": "HINDCOPPER.NS",
    "ICICI Lombard": "ICICIGI.NS",
    "ICICI Prudential Life": "ICICIPRULI.NS",
    
    # More Indian Mid & Small Caps
    "IDBI Bank": "IDBI.NS",
    "IDFC": "IDFC.NS",
    "India Cements": "INDIACEM.NS",
    "Indian Hotels": "INDHOTEL.NS",
    "Indiabulls Housing Finance": "IBULHSGFIN.NS",
    "Indiabulls Real Estate": "IBREALEST.NS",
    "Indraprastha Gas": "IGL.NS",
    "Info Edge": "NAUKRI.NS",
    "Ipca Laboratories": "IPCALAB.NS",
    "Jindal Steel & Power": "JINDALSTEL.NS",
    "JK Cement": "JKCEMENT.NS",
    "JK Lakshmi Cement": "JKLAKSHMI.NS",
    "JK Paper": "JKPAPER.NS",
    "JK Tyre & Industries": "JKTYRE.NS",
    "Jubilant Foodworks": "JUBLFOOD.NS",
    "Kajaria Ceramics": "KAJARIACER.NS",
    "Kalpataru Power": "KALPATPOWR.NS",
    "Kansai Nerolac": "KANSAINER.NS",
    "L&T Finance Holdings": "L&TFH.NS",
    "L&T Technology Services": "LTTS.NS",
    "Laurus Labs": "LAURUSLABS.NS",
    "LIC Housing Finance": "LICHSGFIN.NS",
    "Lupin": "LUPIN.NS",
    "Mahanagar Gas": "MGL.NS",
    "Mahindra & Mahindra Financial": "M&MFIN.NS",
    "Manappuram Finance": "MANAPPURAM.NS",
    "Marico": "MARICO.NS",
    "Max Financial Services": "MFSL.NS",
    "MindTree": "MINDTREE.NS",
    "Motherson Sumi Systems": "MOTHERSUMI.NS",
    
    # Banking & Financial Services
    "AU Small Finance Bank": "AUBANK.NS",
    "City Union Bank": "CUB.NS",
    "DCB Bank": "DCBBANK.NS",
    "Equitas Holdings": "EQUITAS.NS",
    "Equitas Small Finance Bank": "EQUITASBNK.NS",
    "IIFL Finance": "IIFL.NS",
    "Karnataka Bank": "KTKBANK.NS",
    "Karur Vysya Bank": "KARURVYSYA.NS",
    "Muthoot Finance": "MUTHOOTFIN.NS",
    "PNB Housing Finance": "PNBHOUSING.NS",
    "Punjab National Bank": "PNB.NS",
    "RBL Bank": "RBLBANK.NS",
    "Shriram Transport Finance": "SRTRANSFIN.NS",
    "South Indian Bank": "SOUTHBANK.NS",
    "Union Bank of India": "UNIONBANK.NS",
    
    # Pharma & Healthcare
    "Alembic Pharmaceuticals": "APLLTD.NS",
    "Alkem Laboratories": "ALKEM.NS",
    "Cadila Healthcare": "CADILAHC.NS",
    "Fortis Healthcare": "FORTIS.NS",
    "GlaxoSmithKline Pharma": "GLAXO.NS",
    "Ipca Laboratories": "IPCALAB.NS",
    "Natco Pharma": "NATCOPHARM.NS",
    "Pfizer": "PFIZER.NS",
    "Piramal Enterprises": "PEL.NS",
    "Sanofi India": "SANOFI.NS",
    "Strides Pharma Science": "STAR.NS",
    "Torrent Pharmaceuticals": "TORNTPHARM.NS",
    "Wockhardt": "WOCKPHARMA.NS",
    
    # IT & Technology
    "Cyient": "CYIENT.NS",
    "Firstsource Solutions": "FSL.NS",
    "Hexaware Technologies": "HEXAWARE.NS",
    "L&T Infotech": "LTI.NS",
    "Mphasis": "MPHASIS.NS",
    "NIIT Technologies": "COFORGE.NS",
    "Oracle Financial Services": "OFSS.NS",
    "Persistent Systems": "PERSISTENT.NS",
    "Polycab India": "POLYCAB.NS",
    "Tata Elxsi": "TATAELXSI.NS",
    "Zensar Technologies": "ZENSARTECH.NS",
    
    # Manufacturing & Industrial
    "ABB India": "ABB.NS",
    "Amara Raja Batteries": "AMARAJABAT.NS",
    "Astral Poly Technik": "ASTRAL.NS",
    "Bharat Heavy Electricals": "BHEL.NS",
    "Blue Star": "BLUESTARCO.NS",
    "Century Textiles": "CENTURYTEX.NS",
    "Crompton Greaves": "CROMPTON.NS",
    "Finolex Cables": "FINCABLES.NS",
    "Graphite India": "GRAPHITE.NS",
    "Grindwell Norton": "GRINDWELL.NS",
    "Havells India": "HAVELLS.NS",
    "Kirloskar Oil Engines": "KIRLOSENG.NS",
    "NBCC India": "NBCC.NS",
    "Siemens": "SIEMENS.NS",
    "SKF India": "SKFINDIA.NS",
    "Solar Industries": "SOLARINDS.NS",
    "Supreme Industries": "SUPREMEIND.NS",
    "Thermax": "THERMAX.NS",
    "Timken India": "TIMKEN.NS",
    "Voltas": "VOLTAS.NS",
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
    contributions = {}  # Store indicator, signal, score, weight
    weights = {
        'RSI': 1.0, 'MACD': 1.5, 'SMA': 1.2, 'Stochastic': 1.0, 'Ichimoku': 1.5,
        'CMF': 0.8, 'OBV': 0.8, 'VWAP': 1.0, 'ADX': 1.0, 'PSAR': 1.0, 'WilliamsR': 0.8
    }
    
    try:
        # RSI
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
        
        # MACD
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
        
        # SMA
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
        
        # Stochastic
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
        
        # Ichimoku
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
        
        # CMF
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
        
        # OBV
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
        
        # VWAP
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
        
        # ADX
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
        
        # PSAR
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
        
        # Williams %R
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
        
        # Add backtest signals
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

# Function to generate analysis report
def generate_report(ticker: str, info: dict, df: pd.DataFrame, indicators: pd.DataFrame, recommendation: str, signals: list, score: float, fib_levels: dict, pivot: float, support1: float, resistance1: float, backtest_results: tuple, currency_symbol: str, position_size: float, take_profit: float, sentiment: str) -> str:
    if df.empty:
        logger.warning("Empty DataFrame in generate_report")
        return "No data available for analysis."
    
    # Helper function to format values safely
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

# New Function: Calculate Manual Investment
def calculate_manual_investment(df: pd.DataFrame, investment_amount: float, investment_date: datetime, currency_symbol: str) -> dict:
    if df.empty or investment_amount <= 0:
        logger.warning("Invalid data or investment amount for manual investment")
        return {
            'shares': 0, 'buy_price': 0, 'current_price': 0, 'current_value': 0,
            'profit_loss': 0, 'return_pct': 0, 'annualized_return': 0, 'sharpe_ratio': 0
        }
    
    try:
        # Find the closest date in the DataFrame
        df_dates = pd.to_datetime(df.index)
        closest_date = df_dates[df_dates <= investment_date][-1] if any(df_dates <= investment_date) else df_dates[0]
        buy_price = df.loc[closest_date]['Close']
        
        if pd.isna(buy_price) or buy_price <= 0:
            logger.warning(f"No valid price data for date {closest_date}")
            return {
                'shares': 0, 'buy_price': 0, 'current_price': 0, 'current_value': 0,
                'profit_loss': 0, 'return_pct': 0, 'annualized_return': 0, 'sharpe_ratio': 0
            }
        
        shares = investment_amount / buy_price
        current_price = df['Close'][-1]
        current_value = shares * current_price
        profit_loss = current_value - investment_amount
        return_pct = (profit_loss / investment_amount) * 100 if investment_amount > 0 else 0
        
        # Calculate annualized return (CAGR)
        days = (datetime.now() - closest_date).days
        years = days / 365.25
        annualized_return = ((current_value / investment_amount) ** (1 / years) - 1) * 100 if years > 0 else 0
        
        # Calculate simplified Sharpe ratio
        returns = df['Close'].pct_change().loc[closest_date:]
        sharpe_ratio = (returns.mean() / returns.std()) * np.sqrt(252) if returns.std() != 0 else 0
        
        return {
            'shares': shares, 'buy_price': buy_price, 'current_price': current_price,
            'current_value': current_value, 'profit_loss': profit_loss, 'return_pct': return_pct,
            'annualized_return': annualized_return, 'sharpe_ratio': sharpe_ratio
        }
    except Exception as e:
        logger.error(f"Error in calculate_manual_investment: {str(e)}")
        return {
            'shares': 0, 'buy_price': 0, 'current_price': 0, 'current_value': 0,
            'profit_loss': 0, 'return_pct': 0, 'annualized_return': 0, 'sharpe_ratio': 0
        }

# New Function: Analyze TICKER_DB
def analyze_db() -> List[Tuple[str, str, str]]:
    results = []
    total_tickers = len(TICKER_DB)
    
    # Initialize progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, (company, ticker) in enumerate(TICKER_DB.items()):
        try:
            # Update progress
            progress = (i + 1) / total_tickers
            progress_bar.progress(progress)
            status_text.text(f"Analyzing {company} ({ticker})... {i+1}/{total_tickers}")
            
            df, _ = fetch_stock_data(ticker, '1mo', '1d')
            if df.empty or len(df) < 2:
                results.append((company, ticker, "Not Buy"))
                continue
            
            indicators = calculate_indicators(df, 20, 50, 14, 12, 26, 9, 20, 2.0)
            if indicators.empty or len(indicators) < 2:
                results.append((company, ticker, "Not Buy"))
                continue
            
            recommendation, _, _, _ = generate_recommendation(df, indicators)
            results.append((company, ticker, recommendation))
        except Exception as e:
            logger.error(f"Error analyzing {ticker}: {str(e)}")
            results.append((company, ticker, "Not Buy"))
        
        # Small delay to prevent API rate limiting
        time.sleep(0.1)
    
    # Clear progress bar and status
    progress_bar.empty()
    status_text.empty()
    
    return results

# New Function: Simulate Historical Investment Across TICKER_DB
def simulate_historical_investment(investment_amount: float, investment_date: datetime) -> List[dict]:
    results = []
    total_tickers = len(TICKER_DB)
    
    # Initialize progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, (company, ticker) in enumerate(TICKER_DB.items()):
        try:
            # Update progress
            progress = (i + 1) / total_tickers
            progress_bar.progress(progress)
            status_text.text(f"Simulating investment for {company} ({ticker})... {i+1}/{total_tickers}")
            
            # Fetch data from investment date to today
            period = '5y'  # Ensure enough data
            df, info = fetch_stock_data(ticker, period, '1d')
            if df.empty or len(df) < 2:
                results.append({
                    'company': company, 'ticker': ticker, 'currency_symbol': '$',
                    'shares': 0, 'buy_price': 0, 'current_price': 0, 'current_value': 0,
                    'profit_loss': 0, 'return_pct': 0, 'volatility': 0
                })
                continue
            
            # Get currency
            _, currency_symbol = get_currency_and_symbol(info)
            
            # Find closest date
            df_dates = pd.to_datetime(df.index)
            closest_date = df_dates[df_dates <= investment_date][-1] if any(df_dates <= investment_date) else df_dates[0]
            buy_price = df.loc[closest_date]['Close']
            
            if pd.isna(buy_price) or buy_price <= 0:
                results.append({
                    'company': company, 'ticker': ticker, 'currency_symbol': currency_symbol,
                    'shares': 0, 'buy_price': 0, 'current_price': 0, 'current_value': 0,
                    'profit_loss': 0, 'return_pct': 0, 'volatility': 0
                })
                continue
            
            shares = investment_amount / buy_price
            current_price = df['Close'][-1]
            current_value = shares * current_price
            profit_loss = current_value - investment_amount
            return_pct = (profit_loss / investment_amount) * 100 if investment_amount > 0 else 0
            
            # Calculate volatility (standard deviation of returns)
            returns = df['Close'].pct_change().loc[closest_date:]
            volatility = returns.std() * np.sqrt(252) * 100 if not returns.empty else 0
            
            results.append({
                'company': company, 'ticker': ticker, 'currency_symbol': currency_symbol,
                'shares': shares, 'buy_price': buy_price, 'current_price': current_price,
                'current_value': current_value, 'profit_loss': profit_loss, 'return_pct': return_pct,
                'volatility': volatility
            })
        except Exception as e:
            logger.error(f"Error simulating investment for {ticker}: {str(e)}")
            results.append({
                'company': company, 'ticker': ticker, 'currency_symbol': '$',
                'shares': 0, 'buy_price': 0, 'current_price': 0, 'current_value': 0,
                'profit_loss': 0, 'return_pct': 0, 'volatility': 0
            })
        
        # Small delay to prevent API rate limiting
        time.sleep(0.1)
    
    # Clear progress bar and status
    progress_bar.empty()
    status_text.empty()
    
    return results

# Streamlit app
def main():
    st.title("Expert Stock Technical Analysis")
    
    # Watchlist management
    if 'watchlist' not in st.session_state:
        st.session_state.watchlist = []
    
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
        analyze_db_button = st.button("AnalyzeDB")
        
        # New: Historical Investment Simulation
        st.header("Historical Investment Simulation")
        hist_investment_amount = st.number_input("Investment Amount", min_value=1000.0, value=10000.0, step=1000.0)
        default_date = datetime.now() - timedelta(days=3*365)
        hist_investment_date = st.date_input("Investment Date", value=default_date, min_value=datetime(2000, 1, 1), max_value=datetime.now())
        simulate_hist_investment = st.button("Simulate Historical Investment")
    
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
        
        # Correlation heatmap
        st.subheader("Watchlist Correlation")
        heatmap_fig = create_correlation_heatmap(st.session_state.watchlist, period)
        st.plotly_chart(heatmap_fig, use_container_width=True)
    
    # Handle AnalyzeDB button
    if analyze_db_button:
        with st.spinner("Analyzing TICKER_DB..."):
            db_results = analyze_db()
            if db_results:
                with st.expander("TICKER_DB Analysis Results", expanded=True):
                    db_df = pd.DataFrame(db_results, columns=['Company', 'Ticker', 'Recommendation'])
                    st.dataframe(db_df, use_container_width=True)
                    # Download button for DB results
                    db_csv = db_df.to_csv(index=False)
                    st.download_button(
                        label="Download TICKER_DB Analysis",
                        data=db_csv,
                        file_name="ticker_db_analysis.csv",
                        mime="text/csv"
                    )
            else:
                st.warning("No analysis results available for TICKER_DB.")
    
    # Handle Historical Investment Simulation
    if simulate_hist_investment:
        with st.spinner("Simulating historical investments..."):
            hist_results = simulate_historical_investment(hist_investment_amount, hist_investment_date)
            if hist_results:
                st.subheader("Historical Investment Simulation Results")
                hist_df = pd.DataFrame([
                    {
                        'Company': r['company'],
                        'Ticker': r['ticker'],
                        'Shares': f"{r['shares']:.2f}",
                        'Buy Price': f"{r['currency_symbol']}{r['buy_price']:.2f}",
                        'Current Price': f"{r['currency_symbol']}{r['current_price']:.2f}",
                        'Current Value': f"{r['currency_symbol']}{r['current_value']:.2f}",
                        'Profit/Loss': f"{r['currency_symbol']}{r['profit_loss']:.2f}",
                        'Return (%)': f"{r['return_pct']:.2f}",
                        'Volatility (%)': f"{r['volatility']:.2f}"
                    } for r in hist_results
                ])
                st.dataframe(hist_df, use_container_width=True)
                
                # Portfolio diversification suggestion
                top_performers = sorted(hist_results, key=lambda x: x['return_pct'], reverse=True)[:5]
                st.write("**Portfolio Diversification Suggestion**: Consider investing in the following top performers (based on return and volatility):")
                for performer in top_performers:
                    if performer['return_pct'] > 0:
                        st.write(f"- {performer['company']} ({performer['ticker']}): {performer['return_pct']:.2f}% return, {performer['volatility']:.2f}% volatility")
                
                # Download button for historical results
                hist_csv = hist_df.to_csv(index=False)
                st.download_button(
                    label="Download Historical Investment Results",
                    data=hist_csv,
                    file_name="historical_investment_results.csv",
                    mime="text/csv"
                )
            else:
                st.warning("No historical investment results available.")
    
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
                
                # Format indicator values for UI
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
                
                # Update session state
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
                    
                    # Recommendation Reasoning
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
                    
                    # New: Manual Investment Calculation
                    st.subheader("Analysis Report")
                report = generate_report(ticker, info, df, indicators, recommendation, signals, score, fib_levels, pivot, support1, resistance1, (total_return, win_rate, sharpe_ratio, max_drawdown), currency_symbol, position_size, take_profit, sentiment)
                st.markdown(report)
                
                # Download button for report
                report_buffer = io.StringIO()
                report_buffer.write(report)
                st.download_button(
                    label="Download Analysis Report",
                    data=report_buffer.getvalue(),
                    file_name=f"{ticker}_analysis_report.txt",
                    mime="text/plain"
                )
                
                # Display analysis details if requested
                if st.session_state.get('show_details', False):
                    st.subheader("Detailed Analysis Breakdown")
                    details = generate_analysis_details(ticker, recommendation, signals, score)
                    st.markdown(details)
                    st.session_state.show_details = False  # Reset after display
                
        except Exception as e:
            st.error(f"An error occurred during analysis: {str(e)}")
            logger.error(f"Analysis error for {ticker}: {str(e)}")

if __name__ == "__main__":
    main()
