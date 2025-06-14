import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import time
import requests
from packaging import version
from typing import Dict, List, Tuple

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Page config
if not st.session_state.get("page_config_set", False):
    st.set_page_config(layout="wide", page_title="Expert Stock Investment Analysis")
    st.session_state.page_config_set = True

# Ticker database
TICKER_DB = {
    "Reliance Industries": ["RELIANCE.NS", "RELIANCE.BO"],
    "Tata Steel": ["TATASTEEL.NS", "TATASTEEL.BO"],
    "State Bank of India": ["SBIN.NS", "SBIN.BO"],
    "Infosys": ["INFY.NS", "INFY.BO"],
    "HDFC Bank": ["HDFCBANK.NS", "HDFCBANK.BO"],
    "Adani Enterprises": ["ADANIENT.NS", "ADANIENT.BO"],
    "Tata Motors": ["TATAMOTORS.NS", "TATAMOTORS.BO"],
    "Bajaj Finance": ["BAJFINANCE.NS", "BAJFINANCE.BO"],
}

def generate_mock_data(start_date: datetime, end_date: datetime) -> pd.DataFrame:
    """Generate mock stock data for testing."""
    dates = pd.date_range(start=start_date, end=end_date, freq='B')
    data = {
        'Open': np.random.uniform(100, 200, len(dates)),
        'High': np.random.uniform(110, 210, len(dates)),
        'Low': np.random.uniform(90, 190, len(dates)),
        'Close': np.random.uniform(100, 200, len(dates)),
        'Adj Close': np.random.uniform(100, 200, len(dates)),
        'Volume': np.random.randint(1000, 100000, len(dates))
    }
    df = pd.DataFrame(data, index=dates)
    return df

@st.cache_data(ttl=3600)
def fetch_yfinance_data(ticker: str, start_date: datetime, end_date: datetime, retries: int = 3, proxies: Dict = None) -> Tuple[pd.DataFrame, str]:
    """Fetch data using yfinance with version-aware proxy handling."""
    if start_date >= end_date or end_date > datetime.now() + timedelta(days=1):
        error_msg = f"Invalid date range: start={start_date}, end={end_date}"
        logger.error(error_msg)
        return pd.DataFrame(), error_msg
    
    min_date = datetime.now() - timedelta(days=365*10)
    if start_date < min_date:
        start_date = min_date
    
    yf_version = getattr(yf, '__version__', '0.1.0')
    use_proxies = proxies and version.parse(yf_version) >= version.parse('0.2.0')
    
    error_msg = ""
    for attempt in range(retries):
        try:
            if use_proxies:
                df = yf.download(ticker, start=start_date, end=end_date, progress=False, proxies=proxies)
            else:
                df = yf.download(ticker, start=start_date, end=end_date, progress=False)
            if not df.empty:
                return df, ""
            error_msg = f"Empty data for {ticker}"
            logger.warning(f"Empty data for {ticker}, attempt {attempt + 1}")
        except Exception as e:
            error_msg = str(e)
            logger.error(f"yfinance attempt {attempt + 1} failed for {ticker}: {error_msg}")
            if "429" in error_msg.lower():
                error_msg = "Rate limit exceeded (HTTP 429). Try a proxy or Alpha Vantage."
                break
        time.sleep(5 * (attempt + 1))
    
    logger.error(f"All {retries} yfinance attempts failed for {ticker}: {error_msg}")
    return pd.DataFrame(), error_msg

@st.cache_data(ttl=3600)
def fetch_alpha_vantage_data(ticker: str, start_date: datetime, end_date: datetime, api_key: str, proxies: Dict = None) -> Tuple[pd.DataFrame, str]:
    """Fetch data using Alpha Vantage."""
    try:
        url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={ticker}&apikey={api_key}&outputsize=full"
        response = requests.get(url, proxies=proxies, timeout=10)
        data = response.json()
        if "Time Series (Daily)" not in data:
            error_msg = f"No data from Alpha Vantage for {ticker}: {data.get('Note', 'Unknown error')}"
            logger.error(error_msg)
            return pd.DataFrame(), error_msg
        df = pd.DataFrame(data["Time Series (Daily)"]).T
        df.index = pd.to_datetime(df.index)
        df = df[["4. close", "5. volume"]].rename(columns={"4. close": "Close", "5. volume": "Volume"})
        df["Close"] = df["Close"].astype(float)
        df["Volume"] = df["Volume"].astype(int)
        df = df.loc[start_date:end_date]
        return df, ""
    except Exception as e:
        error_msg = f"Alpha Vantage failed for {ticker}: {str(e)}"
        logger.error(error_msg)
        return pd.DataFrame(), error_msg

