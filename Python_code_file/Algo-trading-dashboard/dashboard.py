import pandas as pd
import yfinance as yf
import ta
import streamlit as st
import logging
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import io
import base64

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Custom indicator calculations
def calculate_dema(close: pd.Series, window: int) -> pd.Series:
    try:
        ema = ta.trend.ema_indicator(close=close, window=window)
        ema2 = ta.trend.ema_indicator(close=ema, window=window)
        return 2 * ema - ema2
    except Exception as e:
        logger.error(f"Error calculating DEMA: {str(e)}")
        return pd.Series(np.nan, index=close.index)

def calculate_tema(close: pd.Series, window: int) -> pd.Series:
    try:
        ema1 = ta.trend.ema_indicator(close=close, window=window)
        ema2 = ta.trend.ema_indicator(close=ema1, window=window)
        ema3 = ta.trend.ema_indicator(close=ema2, window=window)
        return 3 * ema1 - 3 * ema2 + ema3
    except Exception as e:
        logger.error(f"Error calculating TEMA: {str(e)}")
        return pd.Series(np.nan, index=close.index)

# Data fetching with enhanced error handling
@st.cache_data
def fetch_market_data(ticker: str, period: str = '1y', interval: str = '1d') -> pd.DataFrame:
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period=period, interval=interval)
        
        if df.empty:
            logger.warning(f"No data fetched for {ticker}")
            return None
            
        # Ensure sufficient data points
        min_data_points = 200 if period in ['1y', '2y', '5y', '10y'] else 50
        if len(df) < min_data_points:
            logger.warning(f"Insufficient data points ({len(df)}) for {ticker}")
            return None
            
        # Clean data
        df = df.dropna()
        df = df[~df.index.duplicated()]
        
        # Verify all required columns exist
        required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        if not all(col in df.columns for col in required_cols):
            logger.error("Missing required columns in DataFrame")
            return None
            
        logger.info(f"Successfully fetched {len(df)} records for {ticker}")
        return df
        
    except Exception as e:
        logger.error(f"Error fetching data for {ticker}: {str(e)}")
        return None

