import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
import logging
from datetime import datetime, timedelta
import numpy as np
import uuid
import streamlit.components.v1 as components
import json

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Advanced Stock Trading Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Ace Editor HTML/JS for Pine Script with improved update handling
ACE_EDITOR_HTML = """
<div id="editor" style="height: 400px; width: 100%;"></div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/ace/1.9.6/ace.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/ace/1.9.6/mode-javascript.js"></script>
<script>
    var editor = ace.edit("editor");
    editor.setTheme("ace/theme/monokai");
    editor.session.setMode("ace/mode/javascript"); // Fallback to JS mode
    editor.setOptions({
        enableBasicAutocompletion: true,
        enableLiveAutocompletion: true,
        enableSnippets: true,
        fontSize: 14
    });
    editor.session.on('change', function() {
        var code = editor.getValue();
        window.parent.postMessage({type: 'pine_script_update', code: code}, '*');
    });
    window.addEventListener('message', function(event) {
        if (event.data.type === 'set_pine_script') {
            editor.setValue(event.data.code, -1);
        }
    });
</script>
"""

# Load tickers from CSV
@st.cache_data
def load_tickers(csv_path: str) -> dict:
    try:
        df = pd.read_csv(csv_path)
        tickers = {row['NAME OF COMPANY']: f"{row['SYMBOL']}.NS" for _, row in df.iterrows()}
        logger.debug(f"Loaded {len(tickers)} tickers from CSV")
        return tickers
    except Exception as e:
        logger.error(f"Error loading tickers from CSV: {str(e)}")
        return {}

# Get stock data with interval support
@st.cache_data(ttl=300)
def get_stock_data(symbol: str, period: str = "1y", interval: str = "1d"):
    try:
        stock = yf.Ticker(symbol)
        hist = stock.history(period=period, interval=interval)
        info = stock.info
        return hist, info
    except Exception as e:
        logger.error(f"Error fetching data for {symbol}: {str(e)}")
        return None, None

# Get higher timeframe data for MTF analysis
@st.cache_data(ttl=300)
def get_mtf_data(symbol: str, period: str = "1y", interval: str = "1d"):
    try:
        stock = yf.Ticker(symbol)
        hist = stock.history(period=period, interval=interval)
        return hist
    except Exception as e:
        logger.error(f"Error fetching MTF data for {symbol}: {str(e)}")
        return None

# Get additional stock details
def get_stock_details(symbol: str):
    try:
        stock = yf.Ticker(symbol)
        info = stock.info
        
        hist = stock.history(period="2d")
        if len(hist) >= 2:
            current_price = hist['Close'].iloc[-1]
            previous_close = hist['Close'].iloc[-2]
        else:
            current_price = info.get('currentPrice', 'N/A')
            previous_close = info.get('previousClose', 'N/A')
        
        details = {
            'company_name': info.get('longName', 'N/A'),
            'current_price': current_price,
            'previous_close': previous_close,
            'open': info.get('open', hist['Open'].iloc[-1] if len(hist) > 0 else 'N/A'),
            'high': info.get('dayHigh', hist['High'].iloc[-1] if len(hist) > 0 else 'N/A'),
            'low': info.get('dayLow', hist['Low'].iloc[-1] if len(hist) > 0 else 'N/A'),
            'volume': info.get('volume', hist['Volume'].iloc[-1] if len(hist) > 0 else 'N/A'),
            'market_cap': info.get('marketCap', 'N/A'),
            'pe_ratio': info.get('trailingPE', 'N/A'),
            'sector': info.get('sector', 'N/A'),
            'industry': info.get('industry', 'N/A'),
            'face_value': info.get('bookValue', 'N/A'),
            'fifty_two_week_high': info.get('fiftyTwoWeekHigh', 'N/A'),
            'fifty_two_week_low': info.get('fiftyTwoWeekLow', 'N/A'),
            'dividend_yield': info.get('dividendYield', 'N/A'),
            'beta': info.get('beta', 'N/A')
        }
        
        return details
    except Exception as e:
        logger.error(f"Error getting stock details for {symbol}: {str(e)}")
        return None

# Detect candlestick patterns
def detect_candlestick_patterns(data):
    patterns = []
    for i in range(2, len(data)):
        open_price = data['Open'].iloc[i]
        close_price = data['Close'].iloc[i]
        high_price = data['High'].iloc[i]
        low_price = data['Low'].iloc[i]
        prev_open = data['Open'].iloc[i-1]
        prev_close = data['Close'].iloc[i-1]
        body = abs(open_price - close_price)
        lower_wick = min(open_price, close_price) - low_price
        upper_wick = high_price - max(open_price, close_price)
        
        if body <= 0.1 * (high_price - low_price):
            patterns.append((data.index[i], 'Doji', 'gray'))
        
        if lower_wick >= 2 * body and upper_wick <= 0.3 * body and i > 0 and data['Close'].iloc[i-1] > data['Open'].iloc[i-1]:
            patterns.append((data.index[i], 'Hammer', 'green'))
        
        if i > 0 and prev_close < prev_open and close_price > open_price and close_price > prev_open and open_price < prev_close:
            patterns.append((data.index[i], 'Bullish Engulfing', 'green'))
        
        if i > 0 and prev_close > prev_open and close_price < open_price and close_price < prev_open and open_price > prev_close:
            patterns.append((data.index[i], 'Bearish Engulfing', 'red'))
        
        if i > 1 and data['Close'].iloc[i-2] < data['Open'].iloc[i-2] and \
           abs(data['Close'].iloc[i-1] - data['Open'].iloc[i-1]) <= 0.1 * (data['High'].iloc[i-1] - data['Low'].iloc[i-1]) and \
           close_price > open_price and close_price > (data['High'].iloc[i-2] + data['Low'].iloc[i-2]) / 2:
            patterns.append((data.index[i], 'Morning Star', 'green'))
        
        if i > 1 and data['Close'].iloc[i-2] > data['Open'].iloc[i-2] and \
           abs(data['Close'].iloc[i-1] - data['Open'].iloc[i-1]) <= 0.1 * (data['High'].iloc[i-1] - data['Low'].iloc[i-1]) and \
           close_price < open_price and close_price < (data['High'].iloc[i-2] + data['Low'].iloc[i-2]) / 2:
            patterns.append((data.index[i], 'Evening Star', 'red'))
    
    return patterns

