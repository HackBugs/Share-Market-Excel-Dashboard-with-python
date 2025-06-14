import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objs as go
from plotly.subplots import make_subplots
from ta.trend import SMAIndicator, EMAIndicator, MACD, IchimokuIndicator
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.volatility import BollingerBands, AverageTrueRange
from ta.volume import OnBalanceVolumeIndicator, ChaikinMoneyFlowIndicator
from datetime import datetime, timedelta
import io
import re

# Set page config for responsive design
st.set_page_config(layout="wide", page_title="Deep Stock Technical Analysis with Ticker Search")

# Pre-loaded ticker dictionary (common Indian and global stocks)
TICKER_DB = {
    "Reliance Industries": "RELIANCE.NS",
    "Tata Steel": "TATASTEEL.NS",
    "State Bank of India": "SBIN.NS",
    "Infosys": "INFY.NS",
    "HDFC Bank": "HDFCBANK.NS",
    "Adani Enterprises": "ADANIENT.NS",
    "Tata Motors": "TATAMOTORS.NS",
    "Bajaj Finance": "BAJFINANCE.NS",
    "Apple": "AAPL",
    "Microsoft": "MSFT",
    "Amazon": "AMZN",
    "Tesla": "TSLA",
    "Vodafone": "VOD.L",
    "Toyota": "7203.T",
    "BP PLC": "BP.L"
}

# Function to search tickers by company name
def search_ticker(query):
    query = query.lower().strip()
    matches = []
    for company, ticker in TICKER_DB.items():
        if re.search(query, company.lower(), re.IGNORECASE):
            matches.append((company, ticker))
    return matches

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

# Function to calculate Fibonacci retracement levels
def calculate_fibonacci_levels(df):
    high = df['High'].max()
    low = df['Low'].min()
    diff = high - low
    levels = {
        '0.0%': high,
        '23.6%': high - 0.236 * diff,
        '38.2%': high - 0.382 * diff,
        '50.0%': high - 0.5 * diff,
        '61.8%': high - 0.618 * diff,
        '100.0%': low
    }
    return levels

# Function to calculate support/resistance levels
def calculate_pivot_points(df):
    pivot = (df['High'][-1] + df['Low'][-1] + df['Close'][-1]) / 3
    support1 = (2 * pivot) - df['High'][-1]
    resistance1 = (2 * pivot) - df['Low'][-1]
    return pivot, support1, resistance1

# Function to calculate VWAP
def calculate_vwap(df):
    typical_price = (df['High'] + df['Low'] + df['Close']) / 3
    vwap = (typical_price * df['Volume']).cumsum() / df['Volume'].cumsum()
    return vwap

# Function to calculate advanced technical indicators
def calculate_indicators(df, sma1_window=20, sma2_window=50):
    sma1 = SMAIndicator(close=df['Close'], window=sma1_window).sma_indicator()
    sma2 = SMAIndicator(close=df['Close'], window=sma2_window).sma_indicator()
    ema20 = EMAIndicator(close=df['Close'], window=20).ema_indicator()
    rsi = RSIIndicator(close=df['Close'], window=14).rsi()
    macd = MACD(close=df['Close'])
    macd_line = macd.macd()
    signal_line = macd.macd_signal()
    histogram = macd.macd_diff()
    bb = BollingerBands(close=df['Close'], window=20, window_dev=2)
    bb_high = bb.bollinger_hband()
    bb_low = bb.bollinger_lband()
    bb_mid = bb.bollinger_mavg()
    atr = AverageTrueRange(high=df['High'], low=df['Low'], close=df['Close'], window=14).average_true_range()
    stoch = StochasticOscillator(high=df['High'], low=df['Low'], close=df['Close'], window=14, smooth_window=3)
    stoch_k = stoch.stoch()
    stoch_d = stoch.stoch_signal()
    ichimoku = IchimokuIndicator(high=df['High'], low=df['Low'], window1=9, window2=26, window3=52)
    tenkan_sen = ichimoku.ichimoku_conversion_line()
    kijun_sen = ichimoku.ichimoku_base_line()
    senkou_span_a = ichimoku.ichimoku_a()
    senkou_span_b = ichimoku.ichimoku_b()
    obv = OnBalanceVolumeIndicator(close=df['Close'], volume=df['Volume']).on_balance_volume()
    cmf = ChaikinMoneyFlowIndicator(high=df['High'], low=df['Low'], close=df['Close'], volume=df['Volume'], window=20).chaikin_money_flow()
    vwap = calculate_vwap(df)
    
    return pd.DataFrame({
        'SMA1': sma1,
        'SMA2': sma2,
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
        'Senkou_Span_B': senkou_span_b,
        'OBV': obv,
        'CMF': cmf,
        'VWAP': vwap
    }, index=df.index)