# Complete indicator calculation with fallbacks
def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return None

    df_indicators = df.copy()
    
    try:
        # Validate data quality
        if len(df) < 50:
            logger.error("Insufficient data points for calculations")
            return None

        # ===== Moving Averages =====
        ma_windows = [5, 9, 10, 20, 21, 50, 100, 200]
        for window in ma_windows:
            try:
                df_indicators[f'SMA{window}'] = ta.trend.sma_indicator(close=df['Close'], window=window)
                if window in [9, 21]:
                    df_indicators[f'EMA{window}'] = ta.trend.ema_indicator(close=df['Close'], window=window)
            except Exception as e:
                logger.warning(f"Failed to calculate MA{window}: {str(e)}")
                df_indicators[f'SMA{window}'] = np.nan
                if window in [9, 21]:
                    df_indicators[f'EMA{window}'] = np.nan

        df_indicators['WMA'] = ta.trend.wma_indicator(close=df['Close'], window=9)
        df_indicators['DEMA'] = calculate_dema(df['Close'], window=9)
        df_indicators['TEMA'] = calculate_tema(df['Close'], window=9)

        # ===== Momentum Indicators =====
        try:
            df_indicators['RSI'] = ta.momentum.rsi(close=df['Close'], window=14)
        except:
            df_indicators['RSI'] = np.nan

        try:
            stoch = ta.momentum.StochasticOscillator(high=df['High'], low=df['Low'], close=df['Close'])
            df_indicators['Stoch_K'] = stoch.stoch()
            df_indicators['Stoch_D'] = stoch.stoch_signal()
        except:
            df_indicators['Stoch_K'] = np.nan
            df_indicators['Stoch_D'] = np.nan

        momentum_indicators = {
            'Williams_R': lambda: ta.momentum.williams_r(high=df['High'], low=df['Low'], close=df['Close']),
            'ROC': lambda: ta.momentum.roc(close=df['Close']),
            'MOM': lambda: ta.momentum.awesome_oscillator(high=df['High'], low=df['Low']),
            'CCI': lambda: ta.trend.cci(high=df['High'], low=df['Low'], close=df['Close']),
            'TSI': lambda: ta.momentum.tsi(close=df['Close']),
            'UO': lambda: ta.momentum.ultimate_oscillator(high=df['High'], low=df['Low'], close=df['Close']),
            'Stoch_RSI': lambda: ta.momentum.stochrsi(close=df['Close']),
            'TRIX': lambda: ta.trend.trix(close=df['Close']),
            'Chande_MO': lambda: ta.momentum.chande_momentum_oscillator(close=df['Close'])
        }

        for name, func in momentum_indicators.items():
            try:
                df_indicators[name] = func()
            except:
                df_indicators[name] = np.nan
                logger.warning(f"Failed to calculate {name}")

        # ===== MACD =====
        try:
            macd = ta.trend.MACD(close=df['Close'])
            df_indicators['MACD'] = macd.macd()
            df_indicators['MACD_Signal'] = macd.macd_signal()
            df_indicators['MACD_Hist'] = macd.macd_diff()
        except:
            df_indicators['MACD'] = np.nan
            df_indicators['MACD_Signal'] = np.nan
            df_indicators['MACD_Hist'] = np.nan

        # ===== Trend Indicators =====
        try:
            adx = ta.trend.ADXIndicator(high=df['High'], low=df['Low'], close=df['Close'])
            df_indicators['ADX'] = adx.adx()
            df_indicators['+DI'] = adx.adx_pos()
            df_indicators['-DI'] = adx.adx_neg()
        except:
            df_indicators['ADX'] = np.nan
            df_indicators['+DI'] = np.nan
            df_indicators['-DI'] = np.nan

        try:
            df_indicators['PSAR'] = ta.trend.psar_up(high=df['High'], low=df['Low'], close=df['Close'])
        except:
            df_indicators['PSAR'] = np.nan

        try:
            aroon = ta.trend.AroonIndicator(close=df['Close'])
            df_indicators['Aroon_Up'] = aroon.aroon_up()
            df_indicators['Aroon_Down'] = aroon.aroon_down()
            df_indicators['Aroon_Osc'] = aroon.aroon_indicator()
        except:
            df_indicators['Aroon_Up'] = np.nan
            df_indicators['Aroon_Down'] = np.nan
            df_indicators['Aroon_Osc'] = np.nan

        # ===== Volume Indicators =====
        volume_indicators = {
            'OBV': lambda: ta.volume.on_balance_volume(close=df['Close'], volume=df['Volume']),
            'CMF': lambda: ta.volume.chaikin_money_flow(high=df['High'], low=df['Low'], close=df['Close'], volume=df['Volume']),
            'MFI': lambda: ta.volume.money_flow_index(high=df['High'], low=df['Low'], close=df['Close'], volume=df['Volume']),
            'VWAP': lambda: ta.volume.volume_weighted_average_price(high=df['High'], low=df['Low'], close=df['Close'], volume=df['Volume']),
            'PVT': lambda: ta.volume.price_volume_trend(close=df['Close'], volume=df['Volume']),
            'Acc_Dist': lambda: ta.volume.acc_dist_index(high=df['High'], low=df['Low'], close=df['Close'], volume=df['Volume'])
        }

        for name, func in volume_indicators.items():
            try:
                df_indicators[name] = func()
            except:
                df_indicators[name] = np.nan
                logger.warning(f"Failed to calculate {name}")

        # ===== Volatility Indicators =====
        try:
            df_indicators['ATR'] = ta.volatility.average_true_range(high=df['High'], low=df['Low'], close=df['Close'])
        except:
            df_indicators['ATR'] = np.nan

        try:
            bb = ta.volatility.BollingerBands(close=df['Close'])
            df_indicators['BB_Upper'] = bb.bollinger_hband()
            df_indicators['BB_Middle'] = bb.bollinger_mavg()
            df_indicators['BB_Lower'] = bb.bollinger_lband()
            df_indicators['BB_Width'] = bb.bollinger_wband()
            df_indicators['BB_Percent_B'] = bb.bollinger_pband()
        except:
            for col in ['BB_Upper', 'BB_Middle', 'BB_Lower', 'BB_Width', 'BB_Percent_B']:
                df_indicators[col] = np.nan

        try:
            keltner = ta.volatility.KeltnerChannel(high=df['High'], low=df['Low'], close=df['Close'])
            df_indicators['Keltner_Upper'] = keltner.keltner_channel_hband()
            df_indicators['Keltner_Middle'] = keltner.keltner_channel_mavg()
            df_indicators['Keltner_Lower'] = keltner.keltner_channel_lband()
        except:
            for col in ['Keltner_Upper', 'Keltner_Middle', 'Keltner_Lower']:
                df_indicators[col] = np.nan

        try:
            donchian = ta.volatility.DonchianChannel(high=df['High'], low=df['Low'], close=df['Close'])
            df_indicators['Donchian_Upper'] = donchian.donchian_channel_hband()
            df_indicators['Donchian_Middle'] = donchian.donchian_channel_mavg()
            df_indicators['Donchian_Lower'] = donchian.donchian_channel_lband()
        except:
            for col in ['Donchian_Upper', 'Donchian_Middle', 'Donchian_Lower']:
                df_indicators[col] = np.nan

        df_indicators['Std_Dev'] = df['Close'].rolling(window=20).std()

        # ===== Supertrend =====
        try:
            supertrend = ta.trend.supertrend(high=df['High'], low=df['Low'], close=df['Close'], period=7, multiplier=3)
            df_indicators['Supertrend'] = supertrend['SUPERTd']
        except:
            df_indicators['Supertrend'] = np.nan

        # ===== Ichimoku Cloud =====
        try:
            ichimoku = ta.trend.IchimokuIndicator(high=df['High'], low=df['Low'])
            df_indicators['Ichimoku_Tenkan'] = ichimoku.ichimoku_conversion_line()
            df_indicators['Ichimoku_Kijun'] = ichimoku.ichimoku_base_line()
            df_indicators['Ichimoku_Span_A'] = ichimoku.ichimoku_a()
            df_indicators['Ichimoku_Span_B'] = ichimoku.ichimoku_b()
            df_indicators['Ichimoku_Cloud_Signal'] = (df_indicators['Ichimoku_Span_A'] > df_indicators['Ichimoku_Span_B']).astype(int)
        except:
            for col in ['Ichimoku_Tenkan', 'Ichimoku_Kijun', 'Ichimoku_Span_A', 'Ichimoku_Span_B', 'Ichimoku_Cloud_Signal']:
                df_indicators[col] = np.nan

        # ===== Pivot Points =====
        try:
            df_indicators['Pivot_Point'] = (df['High'] + df['Low'] + df['Close']) / 3
            df_indicators['Support_1'] = (2 * df_indicators['Pivot_Point']) - df['High']
            df_indicators['Support_2'] = df_indicators['Pivot_Point'] - (df['High'] - df['Low'])
            df_indicators['Resistance_1'] = (2 * df_indicators['Pivot_Point']) - df['Low']
            df_indicators['Resistance_2'] = df_indicators['Pivot_Point'] + (df['High'] - df['Low'])
        except:
            for col in ['Pivot_Point', 'Support_1', 'Support_2', 'Resistance_1', 'Resistance_2']:
                df_indicators[col] = np.nan

        # ===== PPO =====
        try:
            ppo = ta.momentum.PercentagePriceOscillator(close=df['Close'])
            df_indicators['PPO'] = ppo.ppo()
            df_indicators['PPO_Divergence'] = ppo.ppo_hist()
        except:
            df_indicators['PPO'] = np.nan
            df_indicators['PPO_Divergence'] = np.nan

        # Additional calculations
        df_indicators['Volume_MA'] = df['Volume'].rolling(window=20).mean()
        df_indicators['Volume_Spike'] = (df['Volume'] > df_indicators['Volume_MA'] * 2).astype(int)
        df_indicators['Liquidity'] = (df_indicators['Volume_MA'] > 100000).astype(int)

        # Drop columns with all NaN values
        df_indicators = df_indicators.dropna(axis=1, how='all')
        
        logger.info("Successfully calculated indicators")
        return df_indicators

    except Exception as e:
        logger.error(f"Critical error in calculate_indicators: {str(e)}")
        return None