# Calculate volume profile
def calculate_volume_profile(data, bins=50):
    price_range = np.linspace(data['Low'].min(), data['High'].max(), bins)
    volume_profile = np.zeros(bins-1)
    for i in range(bins-1):
        mask = (data['Close'] >= price_range[i]) & (data['Close'] < price_range[i+1])
        volume_profile[i] = data['Volume'][mask].sum()
    return price_range[:-1], volume_profile

# Backtest Pine Script strategy
def backtest_strategy(data, pine_script):
    try:
        if 'strategy(' not in pine_script:
            return None, "Backtesting requires a strategy script (use strategy() constructor)"
        
        signals = pd.Series(0, index=data.index)
        if 'ta.crossover' in pine_script:
            ma1_period = 10
            ma2_period = 20
            if 'input(' in pine_script:
                inputs = [int(s.split('= input(')[1].split(',')[0]) for s in pine_script.split('\n') if 'input(' in s]
                if len(inputs) >= 2:
                    ma1_period, ma2_period = inputs[:2]
            
            data['MA1'] = data['Close'].rolling(window=ma1_period).mean()
            data['MA2'] = data['Close'].rolling(window=ma2_period).mean()
            signals = np.where(data['MA1'] > data['MA2'], 1, 0)
            signals = pd.Series(signals, index=data.index).diff().fillna(0)
        
        position = 0
        trades = []
        entry_price = 0
        for i in range(1, len(data)):
            if signals.iloc[i] == 1 and position == 0:
                entry_price = data['Close'].iloc[i]
                position = 1
                trades.append({'entry_date': data.index[i], 'entry_price': entry_price, 'type': 'buy'})
            elif signals.iloc[i] == -1 and position == 1:
                exit_price = data['Close'].iloc[i]
                position = 0
                profit = exit_price - entry_price
                trades.append({'exit_date': data.index[i], 'exit_price': exit_price, 'type': 'sell', 'profit': profit})
        
        if trades:
            total_profit = sum(trade.get('profit', 0) for trade in trades)
            win_rate = len([t for t in trades if t.get('profit', 0) > 0]) / len(trades) * 100 if trades else 0
            return pd.DataFrame(trades), f"Total Profit: ₹{total_profit:.2f}, Win Rate: {win_rate:.2f}%"
        return None, "No trades executed"
    except Exception as e:
        return None, f"Backtesting error: {str(e)}"

# Validate Pine Script syntax
def validate_pine_script(pine_script):
    errors = []
    required_elements = ['//@version=', 'indicator(', 'strategy(']
    if not any(elem in pine_script for elem in required_elements):
        errors.append("Missing version or constructor (indicator/strategy)")
    
    if pine_script.count('(') != pine_script.count(')'):
        errors.append("Unbalanced parentheses")
    
    if 'ta.' in pine_script and not any(f'ta.{func}' in pine_script for func in ['sma', 'ema', 'rsi', 'macd', 'bbands', 'vwma', 'crossover']):
        errors.append("Unsupported ta.* function detected")
    
    return errors