# Function to generate buy/sell recommendation
def generate_recommendation(df, indicators):
    score = 0
    signals = []
    weights = {
        'RSI': 1.0,
        'MACD': 1.5,
        'SMA': 1.2,
        'Stochastic': 1.0,
        'Ichimoku': 1.5,
        'CMF': 0.8,
        'OBV': 0.8,
        'VWAP': 1.0
    }
    
    latest_rsi = indicators['RSI'][-1]
    if latest_rsi < 30:
        score += 2 * weights['RSI']
        signals.append("RSI Oversold (Buy)")
    elif latest_rsi > 70:
        score -= 2 * weights['RSI']
        signals.append("RSI Overbought (Sell)")
    
    if indicators['MACD'][-1] > indicators['Signal'][-1] and indicators['MACD'][-2] <= indicators['Signal'][-2]:
        score += 2 * weights['MACD']
        signals.append("MACD Bullish Crossover (Buy)")
    elif indicators['MACD'][-1] < indicators['Signal'][-1] and indicators['MACD'][-2] >= indicators['Signal'][-2]:
        score -= 2 * weights['MACD']
        signals.append("MACD Bearish Crossover (Sell)")
    
    if indicators['SMA1'][-1] > indicators['SMA2'][-1] and indicators['SMA1'][-2] <= indicators['SMA2'][-2]:
        score += 2 * weights['SMA']
        signals.append("SMA Bullish Crossover (Buy)")
    elif indicators['SMA1'][-1] < indicators['SMA2'][-1] and indicators['SMA1'][-2] >= indicators['SMA2'][-2]:
        score -= 2 * weights['SMA']
        signals.append("SMA Bearish Crossover (Sell)")
    
    if indicators['Stoch_K'][-1] < 20 and indicators['Stoch_K'][-1] > indicators['Stoch_D'][-1]:
        score += 2 * weights['Stochastic']
        signals.append("Stochastic Oversold (Buy)")
    elif indicators['Stoch_K'][-1] > 80 and indicators['Stoch_K'][-1] < indicators['Stoch_D'][-1]:
        score -= 2 * weights['Stochastic']
        signals.append("Stochastic Overbought (Sell)")
    
    if (df['Close'][-1] > indicators['Senkou_Span_A'][-1] and 
        df['Close'][-1] > indicators['Senkou_Span_B'][-1] and
        indicators['Tenkan_Sen'][-1] > indicators['Kijun_Sen'][-1]):
        score += 2 * weights['Ichimoku']
        signals.append("Ichimoku Bullish (Buy)")
    elif (df['Close'][-1] < indicators['Senkou_Span_A'][-1] and 
          df['Close'][-1] < indicators['Senkou_Span_B'][-1]):
        score -= 2 * weights['Ichimoku']
        signals.append("Ichimoku Bearish (Sell)")
    
    if indicators['CMF'][-1] > 0:
        score += 1 * weights['CMF']
        signals.append("CMF Positive (Buy)")
    elif indicators['CMF'][-1] < 0:
        score -= 1 * weights['CMF']
        signals.append("CMF Negative (Sell)")
    
    if indicators['OBV'][-1] > indicators['OBV'][-2]:
        score += 1 * weights['OBV']
        signals.append("OBV Increasing (Buy)")
    elif indicators['OBV'][-1] < indicators['OBV'][-2]:
        score -= 1 * weights['OBV']
        signals.append("OBV Decreasing (Sell)")
    
    if df['Close'][-1] > indicators['VWAP'][-1]:
        score += 1 * weights['VWAP']
        signals.append("Price Above VWAP (Buy)")
    elif df['Close'][-1] < indicators['VWAP'][-1]:
        score -= 1 * weights['VWAP']
        signals.append("Price Below VWAP (Sell)")
    
    recommendation = "Buy" if score >= 5 else "Not Buy"
    return recommendation, signals, score