def fetch_stock_data(ticker_name: str, ticker_symbols: List[str], start_date: datetime, end_date: datetime, api_key: str, proxies: Dict = None, use_yfinance: bool = False) -> Tuple[pd.DataFrame, str]:
    """Fetch data, prioritizing Alpha Vantage."""
    if not use_yfinance and api_key:
        for ticker in ticker_symbols:
            df, error_msg = fetch_alpha_vantage_data(ticker, start_date, end_date, api_key, proxies)
            if not df.empty:
                return df, ""
    for ticker in ticker_symbols:
        df, error_msg = fetch_yfinance_data(ticker, start_date, end_date, proxies=proxies)
        if not df.empty:
            return df, ""
    return pd.DataFrame(), f"No data for {ticker_name}: {error_msg}"

def test_yahoo_finance_connectivity() -> str:
    """Test connectivity to Yahoo Finance."""
    try:
        response = requests.get("https://finance.yahoo.com", timeout=10)
        return f"Yahoo Finance accessible: HTTP {response.status_code}"
    except Exception as e:
        return f"Failed to reach Yahoo Finance: {str(e)}"

def calculate_technical_indicators(df: pd.DataFrame) -> Dict:
    """Calculate RSI, MACD, Bollinger Bands, and Volume Trend."""
    # RSI (14-day)
    delta = df['Close'].diff()
    gain = delta.where(delta > 0, 0).rolling(window=14).mean()
    loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs)).iloc[-1]
    
    # MACD (12, 26, 9)
    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    macd = exp1 - exp2
    signal = macd.ewm(span=9, adjust=False).mean()
    macd_diff = (macd - signal).iloc[-1]
    
    # Bollinger Bands (20-day)
    sma = df['Close'].rolling(window=20).mean()
    std = df['Close'].rolling(window=20).std()
    upper_band = sma + (std * 2)
    lower_band = sma - (std * 2)
    current_price = df['Close'].iloc[-1]
    bb_position = (current_price - lower_band.iloc[-1]) / (upper_band.iloc[-1] - lower_band.iloc[-1])
    
    # Volume Trend (20-day vs 50-day)
    vol_short = df['Volume'].rolling(window=20).mean().iloc[-1]
    vol_long = df['Volume'].rolling(window=50).mean().iloc[-1]
    vol_trend = vol_short > vol_long
    
    return {
        "rsi": rsi,
        "macd_diff": macd_diff,
        "bb_position": bb_position,
        "vol_trend": vol_trend,
        "current_price": current_price
    }

def analyze_ticker(ticker_name: str, ticker_symbols: List[str], api_key: str, proxies: Dict = None, use_mock: bool = False, use_yfinance: bool = False) -> Dict:
    """Analyze stock using expert techniques and provide buy/not buy recommendation."""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=180)
    
    if use_mock:
        df = generate_mock_data(start_date, end_date)
    else:
        df, error_msg = fetch_stock_data(ticker_name, ticker_symbols, start_date, end_date, api_key, proxies, use_yfinance)
        if df.empty:
            return {"recommendation": "Not Buy", "details": f"Data unavailable: {error_msg}", "score": 0, "current_price": None}
    
    if len(df) < 50:
        return {"recommendation": "Not Buy", "details": "Insufficient data (<50 days)", "score": 0, "current_price": None}
    
    try:
        indicators = calculate_technical_indicators(df)
        rsi = indicators["rsi"]
        macd_diff = indicators["macd_diff"]
        bb_position = indicators["bb_position"]
        vol_trend = indicators["vol_trend"]
        current_price = indicators["current_price"]
        
        # Scoring system
        score = 0
        details = []
        
        # RSI: Buy if oversold (<30), Not Buy if overbought (>70)
        if rsi < 30:
            score += 1
            details.append(f"RSI: Buy (RSI = {rsi:.2f}, oversold)")
        elif rsi > 70:
            score -= 1
            details.append(f"RSI: Not Buy (RSI = {rsi:.2f}, overbought)")
        else:
            details.append(f"RSI: Neutral (RSI = {rsi:.2f})")
        
        # MACD: Buy if MACD crosses above signal, Not Buy if below
        if macd_diff > 0:
            score += 1
            details.append(f"MACD: Buy (MACD > Signal, diff = {macd_diff:.2f})")
        else:
            score -= 1
            details.append(f"MACD: Not Buy (MACD < Signal, diff = {macd_diff:.2f})")
        
        # Bollinger Bands: Buy if near lower band (<0.2), Not Buy if near upper (>0.8)
        if bb_position < 0.2:
            score += 1
            details.append(f"Bollinger Bands: Buy (Price near lower band, position = {bb_position:.2f})")
        elif bb_position > 0.8:
            score -= 1
            details.append(f"Bollinger Bands: Not Buy (Price near upper band, position = {bb_position:.2f})")
        else:
            details.append(f"Bollinger Bands: Neutral (position = {bb_position:.2f})")
        
        # Volume Trend: Buy if short-term volume > long-term
        if vol_trend:
            score += 1
            details.append("Volume Trend: Buy (Short-term volume > long-term)")
        else:
            details.append("Volume Trend: Neutral (No strong volume trend)")
        
        # Decision: Buy if score > 1
        recommendation = "Buy" if score > 1 else "Not Buy"
        details.append(f"Final Score: {score} (Threshold: >1 for Buy)")
        
        return {
            "recommendation": recommendation,
            "details": "\n".join(details),
            "score": score,
            "current_price": current_price
        }
    except Exception as e:
        logger.error(f"Error analyzing {ticker_name}: {str(e)}")
        return {"recommendation": "Not Buy", "details": f"Analysis failed: {str(e)}", "score": 0, "current_price": None}