# Generate trading signals with weights
def generate_signals(df: pd.DataFrame, ticker: str) -> tuple:
    if df is None or df.empty:
        return "No Data", [], {}

    latest = df.iloc[-1]
    signals = []
    signal_strength = 0
    signal_details = {}

    try:
        # Moving Average Signals
        ma_signals = []
        if not pd.isna(latest.get('EMA9')) and not pd.isna(latest.get('EMA21')):
            if latest['EMA9'] > latest['EMA21']:
                ma_signals.append("Bullish EMA Crossover (9>21)")
                signal_strength += 1.5
            else:
                ma_signals.append("Bearish EMA Crossover (9<21)")
                signal_strength -= 1.5
                
        if not pd.isna(latest.get('SMA200')):
            if latest['Close'] > latest['SMA200']:
                ma_signals.append("Price Above 200MA")
                signal_strength += 1.0
            else:
                ma_signals.append("Price Below 200MA")
                signal_strength -= 1.0
                
        if ma_signals:
            signal_details['Moving Averages'] = ma_signals

        # Momentum Signals
        momentum_signals = []
        if not pd.isna(latest.get('RSI')):
            if latest['RSI'] < 30:
                momentum_signals.append("Oversold RSI")
                signal_strength += 1.2
            elif latest['RSI'] > 70:
                momentum_signals.append("Overbought RSI")
                signal_strength -= 1.2
                
        if not pd.isna(latest.get('Stoch_K')) and not pd.isna(latest.get('Stoch_D')):
            if latest['Stoch_K'] < 20 and latest['Stoch_D'] < 20:
                momentum_signals.append("Oversold Stochastic")
                signal_strength += 0.8
            elif latest['Stoch_K'] > 80 and latest['Stoch_D'] > 80:
                momentum_signals.append("Overbought Stochastic")
                signal_strength -= 0.8
                
        if momentum_signals:
            signal_details['Momentum'] = momentum_signals

        # MACD Signals
        macd_signals = []
        if not pd.isna(latest.get('MACD')) and not pd.isna(latest.get('MACD_Signal')):
            if latest['MACD'] > latest['MACD_Signal']:
                macd_signals.append("Bullish MACD Crossover")
                signal_strength += 1.3
            else:
                macd_signals.append("Bearish MACD Crossover")
                signal_strength -= 1.3
                
        if macd_signals:
            signal_details['MACD'] = macd_signals

        # Trend Strength Signals
        trend_signals = []
        if not pd.isna(latest.get('ADX')) and not pd.isna(latest.get('+DI')) and not pd.isna(latest.get('-DI')):
            if latest['ADX'] > 25:
                if latest['+DI'] > latest['-DI']:
                    trend_signals.append("Strong Uptrend (ADX)")
                    signal_strength += 1.7
                else:
                    trend_signals.append("Strong Downtrend (ADX)")
                    signal_strength -= 1.7
            else:
                trend_signals.append("Weak Trend (ADX < 25)")
                
        if trend_signals:
            signal_details['Trend Strength'] = trend_signals

        # Volatility Signals
        vol_signals = []
        if not pd.isna(latest.get('BB_Lower')) and not pd.isna(latest.get('BB_Upper')):
            if latest['Close'] < latest['BB_Lower']:
                vol_signals.append("Below Bollinger Lower Band")
                signal_strength += 1.0
            elif latest['Close'] > latest['BB_Upper']:
                vol_signals.append("Above Bollinger Upper Band")
                signal_strength -= 1.0
                
        if not pd.isna(latest.get('ATR')):
            if latest['ATR'] > df['ATR'].mean():
                vol_signals.append("High Volatility")
            else:
                vol_signals.append("Low Volatility")
                
        if vol_signals:
            signal_details['Volatility'] = vol_signals

        # Volume Signals
        volume_signals = []
        if not pd.isna(latest.get('Volume_Spike')):
            if latest['Volume_Spike']:
                volume_signals.append("Volume Spike Detected")
                if latest['Close'] > latest['Open']:
                    signal_strength += 0.7
                else:
                    signal_strength -= 0.7
                    
        if not pd.isna(latest.get('OBV')):
            if latest['OBV'] > df['OBV'].rolling(20).mean()[-1]:
                volume_signals.append("Rising OBV")
                signal_strength += 0.5
            else:
                volume_signals.append("Falling OBV")
                signal_strength -= 0.5
                
        if volume_signals:
            signal_details['Volume'] = volume_signals

        # Ichimoku Signals
        ichimoku_signals = []
        if (not pd.isna(latest.get('Ichimoku_Span_A')) and 
            not pd.isna(latest.get('Ichimoku_Span_B'))):
            if latest['Close'] > latest['Ichimoku_Span_A'] and latest['Close'] > latest['Ichimoku_Span_B']:
                ichimoku_signals.append("Bullish Ichimoku Cloud")
                signal_strength += 1.2
            elif latest['Close'] < latest['Ichimoku_Span_A'] and latest['Close'] < latest['Ichimoku_Span_B']:
                ichimoku_signals.append("Bearish Ichimoku Cloud")
                signal_strength -= 1.2
                
        if ichimoku_signals:
            signal_details['Ichimoku'] = ichimoku_signals

        # Generate final signal
        if signal_strength > 4:
            final_signal = "Strong Buy"
        elif signal_strength > 2:
            final_signal = "Buy"
        elif signal_strength < -4:
            final_signal = "Strong Sell"
        elif signal_strength < -2:
            final_signal = "Sell"
        else:
            final_signal = "Neutral"

        # Compile all signals
        for category in signal_details.values():
            signals.extend(category)

        return final_signal, signals, signal_details

    except Exception as e:
        logger.error(f"Error generating signals for {ticker}: {str(e)}")
        return "Signal Generation Failed", [], {}