# Function to perform simple backtest
def backtest_strategy(df, indicators):
    signals = []
    position = 0
    returns = []
    
    for i in range(1, len(df)):
        buy_signal = (indicators['SMA1'][i] > indicators['SMA2'][i] and 
                      indicators['SMA1'][i-1] <= indicators['SMA2'][i-1] and
                      indicators['MACD'][i] > indicators['Signal'][i])
        sell_signal = (indicators['SMA1'][i] < indicators['SMA2'][i] and 
                       indicators['SMA1'][i-1] >= indicators['SMA2'][i-1])
        
        if buy_signal and position == 0:
            position = 1
            signals.append(('Buy', df.index[i], df['Close'][i]))
        elif sell_signal and position == 1:
            position = 0
            signals.append(('Sell', df.index[i], df['Close'][i]))
            if len(signals) >= 2:
                returns.append((signals[-1][2] - signals[-2][2]) / signals[-2][2])
    
    total_return = sum(returns) * 100 if returns else 0
    win_rate = sum(1 for r in returns if r > 0) / len(returns) * 100 if returns else 0
    return total_return, win_rate, signals

# Function to create plotly chart
def create_chart(df, indicators, ticker, currency_symbol, fib_levels, pivot, support1, resistance1):
    fig = make_subplots(rows=5, cols=1, shared_xaxes=True, 
                       vertical_spacing=0.05, 
                       subplot_titles=(f'{ticker} Price and Indicators', 'RSI', 'MACD', 'Stochastic', 'Volume & CMF'),
                       row_heights=[0.4, 0.15, 0.15, 0.15, 0.15])
    
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name='Price'
    ), row=1, col=1)
    
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
    
    for level, price in fib_levels.items():
        fig.add_hline(y=price, line_dash="dash", line_color="yellow", annotation_text=f"Fib {level}", row=1, col=1)
    
    fig.add_hline(y=support1, line_dash="dot", line_color="green", annotation_text="S1", row=1, col=1)
    fig.add_hline(y=resistance1, line_dash="dot", line_color="red", annotation_text="R1", row=1, col=1)
    
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
    
    fig.update_layout(
        height=1200,
        showlegend=True,
        template='plotly_dark',
        xaxis_rangeslider_visible=False,
        yaxis_title=f'Price ({currency_symbol})',
        yaxis2_title='RSI',
        yaxis3_title='MACD',
        yaxis4_title='Stochastic',
        yaxis5_title='Volume/CMF'
    )
    
    return fig