def calculate_profit_loss_dates(ticker_name: str, ticker_symbols: List[str], investment: float, start_date: datetime, end_date: datetime, api_key: str, proxies: Dict = None, use_yfinance: bool = False) -> str:
    """Calculate dates when investment would yield profit or loss."""
    analysis_start = start_date
    analysis_end = end_date
    df, error_msg = fetch_stock_data(ticker_name, ticker_symbols, analysis_start, analysis_end, api_key, proxies, use_yfinance)
    
    if df.empty:
        return f"Data unavailable: {error_msg}"
    
    profit_dates = []
    loss_dates = []
    current_date = datetime.now().date()
    
    date_range = pd.date_range(start=analysis_start, end=analysis_end, freq='MS')
    
    for invest_date in date_range:
        if invest_date.date() >= current_date:
            continue
        invest_dt = datetime.combine(invest_date.date(), datetime.min.time())
        if invest_dt >= analysis_end:
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
    
    profit_summary = summarize_dates(profit_dates)
    loss_summary = summarize_dates(loss_dates)
    
    return f"Profit: {profit_summary}\nLoss: {loss_summary}"

def calculate_investment_returns(ticker_name: str, ticker_symbols: List[str], investment: float, start_date: datetime, end_date: datetime, api_key: str, proxies: Dict = None, use_mock: bool = False, use_yfinance: bool = False) -> Dict:
    if use_mock:
        df = generate_mock_data(start_date, end_date)
        error_msg = "Using mock data"
    else:
        df, error_msg = fetch_stock_data(ticker_name, ticker_symbols, start_date, end_date, api_key, proxies, use_yfinance)
        if df.empty:
            return {"error": f"No valid data for {ticker_name}: {error_msg}"}
    
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
            "start_price": start_price,
            "end_price": end_price,
            "mock": use_mock
        }
    except Exception as e:
        logger.error(f"Error calculating returns for {ticker_name}: {str(e)}")
        return {"error": f"Calculation failed for {ticker_name}: {str(e)}"}

