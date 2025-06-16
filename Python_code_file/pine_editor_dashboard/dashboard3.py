import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import logging
from datetime import datetime, timedelta
import uuid

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Stock Trading Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

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

# Create candlestick chart with custom indicators
def create_candlestick_chart(data, symbol, company_name, show_instructions, pine_script=None):
    # Create subplots with secondary y-axis for RSI
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        subplot_titles=(f'{company_name} ({symbol})', 'Volume'),
        row_width=[0.2, 0.7],
        specs=[[{"secondary_y": True}], [{"secondary_y": False}]]
    )
    
    # Candlestick chart
    fig.add_trace(
        go.Candlestick(
            x=data.index,
            open=data['Open'],
            high=data['High'],
            low=data['Low'],
            close=data['Close'],
            name="Price"
        ),
        row=1, col=1
    )
    
    # Volume chart
    fig.add_trace(
        go.Bar(
            x=data.index,
            y=data['Volume'],
            name="Volume",
            marker_color='rgba(158,202,225,0.8)'
        ),
        row=2, col=1
    )
    
    # Add custom indicators if Pine Script is provided
    if pine_script:
        try:
            # This is a placeholder for actual Pine Script parsing and indicator calculation
            # In a real implementation, you would parse the Pine Script and add the indicators
            
            # Example: Add a simple moving average (placeholder)
            if 'ta.vwma' in pine_script or 'vwma' in pine_script:
                window = 20  # Default window
                if 'vwmaLength = input(' in pine_script:
                    # Extract the window parameter from the Pine Script
                    start = pine_script.find('vwmaLength = input(') + len('vwmaLength = input(')
                    end = pine_script.find(',', start)
                    window = int(pine_script[start:end])
                
                # Calculate VWMA (Volume Weighted Moving Average)
                data['VWMA'] = (data['Close'] * data['Volume']).rolling(window=window).sum() / data['Volume'].rolling(window=window).sum()
                fig.add_trace(
                    go.Scatter(
                        x=data.index,
                        y=data['VWMA'],
                        name=f"VWMA ({window})",
                        line=dict(color='purple', width=2)
                    ),
                    row=1, col=1,
                    secondary_y=False
                )
            
            # Example: Add RSI (placeholder)
            if 'ta.rsi' in pine_script or 'rsi' in pine_script:
                window = 14  # Default window
                if 'rsiLength = input(' in pine_script:
                    # Extract the window parameter from the Pine Script
                    start = pine_script.find('rsiLength = input(') + len('rsiLength = input(')
                    end = pine_script.find(',', start)
                    window = int(pine_script[start:end])
                
                # Calculate RSI
                delta = data['Close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
                rs = gain / loss
                data['RSI'] = 100 - (100 / (1 + rs))
                
                # Add RSI as a subplot
                fig.add_trace(
                    go.Scatter(
                        x=data.index,
                        y=data['RSI'],
                        name=f"RSI ({window})",
                        line=dict(color='orange', width=1)
                    ),
                    row=1, col=1,
                    secondary_y=True
                )
                
                # Add overbought/oversold lines
                fig.add_hline(y=70, line_dash="dot", line_color="red", row=1, col=1, secondary_y=True)
                fig.add_hline(y=30, line_dash="dot", line_color="green", row=1, col=1, secondary_y=True)
            
        except Exception as e:
            st.error(f"Error processing Pine Script: {str(e)}")
    
    # Update layout
    fig.update_layout(
        title=f'{company_name} Stock Chart',
        yaxis_title='Price (₹)',
        xaxis_rangeslider_visible=False,
        height=600,
        showlegend=True,
        dragmode='pan',
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
            type="date"
        ),
        yaxis=dict(
            autorange=True,
            fixedrange=False
        ),
        yaxis2=dict(
            title="RSI",
            autorange=True,
            fixedrange=False
        )
    )
    
    fig.update_yaxes(title_text="Volume", row=2, col=1)
    
    if show_instructions:
        fig.add_annotation(
            text="<b>Chart Navigation:</b><br>"
                 "- Drag left/right to scroll<br>"
                 "- Drag up/down to scale Y-axis<br>"
                 "- Mouse wheel to zoom<br>"
                 "- Double-click to reset",
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
        if num >= 10000000:  # 1 crore
            return f"₹{num/10000000:.2f} Cr"
        elif num >= 100000:  # 1 lakh
            return f"₹{num/100000:.2f} L"
        elif num >= 1000:
            return f"₹{num/1000:.2f} K"
        else:
            return f"₹{num:.2f}"
    except:
        return str(num)

# Main dashboard
def main():
    st.title("📈 Stock Trading Dashboard")
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
    
    # Search box
    search_term = st.sidebar.text_input("Search Company Name:", placeholder="Type company name...")
    
    # Filter companies based on search
    if search_term:
        filtered_companies = [name for name in TICKER_DB.keys() 
                            if search_term.lower() in name.lower()]
    else:
        filtered_companies = list(TICKER_DB.keys())
    
    # Company selection
    if filtered_companies:
        selected_company = st.sidebar.selectbox(
            "Select Company:",
            options=filtered_companies,
            index=0
        )
        
        selected_symbol = TICKER_DB[selected_company]
        
        # Time period selection
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
            index=3  # Default to 1 Year
        )
        
        selected_period = period_options[selected_period_name]
        
        # Time interval filter in sidebar
        st.sidebar.markdown("---")
        st.sidebar.header("⏱ Filter Time Interval")
        
        with st.sidebar.expander("Select Time Interval", expanded=True):
            # Ticks section
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
            
            # Seconds section
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
            
            # Minutes section
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
            
            # Days section
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
            
            # Custom interval
            st.markdown("**Custom Interval:**")
            custom_interval = st.text_input("Enter custom interval (e.g., '2h' for 2 hours)", 
                                          value=st.session_state.selected_interval)
            if st.button("Apply Custom Interval"):
                if custom_interval:
                    st.session_state.selected_interval = custom_interval
        
        # Display selected interval
        st.sidebar.markdown(f"**Current Interval:** `{st.session_state.selected_interval}`")
        
        # Pine Script Editor
        st.sidebar.markdown("---")
        st.sidebar.header("📝 Pine Script Editor")
        
        if st.sidebar.button("📝 Open Pine Script Editor"):
            st.session_state.show_pine_editor = not st.session_state.show_pine_editor
        
        if st.session_state.show_pine_editor:
            st.sidebar.markdown("""
            **Pine Script Help:**
            - Write your custom indicators in Pine Script
            - Click "Apply Script" to add them to the chart
            - Example indicators: VWMA, RSI, MACD, etc.
            """)
            
            # Pine Script editor
            pine_script = st.sidebar.text_area(
                "Write your Pine Script here:",
                value=st.session_state.pine_script,
                height=300,
                help="Enter your Pine Script code for custom indicators"
            )
            
            col1, col2 = st.sidebar.columns(2)
            with col1:
                if st.button("Apply Script"):
                    st.session_state.pine_script = pine_script
                    st.success("Pine Script applied successfully!")
            with col2:
                if st.button("Clear Script"):
                    st.session_state.pine_script = ""
                    st.success("Pine Script cleared!")
        
        # Main content area
        st.subheader(f"📊 {selected_company} - Candlestick Chart ({st.session_state.selected_interval} interval)")
        
        # Toggle button for instructions
        if st.button('📋 Show/Hide Chart Navigation Instructions'):
            st.session_state.show_instructions = not st.session_state.show_instructions
        
        with st.spinner("Loading chart data..."):
            hist_data, info = get_stock_data(selected_symbol, selected_period, st.session_state.selected_interval)
        
        if hist_data is not None and not hist_data.empty:
            # Create and display candlestick chart
            fig = create_candlestick_chart(
                hist_data, 
                selected_symbol, 
                selected_company, 
                st.session_state.show_instructions,
                st.session_state.pine_script
            )
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': True})
            
            if st.session_state.show_instructions:
                st.markdown("""
                <div style="background-color:#2D2D2D;padding:10px;border-radius:5px;color:white;">
                <h4 style="color:white;">📋 Chart Navigation Instructions</h4>
                <ul>
                    <li><b>Left/Right Drag:</b> Scroll across time</li>
                    <li><b>Up/Down Drag:</b> Adjust Y-axis scaling</li>
                    <li><b>Mouse Wheel:</b> Zoom in/out</li>
                    <li><b>Double-Click:</b> Reset zoom</li>
                    <li><b>Pinch/Touchpad Gestures:</b> Zoom on touch devices</li>
                </ul>
                </div>
                """, unsafe_allow_html=True)
            
            # Stock Details section
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
    
    else:
        st.sidebar.write("No companies found matching your search.")
    
    # Footer
    st.markdown("---")
    st.markdown("*Data provided by Yahoo Finance. This dashboard is for educational purposes only.*")

if __name__ == "__main__":
    main()