# Function to generate analysis report
def generate_report(ticker, info, df, indicators, recommendation, signals, score, fib_levels, pivot, support1, resistance1, backtest_results, currency_symbol):
    report = f"""
# Deep Technical Analysis Report for {ticker}
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Stock Information
- **Company**: {info.get('longName', 'N/A')}
- **Exchange**: {info.get('exchange', 'N/A')}
- **Currency**: {currency_symbol}
- **Current Price**: {currency_symbol}{df['Close'][-1]:.2f}
- **52 Week High**: {currency_symbol}{info.get('fiftyTwoWeekHigh', 'N/A')}
- **52 Week Low**: {currency_symbol}{info.get('fiftyTwoWeekLow', 'N/A')}

## Recommendation
- **Recommendation**: {recommendation}
- **Signal Score**: {score:.2f}
- **Signals**:
{chr(10).join([f'  - {s}' for s in signals])}

## Technical Indicators
- **RSI**: {indicators['RSI'][-1]:.2f} ({'Oversold' if indicators['RSI'][-1] < 30 else 'Overbought' if indicators['RSI'][-1] > 70 else 'Neutral'})
- **MACD**: {indicators['MACD'][-1]:.2f} (Signal: {indicators['Signal'][-1]:.2f})
- **SMA1 ({indicators['SMA1'].name})**: {indicators['SMA1'][-1]:.2f}
- **SMA2 ({indicators['SMA2'].name})**: {indicators['SMA2'][-1]:.2f}
- **ATR**: {currency_symbol}{indicators['ATR'][-1]:.2f}
- **Stochastic %K**: {indicators['Stoch_K'][-1]:.2f}
- **Stochastic %D**: {indicators['Stoch_D'][-1]:.2f}
- **Ichimoku Cloud**: {'Above' if df['Close'][-1] > max(indicators['Senkou_Span_A'][-1], indicators['Senkou_Span_B'][-1]) else 'Below'}
- **CMF**: {indicators['CMF'][-1]:.2f} ({'Positive' if indicators['CMF'][-1] > 0 else 'Negative'})
- **OBV**: {indicators['OBV'][-1]:,.0f}
- **VWAP**: {currency_symbol}{indicators['VWAP'][-1]:.2f}

## Key Levels
- **Pivot Point**: {currency_symbol}{pivot:.2f}
- **Support 1**: {currency_symbol}{support1:.2f}
- **Resistance 1**: {currency_symbol}{resistance1:.2f}
- **Fibonacci Levels**:
{chr(10).join([f'  - {level}: {currency_symbol}{price:.2f}' for level, price in fib_levels.items()])}

## Risk Assessment
- **Volatility (ATR)**: {currency_symbol}{indicators['ATR'][-1]:.2f}
- **Suggested Stop Loss**: {currency_symbol}{(df['Close'][-1] - 2 * indicators['ATR'][-1]):.2f} (2x ATR below current price)
- **Position Sizing**: Risk no more than 1-2% of capital per trade

## Backtest Results
- **Total Return**: {backtest_results[0]:.2f}%
- **Win Rate**: {backtest_results[1]:.2f}%

## Conclusion
This analysis suggests a **{recommendation}** position based on a comprehensive evaluation of technical indicators. Consider the signal score, risk assessment, and key levels before making a trading decision. Always combine with fundamental analysis and proper risk management.
"""
    return report