# Generate comprehensive analysis report
def generate_analysis_report(df: pd.DataFrame, ticker: str, signal: str, signal_details: dict):
    if df is None or df.empty:
        return None

    latest = df.iloc[-1]
    report = f"Technical Analysis Report for {ticker}\n"
    report += f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    report += f"\n=== Summary ===\n"
    report += f"Final Signal: {signal}\n"
    report += f"Price: {latest['Close']:.2f}\n"
    report += f"Volume: {latest['Volume']:,.0f}\n"
    
    report += f"\n=== Key Metrics ===\n"
    if 'RSI' in latest:
        report += f"RSI: {latest['RSI']:.2f} ({'Overbought' if latest['RSI'] > 70 else 'Oversold' if latest['RSI'] < 30 else 'Neutral'})\n"
    if 'ADX' in latest:
        report += f"ADX: {latest['ADX']:.2f} ({'Strong Trend' if latest['ADX'] > 25 else 'Weak Trend'})\n"
    if 'MACD' in latest:
        report += f"MACD: {latest['MACD']:.4f} ({'Bullish' if 'MACD_Signal' in latest and latest['MACD'] > latest['MACD_Signal'] else 'Bearish'})\n"
    if 'ATR' in latest:
        report += f"ATR: {latest['ATR']:.2f} ({'High Volatility' if 'ATR' in df.columns and latest['ATR'] > df['ATR'].mean() else 'Low Volatility'})\n"
    
    report += f"\n=== Moving Averages ===\n"
    if 'EMA9' in latest:
        report += f"EMA9: {latest['EMA9']:.2f}\n"
    if 'EMA21' in latest:
        report += f"EMA21: {latest['EMA21']:.2f}\n"
    if 'SMA50' in latest:
        report += f"SMA50: {latest['SMA50']:.2f}\n"
    if 'SMA200' in latest:
        report += f"SMA200: {latest['SMA200']:.2f}\n"
        report += f"Price Position vs SMAs: {'Above' if latest['Close'] > latest['SMA200'] else 'Below'} 200MA\n"
    
    report += f"\n=== Detailed Signals ===\n"
    for category, signals in signal_details.items():
        report += f"\n{category}:\n"
        for signal in signals:
            report += f"- {signal}\n"
    
    report += f"\n=== Support & Resistance ===\n"
    if 'Pivot_Point' in latest:
        report += f"Pivot Point: {latest['Pivot_Point']:.2f}\n"
    if 'Support_1' in latest:
        report += f"Support 1: {latest['Support_1']:.2f}\n"
    if 'Support_2' in latest:
        report += f"Support 2: {latest['Support_2']:.2f}\n"
    if 'Resistance_1' in latest:
        report += f"Resistance 1: {latest['Resistance_1']:.2f}\n"
    if 'Resistance_2' in latest:
        report += f"Resistance 2: {latest['Resistance_2']:.2f}\n"
    
    report += f"\n=== Recommendation ===\n"
    if "Buy" in signal:
        report += "Consider taking a long position with appropriate risk management.\n"
    elif "Sell" in signal:
        report += "Consider taking a short position or exiting long positions.\n"
    else:
        report += "Market conditions are neutral. Consider waiting for clearer signals.\n"
    
    return report