# Create advanced candlestick chart
def create_candlestick_chart(data, symbol, company_name, show_instructions, pine_script=None, mtf_data=None, show_mtf=False, 
                            show_volume_profile=False, chart_style=None, indicators=None):
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        subplot_titles=(f'{company_name} ({symbol})', 'Volume', 'RSI/MACD'),
        row_heights=[0.6, 0.2, 0.2],
        specs=[[{"secondary_y": True}], [{"secondary_y": False}], [{"secondary_y": False}]]
    )
    
    candle_colors = {
        'classic': {'up': 'green', 'down': 'red', 'wick': 'black'},
        'hollow': {'up': 'white', 'down': 'black', 'wick': 'black'},
        'heikin_ashi': {'up': '#00ff00', 'down': '#ff0000', 'wick': '#333333'}
    }
    selected_colors = candle_colors.get(chart_style, candle_colors['classic'])
    
    fig.add_trace(
        go.Candlestick(
            x=data.index,
            open=data['Open'],
            high=data['High'],
            low=data['Low'],
            close=data['Close'],
            name="Price",
            increasing_line_color=selected_colors['up'],
            decreasing_line_color=selected_colors['down'],
            whiskerwidth=0.5
        ),
        row=1, col=1, secondary_y=False
    )
    
    if show_mtf and mtf_data is not None and not mtf_data.empty:
        fig.add_trace(
            go.Candlestick(
                x=mtf_data.index,
                open=mtf_data['Open'],
                high=mtf_data['High'],
                low=mtf_data['Low'],
                close=mtf_data['Close'],
                name="MTF Price",
                increasing_line_color='rgba(0, 255, 255, 0.3)',
                decreasing_line_color='rgba(255, 0, 255, 0.3)',
                whiskerwidth=0.3,
                opacity=0.5
            ),
            row=1, col=1, secondary_y=False
        )
    
    fig.add_trace(
        go.Bar(
            x=data.index,
            y=data['Volume'],
            name="Volume",
            marker_color='rgba(158,202,225,0.8)'
        ),
        row=2, col=1
    )
    
    if show_volume_profile:
        price_levels, volume_profile = calculate_volume_profile(data)
        fig.add_trace(
            go.Bar(
                y=price_levels,
                x=volume_profile,
                orientation='h',
                name="Volume Profile",
                marker_color='rgba(100, 150, 200, 0.5)',
                opacity=0.3
            ),
            row=1, col=1, secondary_y=True
        )
    
    patterns = detect_candlestick_patterns(data)
    for date, pattern, color in patterns:
        fig.add_annotation(
            x=date,
            y=data.loc[date]['High'] if color == 'green' else data.loc[date]['Low'],
            text=pattern,
            showarrow=True,
            arrowhead=2,
            ax=0,
            ay=-30 if color == 'green' else 30,
            font=dict(color=color, size=10),
            bgcolor='rgba(255,255,255,0.8)'
        )
        fig.add_trace(
            go.Scatter(
                x=[date],
                y=[data.loc[date]['High'] if color == 'green' else data.loc[date]['Low']],
                mode='markers',
                marker=dict(symbol='triangle-up' if color == 'green' else 'triangle-down', size=10, color=color),
                name=pattern
            ),
            row=1, col=1, secondary_y=False
        )
    
    if indicators:
        if 'SMA' in indicators:
            sma_period = indicators.get('sma_period', 20)
            data['SMA'] = data['Close'].rolling(window=sma_period).mean()
            fig.add_trace(
                go.Scatter(
                    x=data.index,
                    y=data['SMA'],
                    name=f"SMA ({sma_period})",
                    line=dict(color='blue', width=2)
                ),
                row=1, col=1, secondary_y=False
            )
        
        if 'EMA' in indicators:
            ema_period = indicators.get('ema_period', 20)
            data['EMA'] = data['Close'].ewm(span=ema_period, adjust=False).mean()
            fig.add_trace(
                go.Scatter(
                    x=data.index,
                    y=data['EMA'],
                    name=f"EMA ({ema_period})",
                    line=dict(color='orange', width=2)
                ),
                row=1, col=1, secondary_y=False
            )
        
        if 'Bollinger Bands' in indicators:
            bb_period = indicators.get('bb_period', 20)
            bb_std = indicators.get('bb_std', 2)
            data['BB_Mid'] = data['Close'].rolling(window=bb_period).mean()
            data['BB_Std'] = data['Close'].rolling(window=bb_period).std()
            data['BB_Upper'] = data['BB_Mid'] + bb_std * data['BB_Std']
            data['BB_Lower'] = data['BB_Mid'] - bb_std * data['BB_Std']
            fig.add_trace(
                go.Scatter(
                    x=data.index,
                    y=data['BB_Upper'],
                    name="BB Upper",
                    line=dict(color='gray', width=1, dash='dash')
                ),
                row=1, col=1, secondary_y=False
            )
            fig.add_trace(
                go.Scatter(
                    x=data.index,
                    y=data['BB_Lower'],
                    name="BB Lower",
                    line=dict(color='gray', width=1, dash='dash')
                ),
                row=1, col=1, secondary_y=False
            )
            fig.add_trace(
                go.Scatter(
                    x=data.index,
                    y=data['BB_Mid'],
                    name="BB Mid",
                    line=dict(color='gray', width=1)
                ),
                row=1, col=1, secondary_y=False
            )
        
        if 'MACD' in indicators:
            macd_fast = indicators.get('macd_fast', 12)
            macd_slow = indicators.get('macd_slow', 26)
            macd_signal = indicators.get('macd_signal', 9)
            data['EMA_Fast'] = data['Close'].ewm(span=macd_fast, adjust=False).mean()
            data['EMA_Slow'] = data['Close'].ewm(span=macd_slow, adjust=False).mean()
            data['MACD'] = data['EMA_Fast'] - data['EMA_Slow']
            data['MACD_Signal'] = data['MACD'].ewm(span=macd_signal, adjust=False).mean()
            data['MACD_Hist'] = data['MACD'] - data['MACD_Signal']
            fig.add_trace(
                go.Scatter(
                    x=data.index,
                    y=data['MACD'],
                    name="MACD",
                    line=dict(color='blue', width=1)
                ),
                row=3, col=1
            )
            fig.add_trace(
                go.Scatter(
                    x=data.index,
                    y=data['MACD_Signal'],
                    name="MACD Signal",
                    line=dict(color='red', width=1)
                ),
                row=3, col=1
            )
            fig.add_trace(
                go.Bar(
                    x=data.index,
                    y=data['MACD_Hist'],
                    name="MACD Histogram",
                    marker_color='gray'
                ),
                row=3, col=1
            )
    
    # Process Pine Script with detailed error logging
    if pine_script:
        try:
            errors = validate_pine_script(pine_script)
            if errors:
                st.error(f"Pine Script validation errors: {'; '.join(errors)}")
                logger.error(f"Pine Script validation failed: {errors}")
                return fig
            
            logger.debug(f"Processing Pine Script: {pine_script[:100]}...")
            
            if 'ta.vwma' in pine_script:
                window = 20
                if 'vwmaLength = input(' in pine_script:
                    start = pine_script.find('vwmaLength = input(') + len('vwmaLength = input(')
                    end = pine_script.find(',', start)
                    try:
                        window = int(pine_script[start:end])
                    except ValueError:
                        st.error("Invalid VWMA length parameter")
                        return fig
                data['VWMA'] = (data['Close'] * data['Volume']).rolling(window=window).sum() / data['Volume'].rolling(window=window).sum()
                fig.add_trace(
                    go.Scatter(
                        x=data.index,
                        y=data['VWMA'],
                        name=f"VWMA ({window})",
                        line=dict(color='purple', width=2)
                    ),
                    row=1, col=1, secondary_y=False
                )
            
            if 'ta.rsi' in pine_script:
                window = 14
                if 'rsiLength = input(' in pine_script:
                    start = pine_script.find('rsiLength = input(') + len('rsiLength = input(')
                    end = pine_script.find(',', start)
                    try:
                        window = int(pine_script[start:end])
                    except ValueError:
                        st.error("Invalid RSI length parameter")
                        return fig
                delta = data['Close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
                rs = gain / loss
                data['RSI'] = 100 - (100 / (1 + rs))
                fig.add_trace(
                    go.Scatter(
                        x=data.index,
                        y=data['RSI'],
                        name=f"RSI ({window})",
                        line=dict(color='orange', width=1)
                    ),
                    row=3, col=1
                )
                fig.add_hline(y=70, line_dash="dot", line_color="red", row=3, col=1)
                fig.add_hline(y=30, line_dash="dot", line_color="green", row=3, col=1)
            
            if 'ta.macd' in pine_script:
                fast = 12
                slow = 26
                signal = 9
                if 'fastLength = input(' in pine_script:
                    start = pine_script.find('fastLength = input(') + len('fastLength = input(')
                    end = pine_script.find(',', start)
                    try:
                        fast = int(pine_script[start:end])
                    except ValueError:
                        st.error("Invalid MACD fast length parameter")
                        return fig
                if 'slowLength = input(' in pine_script:
                    start = pine_script.find('slowLength = input(') + len('slowLength = input(')
                    end = pine_script.find(',', start)
                    try:
                        slow = int(pine_script[start:end])
                    except ValueError:
                        st.error("Invalid MACD slow length parameter")
                        return fig
                if 'signalLength = input(' in pine_script:
                    start = pine_script.find('signalLength = input(') + len('signalLength = input(')
                    end = pine_script.find(',', start)
                    try:
                        signal = int(pine_script[start:end])
                    except ValueError:
                        st.error("Invalid MACD signal length parameter")
                        return fig
                data['EMA_Fast'] = data['Close'].ewm(span=fast, adjust=False).mean()
                data['EMA_Slow'] = data['Close'].ewm(span=slow, adjust=False).mean()
                data['MACD'] = data['EMA_Fast'] - data['EMA_Slow']
                data['MACD_Signal'] = data['MACD'].ewm(span=signal, adjust=False).mean()
                data['MACD_Hist'] = data['MACD'] - data['MACD_Signal']
                fig.add_trace(
                    go.Scatter(
                        x=data.index,
                        y=data['MACD'],
                        name="MACD",
                        line=dict(color='blue', width=1)
                    ),
                    row=3, col=1
                )
                fig.add_trace(
                    go.Scatter(
                        x=data.index,
                        y=data['MACD_Signal'],
                        name="MACD Signal",
                        line=dict(color='red', width=1)
                    ),
                    row=3, col=1
                )
                fig.add_trace(
                    go.Bar(
                        x=data.index,
                        y=data['MACD_Hist'],
                        name="MACD Histogram",
                        marker_color='gray'
                    ),
                    row=3, col=1
                )
            
            if 'ta.bbands' in pine_script:
                period = 20
                std = 2
                if 'length = input(' in pine_script:
                    start = pine_script.find('length = input(') + len('length = input(')
                    end = pine_script.find(',', start)
                    try:
                        period = int(pine_script[start:end])
                    except ValueError:
                        st.error("Invalid Bollinger Bands length parameter")
                        return fig
                if 'stdDev = input(' in pine_script:
                    start = pine_script.find('stdDev = input(') + len('stdDev = input(')
                    end = pine_script.find(',', start)
                    try:
                        std = float(pine_script[start:end])
                    except ValueError:
                        st.error("Invalid Bollinger Bands stdDev parameter")
                        return fig
                data['BB_Mid'] = data['Close'].rolling(window=period).mean()
                data['BB_Std'] = data['Close'].rolling(window=period).std()
                data['BB_Upper'] = data['BB_Mid'] + std * data['BB_Std']
                data['BB_Lower'] = data['BB_Mid'] - std * data['BB_Std']
                fig.add_trace(
                    go.Scatter(
                        x=data.index,
                        y=data['BB_Upper'],
                        name="BB Upper",
                        line=dict(color='gray', width=1, dash='dash')
                    ),
                    row=1, col=1, secondary_y=False
                )
                fig.add_trace(
                    go.Scatter(
                        x=data.index,
                        y=data['BB_Lower'],
                        name="BB Lower",
                        line=dict(color='gray', width=1, dash='dash')
                    ),
                    row=1, col=1, secondary_y=False
                )
                fig.add_trace(
                    go.Scatter(
                        x=data.index,
                        y=data['BB_Mid'],
                        name="BB Mid",
                        line=dict(color='gray', width=1)
                    ),
                    row=1, col=1, secondary_y=False
                )
            
            if 'request.security(' in pine_script:
                try:
                    symbol = pine_script.split('request.security("')[1].split('"')[0]
                    timeframe = pine_script.split(', "')[1].split('"')[0]
                    mtf_data = get_mtf_data(symbol, period="1y", interval=timeframe)
                    if mtf_data is not None and not mtf_data.empty:
                        fig.add_trace(
                            go.Scatter(
                                x=mtf_data.index,
                                y=mtf_data['Close'],
                                name=f"Security ({symbol}, {timeframe})",
                                line=dict(color='cyan', width=1, dash='dot')
                            ),
                            row=1, col=1, secondary_y=False
                        )
                    else:
                        st.warning(f"No data for security {symbol} at timeframe {timeframe}")
                except IndexError:
                    st.error("Invalid request.security syntax")
                    return fig
            
            if 'ta.crossover' in pine_script:
                ma1_period = 10
                ma2_period = 20
                if 'input(' in pine_script:
                    inputs = [int(s.split('= input(')[1].split(',')[0]) for s in pine_script.split('\n') if 'input(' in s]
                    if len(inputs) >= 2:
                        ma1_period, ma2_period = inputs[:2]
                data['MA1'] = data['Close'].rolling(window=ma1_period).mean()
                data['MA2'] = data['Close'].rolling(window=ma2_period).mean()
                data['Crossover'] = np.where(data['MA1'] > data['MA2'], 1, 0).diff()
                buy_signals = data[data['Crossover'] == 1].index
                sell_signals = data[data['Crossover'] == -1].index
                fig.add_trace(
                    go.Scatter(
                        x=buy_signals,
                        y=data.loc[buy_signals]['Close'],
                        mode='markers',
                        name='Buy Signal',
                        marker=dict(symbol='triangle-up', size=10, color='green')
                    ),
                    row=1, col=1, secondary_y=False
                )
                fig.add_trace(
                    go.Scatter(
                        x=sell_signals,
                        y=data.loc[sell_signals]['Close'],
                        mode='markers',
                        name='Sell Signal',
                        marker=dict(symbol='triangle-down', size=10, color='red')
                    ),
                    row=1, col=1, secondary_y=False
                )
                
        except Exception as e:
            st.error(f"Error processing Pine Script: {str(e)}")
            logger.error(f"Pine Script processing failed: {str(e)}")
            return fig
    
    fig.update_layout(
        title=f'{company_name} Advanced Stock Chart',
        yaxis_title='Price (₹)',
        yaxis2_title='Volume Profile',
        yaxis3_title='RSI / MACD',
        xaxis_rangeslider_visible=False,
        height=800,
        showlegend=True,
        hovermode='x unified',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(
            rangeselector=dict(
                buttons=list([
                    dict(count=1, label="1m", step="month", stepmode="backward"),
                    dict(count=6, label="6m", step="month", stepmode="backward"),
                    dict(count=1, label="YTD", step="year", stepmode="todate"),
                    dict(count=1, label="1y", step="year", stepmode="backward"),
                    dict(step="all")
                ]),
                bgcolor='rgba(150, 200, 250, 0.4)',
                activecolor='rgba(100, 150, 250, 0.6)',
                bordercolor='rgba(0,0,0,0)',
                borderwidth=0,
                font=dict(color='white')
            ),
            rangeslider=dict(visible=False),
            type="date",
            showgrid=True,
            gridcolor='rgba(200,200,200,0.2)',
            autorange=True,
            fixedrange=False
        ),
        yaxis=dict(
            autorange=True,
            fixedrange=False,
            showgrid=True,
            gridcolor='rgba(200,200,200,0.2)'
        ),
        yaxis2=dict(
            autorange=True,
            fixedrange=True,
            showgrid=False
        ),
        yaxis3=dict(
            autorange=True,
            fixedrange=False,
            showgrid=True,
            gridcolor='rgba(200,200,200,0.2)'
        )
    )
    
    if show_instructions:
        fig.add_annotation(
            text="<b>Chart Navigation:</b><br>"
                 "- Click 'Pan' in mode bar or hold Shift+drag to pan<br>"
                 "- Click 'Zoom' in mode bar or drag to zoom area<br>"
                 "- Mouse wheel/pinch to zoom in/out<br>"
                 "- Double-click to reset<br>"
                 "- Click patterns for details",
            align='left',
            showarrow=False,
            xref='paper',
            yref='paper',
            x=0.02,
            y=1.15,
            bordercolor='#2D2D2D',
            borderwidth=1,
            borderpad=4,
            bgcolor='#2D2D2D',
            font=dict(color='white'),
            opacity=0.9
        )
    
    return fig

# Format numbers
def format_number(num):
    if num == 'N/A' or num is None:
        return 'N/A'
    
    try:
        num = float(num)
        if num >= 10000000:
            return f"₹{num/10000000:.2f} Cr"
        elif num >= 100000:
            return f"₹{num/100000:.2f} L"
        elif num >= 1000:
            return f"₹{num/1000:.2f} K"
        else:
            return f"₹{num:.2f}"
    except:
        return str(num)

# Pine Script Templates
PINE_TEMPLATES = {
    "Moving Average Crossover": """
//@version=6
strategy("MA Crossover", overlay=true)
ma1 = ta.sma(close, input(10, "Fast MA"))
ma2 = ta.sma(close, input(20, "Slow MA"))
buySignal = ta.crossover(ma1, ma2)
sellSignal = ta.crossunder(ma1, ma2)
if (buySignal)
    strategy.entry("Buy", strategy.long)
if (sellSignal)
    strategy.entry("Sell", strategy.short)
plot(ma1, color=color.blue, title="Fast MA")
plot(ma2, color=color.red, title="Slow MA")
""",
    "RSI Divergence": """
//@version=6
indicator("RSI Divergence", overlay=false)
rsi = ta.rsi(close, input(14, "RSI Length"))
overbought = input(70, "Overbought")
oversold = input(30, "Oversold")
plot(rsi, color=color.orange, title="RSI")
hline(overbought, "Overbought", color=color.red, linestyle=hline.style_dotted)
hline(oversold, "Oversold", color=color.green, linestyle=hline.style_dotted)
""",
    "VWMA Indicator": """
//@version=6
indicator("VWMA", overlay=true)
vwma = ta.vwma(close, input(20, "VWMA Length"))
plot(vwma, color=color.purple, title="VWMA")
"""
}

# Main dashboard
def main():
    st.title("📊 Advanced Stock Trading Dashboard")
    st.markdown("---")
    
    # Initialize session states
    if 'show_instructions' not in st.session_state:
        st.session_state.show_instructions = False
    if 'selected_interval' not in st.session_state:
        st.session_state.selected_interval = "1d"
    if 'pine_script' not in st.session_state:
        st.session_state.pine_script = ""
    if 'show_pine_editor' not in st.session_state:
        st.session_state.show_pine_editor = False
    if 'chart_style' not in st.session_state:
        st.session_state.chart_style = "classic"
    if 'indicators' not in st.session_state:
        st.session_state.indicators = {}
    if 'show_mtf' not in st.session_state:
        st.session_state.show_mtf = False
    if 'mtf_interval' not in st.session_state:
        st.session_state.mtf_interval = "1d"
    if 'show_volume_profile' not in st.session_state:
        st.session_state.show_volume_profile = False
    if 'saved_scripts' not in st.session_state:
        st.session_state.saved_scripts = {}
    if 'pine_script_update' not in st.session_state:
        st.session_state.pine_script_update = ""
    
    # Load tickers
    csv_path = r"E:\Coding\Attandance\Stock sheet\EQUITY_L.csv"
    
    if 'TICKER_DB' not in st.session_state:
        with st.spinner("Loading stock data..."):
            st.session_state.TICKER_DB = load_tickers(csv_path)
    
    TICKER_DB = st.session_state.TICKER_DB
    
    if not TICKER_DB:
        st.error("Failed to load ticker data. Please check the CSV file path.")
        return
    
    # Sidebar for search and selection
    st.sidebar.header("🔍 Search Stocks")
    
    search_term = st.sidebar.text_input("Search Company Name:", placeholder="Type company name...")
    
    if search_term:
        filtered_companies = [name for name in TICKER_DB.keys() 
                            if search_term.lower() in name.lower()]
    else:
        filtered_companies = list(TICKER_DB.keys())
    
    if filtered_companies:
        selected_company = st.sidebar.selectbox(
            "Select Company:",
            options=filtered_companies,
            index=0
        )
        
        selected_symbol = TICKER_DB[selected_company]
        
        period_options = {
            "1 Month": "1mo",
            "3 Months": "3mo",
            "6 Months": "6mo",
            "1 Year": "1y",
            "2 Years": "2y",
            "5 Years": "5y"
        }
        
        selected_period_name = st.sidebar.selectbox(
            "Select Time Period:",
            options=list(period_options.keys()),
            index=3
        )
        
        selected_period = period_options[selected_period_name]
        
        st.sidebar.markdown("---")
        st.sidebar.header("⏱ Filter Time Interval")
        
        with st.sidebar.expander("Select Time Interval", expanded=True):
            st.markdown("**Ticks:**")
            tick_col1, tick_col2 = st.columns(2)
            with tick_col1:
                if st.button("1 tick"):
                    st.session_state.selected_interval = "1t"
            with tick_col2:
                if st.button("10 ticks"):
                    st.session_state.selected_interval = "10t"
            
            tick_col3, tick_col4 = st.columns(2)
            with tick_col3:
                if st.button("100 ticks"):
                    st.session_state.selected_interval = "100t"
            with tick_col4:
                if st.button("1000 ticks"):
                    st.session_state.selected_interval = "1000t"
            
            st.markdown("**Seconds:**")
            sec_col1, sec_col2 = st.columns(2)
            with sec_col1:
                if st.button("1 second"):
                    st.session_state.selected_interval = "1s"
                if st.button("10 seconds"):
                    st.session_state.selected_interval = "10s"
                if st.button("30 seconds"):
                    st.session_state.selected_interval = "30s"
            with sec_col2:
                if st.button("5 seconds"):
                    st.session_state.selected_interval = "5s"
                if st.button("15 seconds"):
                    st.session_state.selected_interval = "15s"
                if st.button("45 seconds"):
                    st.session_state.selected_interval = "45s"
            
            st.markdown("**Minutes:**")
            min_col1, min_col2 = st.columns(2)
            with min_col1:
                if st.button("1 minute"):
                    st.session_state.selected_interval = "1m"
                if st.button("5 minutes"):
                    st.session_state.selected_interval = "5m"
                if st.button("30 minutes"):
                    st.session_state.selected_interval = "30m"
            with min_col2:
                if st.button("2 minutes"):
                    st.session_state.selected_interval = "2m"
                if st.button("15 minutes"):
                    st.session_state.selected_interval = "15m"
                if st.button("45 minutes"):
                    st.session_state.selected_interval = "45m"
            
            st.markdown("**Days:**")
            day_col1, day_col2 = st.columns(2)
            with day_col1:
                if st.button("1 day"):
                    st.session_state.selected_interval = "1d"
                if st.button("1 month"):
                    st.session_state.selected_interval = "1mo"
            with day_col2:
                if st.button("1 week"):
                    st.session_state.selected_interval = "1wk"
                if st.button("3 months"):
                    st.session_state.selected_interval = "3mo"
            
            st.markdown("**Custom Interval:**")
            custom_interval = st.text_input("Enter custom interval (e.g., '2h' for 2 hours)", 
                                          value=st.session_state.selected_interval)
            if st.button("Apply Custom Interval"):
                if custom_interval:
                    st.session_state.selected_interval = custom_interval
        
        st.sidebar.markdown(f"**Current Interval:** `{st.session_state.selected_interval}`")
        
        st.sidebar.markdown("---")
        st.sidebar.header("🎨 Chart Customization")
        
        chart_style = st.sidebar.selectbox(
            "Select Chart Style:",
            options=["classic", "hollow", "heikin_ashi"],
            index=0
        )
        st.session_state.chart_style = chart_style
        
        st.sidebar.markdown("**Technical Indicators**")
        show_sma = st.sidebar.checkbox("Show SMA")
        sma_period = st.sidebar.number_input("SMA Period", min_value=1, max_value=200, value=20) if show_sma else 20
        show_ema = st.sidebar.checkbox("Show EMA")
        ema_period = st.sidebar.number_input("EMA Period", min_value=1, max_value=200, value=20) if show_ema else 20
        show_bbands = st.sidebar.checkbox("Show Bollinger Bands")
        bb_period = st.sidebar.number_input("BB Period", min_value=1, max_value=200, value=20) if show_bbands else 20
        bb_std = st.sidebar.number_input("BB Std Dev", min_value=0.1, max_value=5.0, value=2.0, step=0.1) if show_bbands else 2.0
        show_macd = st.sidebar.checkbox("Show MACD")
        macd_fast = st.sidebar.number_input("MACD Fast", min_value=1, max_value=50, value=12) if show_macd else 12
        macd_slow = st.sidebar.number_input("MACD Slow", min_value=1, max_value=100, value=26) if show_macd else 26
        macd_signal = st.sidebar.number_input("MACD Signal", min_value=1, max_value=50, value=9) if show_macd else 9
        
        indicators = {}
        if show_sma:
            indicators['SMA'] = True
            indicators['sma_period'] = sma_period
        if show_ema:
            indicators['EMA'] = True
            indicators['ema_period'] = ema_period
        if show_bbands:
            indicators['Bollinger Bands'] = True
            indicators['bb_period'] = bb_period
            indicators['bb_std'] = bb_std
        if show_macd:
            indicators['MACD'] = True
            indicators['macd_fast'] = macd_fast
            indicators['macd_slow'] = macd_slow
            indicators['macd_signal'] = macd_signal
        st.session_state.indicators = indicators
        
        st.sidebar.markdown("**Multi-Timeframe Analysis**")
        show_mtf = st.sidebar.checkbox("Show Higher Timeframe")
        mtf_interval = st.sidebar.selectbox(
            "MTF Interval",
            options=["1h", "4h", "1d", "1wk"],
            index=2
        ) if show_mtf else "1d"
        st.session_state.show_mtf = show_mtf
        st.session_state.mtf_interval = mtf_interval
        
        show_volume_profile = st.sidebar.checkbox("Show Volume Profile")
        st.session_state.show_volume_profile = show_volume_profile
        
        st.sidebar.markdown("**Alerts (Placeholder)**")
        alert_price = st.sidebar.number_input("Set Price Alert", min_value=0.0, value=0.0, step=0.1)
        if st.sidebar.button("Set Alert"):
            st.sidebar.success(f"Alert set for price ₹{alert_price:.2f} (Placeholder)")
        
        # Pine Script Editor
        st.sidebar.markdown("---")
        st.sidebar.header("📝 Pine Script Editor")
        
        if st.sidebar.button("📝 Open Advanced Pine Script Editor"):
            st.session_state.show_pine_editor = not st.session_state.show_pine_editor
        
        # Main content area
        tabs = st.tabs(["Chart", "Pine Script Editor"])
        
        with tabs[0]:
            st.subheader(f"📈 {selected_company} - Advanced Candlestick Chart ({st.session_state.selected_interval} interval)")
            
            if st.button('📋 Show/Hide Chart Navigation Instructions'):
                st.session_state.show_instructions = not st.session_state.show_instructions
            
            with st.spinner("Loading chart data..."):
                hist_data, info = get_stock_data(selected_symbol, selected_period, st.session_state.selected_interval)
                mtf_data = get_mtf_data(selected_symbol, selected_period, st.session_state.mtf_interval) if st.session_state.show_mtf else None
            
            if hist_data is not None and not hist_data.empty:
                fig = create_candlestick_chart(
                    hist_data, 
                    selected_symbol, 
                    selected_company, 
                    st.session_state.show_instructions,
                    st.session_state.pine_script,
                    mtf_data,
                    st.session_state.show_mtf,
                    st.session_state.show_volume_profile,
                    st.session_state.chart_style,
                    st.session_state.indicators
                )
                st.plotly_chart(fig, use_container_width=True, config={
                    'displayModeBar': True,
                    'modeBarButtonsToAdd': ['zoom2d', 'pan2d', 'zoomIn2d', 'zoomOut2d', 'autoScale2d', 'resetScale2d'],
                    'scrollZoom': True,
                    'displaylogo': False
                })
                
                if st.session_state.show_instructions:
                    st.markdown("""
                    <div style="background-color:#2D2D2D;padding:10px;border-radius:5px;color:white;">
                    <h4 style="color:white;">📋 Chart Navigation Instructions</h4>
                    <ul>
                        <li><b>Pan:</b> Select 'Pan' in mode bar (top-right) or hold Shift+drag</li>
                        <li><b>Zoom:</b> Select 'Zoom' in mode bar, drag to select area, or use mouse wheel/pinch</li>
                        <li><b>Zoom In/Out:</b> Use '+' or '-' buttons in mode bar</li>
                        <li><b>Reset:</b> Double-click or click 'Reset' in mode bar</li>
                        <li><b>Patterns:</b> Click patterns for details</li>
                    </ul>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("---")
                st.subheader(f"📋 Stock Details: {selected_company}")
                
                with st.spinner("Fetching stock details..."):
                    details = get_stock_details(selected_symbol)
                
                if details:
                    col1, col2 = st.columns([1, 1])
                    
                    with col1:
                        st.markdown("### 💰 Stock Price Details")
                        st.markdown(f"**Data Fetched At:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                        
                        if details['current_price'] != 'N/A':
                            change = float(details['current_price']) - float(details['previous_close']) if details['previous_close'] != 'N/A' else 0
                            change_pct = (change / float(details['previous_close']) * 100) if details['previous_close'] != 'N/A' and float(details['previous_close']) != 0 else 0
                            
                            arrow = "↗️" if change >= 0 else "↘️"
                            
                            st.metric(
                                "Current Price",
                                f"₹{details['current_price']:.2f}" if details['current_price'] != 'N/A' else 'N/A',
                                f"{arrow} ₹{change:.2f} ({change_pct:.2f}%)"
                            )
                        else:
                            st.metric("Current Price", "N/A")
                        
                        st.write(f"**Previous Close:** ₹{details['previous_close']:.2f}" if details['previous_close'] != 'N/A' else "**Previous Close:** N/A")
                        st.write(f"**Open:** ₹{details['open']:.2f}" if details['open'] != 'N/A' else "**Open:** N/A")
                        st.write(f"**High:** ₹{details['high']:.2f}" if details['high'] != 'N/A' else "**High:** N/A")
                        st.write(f"**Low:** ₹{details['low']:.2f}" if details['low'] != 'N/A' else "**Low:** N/A")
                    
                    with col2:
                        st.write(f"**52W High:** ₹{details['fifty_two_week_high']:.2f}" if details['fifty_two_week_high'] != 'N/A' else "**52W High:** N/A")
                        st.write(f"**52W Low:** ₹{details['fifty_two_week_low']:.2f}" if details['fifty_two_week_low'] != 'N/A' else "**52W Low:** N/A")
                        
                        st.markdown("### 📈 Trade Information")
                        st.write(f"**Volume:** {format_number(details['volume'])}")
                        st.write(f"**Market Cap:** {format_number(details['market_cap'])}")
                        st.write(f"**PE Ratio:** {details['pe_ratio']:.2f}" if details['pe_ratio'] != 'N/A' else "**PE Ratio:** N/A")
                        st.write(f"**Beta:** {details['beta']:.2f}" if details['beta'] != 'N/A' else "**Beta:** N/A")
                        st.write(f"**Dividend Yield:** {details['dividend_yield']:.2%}" if details['dividend_yield'] != 'N/A' else "**Dividend Yield:** N/A")
                        st.write(f"**Face Value:** ₹{details['face_value']:.2f}" if details['face_value'] != 'N/A' else "**Face Value:** N/A")
                    
                    st.markdown("### 🏢 Securities Information")
                    st.write(f"**Sector:** {details['sector']}")
                    st.write(f"**Industry:** {details['industry']}")
                
                else:
                    st.error("Failed to fetch stock details.")
            
            else:
                st.error("Failed to load chart data.")
        
        with tabs[1]:
            if st.session_state.show_pine_editor:
                st.subheader("Advanced Pine Script Editor")
                
                editor_tabs = st.tabs(["Code Editor", "Condition Builder"])
                
                with editor_tabs[0]:
                    st.markdown("""
                    **Pine Script Editor Features:**
                    - Syntax highlighting and autocompletion
                    - Real-time error detection
                    - Backtesting for strategies
                    - Save/load scripts
                    - Pre-built templates
                    - Auto-apply pasted scripts (optional)
                    """)
                    
                    # Template selection
                    template = st.selectbox("Select Template", options=["None"] + list(PINE_TEMPLATES.keys()))
                    if template != "None":
                        st.session_state.pine_script = PINE_TEMPLATES[template]
                        st.session_state.pine_script_update = PINE_TEMPLATES[template]
                    
                    # Auto-apply toggle
                    auto_apply = st.checkbox("Auto-apply pasted scripts", value=True)
                    
                    # Ace Editor
                    components.html(ACE_EDITOR_HTML, height=450)
                    
                    # Capture Pine Script updates
                    pine_script_js = """
                    <script>
                        window.addEventListener('message', function(event) {
                            if (event.data.type === 'pine_script_update') {
                                sessionStorage.setItem('pine_script', event.data.code);
                            }
                        });
                        setInterval(function() {
                            var code = sessionStorage.getItem('pine_script') || '';
                            document.getElementById('pine_script_input').value = code;
                        }, 500);
                    </script>
                    <input type="hidden" id="pine_script_input" value="">
                    """
                    components.html(pine_script_js, height=0)
                    
                    pine_script_input = st.text_input("Hidden Pine Script", value="", key="pine_script_input", label_visibility="hidden")
                    if pine_script_input and pine_script_input != st.session_state.pine_script_update:
                        st.session_state.pine_script_update = pine_script_input
                        if auto_apply:
                            errors = validate_pine_script(pine_script_input)
                            if not errors:
                                st.session_state.pine_script = pine_script_input
                                st.success("Pasted Pine Script applied automatically!")
                            else:
                                st.error(f"Cannot auto-apply: {'; '.join(errors)}")
                    
                    # Save/load scripts
                    script_name = st.text_input("Script Name", value="MyScript")
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        if st.button("Apply Script"):
                            st.session_state.pine_script = st.session_state.pine_script_update
                            st.success("Pine Script applied!")
                    with col2:
                        if st.button("Save Script"):
                            st.session_state.saved_scripts[script_name] = st.session_state.pine_script_update
                            st.success(f"Script '{script_name}' saved!")
                    with col3:
                        if st.button("Clear Script"):
                            st.session_state.pine_script = ""
                            st.session_state.pine_script_update = ""
                            st.markdown("""
                            <script>
                                window.parent.postMessage({type: 'set_pine_script', code: ''}, '*');
                            </script>
                            """, unsafe_allow_html=True)
                            st.success("Script cleared!")
                    with col4:
                        saved_script = st.selectbox("Load Script", options=["None"] + list(st.session_state.saved_scripts.keys()))
                        if saved_script != "None":
                            st.session_state.pine_script = st.session_state.saved_scripts[saved_script]
                            st.session_state.pine_script_update = st.session_state.saved_scripts[saved_script]
                            st.markdown("""
                            <script>
                                window.parent.postMessage({type: 'set_pine_script', code: `%s`}, '*');
                            </script>
                            """ % st.session_state.pine_script.replace('`', '\\`').replace('\n', '\\n'), unsafe_allow_html=True)
                    
                    # Backtesting
                    if st.button("Backtest Strategy"):
                        trades, results = backtest_strategy(hist_data, st.session_state.pine_script)
                        if trades is not None:
                            st.write(f"**Backtest Results:** {results}")
                            st.dataframe(trades)
                        else:
                            st.error(results)
                
                with editor_tabs[1]:
                    st.markdown("**Condition Builder (No Coding Required)**")
                    st.write("Build indicators/strategies using visual controls.")
                    
                    indicator_type = st.selectbox("Indicator/Strategy Type", options=["Moving Average Crossover", "RSI", "MACD"])
                    script = ""
                    if indicator_type == "Moving Average Crossover":
                        ma1_period = st.number_input("Fast MA Period", min_value=1, value=10)
                        ma2_period = st.number_input("Slow MA Period", min_value=1, value=20)
                        script = f"""
//@version=6
strategy("MA Crossover", overlay=true)
ma1 = ta.sma(close, {ma1_period})
ma2 = ta.sma(close, {ma2_period})
buySignal = ta.crossover(ma1, ma2)
sellSignal = ta.crossunder(ma1, ma2)
if (buySignal)
    strategy.entry("Buy", strategy.long)
if (sellSignal)
    strategy.entry("Sell", strategy.short)
plot(ma1, color=color.blue, title="Fast MA")
plot(ma2, color=color.red, title="Slow MA")
"""
                    elif indicator_type == "RSI":
                        rsi_period = st.number_input("RSI Period", min_value=1, value=14)
                        overbought = st.number_input("Overbought Level", min_value=0, value=70)
                        oversold = st.number_input("Oversold Level", min_value=0, value=30)
                        script = f"""
//@version=6
indicator("RSI", overlay=false)
rsi = ta.rsi(close, {rsi_period})
plot(rsi, color=color.orange, title="RSI")
hline({overbought}, "Overbought", color=color.red, linestyle=hline.style_dotted)
hline({oversold}, "Oversold", color=color.green, linestyle=hline.style_dotted)
"""
                    elif indicator_type == "MACD":
                        fast = st.number_input("Fast Period", min_value=1, value=12)
                        slow = st.number_input("Slow Period", min_value=1, value=26)
                        signal = st.number_input("Signal Period", min_value=1, value=9)
                        script = f"""
//@version=6
indicator("MACD", overlay=false)
[macdLine, signalLine, histLine] = ta.macd(close, {fast}, {slow}, {signal})
plot(macdLine, color=color.blue, title="MACD")
plot(signalLine, color=color.red, title="Signal")
plot(histLine, color=color.gray, title="Histogram", style=plot.style_histogram)
"""
                    
                    if st.button("Generate Script"):
                        st.session_state.pine_script = script
                        st.session_state.pine_script_update = script
                        st.markdown("""
                        <script>
                            window.parent.postMessage({type: 'set_pine_script', code: `%s`}, '*');
                        </script>
                        """ % script.replace('`', '\\`').replace('\n', '\\n'), unsafe_allow_html=True)
                        st.success("Script generated and applied!")
                    
                    st.code(script, language="pine")
    
    else:
        st.sidebar.write("No companies found matching your search.")
    
    st.markdown("---")
    st.markdown("*Data provided by Yahoo Finance. This dashboard is for educational purposes only.*")

if __name__ == "__main__":
    main()
