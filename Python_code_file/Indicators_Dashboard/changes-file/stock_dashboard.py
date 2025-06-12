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
from datetime import datetime
import numpy as np

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Helper function to replace NaN and non-serializable values in a dictionary
def clean_dict(data):
    if isinstance(data, dict):
        return {k: clean_dict(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [clean_dict(item) for item in data]
    elif isinstance(data, float) and (np.isnan(data) or np.isinf(data)):
        return 'N/A'
    elif isinstance(data, pd.Series):
        return clean_dict(data.to_dict())
    return data

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

# Load tickers
csv_path = r"E:\Coding\Attandance\Stock sheet\EQUITY_L.csv"
TICKER_DB = load_tickers(csv_path)

# Initialize Flask app
app = Flask(__name__)

# Custom functions for DEMA and TEMA
def calculate_dema(close, window=9):
    ema1 = EMAIndicator(close, window=window).ema_indicator()
    ema2 = EMAIndicator(ema1, window=window).ema_indicator()
    dema = 2 * ema1 - ema2
    return dema

def calculate_tema(close, window=9):
    ema1 = EMAIndicator(close, window=window).ema_indicator()
    ema2 = EMAIndicator(ema1, window=window).ema_indicator()
    ema3 = EMAIndicator(ema2, window=window).ema_indicator()
    tema = 3 * ema1 - 3 * ema2 + ema3
    return tema

# Available indicators and timeframes
INDICATORS = [
    'EMA9', 'EMA21', 'SMA5', 'SMA10', 'SMA20', 'SMA50', 'SMA100', 'SMA200', 'WMA', 'DEMA', 'TEMA',
    'RSI', 'Stochastic %K', 'Stochastic %D', 'Williams %R', 'ROC', 'MOM', 'CCI', 'TSI', 'UO',
    'MACD', 'MACD Signal', 'MACD Histogram', 'ADX', '+DI', '-DI', 'PSAR', 'Aroon Up', 'Aroon Down', 'Aroon Oscillator',
    'OBV', 'CMF', 'MFI', 'VWAP', 'PVT',
    'ATR', 'Bollinger Upper', 'Bollinger Middle', 'Bollinger Lower', 'Bollinger Width', 'Bollinger %B',
    'Keltner Upper', 'Keltner Middle', 'Keltner Lower', 'Donchian Upper', 'Donchian Middle', 'Donchian Lower',
    'Std Dev', 'Stochastic RSI', 'TRIX', 'Chande MO', 'Supertrend',
    'Accumulation/Distribution', 'Ichimoku Tenkan', 'Ichimoku Kijun', 'Ichimoku Span A', 'Ichimoku Span B', 'Ichimoku Cloud Signal',
    'Pivot Point', 'Support 1', 'Support 2', 'Resistance 1', 'Resistance 2',
    'PPO', 'PPO Divergence'
]
TIMEFRAMES = ['5min', '15min', '30min', '60min', '1d', '1wk']

# Function to fetch stock details and historical data for candlestick chart
def fetch_stock_details(symbol):
    try:
        stock = yf.Ticker(symbol)
        info = stock.info
        history = stock.history(period='1d', interval='1m')
        if history.empty:
            logger.warning(f"Intraday data unavailable for {symbol}, falling back to daily data")
            history = stock.history(period='1d')
        daily_history = stock.history(period='2d')

        # Fetch data for candlestick chart (last 30 days, daily interval)
        candle_history = stock.history(period='1mo', interval='1d')
        candle_data = []
        if not candle_history.empty:
            for index, row in candle_history.iterrows():
                candle_data.append({
                    'date': index.strftime('%Y-%m-%d'),
                    'open': round(row['Open'], 2),
                    'high': round(row['High'], 2),
                    'low': round(row['Low'], 2),
                    'close': round(row['Close'], 2)
                })

        if history.empty or daily_history.empty:
            logger.error(f"No data available for {symbol}")
            return None

        current_price = history['Close'].iloc[-1] if not history.empty else 'N/A'
        prev_close = daily_history['Close'].iloc[-2] if len(daily_history) > 1 else 'N/A'
        open_price = daily_history['Open'].iloc[-1] if not daily_history.empty else 'N/A'
        high = daily_history['High'].iloc[-1] if not daily_history.empty else 'N/A'
        low = daily_history['Low'].iloc[-1] if not daily_history.empty else 'N/A'
        close = daily_history['Close'].iloc[-1] if not daily_history.empty else 'N/A'
        vwap = VolumeWeightedAveragePrice(daily_history['High'], daily_history['Low'], daily_history['Close'], daily_history['Volume']).volume_weighted_average_price().iloc[-1] if not daily_history.empty else 'N/A'

        details = {
            'fetch_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S IST'),
            'current_price': round(current_price, 2) if isinstance(current_price, (int, float)) and not np.isnan(current_price) else 'N/A',
            'prev_close': round(prev_close, 2) if isinstance(prev_close, (int, float)) and not np.isnan(prev_close) else 'N/A',
            'open': round(open_price, 2) if isinstance(open_price, (int, float)) and not np.isnan(open_price) else 'N/A',
            'high': round(high, 2) if isinstance(high, (int, float)) and not np.isnan(high) else 'N/A',
            'low': round(low, 2) if isinstance(low, (int, float)) and not np.isnan(low) else 'N/A',
            'close': round(close, 2) if isinstance(close, (int, float)) and not np.isnan(close) else 'N/A',
            'indicative_close': 'N/A',
            'vwap': round(vwap, 2) if isinstance(vwap, (int, float)) and not np.isnan(vwap) else 'N/A',
            'adjusted_price': 'N/A',
            'candle_data': candle_data,
            'trade_info': {
                'traded_volume_lakhs': round(daily_history['Volume'].iloc[-1] / 1e5, 2) if not daily_history.empty else 'N/A',
                'traded_value_cr': '344.47',
                'market_cap_cr': info.get('marketCap', 'N/A') / 1e7 if info.get('marketCap') else 'N/A',
                'free_float_market_cap_cr': '31424.23',
                'impact_cost': '0.14',
                'deliverable_traded_quantity': '49.21 %',
                'applicable_margin_rate': '26.11',
                'face_value': '10'
            },
            'price_info': {
                '52_week_high': info.get('fiftyTwoWeekHigh', 'N/A'),
                '52_week_low': info.get('fiftyTwoWeekLow', 'N/A'),
                'upper_band': '994.95',
                'lower_band': '814.05',
                'price_band': 'No Band',
                'daily_volatility': info.get('volatility', '3.40') if info.get('volatility') else '3.40',
                'annualised_volatility': '64.96',
                'tick_size': '0.05'
            },
            'securities_info': {
                'status': 'Listed',
                'trading_status': 'Active',
                'date_of_listing': '31-Jul-2015',
                'adjusted_pe': info.get('trailingPE', '42.73') if info.get('trailingPE') else '42.73',
                'symbol_pe': '121.46',
                'index': 'NIFTY NEXT 50',
                'basic_industry': info.get('industry', 'Power Distribution') if info.get('industry') else 'Power Distribution'
            }
        }
        return clean_dict(details)
    except Exception as e:
        logger.error(f"Error fetching stock details for {symbol}: {str(e)}")
        return None

# Function to fetch historical indicator data for charting
def fetch_indicator_history(symbol, indicator, timeframe, period):
    try:
        interval_map = {'5min': '5m', '15min': '15m', '30min': '30m', '60min': '60m', '1d': '1d', '1wk': '1wk'}
        period_map = {'5min': '5d', '15min': '10d', '30min': '20d', '60min': '30d', '1d': '3mo', '1wk': '1y'}
        interval = interval_map[timeframe]
        if period not in period_map:
            period = period_map[timeframe]

        stock = yf.Ticker(symbol)
        data = stock.history(period=period, interval=interval)
        if data.empty:
            logger.warning(f"No intraday data for {symbol} at {interval}, falling back to daily data")
            data = stock.history(period=period, interval='1d')
        if data.empty:
            logger.error(f"No data returned for {symbol}, timeframe {timeframe}")
            return []

        data = add_all_ta_features(data, open="Open", high="High", low="Low", close="Close", volume="Volume")
        indicator_data = []

        if indicator == 'EMA9':
            values = EMAIndicator(data['Close'], window=9).ema_indicator()
        elif indicator == 'EMA21':
            values = EMAIndicator(data['Close'], window=21).ema_indicator()
        elif indicator.startswith('SMA'):
            period_num = int(indicator.replace('SMA', ''))
            values = SMAIndicator(data['Close'], window=period_num).sma_indicator()
        elif indicator == 'WMA':
            values = WMAIndicator(data['Close'], window=9).wma()
        elif indicator == 'DEMA':
            values = calculate_dema(data['Close'], window=9)
        elif indicator == 'TEMA':
            values = calculate_tema(data['Close'], window=9)
        elif indicator == 'RSI':
            values = RSIIndicator(data['Close'], window=14).rsi()
        elif indicator == 'Stochastic %K':
            values = StochasticOscillator(data['High'], data['Low'], data['Close'], window=14).stoch()
        elif indicator == 'Stochastic %D':
            values = StochasticOscillator(data['High'], data['Low'], data['Close'], window=14).stoch_signal()
        elif indicator == 'Williams %R':
            values = WilliamsRIndicator(data['High'], data['Low'], data['Close'], lbp=14).williams_r()
        elif indicator == 'ROC':
            values = ROCIndicator(data['Close'], window=12).roc()
        elif indicator == 'MOM':
            values = data['Close'] - data['Close'].shift(10)
        elif indicator == 'CCI':
            values = data['trend_cci']
        elif indicator == 'TSI':
            values = TSIIndicator(data['Close']).tsi()
        elif indicator == 'UO':
            values = UltimateOscillator(data['High'], data['Low'], data['Close']).ultimate_oscillator()
        elif indicator == 'MACD':
            values = MACD(data['Close']).macd()
        elif indicator == 'MACD Signal':
            values = MACD(data['Close']).macd_signal()
        elif indicator == 'MACD Histogram':
            values = MACD(data['Close']).macd_diff()
        elif indicator == 'ADX':
            values = ADXIndicator(data['High'], data['Low'], data['Close']).adx()
        elif indicator == 'DMI':
            plus_di = ADXIndicator(data['High'], data['Low'], data['Close']).adx_pos()
            minus_di = ADXIndicator(data['High'], data['Low'], data['Close']).adx_neg()
            values = plus_di - minus_di
        elif indicator == '+DI':
            values = ADXIndicator(data['High'], data['Low'], data['Close']).adx_pos()
        elif indicator == '-DI':
            values = ADXIndicator(data['High'], data['Low'], data['Close']).adx_neg()
        elif indicator == 'PSAR':
            values = PSARIndicator(data['High'], data['Low'], data['Close']).psar()
        elif indicator == 'Aroon Up':
            values = AroonIndicator(data['Close']).aroon_up()
        elif indicator == 'Aroon Down':
            values = AroonIndicator(data['Close']).aroon_down()
        elif indicator == 'Aroon Oscillator':
            values = AroonIndicator(data['Close']).aroon_indicator()
        elif indicator == 'OBV':
            values = OnBalanceVolumeIndicator(data['Close'], data['Volume']).on_balance_volume()
        elif indicator == 'CMF':
            values = ChaikinMoneyFlowIndicator(data['High'], data['Low'], data['Close'], data['Volume']).chaikin_money_flow()
        elif indicator == 'MFI':
            values = MFIIndicator(data['High'], data['Low'], data['Close'], data['Volume']).money_flow_index()
        elif indicator == 'VWAP':
            values = VolumeWeightedAveragePrice(data['High'], data['Low'], data['Close'], data['Volume']).volume_weighted_average_price()
        elif indicator == 'PVT':
            values = ((data['Close'].diff() / data['Close'].shift(1)) * data['Volume']).cumsum()
        elif indicator == 'ATR':
            values = AverageTrueRange(data['High'], data['Low'], data['Close']).average_true_range()
        elif indicator == 'Bollinger Upper':
            values = BollingerBands(data['Close']).bollinger_hband()
        elif indicator == 'Bollinger Middle':
            values = BollingerBands(data['Close']).bollinger_mavg()
        elif indicator == 'Bollinger Lower':
            values = BollingerBands(data['Close']).bollinger_lband()
        elif indicator == 'Bollinger Width':
            values = BollingerBands(data['Close']).bollinger_wband()
        elif indicator == 'Bollinger %B':
            values = BollingerBands(data['Close']).bollinger_pband()
        elif indicator == 'Keltner Upper':
            values = KeltnerChannel(data['High'], data['Low'], data['Close']).keltner_channel_hband()
        elif indicator == 'Keltner Middle':
            values = KeltnerChannel(data['High'], data['Low'], data['Close']).keltner_channel_mband()
        elif indicator == 'Keltner Lower':
            values = KeltnerChannel(data['High'], data['Low'], data['Close']).keltner_channel_lband()
        elif indicator == 'Donchian Upper':
            values = DonchianChannel(data['High'], data['Low'], data['Close']).donchian_channel_hband()
        elif indicator == 'Donchian Middle':
            values = DonchianChannel(data['High'], data['Low'], data['Close']).donchian_channel_mband()
        elif indicator == 'Donchian Lower':
            values = DonchianChannel(data['High'], data['Low'], data['Close']).donchian_channel_lband()
        elif indicator == 'Std Dev':
            values = data['Close'].rolling(window=20).std()
        elif indicator == 'Stochastic RSI':
            values = data['momentum_stoch_rsi']
        elif indicator == 'TRIX':
            values = data['trend_trix']
        elif indicator == 'Chande MO':
            values = data['momentum_cmo']
        elif indicator == 'Supertrend':
            values = data['trend_psar']
        elif indicator == 'Accumulation/Distribution':
            values = AccDistIndexIndicator(data['High'], data['Low'], data['Close'], data['Volume']).acc_dist_index()
        elif indicator == 'Ichimoku Tenkan':
            values = (data['High'].rolling(window=9).max() + data['Low'].rolling(window=9).min()) / 2
        elif indicator == 'Ichimoku Kijun':
            values = (data['High'].rolling(window=26).max() + data['Low'].rolling(window=26).min()) / 2
        elif indicator == 'Ichimoku Span A':
            tenkan = (data['High'].rolling(window=9).max() + data['Low'].rolling(window=9).min()) / 2
            kijun = (data['High'].rolling(window=26).max() + data['Low'].rolling(window=26).min()) / 2
            values = ((tenkan + kijun) / 2).shift(26)
        elif indicator == 'Ichimoku Span B':
            values = ((data['High'].rolling(window=52).max() + data['Low'].rolling(window=52).min()) / 2).shift(26)
        elif indicator == 'Ichimoku Cloud Signal':
            tenkan = (data['High'].rolling(window=9).max() + data['Low'].rolling(window=9).min()) / 2
            kijun = (data['High'].rolling(window=26).max() + data['Low'].rolling(window=26).min()) / 2
            span_a = ((tenkan + kijun) / 2).shift(26)
            span_b = ((data['High'].rolling(window=52).max() + data['Low'].rolling(window=52).min()) / 2).shift(26)
            price = data['Close']
            values = price  # Return price for comparison
        elif indicator == 'Pivot Point':
            pivot = (data['High'].iloc[-1] + data['Low'].iloc[-1] + data['Close'].iloc[-1]) / 3
            values = pd.Series(pivot, index=data.index)
        elif indicator == 'Support 1':
            pivot = (data['High'].iloc[-1] + data['Low'].iloc[-1] + data['Close'].iloc[-1]) / 3
            s1 = (2 * pivot) - data['High'].iloc[-1]
            values = pd.Series(s1, index=data.index)
        elif indicator == 'Support 2':
            pivot = (data['High'].iloc[-1] + data['Low'].iloc[-1] + data['Close'].iloc[-1]) / 3
            s2 = pivot - (data['High'].iloc[-1] - data['Low'].iloc[-1])
            values = pd.Series(s2, index=data.index)
        elif indicator == 'Resistance 1':
            pivot = (data['High'].iloc[-1] + data['Low'].iloc[-1] + data['Close'].iloc[-1]) / 3
            r1 = (2 * pivot) - data['Low'].iloc[-1]
            values = pd.Series(r1, index=data.index)
        elif indicator == 'Resistance 2':
            pivot = (data['High'].iloc[-1] + data['Low'].iloc[-1] + data['Close'].iloc[-1]) / 3
            r2 = pivot + (data['High'].iloc[-1] - data['Low'].iloc[-1])
            values = pd.Series(r2, index=data.index)
        elif indicator == 'PPO':
            ema_fast = EMAIndicator(data['Close'], window=12).ema_indicator()
            ema_slow = EMAIndicator(data['Close'], window=26).ema_indicator()
            values = ((ema_fast - ema_slow) / ema_slow) * 100
        elif indicator == 'PPO Divergence':
            ema_fast = EMAIndicator(data['Close'], window=12).ema_indicator()
            ema_slow = EMAIndicator(data['Close'], window=26).ema_indicator()
            values = ((ema_fast - ema_slow) / ema_slow) * 100

        for i, (timestamp, value) in enumerate(values.items()):
            if pd.isna(value):
                continue
            indicator_data.append({
                'date': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'value': round(value, 2)
            })

        return indicator_data
    except Exception as e:
        logger.error(f"Error fetching historical data for {indicator}: {str(e)}")
        return []

# Function to fetch data and calculate indicators
def fetch_indicator_data(symbol, indicator, timeframe):
    try:
        interval_map = {'5min': '5m', '15min': '15m', '30min': '30m', '60min': '60m', '1d': '1d', '1wk': '1wk'}
        period_map = {'5min': '5d', '15min': '10d', '30min': '20d', '60min': '30d', '1d': '3mo', '1wk': '1y'}
        interval = interval_map[timeframe]
        period = period_map[timeframe]

        stock = yf.Ticker(symbol)
        data = stock.history(period=period, interval=interval)
        if data.empty:
            logger.warning(f"No intraday data for {symbol} at {interval}, falling back to daily data")
            data = stock.history(period=period, interval='1d')
        if data.empty:
            logger.error(f"No data returned for {symbol}, timeframe {timeframe}")
            return None, 'N/A'

        data = add_all_ta_features(data, open="Open", high="High", low="Low", close="Close", volume="Volume")

        if indicator == 'EMA9':
            ema9 = EMAIndicator(data['Close'], window=9).ema_indicator()
            value = ema9.iloc[-1]
            return value, 'Up' if ema9.iloc[-1] > ema9.iloc[-2] else 'Down'
        elif indicator == 'EMA21':
            ema21 = EMAIndicator(data['Close'], window=21).ema_indicator()
            value = ema21.iloc[-1]
            return value, 'Up' if ema21.iloc[-1] > ema21.iloc[-2] else 'Down'
        elif indicator.startswith('SMA'):
            period = int(indicator.replace('SMA', ''))
            sma = SMAIndicator(data['Close'], window=period).sma_indicator()
            value = sma.iloc[-1]
            return value, 'Up' if sma.iloc[-1] > sma.iloc[-2] else 'Down'
        elif indicator == 'WMA':
            wma = WMAIndicator(data['Close'], window=9).wma()
            value = wma.iloc[-1]
            return value, 'Up' if wma.iloc[-1] > wma.iloc[-2] else 'Down'
        elif indicator == 'DEMA':
            dema = calculate_dema(data['Close'], window=9)
            value = dema.iloc[-1]
            return value, 'Up' if dema.iloc[-1] > dema.iloc[-2] else 'Down'
        elif indicator == 'TEMA':
            tema = calculate_tema(data['Close'], window=9)
            value = tema.iloc[-1]
            return value, 'Up' if tema.iloc[-1] > tema.iloc[-2] else 'Down'
        elif indicator == 'RSI':
            rsi = RSIIndicator(data['Close'], window=14).rsi()
            value = rsi.iloc[-1]
            return value, 'Buy' if value < 30 else 'Sell' if value > 70 else 'Neutral'
        elif indicator == 'Stochastic %K':
            stoch = StochasticOscillator(data['High'], data['Low'], data['Close'], window=14).stoch()
            value = stoch.iloc[-1]
            return value, 'Buy' if value < 20 else 'Sell' if value > 80 else 'Neutral'
        elif indicator == 'Stochastic %D':
            stoch_d = StochasticOscillator(data['High'], data['Low'], data['Close'], window=14).stoch_signal()
            value = stoch_d.iloc[-1]
            return value, 'Buy' if value < 20 else 'Sell' if value > 80 else 'Neutral'
        elif indicator == 'Williams %R':
            willr = WilliamsRIndicator(data['High'], data['Low'], data['Close'], lbp=14).williams_r()
            value = willr.iloc[-1]
            return value, 'Buy' if value < -80 else 'Sell' if value > -20 else 'Neutral'
        elif indicator == 'ROC':
            roc = ROCIndicator(data['Close'], window=12).roc()
            value = roc.iloc[-1]
            return value, 'Up' if value > 0 else 'Down'
        elif indicator == 'MOM':
            value = data['Close'].iloc[-1] - data['Close'].shift(10).iloc[-1]
            return value, 'Up' if value > 0 else 'Down'
        elif indicator == 'CCI':
            value = data['trend_cci'].iloc[-1]
            return value, 'Buy' if value < -100 else 'Sell' if value > 100 else 'Neutral'
        elif indicator == 'TSI':
            tsi = TSIIndicator(data['Close']).tsi()
            value = tsi.iloc[-1]
            return value, 'Buy' if value < -25 else 'Sell' if value > 25 else 'Neutral'
        elif indicator == 'UO':
            uo = UltimateOscillator(data['High'], data['Low'], data['Close']).ultimate_oscillator()
            value = uo.iloc[-1]
            return value, 'Buy' if value < 30 else 'Sell' if value > 70 else 'Neutral'
        elif indicator == 'MACD':
            macd = MACD(data['Close']).macd()
            value = macd.iloc[-1]
            signal = MACD(data['Close']).macd_signal().iloc[-1]
            return value, 'Buy' if value > signal else 'Sell'
        elif indicator == 'MACD Signal':
            value = MACD(data['Close']).macd_signal().iloc[-1]
            return value, 'N/A'
        elif indicator == 'MACD Histogram':
            value = MACD(data['Close']).macd_diff().iloc[-1]
            return value, 'Buy' if value > 0 else 'Sell'
        elif indicator == 'ADX':
            adx = ADXIndicator(data['High'], data['Low'], data['Close']).adx()
            value = adx.iloc[-1]
            return value, 'Strong' if value > 25 else 'Weak'
        elif indicator == 'DMI':
            plus_di = ADXIndicator(data['High'], data['Low'], data['Close']).adx_pos().iloc[-1]
            minus_di = ADXIndicator(data['High'], data['Low'], data['Close']).adx_neg().iloc[-1]
            value = plus_di - minus_di
            return value, 'Buy' if value > 0 else 'Sell'
        elif indicator == '+DI':
            value = ADXIndicator(data['High'], data['Low'], data['Close']).adx_pos().iloc[-1]
            return value, 'N/A'
        elif indicator == '-DI':
            value = ADXIndicator(data['High'], data['Low'], data['Close']).adx_neg().iloc[-1]
            return value, 'N/A'
        elif indicator == 'PSAR':
            psar = PSARIndicator(data['High'], data['Low'], data['Close']).psar()
            value = psar.iloc[-1]
            return value, 'Buy' if value < data['Close'].iloc[-1] else 'Sell'
        elif indicator == 'Aroon Up':
            aroon = AroonIndicator(data['Close']).aroon_up()
            value = aroon.iloc[-1]
            return value, 'Buy' if value > 50 else 'Sell'
        elif indicator == 'Aroon Down':
            aroon = AroonIndicator(data['Close']).aroon_down()
            value = aroon.iloc[-1]
            return value, 'Sell' if value > 50 else 'Buy'
        elif indicator == 'Aroon Oscillator':
            aroon = AroonIndicator(data['Close']).aroon_indicator()
            value = aroon.iloc[-1]
            return value, 'Buy' if value > 0 else 'Sell'
        elif indicator == 'OBV':
            obv = OnBalanceVolumeIndicator(data['Close'], data['Volume']).on_balance_volume()
            value = obv.iloc[-1]
            return value, 'Up' if obv.iloc[-1] > obv.iloc[-2] else 'Down'
        elif indicator == 'CMF':
            cmf = ChaikinMoneyFlowIndicator(data['High'], data['Low'], data['Close'], data['Volume']).chaikin_money_flow()
            value = cmf.iloc[-1]
            return value, 'Buy' if value > 0 else 'Sell'
        elif indicator == 'MFI':
            mfi = MFIIndicator(data['High'], data['Low'], data['Close'], data['Volume']).money_flow_index()
            value = mfi.iloc[-1]
            return value, 'Buy' if value < 20 else 'Sell' if value > 80 else 'Neutral'
        elif indicator == 'VWAP':
            vwap = VolumeWeightedAveragePrice(data['High'], data['Low'], data['Close'], data['Volume']).volume_weighted_average_price()
            value = vwap.iloc[-1]
            return value, 'Up' if value > data['Close'].iloc[-1] else 'Down'
        elif indicator == 'PVT':
            value = ((data['Close'].diff() / data['Close'].shift(1)) * data['Volume']).cumsum().iloc[-1]
            return value, 'Up' if value > 0 else 'Down'
        elif indicator == 'ATR':
            atr = AverageTrueRange(data['High'], data['Low'], data['Close']).average_true_range()
            value = atr.iloc[-1]
            return value, 'N/A'
        elif indicator == 'Bollinger Upper':
            bb = BollingerBands(data['Close']).bollinger_hband()
            value = bb.iloc[-1]
            return value, 'N/A'
        elif indicator == 'Bollinger Middle':
            bb = BollingerBands(data['Close']).bollinger_mavg()
            value = bb.iloc[-1]
            return value, 'N/A'
        elif indicator == 'Bollinger Lower':
            bb = BollingerBands(data['Close']).bollinger_lband()
            value = bb.iloc[-1]
            return value, 'N/A'
        elif indicator == 'Bollinger Width':
            bb = BollingerBands(data['Close']).bollinger_wband()
            value = bb.iloc[-1]
            return value, 'N/A'
        elif indicator == 'Bollinger %B':
            bb = BollingerBands(data['Close']).bollinger_pband()
            value = bb.iloc[-1]
            return value, 'Buy' if value < 0 else 'Sell' if value > 1 else 'Neutral'
        elif indicator == 'Keltner Upper':
            kc = KeltnerChannel(data['High'], data['Low'], data['Close']).keltner_channel_hband()
            value = kc.iloc[-1]
            return value, 'N/A'
        elif indicator == 'Keltner Middle':
            kc = KeltnerChannel(data['High'], data['Low'], data['Close']).keltner_channel_mband()
            value = kc.iloc[-1]
            return value, 'N/A'
        elif indicator == 'Keltner Lower':
            kc = KeltnerChannel(data['High'], data['Low'], data['Close']).keltner_channel_lband()
            value = kc.iloc[-1]
            return value, 'N/A'
        elif indicator == 'Donchian Upper':
            dc = DonchianChannel(data['High'], data['Low'], data['Close']).donchian_channel_hband()
            value = dc.iloc[-1]
            return value, 'N/A'
        elif indicator == 'Donchian Middle':
            dc = DonchianChannel(data['High'], data['Low'], data['Close']).donchian_channel_mband()
            value = dc.iloc[-1]
            return value, 'N/A'
        elif indicator == 'Donchian Lower':
            dc = DonchianChannel(data['High'], data['Low'], data['Close']).donchian_channel_lband()
            value = dc.iloc[-1]
            return value, 'N/A'
        elif indicator == 'Std Dev':
            value = data['Close'].std()
            return value, 'N/A'
        elif indicator == 'Stochastic RSI':
            value = data['momentum_stoch_rsi'].iloc[-1]
            return value, 'Buy' if value < 0.2 else 'Sell' if value > 0.8 else 'Neutral'
        elif indicator == 'TRIX':
            value = data['trend_trix'].iloc[-1]
            return value, 'Buy' if value > 0 else 'Sell'
        elif indicator == 'Chande MO':
            value = data['momentum_cmo'].iloc[-1]
            return value, 'Buy' if value < -50 else 'Sell' if value > 50 else 'Neutral'
        elif indicator == 'Supertrend':
            value = data['trend_psar'].iloc[-1]
            return value, 'Buy' if value < data['Close'].iloc[-1] else 'Sell'
        elif indicator == 'Accumulation/Distribution':
            ad = AccDistIndexIndicator(data['High'], data['Low'], data['Close'], data['Volume']).acc_dist_index()
            value = ad.iloc[-1]
            return value, 'Up' if ad.iloc[-1] > ad.iloc[-2] else 'Down'
        elif indicator == 'Ichimoku Tenkan':
            tenkan = (data['High'].rolling(window=9).max() + data['Low'].rolling(window=9).min()) / 2
            value = tenkan.iloc[-1]
            return value, 'N/A'
        elif indicator == 'Ichimoku Kijun':
            kijun = (data['High'].rolling(window=26).max() + data['Low'].rolling(window=26).min()) / 2
            value = kijun.iloc[-1]
            return value, 'N/A'
        elif indicator == 'Ichimoku Span A':
            tenkan = (data['High'].rolling(window=9).max() + data['Low'].rolling(window=9).min()) / 2
            kijun = (data['High'].rolling(window=26).max() + data['Low'].rolling(window=26).min()) / 2
            span_a = ((tenkan + kijun) / 2).shift(26)
            value = span_a.iloc[-1]
            return value, 'N/A'
        elif indicator == 'Ichimoku Span B':
            span_b = ((data['High'].rolling(window=52).max() + data['Low'].rolling(window=52).min()) / 2).shift(26)
            value = span_b.iloc[-1]
            return value, 'N/A'
        elif indicator == 'Ichimoku Cloud Signal':
            tenkan = (data['High'].rolling(window=9).max() + data['Low'].rolling(window=9).min()) / 2
            kijun = (data['High'].rolling(window=26).max() + data['Low'].rolling(window=26).min()) / 2
            span_a = ((tenkan + kijun) / 2).shift(26)
            span_b = ((data['High'].rolling(window=52).max() + data['Low'].rolling(window=52).min()) / 2).shift(26)
            price = data['Close'].iloc[-1]
            span_a_value = span_a.iloc[-1]
            span_b_value = span_b.iloc[-1]
            if pd.isna(span_a_value) or pd.isna(span_b_value):
                return 'N/A', 'N/A'
            cloud_top = max(span_a_value, span_b_value)
            cloud_bottom = min(span_a_value, span_b_value)
            if price > cloud_top:
                signal = 'Buy'
            elif price < cloud_bottom:
                signal = 'Sell'
            else:
                signal = 'Neutral'
            return price, signal
        elif indicator == 'Pivot Point':
            pivot = (data['High'].iloc[-1] + data['Low'].iloc[-1] + data['Close'].iloc[-1]) / 3
            return pivot, 'N/A'
        elif indicator == 'Support 1':
            pivot = (data['High'].iloc[-1] + data['Low'].iloc[-1] + data['Close'].iloc[-1]) / 3
            s1 = (2 * pivot) - data['High'].iloc[-1]
            return s1, 'N/A'
        elif indicator == 'Support 2':
            pivot = (data['High'].iloc[-1] + data['Low'].iloc[-1] + data['Close'].iloc[-1]) / 3
            s2 = pivot - (data['High'].iloc[-1] - data['Low'].iloc[-1])
            return s2, 'N/A'
        elif indicator == 'Resistance 1':
            pivot = (data['High'].iloc[-1] + data['Low'].iloc[-1] + data['Close'].iloc[-1]) / 3
            r1 = (2 * pivot) - data['Low'].iloc[-1]
            return r1, 'N/A'
        elif indicator == 'Resistance 2':
            pivot = (data['High'].iloc[-1] + data['Low'].iloc[-1] + data['Close'].iloc[-1]) / 3
            r2 = pivot + (data['High'].iloc[-1] - data['Low'].iloc[-1])
            return r2, 'N/A'
        elif indicator == 'PPO':
            ema_fast = EMAIndicator(data['Close'], window=12).ema_indicator()
            ema_slow = EMAIndicator(data['Close'], window=26).ema_indicator()
            ppo = ((ema_fast - ema_slow) / ema_slow) * 100
            value = ppo.iloc[-1]
            return value, 'N/A'
        elif indicator == 'PPO Divergence':
            ema_fast = EMAIndicator(data['Close'], window=12).ema_indicator()
            ema_slow = EMAIndicator(data['Close'], window=26).ema_indicator()
            ppo = ((ema_fast - ema_slow) / ema_slow) * 100
            ppo_current = ppo.iloc[-1]
            ppo_prev = ppo.iloc[-2]
            price_current = data['Close'].iloc[-1]
            price_prev = data['Close'].iloc[-2]
            if (price_current < price_prev and ppo_current > ppo_prev):
                signal = 'Bullish Divergence'
            elif (price_current > price_prev and ppo_current < ppo_prev):
                signal = 'Bearish Divergence'
            else:
                signal = 'No Divergence'
            return ppo_current, signal
        return None, 'N/A'
    except Exception as e:
        logger.error(f"Error fetching {indicator} for {symbol}: {str(e)}")
        return None, 'N/A'

# Route for the main dashboard
@app.route('/')
def index():
    if not TICKER_DB:
        logger.error("TICKER_DB is empty. Check CSV file.")
        return "Error: Unable to load ticker data. Check server logs.", 500
    return render_template('index.html', companies=list(TICKER_DB.keys()), indicators=INDICATORS)

# Route to fetch indicator data and stock details
@app.route('/get_data', methods=['POST'])
def get_data():
    company = request.form.get('company')
    selected_indicators = request.form.getlist('indicators')
    symbol = TICKER_DB.get(company)
    
    if not symbol:
        logger.error(f"Invalid company name: {company}")
        return jsonify({'error': f'Invalid company name: {company}'})

    # Fetch stock details
    stock_details = fetch_stock_details(symbol)
    if not stock_details:
        logger.error(f"Failed to fetch stock details for {symbol}")
        return jsonify({'error': f'Failed to fetch stock details for {symbol}'})

    # Fetch indicator data
    data = []
    for timeframe in TIMEFRAMES:
        row = {'timeframe': timeframe}
        for indicator in selected_indicators:
            value, signal = fetch_indicator_data(symbol, indicator, timeframe)
            if isinstance(value, (int, float)) and (np.isnan(value) or np.isinf(value)):
                value = 'N/A'
            row[indicator] = {'value': round(value, 2) if isinstance(value, (int, float)) else 'N/A', 'signal': signal}
        data.append(row)

    # Generate strategy report
    strategy_report = f"Analysis Strategy Report for {company} ({symbol})\n"
    strategy_report += f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    strategy_report += "Strategy Overview:\n"
    strategy_report += "This analysis uses a combination of technical indicators to identify trends, momentum, and potential buy/sell signals.\n\n"
    strategy_report += "Indicators Used:\n"
    for indicator in selected_indicators:
        strategy_report += f"- {indicator}: Provides insights into "
        if 'EMA' in indicator or 'SMA' in indicator or 'WMA' in indicator or 'DEMA' in indicator or 'TEMA' in indicator:
            strategy_report += "price trends and potential reversals.\n"
        elif 'RSI' in indicator or 'Stochastic' in indicator or 'Williams' in indicator or 'MOM' in indicator or 'CCI' in indicator or 'TSI' in indicator or 'UO' in indicator:
            strategy_report += "momentum and overbought/oversold conditions.\n"
        elif 'MACD' in indicator or 'ADX' in indicator or 'DMI' in indicator or '+DI' in indicator or '-DI' in indicator or 'PSAR' in indicator or 'Aroon' in indicator or 'PPO' in indicator:
            strategy_report += "trend strength and direction.\n"
        elif 'OBV' in indicator or 'CMF' in indicator or 'MFI' in indicator or 'VWAP' in indicator or 'PVT' in indicator or 'Accumulation/Distribution' in indicator:
            strategy_report += "volume trends and price-volume relationships.\n"
        elif 'ATR' in indicator or 'Bollinger' in indicator or 'Keltner' in indicator or 'Donchian' in indicator or 'Std Dev' in indicator or 'Ichimoku' in indicator or 'Pivot' in indicator or 'Support' in indicator or 'Resistance' in indicator:
            strategy_report += "volatility, support/resistance, and potential breakout levels.\n"
        else:
            strategy_report += "advanced or composite signals.\n"
    strategy_report += "\nSignals Interpretation:\n"
    for timeframe_data in data:
        strategy_report += f"\nTimeframe: {timeframe_data['timeframe']}\n"
        for indicator in selected_indicators:
            signal = timeframe_data[indicator]['signal']
            value = timeframe_data[indicator]['value']
            strategy_report += f"- {indicator}: {value} ({signal})\n"

    response = {
        'data': data,
        'indicators': selected_indicators,
        'stock_details': stock_details,
        'strategy_report': strategy_report
    }
    return jsonify(clean_dict(response))

# Route to fetch historical indicator data for charts
@app.route('/get_indicator_history', methods=['POST'])
def get_indicator_history():
    company = request.form.get('company')
    indicator = request.form.get('indicator')
    timeframe = request.form.get('timeframe')
    symbol = TICKER_DB.get(company)

    if not symbol:
        return jsonify({'error': f'Invalid company name: {company}'})

    history = fetch_indicator_history(symbol, indicator, timeframe, period='1mo')
    return jsonify(history)

# Route to calculate P&L
@app.route('/calculate_pnl', methods=['POST'])
def calculate_pnl():
    buy_price = float(request.form.get('buy_price'))
    quantity = float(request.form.get('quantity'))
    current_price = float(request.form.get('current_price'))
    
    profit_loss = (current_price - buy_price) * quantity
    percentage_change = ((current_price - buy_price) / buy_price) * 100 if buy_price != 0 else 0

    return jsonify({
        'profit_loss': round(profit_loss, 2),
        'percentage_change': round(percentage_change, 2)
    })

if __name__ == '__main__':
    from waitress import serve
    serve(app, host='127.0.0.1', port=5000)