# Streamlit app
def main():
    st.title("Deep Stock Technical Analysis with Ticker Search")
    
    # Sidebar for inputs
    with st.sidebar:
        st.header("Stock Selection")
        
        # Ticker search
        search_query = st.text_input("Search Company Name (e.g., Reliance, Apple)", "")
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
                st.warning("No matching stocks found. Try a different name or enter the ticker manually.")
        
        # Manual ticker input
        ticker = st.text_input("Enter Stock Ticker (e.g., RELIANCE.NS)", value=selected_ticker if selected_ticker else "")
        
        period = st.selectbox("Select Time Period", ['1mo', '3mo', '6mo', '1y', '2y', '5y'], index=3)
        interval = st.selectbox("Select Data Interval", ['1d', '1wk', '1mo'], index=0)
        st.subheader("Indicator Settings")
        sma1_window = st.slider("SMA1 Window", 5, 50, 20)
        sma2_window = st.slider("SMA2 Window", 10, 100, 50)
        analyze = st.button("Analyze")
    
    if analyze and ticker:
        try:
            with st.spinner("Fetching data..."):
                df, info = fetch_stock_data(ticker, period, interval)
                
                if df.empty:
                    st.error("No data found for the given ticker.")
                    return
                
                currency, currency_symbol = get_currency_and_symbol(info)
                indicators = calculate_indicators(df, sma1_window, sma2_window)
                fib_levels = calculate_fibonacci_levels(df)
                pivot, support1, resistance1 = calculate_pivot_points(df)
                recommendation, signals, score = generate_recommendation(df, indicators)
                total_return, win_rate, backtest_signals = backtest_strategy(df, indicators)
                
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    fig = create_chart(df, indicators, ticker, currency_symbol, fib_levels, pivot, support1, resistance1)
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    st.subheader("Recommendation")
                    if recommendation == "Buy":
                        st.button("Buy", key="buy", help="Bullish Signal", disabled=True, 
                                 type="primary", use_container_width=True, 
                                 args={'styles': {'background-color': 'green'}})
                    else:
                        st.button("Not Buy", key="sell", help="Bearish/Neutral Signal", disabled=True, 
                                 type="primary", use_container_width=True, 
                                 args={'styles': {'background-color': 'red'}})
                    
                    st.write(f"**Signal Score**: {score:.2f}")
                    st.write("**Signals**:")
                    for signal in signals:
                        st.write(f"- {signal}")
                    
                    st.subheader("Stock Information")
                    st.write(f"**Company**: {info.get('longName', 'N/A')}")
                    st.write(f"**Exchange**: {info.get('exchange', 'N/A')}")
                    st.write(f"**Currency**: {currency} ({currency_symbol})")
                    st.write(f"**Current Price**: {currency_symbol}{df['Close'][-1]:.2f}")
                    st.write(f"**52 Week High**: {currency_symbol}{info.get('fiftyTwoWeekHigh', 'N/A')}")
                    st.write(f"**52 Week Low**: {currency_symbol}{info.get('fiftyTwoWeekLow', 'N/A')}")
                    
                    st.subheader("Key Levels")
                    st.write(f"**Pivot Point**: {currency_symbol}{pivot:.2f}")
                    st.write(f"**Support 1**: {currency_symbol}{support1:.2f}")
                    st.write(f"**Resistance 1**: {currency_symbol}{resistance1:.2f}")
                    st.write("**Fibonacci Levels**:")
                    for level, price in fib_levels.items():
                        st.write(f"- {level}: {currency_symbol}{price:.2f}")
                    
                    st.subheader("Advanced Indicators")
                    st.write(f"**RSI**: {indicators['RSI'][-1]:.2f}")
                    st.write(f"**ATR**: {currency_symbol}{indicators['ATR'][-1]:.2f}")
                    st.write(f"**Stochastic %K**: {indicators['Stoch_K'][-1]:.2f}")
                    st.write(f"**Stochastic %D**: {indicators['Stoch_D'][-1]:.2f}")
                    st.write(f"**CMF**: {indicators['CMF'][-1]:.2f}")
                    st.write(f"**OBV**: {indicators['OBV'][-1]:,.0f}")
                    st.write(f"**VWAP**: {currency_symbol}{indicators['VWAP'][-1]:.2f}")
                    
                    st.subheader("Daily Performance")
                    latest_change = ((df['Close'][-1] - df['Close'][-2]) / df['Close'][-2] * 100) if len(df) > 1 else 0
                    st.write(f"**Daily Change**: {latest_change:.2f}%")
                    
                    st.subheader("Backtest Results")
                    st.write(f"**Total Return**: {total_return:.2f}%")
                    st.write(f"**Win Rate**: {win_rate:.2f}%")
                
                st.subheader("Analysis Report")
                report = generate_report(ticker, info, df, indicators, recommendation, signals, score, 
                                       fib_levels, pivot, support1, resistance1, (total_return, win_rate), currency_symbol)
                st.markdown(report)
                
                buffer = io.StringIO()
                buffer.write(report)
                st.download_button(
                    label="Download Analysis Report",
                    data=buffer.getvalue(),
                    file_name=f"{ticker}_analysis_report.txt",
                    mime="text/plain"
                )
        
        except Exception as e:
            st.error(f"Error: {str(e)}")
    
    st.markdown("""
    ### Instructions
    - Search for a company by name (e.g., 'Reliance', 'Apple') to find its ticker, or enter the ticker manually (e.g., RELIANCE.NS).
    - Select a matching stock from the dropdown if searching by name.
    - Choose a time period and data interval (daily, weekly, monthly).
    - Adjust SMA windows for custom analysis.
    - Click 'Analyze' to view deep technical analysis.
    - The app automatically detects the currency (e.g., INR/₹ for Indian stocks, USD/$ for US stocks).
    - Green 'Buy' or red 'Not Buy' buttons indicate trading recommendations.
    - Download the detailed analysis report for offline review.
    - Recommendations are based on RSI, MACD, SMA, Stochastic, Ichimoku, CMF, OBV, and VWAP signals.
    - Always combine with fundamental analysis and proper risk management.
    """)

if __name__ == "__main__":
    main()