# Plot interactive chart with selected indicators
def plot_chart(df: pd.DataFrame, ticker: str):
    if df is None or df.empty:
        return None

    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, 
                       vertical_spacing=0.05, 
                       row_heights=[0.6, 0.2, 0.2],
                       subplot_titles=(f'{ticker} Price', 'Volume', 'Momentum Indicators'))

    # Candlestick with Moving Averages
    fig.add_trace(go.Candlestick(x=df.index,
                               open=df['Open'],
                               high=df['High'],
                               low=df['Low'],
                               close=df['Close'],
                               name='Price'), row=1, col=1)

    # Add available indicators
    if 'EMA9' in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df['EMA9'], line=dict(color='blue', width=1), name='EMA9'), row=1, col=1)
    if 'EMA21' in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df['EMA21'], line=dict(color='orange', width=1), name='EMA21'), row=1, col=1)
    if 'SMA200' in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA200'], line=dict(color='red', width=1), name='SMA200'), row=1, col=1)
    if 'BB_Upper' in df.columns and 'BB_Lower' in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df['BB_Upper'], line=dict(color='gray', width=1, dash='dash'), 
                               name='BB Upper', fill=None), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['BB_Lower'], line=dict(color='gray', width=1, dash='dash'), 
                               name='BB Lower', fill='tonexty'), row=1, col=1)
    if 'Ichimoku_Span_A' in df.columns and 'Ichimoku_Span_B' in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df['Ichimoku_Span_A'], line=dict(color='green', width=1, dash='dash'), 
                               name='Ichimoku Span A'), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['Ichimoku_Span_B'], line=dict(color='red', width=1, dash='dash'), 
                               name='Ichimoku Span B', fill='tonexty'), row=1, col=1)

    # Volume
    colors = ['green' if row['Close'] >= row['Open'] else 'red' for _, row in df.iterrows()]
    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name='Volume', marker_color=colors), row=2, col=1)
    if 'Volume_MA' in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df['Volume_MA'], line=dict(color='black', width=1), name='Vol MA(20)'), row=2, col=1)

    # Momentum Indicators
    if 'RSI' in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], line=dict(color='purple', width=1), name='RSI'), row=3, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1)
    if 'MACD' in df.columns and 'MACD_Signal' in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df['MACD'], line=dict(color='blue', width=1), name='MACD'), row=3, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['MACD_Signal'], line=dict(color='orange', width=1), name='MACD Signal'), row=3, col=1)
    if 'MACD_Hist' in df.columns:
        fig.add_trace(go.Bar(x=df.index, y=df['MACD_Hist'], name='MACD Hist', marker_color='gray'), row=3, col=1)

    fig.update_layout(title=f'{ticker} Technical Analysis',
                     height=900,
                     xaxis_rangeslider_visible=False,
                     showlegend=True)
    
    return fig

