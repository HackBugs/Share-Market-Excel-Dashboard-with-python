import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import logging
from datetime import datetime, timedelta

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

# Get stock data
@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_stock_data(symbol: str, period: str = "1y"):
    try:
        stock = yf.Ticker(symbol)
        hist = stock.history(period=period)
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

# Create candlestick chart with enhanced navigation features
def create_candlestick_chart(data, symbol, company_name, show_instructions):
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        subplot_titles=(f'{company_name} ({symbol})', 'Volume'),
        row_width=[0.2, 0.7]
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
    
    # Update layout with navigation features
    fig.update_layout(
        title=f'{company_name} Stock Chart',
        yaxis_title='Price (₹)',
        xaxis_rangeslider_visible=False,
        height=600,
        showlegend=False,
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
        )
    )
    
    fig.update_yaxes(title_text="Volume", row=2, col=1)
    
    # Add navigation instructions only if show_instructions is True
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
    
    # Initialize session state for instructions toggle
    if 'show_instructions' not in st.session_state:
        st.session_state.show_instructions = False
    
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
        
        # Main content area - Candlestick Chart at the top
        st.subheader(f"📊 {selected_company} - Candlestick Chart")
        
        # Toggle button for instructions
        if st.button('📋 Show/Hide Chart Navigation Instructions'):
            st.session_state.show_instructions = not st.session_state.show_instructions
        
        with st.spinner("Loading chart data..."):
            hist_data, info = get_stock_data(selected_symbol, selected_period)
        
        if hist_data is not None and not hist_data.empty:
            # Create and display candlestick chart
            fig = create_candlestick_chart(hist_data, selected_symbol, selected_company, st.session_state.show_instructions)
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': True})
            
            # Display instructions in a styled container when toggled
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
            
            # Stock Details section at the bottom
            st.markdown("---")
            st.subheader(f"📋 Stock Details: {selected_company}")
            
            with st.spinner("Fetching stock details..."):
                details = get_stock_details(selected_symbol)
            
            if details:
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    # Stock Price Details
                    st.markdown("### 💰 Stock Price Details")
                    st.markdown(f"**Data Fetched At:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    
                    if details['current_price'] != 'N/A':
                        change = float(details['current_price']) - float(details['previous_close']) if details['previous_close'] != 'N/A' else 0
                        change_pct = (change / float(details['previous_close']) * 100) if details['previous_close'] != 'N/A' and float(details['previous_close']) != 0 else 0
                        
                        color = "green" if change >= 0 else "red"
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
                    
                    # Trade Information
                    st.markdown("### 📈 Trade Information")
                    st.write(f"**Volume:** {format_number(details['volume'])}")
                    st.write(f"**Market Cap:** {format_number(details['market_cap'])}")
                    st.write(f"**PE Ratio:** {details['pe_ratio']:.2f}" if details['pe_ratio'] != 'N/A' else "**PE Ratio:** N/A")
                    st.write(f"**Beta:** {details['beta']:.2f}" if details['beta'] != 'N/A' else "**Beta:** N/A")
                    st.write(f"**Dividend Yield:** {details['dividend_yield']:.2%}" if details['dividend_yield'] != 'N/A' else "**Dividend Yield:** N/A")
                    st.write(f"**Face Value:** ₹{details['face_value']:.2f}" if details['face_value'] != 'N/A' else "**Face Value:** N/A")
                
                # Securities Information
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