def main():
    st.title("Expert Stock Investment Analysis")
    
    # Debug and mock data toggles
    debug_mode = st.checkbox("Enable Debug Mode (Show Detailed Errors)")
    use_mock_data = st.checkbox("Use Mock Data (Bypass API)")
    use_yfinance = st.checkbox("Force yfinance (Disable Alpha Vantage)")
    
    # API key input
    st.sidebar.header("API Settings")
    alpha_vantage_key = st.sidebar.text_input("Alpha Vantage API Key", type="password")
    if not alpha_vantage_key and not use_mock_data and not use_yfinance:
        st.sidebar.warning("Please enter an Alpha Vantage API key or use mock data.")
    
    # Proxy settings
    st.sidebar.header("Network Settings")
    use_proxy = st.sidebar.checkbox("Use Proxy")
    proxies = None
    if use_proxy:
        proxy_url = st.sidebar.text_input("Proxy URL (e.g., http://proxy:port)")
        if proxy_url:
            proxies = {"http": proxy_url, "https": proxy_url}
    
    # Connectivity test
    if st.button("Test Yahoo Finance Connectivity"):
        result = test_yahoo_finance_connectivity()
        st.info(result)
        if "429" in result:
            st.warning("HTTP 429: Too Many Requests. Use a proxy or Alpha Vantage.")
    
    # Cache clear button
    if st.button("Clear Cache"):
        st.cache_data.clear()
        st.success("Cache cleared successfully!")
    
    # Feature 1: Manual Investment Calculator
    st.header("Investment Profit/Loss Calculator")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        ticker = st.selectbox("Select Stock", list(TICKER_DB.keys()))
    with col2:
        investment = st.number_input("Investment Amount (INR)", min_value=1000.0, value=10000.0)
    with col3:
        invest_date = st.date_input("Investment Date", value=datetime.now() - timedelta(days=30), max_value=datetime.now().date())
    
    if st.button("Calculate Returns"):
        ticker_symbols = TICKER_DB[ticker]
        end_date = datetime.now()
        start_date = datetime.combine(invest_date, datetime.min.time())
        
        with st.spinner(f"Fetching data for {ticker}..."):
            results = calculate_investment_returns(ticker, ticker_symbols, investment, start_date, end_date, alpha_vantage_key, proxies, use_mock_data, use_yfinance)
        
        if "error" not in results:
            st.subheader(f"Results for {ticker}")
            if results.get("mock"):
                st.warning("Using mock data for testing")
            st.write(f"Shares Purchased: {results['shares']:.2f}")
            st.write(f"Initial Investment: ₹{investment:,.2f}")
            st.write(f"Current Value: ₹{results['final_value']:,.2f}")
            st.write(f"Profit/Loss: ₹{results['profit_loss']:,.2f}")
            st.write(f"Return Percentage: {results['profit_loss_pct']:.2f}%")
        else:
            st.error(results["error"])
            if debug_mode:
                st.text_area("Debug Log", logger.handlers[0].stream.getvalue(), height=200)
    
    # Feature 2: Analyze DB
    st.header("Database Analysis")
    if st.button("AnalyzeDB"):
        analysis_results = []
        progress_bar = st.progress(0)
        total_tickers = len(TICKER_DB)
        failed_tickers = []
        
        for idx, (ticker_name, ticker_symbols) in enumerate(TICKER_DB.items()):
            with st.spinner(f"Analyzing {ticker_name}..."):
                result = analyze_ticker(ticker_name, ticker_symbols, alpha_vantage_key, proxies, use_mock_data, use_yfinance)
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
            # Format Current Price
            results_df["Current Price"] = results_df["Current Price"].apply(
                lambda x: f"₹{x:,.2f}" if pd.notna(x) else "N/A"
            )
            st.subheader("Analysis Results")
            st.write("Recommendations based on expert techniques (RSI, MACD, Bollinger Bands, Volume Trend):")
            st.dataframe(results_df[["Stock", "Current Price", "Recommendation", "Score"]], use_container_width=True)
            
            # Display details for each stock
            for result in analysis_results:
                with st.expander(f"Details for {result['Stock']}"):
                    st.text(result["Analysis Details"])
        else:
            st.error("No analysis results available")
            if debug_mode:
                st.text_area("Debug Log", logger.handlers[0].stream.getvalue(), height=200)
    
    # Feature 3: Historical Investment Analysis
    st.header("Historical Investment Analysis")
    col1, col2 = st.columns(2)
    
    with col1:
        hist_investment = st.number_input("Historical Investment Amount (INR)", min_value=1000.0, value=10000.0)
    with col2:
        hist_date = st.date_input("Historical Investment Date", value=datetime.now() - timedelta(days=365*3), max_value=datetime.now().date())
    
    if st.button("Calculate Historical Returns"):
        end_date = datetime.now()
        start_date = datetime.combine(hist_date, datetime.min.time())
        
        hist_results = []
        progress_bar = st.progress(0)
        total_tickers = len(TICKER_DB)
        failed_tickers = []
        
        for idx, (ticker_name, ticker_symbols) in enumerate(TICKER_DB.items()):
            with st.spinner(f"Calculating returns for {ticker_name}..."):
                results = calculate_investment_returns(ticker_name, ticker_symbols, hist_investment, start_date, end_date, alpha_vantage_key, proxies, use_mock_data, use_yfinance)
                if "error" not in results:
                    profit_loss_dates = calculate_profit_loss_dates(
                        ticker_name, ticker_symbols, hist_investment,
                        start_date, end_date, alpha_vantage_key,
                        proxies, use_yfinance
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

if __name__ == "__main__":
    main()
