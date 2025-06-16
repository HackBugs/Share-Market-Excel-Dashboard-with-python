import pandas as pd
import logging
import yfinance as yf
from ta import add_all_ta_features
from ta.trend import EMAIndicator, SMAIndicator, WMAIndicator, MACD, ADXIndicator, PSARIndicator, AroonIndicator
from ta.momentum import RSIIndicator, StochasticOscillator, WilliamsRIndicator, ROCIndicator, TSIIndicator, UltimateOscillator
from ta.volume import OnBalanceVolumeIndicator, ChaikinMoneyFlowIndicator, MFIIndicator, VolumeWeightedAveragePrice, AccDistIndexIndicator
from ta.volatility import AverageTrueRange, BollingerBands, KeltnerChannel, DonchianChannel
from flask import Flask, request, render_template, jsonify
import os
from datetime import datetime, timedelta
import numpy as np
import json

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Load tickers from CSV
def load_tickers(csv_path: str) -> dict:
    try:
        df = pd.read_csv(csv_path)
        tickers = {row['NAME OF COMPANY']: f"{row['SYMBOL']}.NS" for _, row in df.iterrows()}
        logger.debug(f"Loaded {len(tickers)} tickers from CSV: {tickers}")
        return tickers
    except Exception as e:
        logger.error(f"Error loading tickers from CSV: {str(e)}")
        return {}

# Fetch intraday data using yfinance
def fetch_intraday_data(ticker: str, interval='5m', period='1d'):
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period=period, interval=interval)
        logger.debug(f"Fetched data for {ticker}: {df.shape}")
        return df
    except Exception as e:
        logger.error(f"Error fetching data for {ticker}: {str(e)}")
        return pd.DataFrame()

# Calculate technical indicators
def calculate_indicators(df):
    try:
        df = add_all_ta_features(df, open="Open", high="High", low="Low", close="Close", volume="Volume")
        
        # VWAP
        vwap = VolumeWeightedAveragePrice(high=df['High'], low=df['Low'], close=df['Close'], volume=df['Volume'])
        df['VWAP'] = vwap.volume_weighted_average_price()
        
        # Bollinger Bands
        bb = BollingerBands(close=df['Close'], window=20, window_dev=2)
        df['BB_Upper'] = bb.bollinger_hband()
        df['BB_Middle'] = bb.bollinger_mavg()
        df['BB_Lower'] = bb.bollinger_lband()
        
        # Support and Resistance (Pivot Points)
        df['Pivot'] = (df['High'] + df['Low'] + df['Close']) / 3
        df['Support1'] = 2 * df['Pivot'] - df['High']
        df['Resistance1'] = 2 * df['Pivot'] - df['Low']
        
        return df
    except Exception as e:
        logger.error(f"Error calculating indicators: {str(e)}")
        return df

# Load tickers
csv_path = r"E:\Coding\Attandance\Stock sheet\EQUITY_L.csv"
TICKER_DB = load_tickers(csv_path)

@app.route('/')
def index():
    return render_template('index.html', companies=TICKER_DB.keys())

@app.route('/get_data', methods=['POST'])
def get_data():
    company_name = request.form.get('company')
    ticker = TICKER_DB.get(company_name)
    if not ticker:
        return jsonify({'error': 'Invalid company selected'})

    # Fetch intraday data
    df = fetch_intraday_data(ticker)
    if df.empty:
        return jsonify({'error': 'No data available for selected company'})

    # Calculate indicators
    df = calculate_indicators(df)

    # Latest data point
    latest = df.iloc[-1]
    open_price = latest['Open']
    high_price = latest['High']
    low_price = latest['Low']
    close_price = latest['Close']
    volume = latest['Volume']
    vwap = latest['VWAP']
    bb_upper = latest['BB_Upper']
    bb_middle = latest['BB_Middle']
    bb_lower = latest['BB_Lower']
    support1 = latest['Support1']
    resistance1 = latest['Resistance1']

    # Volume chart data (compare with sample top 5 stocks)
    volume_data = {
        'labels': [company_name, 'TATASTEEL', 'BAJFINANCE', 'POWERGRID', 'WIPRO'],
        'datasets': [{
            'label': 'Volume (Lakhs)',
            'data': [volume / 100000, 793.48, 430.37, 438.34, 454.16],  # Convert to lakhs
            'backgroundColor': ['#4CAF50', '#2196F3', '#FFC107', '#E91E63', '#9C27B0'],
            'borderColor': ['#388E3C', '#1976D2', '#FFB300', '#C2185B', '#7B1FA2'],
            'borderWidth': 1
        }]
    }

    # Price movement chart data
    price_data = {
        'labels': ['Open', 'Low', 'High', 'LTP', 'VWAP', 'Support1', 'Resistance1'],
        'datasets': [{
            'label': 'Price (₹)',
            'data': [open_price, low_price, high_price, close_price, vwap, support1, resistance1],
            'fill': False,
            'borderColor': '#2196F3',
            'backgroundColor': '#2196F3',
            'tension': 0.1,
            'pointBackgroundColor': ['#4CAF50', '#E91E63', '#4CAF50', '#FFC107', '#9C27B0', '#FF5722', '#FF5722'],
            'pointRadius': 5
        }]
    }

    return jsonify({
        'volume_chart': volume_data,
        'price_chart': price_data,
        'ticker': ticker,
        'company': company_name
    })

if __name__ == '__main__':
    app.run(debug=True)