# Streamlit App
def main():
    st.set_page_config(layout="wide", page_title="Advanced Stock Analysis Dashboard")
    
    st.title("📈 Advanced Stock Technical Analysis Dashboard")
    
    # Input parameters
    col1, col2 = st.columns(2)
    with col1:
        ticker = st.text_input("Enter Stock Symbol (e.g. SBIN.NS)", "SBIN.NS").upper()
    with col2:
        period = st.selectbox("Select Time Period", ['1mo', '3mo', '6mo', '1y', '2y', '5y'], index=3)
    
    if st.button("Analyze", type="primary"):
        with st.spinner(f"Fetching data for {ticker}..."):
            data = fetch_market_data(ticker, period=period)
            
            if data is None:
                st.error(f"Failed to fetch data for {ticker}. Please try:")
                st.markdown("- A different time period (try 1y or longer)")
                st.markdown("- Verifying the ticker symbol is correct")
                st.markdown("- Checking your internet connection")
                return
                
            with st.spinner("Calculating indicators..."):
                data_with_indicators = calculate_indicators(data)
                
                if data_with_indicators is None:
                    st.error(f"Failed to calculate indicators for {ticker}. The data may be insufficient.")
                    return
                    
                with st.spinner("Generating signals..."):
                    signal, signals, signal_details = generate_signals(data_with_indicators, ticker)
                    analysis_report = generate_analysis_report(data_with_indicators, ticker, signal, signal_details)
        
        # Display results in tabs
        tab1, tab2, tab3, tab4 = st.tabs(["Summary", "Signals", "Chart", "Download"])
        
        with tab1:
            st.subheader(f"Analysis Summary for {ticker}")
            
            # Signal and key metrics
            cols = st.columns([1, 2])
            with cols[0]:
                if "Buy" in signal:
                    st.success(f"## {signal}", icon="📈")
                elif "Sell" in signal:
                    st.error(f"## {signal}", icon="📉")
                else:
                    st.warning(f"## {signal}", icon="➖")
                
                st.metric("Current Price", f"₹{data_with_indicators.iloc[-1]['Close']:.2f}")
                st.metric("Volume", f"{data_with_indicators.iloc[-1]['Volume']/1e6:.2f}M")
                
            with cols[1]:
                st.subheader("Key Metrics")
                metric_cols = st.columns(3)
                with metric_cols[0]:
                    if 'RSI' in data_with_indicators:
                        st.metric("RSI", f"{data_with_indicators.iloc[-1]['RSI']:.2f}", 
                                "Overbought" if data_with_indicators.iloc[-1]['RSI'] > 70 else "Oversold" if data_with_indicators.iloc[-1]['RSI'] < 30 else "Neutral")
                    if 'ADX' in data_with_indicators:
                        st.metric("ADX", f"{data_with_indicators.iloc[-1]['ADX']:.2f}", 
                                "Strong Trend" if data_with_indicators.iloc[-1]['ADX'] > 25 else "Weak Trend")
                with metric_cols[1]:
                    if 'MACD' in data_with_indicators:
                        st.metric("MACD", f"{data_with_indicators.iloc[-1]['MACD']:.4f}", 
                                "Bullish" if 'MACD_Signal' in data_with_indicators and data_with_indicators.iloc[-1]['MACD'] > data_with_indicators.iloc[-1]['MACD_Signal'] else "Bearish")
                    if 'ATR' in data_with_indicators:
                        st.metric("ATR", f"{data_with_indicators.iloc[-1]['ATR']:.2f}", 
                                "High Vol" if 'ATR' in data_with_indicators.columns and data_with_indicators.iloc[-1]['ATR'] > data_with_indicators['ATR'].mean() else "Low Vol")
                with metric_cols[2]:
                    if 'SMA200' in data_with_indicators:
                        st.metric("200MA", f"₹{data_with_indicators.iloc[-1]['SMA200']:.2f}")
                        st.metric("Trend", 
                                "Bullish" if data_with_indicators.iloc[-1]['Close'] > data_with_indicators.iloc[-1]['SMA200'] else "Bearish")
        
        with tab2:
            st.subheader("Detailed Signals")
            
            if not signals:
                st.info("No strong signals detected")
            else:
                for category, sigs in signal_details.items():
                    with st.expander(f"{category} ({len(sigs)} signals)"):
                        for sig in sigs:
                            if "Bullish" in sig or "Buy" in sig:
                                st.success(sig)
                            elif "Bearish" in sig or "Sell" in sig:
                                st.error(sig)
                            else:
                                st.info(sig)
        
        with tab3:
            st.subheader("Interactive Chart")
            fig = plot_chart(data_with_indicators, ticker)
            st.plotly_chart(fig, use_container_width=True)
        
        with tab4:
            st.subheader("Download Analysis")
            
            # CSV download
            csv = data_with_indicators.to_csv(index=True).encode('utf-8')
            st.download_button(
                label="Download Indicator Data (CSV)",
                data=csv,
                file_name=f"{ticker}_indicators.csv",
                mime="text/csv",
                help="Download all calculated indicators as CSV"
            )
            
            # Report download
            st.download_button(
                label="Download Analysis Report (TXT)",
                data=analysis_report,
                file_name=f"{ticker}_analysis_report.txt",
                mime="text/plain",
                help="Download detailed analysis report"
            )
            
            st.info("💡 The CSV contains all calculated indicators for further analysis")
            st.info("📝 The report contains the signal interpretation and summary")

if __name__ == "__main__":
    main()
