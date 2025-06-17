import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import requests
import json
from datetime import datetime
import time
import qrcode
from io import BytesIO
from PIL import Image
import numpy as np
import base64

# Streamlit page configuration (must be first Streamlit command)
st.set_page_config(
    page_title="HyperGen Global Analysis Nexus",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Check for kaleido availability (non-Streamlit context)
kaleido_available = True
try:
    import plotly.io as pio
    pio.kaleido.scope  # Verify kaleido is accessible
except ImportError:
    kaleido_available = False

# Futuristic CSS with WebGL background, holographic panels, tooltips, and enhanced comparison table
st.markdown("""
    <style>
    /* Global styling */
    body {
        background: linear-gradient(135deg, #0a0a23, #1e1e2e);
    }
    .main {
        background: transparent;
        color: #e0e0ff;
        backdrop-filter: blur(10px);
    }
    .main .block-container {
        padding: 1.5rem;
        max-width: 95%;
        background: rgba(30, 30, 46, 0.7);
        border-radius: 15px;
        box-shadow: 0 0 20px rgba(78, 204, 163, 0.3);
    }
    h1, h2, h3, label {
        font-family: 'Orbitron', sans-serif;
        color: #4ecca3;
        text-shadow: 0 0 5px rgba(78, 204, 163, 0.5);
    }
    .stButton > button {
        background: linear-gradient(45deg, #4ecca3, #39a0ca);
        color: #ffffff;
        border: none;
        border-radius: 10px;
        padding: 0.5rem 1rem;
        transition: all 0.3s;
        box-shadow: 0 0 10px rgba(78, 204, 163, 0.5);
    }
    .stButton > button:hover {
        transform: scale(1.05);
        box-shadow: 0 0 15px rgba(78, 204, 163, 0.8);
    }
    .stPlotlyChart {
        border-radius: 15px;
        box-shadow: 0 0 20px rgba(78, 204, 163, 0.3);
        background: rgba(10, 10, 35, 0.8);
    }
    .plotly .bg {
        fill: rgba(0,0,0,0) !important;
    }
    /* Sidebar */
    .css-1lcbmhc {
        background: rgba(42, 42, 58, 0.8);
        backdrop-filter: blur(10px);
    }
    .css-1lcbmhc h1, .css-1lcbmhc h2, .css-1lcbmhc label {
        color: #4ecca3 !important;
    }
    /* Footer */
    .footer {
        text-align: center;
        color: #a0a0ff;
        font-size: 0.9rem;
        margin-top: 2rem;
        text-shadow: 0 0 3px rgba(160, 160, 255, 0.5);
    }
    /* Holographic data card */
    .data-card {
        background: rgba(42, 42, 58, 0.9);
        padding: 1rem;
        border-radius: 10px;
        margin-top: 1rem;
        box-shadow: 0 0 15px rgba(78, 204, 163, 0.3);
        transform: perspective(1000px) rotateX(5deg);
        transition: transform 0.3s;
    }
    .data-card:hover {
        transform: perspective(1000px) rotateX(0deg);
    }
    /* Alert */
    .alert {
        background: rgba(255, 50, 50, 0.2);
        padding: 0.5rem;
        border-radius: 5px;
        color: #ff6666;
        margin: 0.5rem 0;
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0% { box-shadow: 0 0 5px rgba(255, 50, 50, 0.5); }
        50% { box-shadow: 0 0 15px rgba(255, 50, 50, 0.8); }
        100% { box-shadow: 0 0 5px rgba(255, 50, 50, 0.5); }
    }
    /* Comparison table */
    .comparison-table {
        border: 2px solid #4ecca3;
        border-radius: 10px;
        padding: 1rem;
        background: rgba(42, 42, 58, 0.9);
        box-shadow: 0 0 15px rgba(78, 204, 163, 0.3);
    }
    .comparison-table tr:hover {
        background: rgba(78, 204, 163, 0.2);
        transition: background 0.3s;
    }
    .comparison-table th {
        animation: glow 2s infinite alternate;
    }
    @keyframes glow {
        from { text-shadow: 0 0 3px #4ecca3; }
        to { text-shadow: 0 0 8px #4ecca3; }
    }
    /* Progress bar */
    .progress-bar {
        width: 100%;
        background: rgba(42, 42, 58, 0.9);
        border-radius: 5px;
        overflow: hidden;
    }
    .progress-fill {
        height: 10px;
        background: linear-gradient(90deg, #4ecca3, #39a0ca);
        animation: progress 2s infinite;
    }
    @keyframes progress {
        0% { width: 0%; }
        100% { width: 100%; }
    }
    /* Tooltip */
    .tooltip {
        position: relative;
        display: inline-block;
    }
    .tooltip .tooltiptext {
        visibility: hidden;
        width: 200px;
        background: rgba(42, 42, 58, 0.9);
        color: #e0e0ff;
        text-align: center;
        border-radius: 6px;
        padding: 5px;
        position: absolute;
        z-index: 1;
        bottom: 125%;
        left: 50%;
        margin-left: -100px;
        opacity: 0;
        transition: opacity 0.3s;
        box-shadow: 0 0 10px rgba(78, 204, 163, 0.5);
    }
    .tooltip:hover .tooltiptext {
        visibility: visible;
        opacity: 1;
    }
    /* Responsive design */
    @media (max-width: 768px) {
        .stButton > button {
            width: 100%;
            margin-bottom: 0.5rem;
        }
        .comparison-table {
            font-size: 0.9rem;
        }
    }
    /* WebGL background */
    #webgl-bg {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        z-index: -1;
        opacity: 0.3;
    }
    </style>
    <canvas id="webgl-bg"></canvas>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r134/three.min.js"></script>
    <script>
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
    const renderer = new THREE.WebGLRenderer({canvas: document.getElementById('webgl-bg'), alpha: true});
    renderer.setSize(window.innerWidth, window.innerHeight);
    const geometry = new THREE.BufferGeometry();
    const vertices = new Float32Array(1000 * 3);
    for (let i = 0; i < vertices.length; i++) {
        vertices[i] = (Math.random() - 0.5) * 100;
    }
    geometry.setAttribute('position', new THREE.BufferAttribute(vertices, 3));
    const material = new THREE.PointsMaterial({color: 0x4ecca3, size: 0.5});
    const points = new THREE.Points(geometry, material);
    scene.add(points);
    camera.position.z = 50;
    function animate() {
        requestAnimationFrame(animate);
        points.rotation.y += 0.002;
        renderer.render(scene, camera);
    }
    animate();
    </script>
    <audio id="click-sound" src="https://cdn.pixabay.com/audio/2023/03/25/audio_0b7d2852e3.mp3"></audio>
    <script>
    document.querySelectorAll('.stButton > button').forEach(button => {
        button.addEventListener('click', () => {
            document.getElementById('click-sound').play();
        });
    });
    </script>
""", unsafe_allow_html=True)

# Fallback data
FALLBACK_INFLATION = [
    {"country": "United States", "iso3": "USA", "inflation": 8.0},
    {"country": "Germany", "iso3": "DEU", "inflation": 6.9},
    {"country": "India", "iso3": "IND", "inflation": 6.7},
    {"country": "Brazil", "iso3": "BRA", "inflation": 9.3},
    {"country": "China", "iso3": "CHN", "inflation": 2.0},
    {"country": "United Kingdom", "iso3": "GBR", "inflation": 9.1},
]
CONFLICT_COUNTRIES = [
    {"country": "Ukraine", "iso3": "UKR", "conflict": "Russia-Ukraine War", "intensity": 9, "sentiment": "Negative", "conflict_deaths": 100000, "population": 44000000, "death_ratio": 2272.73},
    {"country": "Israel", "iso3": "ISR", "conflict": "Israel-Palestine Conflict", "intensity": 7, "sentiment": "Mixed", "conflict_deaths": 5000, "population": 9200000, "death_ratio": 543.48},
    {"country": "Yemen", "iso3": "YEM", "conflict": "Yemeni Civil War", "intensity": 6, "sentiment": "Negative", "conflict_deaths": 20000, "population": 31000000, "death_ratio": 645.16},
    {"country": "Syria", "iso3": "SYR", "conflict": "Syrian Civil War", "intensity": 5, "sentiment": "Negative", "conflict_deaths": 15000, "population": 18000000, "death_ratio": 833.33},
    {"country": "Sudan", "iso3": "SDN", "conflict": "Sudanese Civil War", "intensity": 8, "sentiment": "Negative", "conflict_deaths": 25000, "population": 44000000, "death_ratio": 568.18},
]
FALLBACK_MORTALITY = [
    {"country": "United States", "iso3": "USA", "mortality_rate": 8.9},
    {"country": "Germany", "iso3": "DEU", "mortality_rate": 11.4},
    {"country": "India", "iso3": "IND", "mortality_rate": 7.3},
    {"country": "Brazil", "iso3": "BRA", "mortality_rate": 6.8},
    {"country": "China", "iso3": "CHN", "mortality_rate": 7.1},
    {"country": "United Kingdom", "iso3": "GBR", "mortality_rate": 9.4},
]

# Cache API calls
@st.cache_data(ttl=3600)
def fetch_worldbank_data(indicator, year, indicator_col):
    url = f"https://api.worldbank.org/v2/country/all/indicator/{indicator}?format=json&per_page=300&date={year}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()[1]
        result = []
        for entry in data:
            if entry['value'] is not None:
                scale = 1e9 if indicator in ["NY.GDP.MKTP.CD", "MS.MIL.XPND.CD"] else 1
                result.append({
                    'country': entry['country']['value'],
                    'iso3': entry['countryiso3code'],
                    indicator_col: entry['value'] / scale,
                    'year': year
                })
        return pd.DataFrame(result)
    except (requests.RequestException, KeyError, IndexError) as e:
        st.error(f"Failed to fetch {indicator} data for {year}: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def fetch_inflation_data(year):
    url = f"https://api.worldbank.org/v2/country/all/indicator/FP.CPI.TOTL.ZG?format=json&per_page=300&date={year}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()[1]
        inflation_data = []
        for entry in data:
            if entry['value'] is not None:
                inflation_data.append({
                    'country': entry['country']['value'],
                    'iso3': entry['countryiso3code'],
                    'inflation': entry['value'],
                    'year': year
                })
        df = pd.DataFrame(inflation_data)
        if df.empty:
            st.warning(f"World Bank API returned no inflation data for {year}. Using fallback data.")
            return pd.DataFrame([{**d, 'year': year} for d in FALLBACK_INFLATION])
        return df
    except (requests.RequestException, json.JSONDecodeError, KeyError, IndexError) as e:
        st.warning(f"Failed to fetch inflation data: {str(e)}. Using fallback data.")
        return pd.DataFrame([{**d, 'year': year} for d in FALLBACK_INFLATION])

@st.cache_data(ttl=3600)
def fetch_mortality_data(year):
    url = f"https://api.worldbank.org/v2/country/all/indicator/SP.DYN.CDRT.IN?format=json&per_page=300&date={year}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()[1]
        mortality_data = []
        for entry in data:
            if entry['value'] is not None:
                mortality_data.append({
                    'country': entry['country']['value'],
                    'iso3': entry['countryiso3code'],
                    'mortality_rate': entry['value'],
                    'year': year
                })
        df = pd.DataFrame(mortality_data)
        if df.empty:
            st.warning(f"World Bank API returned no mortality data for {year}. Using fallback data.")
            return pd.DataFrame([{**d, 'year': year} for d in FALLBACK_MORTALITY])
        return df
    except (requests.RequestException, json.JSONDecodeError, KeyError, IndexError) as e:
        st.warning(f"Failed to fetch mortality data: {str(e)}. Using fallback data.")
        return pd.DataFrame([{**d, 'year': year} for d in FALLBACK_MORTALITY])

@st.cache_data(ttl=3600)
def fetch_military_data():
    military_data = [
        {"country": "United States", "iso3": "USA", "military_personnel": 1390000, "tanks": 5600, "aircraft": 13500, "naval_vessels": 480, "missiles": 6000},
        {"country": "China", "iso3": "CHN", "military_personnel": 2035000, "tanks": 5000, "aircraft": 3300, "naval_vessels": 730, "missiles": 2500},
        {"country": "India", "iso3": "IND", "military_personnel": 1455550, "tanks": 4770, "aircraft": 2200, "naval_vessels": 295, "missiles": 400},
        {"country": "Russia", "iso3": "RUS", "military_personnel": 1150000, "tanks": 12800, "aircraft": 4200, "naval_vessels": 605, "missiles": 5800},
        {"country": "Ukraine", "iso3": "UKR", "military_personnel": 500000, "tanks": 1800, "aircraft": 300, "naval_vessels": 25, "missiles": 300},
    ]
    return pd.DataFrame(military_data)

# Initialize session state
if 'user_profile' not in st.session_state:
    st.session_state.user_profile = {"role": "General", "favorites": [], "config": {}, "theme": "Neon", "cloud_sync": False}
if 'comments' not in st.session_state:
    st.session_state.comments = []
if 'compare_countries' not in st.session_state:
    st.session_state.compare_countries = []

# Sidebar with futuristic controls
st.sidebar.title("Quantum Control Nexus")
user_role = st.sidebar.selectbox("User Profile", ["General", "Economist", "Defense Analyst", "Policy Maker"], index=0)
theme = st.sidebar.selectbox("Visual Theme", ["Neon", "Cyberpunk", "Quantum"], index=0)
cloud_sync = st.sidebar.checkbox("Cloud Sync Profile", value=False)
st.session_state.user_profile["role"] = user_role
st.session_state.user_profile["theme"] = theme
st.session_state.user_profile["cloud_sync"] = cloud_sync
view_mode = st.sidebar.radio("Visualization Mode", ["2D Map", "3D Globe"], index=0)
year = st.sidebar.selectbox("Temporal Frame", [2022, 2021, 2020], index=0)
indicator = st.sidebar.radio("Primary Vector", ["GDP", "GDP per Capita", "Inflation", "Unemployment", "Military Expenditure", "Trade Balance", "Debt-to-GDP", "Mortality Rate"], index=0)
secondary_indicator = st.sidebar.selectbox("Secondary Vector (Overlay)", ["None"] + ["GDP", "GDP per Capita", "Inflation", "Unemployment", "Military Expenditure", "Trade Balance", "Debt-to-GDP", "Mortality Rate"], index=0)
show_secondary_overlay = st.sidebar.checkbox("Show Secondary Overlay", value=True, disabled=secondary_indicator == "None")
color_scale = st.sidebar.selectbox("Visual Spectrum", ["Plasma", "Inferno", "Viridis", "Magma", "Cividis", "Neon"], index=0)
countries = st.sidebar.multiselect(
    "Target Nodes",
    fetch_worldbank_data("NY.GDP.MKTP.CD", year, "gdp")["country"].tolist() if not fetch_worldbank_data("NY.GDP.MKTP.CD", year, "gdp").empty else [d["country"] for d in FALLBACK_INFLATION],
    default=st.session_state.user_profile.get("config", {}).get("countries", [])
)
highlight_conflicts = st.sidebar.checkbox("Conflict Overlay", value=True)
show_death_ratio = st.sidebar.checkbox("Show Conflict Death Ratio", value=True)
show_military = st.sidebar.checkbox("Military Data Stream", value=True)
live_data = st.sidebar.checkbox("Live Data Feed", value=False)
predictive_mode = st.sidebar.checkbox("Predictive Analytics", value=False)
mortality_viz_type = st.sidebar.selectbox("Mortality Dashboard View", ["Choropleth", "Bar Chart"], index=0)
save_config = st.sidebar.button("Save Neural Configuration")
if save_config:
    st.session_state.user_profile["config"] = {"countries": countries, "indicator": indicator, "secondary_indicator": secondary_indicator, "year": year, "theme": theme}
    st.sidebar.success("Configuration synced to neural core." if cloud_sync else "Configuration saved locally.")
if st.sidebar.button("Reset Filters"):
    st.session_state.user_profile["config"] = {}
    st.session_state.compare_countries = []
    st.sidebar.success("Filters reset.")

# Natural Language Query
nlq = st.sidebar.text_input("Neural Query Interface", placeholder="Ask: 'Top 5 GDP countries?'")
if nlq:
    if "top 5" in nlq.lower() and "gdp" in nlq.lower():
        df_gdp = fetch_worldbank_data("NY.GDP.MKTP.CD", year, "gdp")
        top_5 = df_gdp.nlargest(5, "gdp")[["country", "gdp"]].to_dict("records")
        st.sidebar.markdown("### AI Response\n" + "\n".join([f"{i+1}. {r['country']}: ${r['gdp']:,.2f}B" for i, r in enumerate(top_5)]))
    elif "top 5" in nlq.lower() and "mortality" in nlq.lower():
        df_mortality = fetch_mortality_data(year)
        top_5 = df_mortality.nlargest(5, "mortality_rate")[["country", "mortality_rate"]].to_dict("records")
        st.sidebar.markdown("### AI Response\n" + "\n".join([f"{i+1}. {r['country']}: {r['mortality_rate']:,.1f} per 1,000" for i, r in enumerate(top_5)]))
    else:
        st.sidebar.warning("Query not recognized. Try: 'Top 5 GDP countries?' or 'Top 5 mortality rate countries?'")

# Data fetching and merging
indicator_map = {
    "GDP": ("gdp", "NY.GDP.MKTP.CD", "Billion US$"),
    "GDP per Capita": ("gdp_per_capita", "NY.GDP.PCAP.CD", "US$"),
    "Inflation": ("inflation", None, "%"),
    "Unemployment": ("unemployment", "SL.UEM.TOTL.ZS", "%"),
    "Military Expenditure": ("military_expenditure", "MS.MIL.XPND.CD", "Billion US$"),
    "Trade Balance": ("trade_balance", "NE.TRD.GNFS.ZS", "% of GDP"),
    "Debt-to-GDP": ("debt_to_gdp", "GC.DOD.TOTL.GD.ZS", "%"),
    "Mortality Rate": ("mortality_rate", "SP.DYN.CDRT.IN", "per 1,000")
}
indicator_col, indicator_code, indicator_unit = indicator_map[indicator]
df = fetch_worldbank_data(indicator_code, year, indicator_col) if indicator != "Inflation" else fetch_inflation_data(year)
if indicator == "Mortality Rate":
    df = fetch_mortality_data(year)

# Secondary indicator data
secondary_df = pd.DataFrame()
secondary_col = None
secondary_unit = None
if secondary_indicator != "None":
    secondary_col, secondary_code, secondary_unit = indicator_map[secondary_indicator]
    secondary_df = fetch_worldbank_data(secondary_code, year, secondary_col) if secondary_indicator != "Inflation" else fetch_inflation_data(year)
    if secondary_indicator == "Mortality Rate":
        secondary_df = fetch_mortality_data(year)

# Merge primary and secondary data
if not df.empty and not secondary_df.empty and secondary_indicator != "None":
    df = df.merge(secondary_df[["iso3", secondary_col, "country"]], on=["iso3", "country"], how="left")
    if secondary_col not in df.columns:
        st.warning(f"Failed to merge {secondary_indicator} data. Displaying primary indicator only.")
elif secondary_indicator != "None" and secondary_df.empty:
    st.warning(f"No data available for {secondary_indicator} in {year}. Displaying primary indicator only.")

# Data quality check and summary
if not df.empty:
    completeness_summary = f"Primary Indicator ({indicator}): {len(df)} countries with data."
    if secondary_indicator != "None" and secondary_col in df.columns:
        missing_ratio = df[secondary_col].isna().mean()
        completeness_summary += f"\nSecondary Indicator ({secondary_indicator}): {len(df) - df[secondary_col].isna().sum()} countries with data ({missing_ratio:.0%} missing)."
        if missing_ratio > 0.5:
            st.warning(f"Over {missing_ratio:.0%} of {secondary_indicator} data is missing. Consider selecting a different secondary indicator or disabling the overlay.")
    st.sidebar.markdown(f"### Data Completeness\n{completeness_summary}")

# Cache merged DataFrame
@st.cache_data(ttl=3600)
def cache_merged_df(df, secondary_df, indicator_col, secondary_col):
    return df.copy()

if not df.empty:
    df = cache_merged_df(df, secondary_df, indicator_col, secondary_col)

# Data range filter
if not df.empty and indicator_col in df.columns:
    min_val = float(df[indicator_col].min())
    max_val = float(df[indicator_col].max())
    data_range = st.sidebar.slider(
        f"{indicator} Vector Range ({indicator_unit})",
        min_val,
        max_val,
        (min_val, max_val)
    )
    df = df[(df[indicator_col] >= data_range[0]) & (df[indicator_col] <= data_range[1])]
if countries:
    df = df[df["country"].isin(countries)]

# Merge additional data
military_df = fetch_military_data()
conflict_df = pd.DataFrame(CONFLICT_COUNTRIES)
if not df.empty:
    df = df.merge(military_df, on=["country", "iso3"], how="left")
    df = df.merge(conflict_df[["country", "iso3", "conflict", "intensity", "sentiment", "death_ratio"]], on=["country", "iso3"], how="left")

# Predictive analytics
if predictive_mode and indicator == "GDP" and not df.empty:
    df_pred = df[["country", "iso3", "gdp"]].copy()
    df_pred["gdp_2023"] = df_pred["gdp"] * (1 + np.random.uniform(0.01, 0.05, len(df_pred)))  # Simulated growth
    df_pred = df_pred.rename(columns={"gdp": "gdp_value"})  # Rename to avoid melt conflict
    # Merge military and conflict data to support hover_data
    df_pred = df_pred.merge(military_df, on=["country", "iso3"], how="left")
    df_pred = df_pred.merge(conflict_df[["country", "iso3", "conflict", "intensity", "sentiment", "death_ratio"]], on=["country", "iso3"], how="left")
    df_pred = df_pred.melt(
        id_vars=["country", "iso3", "military_personnel", "tanks", "aircraft", "naval_vessels", "missiles", "conflict", "intensity", "sentiment", "death_ratio"],
        value_vars=["gdp_value", "gdp_2023"],
        var_name="year",
        value_name="gdp_melted"
    )
    df_pred["year"] = df_pred["year"].map({"gdp_value": year, "gdp_2023": 2023})
    if df_pred.empty:
        st.warning("Predictive data generation failed. Displaying current data only.")
        predictive_mode = False

# Create futuristic visualization
def create_visualization():
    if df.empty:
        return px.choropleth(title=f"Global {indicator} {year} - Data Unavailable")
    
    # Use df_pred if in predictive mode and indicator is GDP, else use df
    current_df = df_pred if predictive_mode and indicator == "GDP" else df
    current_indicator_col = "gdp_melted" if predictive_mode and indicator == "GDP" else indicator_col

    # Filter hover_data to include only columns present in current_df
    hover_data = {current_indicator_col: f":,.{'2f' if indicator != 'Inflation' else '1f'}{indicator_unit[0]}"}
    if secondary_indicator != "None" and secondary_col in current_df.columns:
        hover_data[secondary_col] = f":,.{'2f' if secondary_indicator != 'Inflation' else '1f'}{secondary_unit[0]}"
    if show_military:
        military_cols = ["military_personnel", "tanks", "aircraft", "naval_vessels", "missiles"]
        for col in military_cols:
            if col in current_df.columns:
                hover_data[col] = ":,.0f"
    if highlight_conflicts:
        conflict_cols = ["conflict", "intensity", "sentiment"]
        if show_death_ratio:
            conflict_cols.append("death_ratio")
        for col in conflict_cols:
            if col in current_df.columns:
                hover_data[col] = True if col in ["conflict", "sentiment"] else ":,.1f"

    if view_mode == "3D Globe":
        fig = go.Figure()
        fig.add_trace(go.Scattergeo(
            locations=current_df["iso3"],
            marker=dict(
                size=current_df[current_indicator_col] / current_df[current_indicator_col].max() * 20,
                color=current_df[current_indicator_col],
                colorscale="Plasma" if color_scale == "Neon" else color_scale.lower(),
                colorbar=dict(title=f"{indicator} ({indicator_unit})"),
                showscale=True
            ),
            hovertemplate="<b>%{location}</b><br>" + "<br>".join([f"{k}: %{{customdata[{i}]}}" for i, k in enumerate(hover_data.keys())]),
            customdata=current_df[list(hover_data.keys())]
        ))
        if secondary_indicator != "None" and secondary_col in current_df.columns and show_secondary_overlay:
            # Precompute normalized sizes and handle NaN
            secondary_sizes = current_df[secondary_col] / current_df[secondary_col].max() * 15
            secondary_sizes = secondary_sizes.fillna(1).clip(lower=1)
            secondary_colors = current_df[secondary_col].fillna(0)  # Default color for NaN
            if not secondary_sizes.isna().all():
                fig.add_trace(go.Scattergeo(
                    locations=current_df["iso3"],
                    marker=dict(
                        size=secondary_sizes,
                        color=secondary_colors,
                        colorscale="Viridis",
                        showscale=True,
                        colorbar=dict(title=f"{secondary_indicator} ({secondary_unit})", x=0.85)
                    ),
                    hoverinfo="skip"
                ))
        if highlight_conflicts and "conflict" in current_df.columns:
            conflict_df_subset = current_df[current_df["conflict"].notna()]
            fig.add_trace(go.Scattergeo(
                locations=conflict_df_subset["iso3"],
                mode="markers",
                marker=dict(size=12, color="red", symbol="square", line=dict(width=2, color="yellow")),
                hoverinfo="skip"
            ))
        fig.update_geos(
            projection_type="orthographic",
            showcountries=True,
            countrycolor="white",
            showocean=True,
            oceancolor="#0a0a23",
            showland=True,
            landcolor="#2a2a3a",
            bgcolor="rgba(0,0,0,0)"
        )
    else:
        fig = px.choropleth(
            current_df,
            locations="iso3",
            color=current_indicator_col,
            hover_name="country",
            hover_data=hover_data,
            color_continuous_scale="Plasma" if color_scale == "Neon" else color_scale.lower(),
            title=f"Global {indicator} ({indicator_unit}, {year})" + (" - Predictive" if predictive_mode else "") + (" - Fallback Data" if indicator == "Inflation" and current_df.equals(pd.DataFrame([{**d, 'year': year} for d in FALLBACK_INFLATION])) else ""),
            projection="natural earth",
            animation_frame="year" if (live_data or predictive_mode) else None,
            height=800
        )
        if secondary_indicator != "None" and secondary_col in current_df.columns and show_secondary_overlay:
            # Precompute normalized sizes and handle NaN
            secondary_sizes = current_df[secondary_col] / current_df[secondary_col].max() * 15
            secondary_sizes = secondary_sizes.fillna(1).clip(lower=1)
            secondary_colors = current_df[secondary_col].fillna(0)  # Default color for NaN
            if not secondary_sizes.isna().all():
                fig.add_trace(go.Scattergeo(
                    locations=current_df["iso3"],
                    marker=dict(
                        size=secondary_sizes,
                        color=secondary_colors,
                        colorscale="Viridis",
                        showscale=True,
                        colorbar=dict(title=f"{secondary_indicator} ({secondary_unit})", x=0.85)
                    ),
                    hoverinfo="skip"
                ))
        if highlight_conflicts and "conflict" in current_df.columns:
            conflict_df_subset = current_df[current_df["conflict"].notna()]
            fig.add_trace(go.Scattergeo(
                locations=conflict_df_subset["iso3"],
                mode="markers",
                marker=dict(size=12, color="red", symbol="square", line=dict(width=2, color="yellow")),
                hoverinfo="skip"
            ))
        fig.update_layout(
            margin={"r":10,"t":50,"l":10,"b":10},
            coloraxis_colorbar=dict(
                len=0.75,
                title=f"{indicator} ({indicator_unit})",
                tickformat=",.0f" if indicator != "Inflation" else ".1f",
                bgcolor="rgba(30, 30, 46, 0.7)"
            ),
            geo=dict(
                showframe=False,
                showcoastlines=True,
                coastlinecolor="white",
                showland=True,
                landcolor="#2a2a3a",
                showocean=True,
                oceancolor="#0a0a23",
                bgcolor="rgba(0,0,0,0)"
            ),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#e0e0ff", family="Orbitron"),
            transition=dict(duration=500, easing="cubic-in-out")
        )
    return fig

# Mortality rate visualization
def create_mortality_visualization(mortality_df, viz_type):
    if mortality_df.empty:
        return px.choropleth(title=f"Mortality Rate {year} - Data Unavailable")
    
    if viz_type == "Choropleth":
        fig = px.choropleth(
            mortality_df,
            locations="iso3",
            color="mortality_rate",
            hover_name="country",
            hover_data={"mortality_rate": ":,.1f"},
            color_continuous_scale="Plasma" if color_scale == "Neon" else color_scale.lower(),
            title=f"Global Mortality Rate (per 1,000, {year})",
            projection="natural earth",
            height=600
        )
    else:
        fig = px.bar(
            mortality_df,
            x="country",
            y="mortality_rate",
            color="mortality_rate",
            color_continuous_scale="Plasma" if color_scale == "Neon" else color_scale.lower(),
            title=f"Mortality Rate by Country (per 1,000, {year})",
            height=600
        )
    fig.update_layout(
        margin={"r":10,"t":50,"l":10,"b":10},
        coloraxis_colorbar=dict(
            len=0.75,
            title="Mortality Rate (per 1,000)",
            tickformat=",.1f",
            bgcolor="rgba(30, 30, 46, 0.7)"
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e0e0ff", family="Orbitron"),
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=False)
    )
    return fig

# Header with holographic logo
st.markdown(f"""
    <div style='display: flex; align-items: center; animation: glow 2s infinite alternate;'>
        <img src='https://images.weserv.nl/?url=https://raw.githubusercontent.com/HackBugs/Website-Collection/main/Website_Data/earth1.png&w=60&h=60&fit=cover&q=80' style='margin-right: 1rem; width: 60px; filter: drop-shadow(0 0 10px #4ecca3);' alt='Logo'>
        <h1>HyperGen Global Analysis Nexus</h1>
    </div>
    <style>
    @keyframes glow {{
        from {{ text-shadow: 0 0 5px #4ecca3; }}
        to {{ text-shadow: 0 0 15px #4ecca3; }}
    }}
    </style>
""", unsafe_allow_html=True)

# Dynamic alerts
if highlight_conflicts and not df.empty:
    conflict_df_subset = df[df["conflict"].notna()]
    if not conflict_df_subset.empty:
        for _, row in conflict_df_subset.iterrows():
            death_info = f", Death Ratio: {row['death_ratio']:.1f} per million" if show_death_ratio and pd.notna(row['death_ratio']) else ""
            st.markdown(
                f"<div class='alert'>ALERT: Conflict in {row['country']} ({row['conflict']}, Intensity: {row['intensity']:.1f}, Sentiment: {row['sentiment']}{death_info})</div>",
                unsafe_allow_html=True
            )

# Main visualization
st.subheader(f"Quantum {indicator} Visualization ({year})")
if live_data:
    with st.spinner("Streaming live data..."):
        for y in [2020, 2021, 2022]:
            temp_df = fetch_worldbank_data(indicator_code, y, indicator_col) if indicator != "Inflation" else fetch_inflation_data(y)
            if indicator == "Mortality Rate":
                temp_df = fetch_mortality_data(y)
            if not temp_df.empty:
                temp_df["year"] = y
                # Merge secondary, military, and conflict data for live data
                if secondary_indicator != "None":
                    secondary_temp_df = fetch_worldbank_data(indicator_map[secondary_indicator][1], y, indicator_map[secondary_indicator][0]) if secondary_indicator != "Inflation" else fetch_inflation_data(y)
                    if secondary_indicator == "Mortality Rate":
                        secondary_temp_df = fetch_mortality_data(y)
                    if not secondary_temp_df.empty:
                        temp_df = temp_df.merge(secondary_temp_df[["iso3", indicator_map[secondary_indicator][0], "country"]], on=["iso3", "country"], how="left")
                temp_df = temp_df.merge(military_df, on=["country", "iso3"], how="left")
                temp_df = temp_df.merge(conflict_df[["country", "iso3", "conflict", "intensity", "sentiment", "death_ratio"]], on=["country", "iso3"], how="left")
                # Apply country and data range filters
                if countries:
                    temp_df = temp_df[temp_df["country"].isin(countries)]
                if indicator_col in temp_df.columns:
                    temp_df = temp_df[(temp_df[indicator_col] >= data_range[0]) & (temp_df[indicator_col] <= data_range[1])]
                df = temp_df
                st.plotly_chart(create_visualization(), use_container_width=True)
                time.sleep(1)
            else:
                st.warning(f"No data available for {y}. Skipping year.")
else:
    st.plotly_chart(create_visualization(), use_container_width=True)

# Mortality Rate Dashboard
# st.markdown("### Mortality Rate Dashboard")
# mortality_df = fetch_mortality_data(year)
# if not mortality_df.empty:
#     st.plotly_chart(create_mortality_visualization(mortality_df, mortality_viz_type), use_container_width=True)
#     csv = mortality_df[["country", "iso3", "mortality_rate"]].to_csv(index=False).encode('utf-8')
#     st.download_button("Download Mortality Data as CSV", csv, f"mortality_{year}.csv", "text/csv")
# else:
#     st.warning("No mortality data available for the selected year.")

# AR Preview
st.markdown("### Augmented Reality Interface")
ar_url = "https://example.com/ar-view"  # Placeholder; replace with A-Frame hosted URL
qr = qrcode.make(ar_url)
qr_buffer = BytesIO()
qr.save(qr_buffer, format="PNG")
qr_img = Image.open(qr_buffer)
st.image(qr_img, caption="Scan for AR Visualization", width=150)

# Sentiment Analysis
st.markdown("### Conflict Sentiment Analysis")
if highlight_conflicts and not df.empty:
    sentiment_data = df[df["sentiment"].notna()][["country", "conflict", "sentiment", "death_ratio"]]
    if not sentiment_data.empty:
        st.markdown("**Public Sentiment and Death Ratio (Simulated from X posts):**\n" + "\n".join([f"- {row['country']}: {row['sentiment']} ({row['conflict']})" + (f", Death Ratio: {row['death_ratio']:.1f} per million" if show_death_ratio and pd.notna(row['death_ratio']) else "") for _, row in sentiment_data.iterrows()]))
    else:
        st.warning("No sentiment data available.")

# AI Insights and Compare Countries
if not df.empty:
    st.markdown("### AI-Driven Insights")
    selected_country = st.selectbox("Select Node for Analysis", ["None"] + df["country"].tolist(), index=0)
    if selected_country != "None":
        country_data = df[df["country"] == selected_country].iloc[0]
        ai_summary = f"**{selected_country} Analysis**: {indicator} at {country_data[indicator_col]:,.{'2f' if indicator != 'Inflation' else '1f'}} {indicator_unit} in {year}. "
        if indicator == "GDP" and country_data[indicator_col] > 1000:
            ai_summary += "Strong economic output, likely driven by diversified industries."
        elif indicator == "Inflation" and country_data[indicator_col] > 10:
            ai_summary += "High inflation suggests economic instability."
        elif indicator == "Mortality Rate" and country_data[indicator_col] > 10:
            ai_summary += "High mortality rate suggests health or social challenges."
        st.markdown(ai_summary)
        with st.expander(f"{selected_country} Neural Data Core", expanded=True):
            death_info = f"<p><b>Conflict Death Ratio:</b> {country_data.get('death_ratio', 'N/A'):,.1f} per million</p>" if show_death_ratio and pd.notna(country_data.get('death_ratio')) else ""
            st.markdown(f"""
                <div class='data-card'>
                    <h3>{selected_country}</h3>
                    <p><b>{indicator} ({year}):</b> {country_data[indicator_col]:,.{'2f' if indicator != 'Inflation' else '1f'}} {indicator_unit}</p>
                    {f"<p><b>{secondary_indicator} ({year}):</b> {country_data.get(secondary_col, 'N/A'):,.{'2f' if secondary_indicator != 'Inflation' else '1f'}} {secondary_unit}</p>" if secondary_indicator != "None" and secondary_col in df.columns else ""}
                    <p><b>Military Personnel:</b> {country_data.get('military_personnel', 'N/A'):,.0f}</p>
                    <p><b>Tanks:</b> {country_data.get('tanks', 'N/A'):,.0f}</p>
                    <p><b>Aircraft:</b> {country_data.get('aircraft', 'N/A'):,.0f}</p>
                    <p><b>Naval Vessels:</b> {country_data.get('naval_vessels', 'N/A'):,.0f}</p>
                    <p><b>Missiles:</b> {country_data.get('missiles', 'N/A'):,.0f}</p>
                    <p><b>Conflict:</b> {country_data.get('conflict', 'None')} (Intensity: {country_data.get('intensity', 'N/A')}, Sentiment: {country_data.get('sentiment', 'N/A')})</p>
                    {death_info}
                </div>
            """, unsafe_allow_html=True)

    st.markdown("### Comparative Analysis")
    st.subheader("Country Comparison")
    search_query = st.text_input("Search Country", placeholder="Type country name...")
    country_list = df["country"].tolist() if not df.empty else [d["country"] for d in FALLBACK_INFLATION]
    filtered_countries = [c for c in country_list if search_query.lower() in c.lower()] if search_query else country_list
    selected_country = st.selectbox("Select Country to Add", filtered_countries, index=0 if filtered_countries else None)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        with st.container():
            st.markdown("<div class='tooltip'>Add to Comparison<span class='tooltiptext'>Add the selected country to the comparison list</span></div>", unsafe_allow_html=True)
            if st.button("Add to Comparison") and selected_country:
                if selected_country not in st.session_state.compare_countries:
                    st.session_state.compare_countries.append(selected_country)
                    st.success(f"{selected_country} added to comparison.")
    with col2:
        with st.container():
            st.markdown("<div class='tooltip'>Clear Selection<span class='tooltiptext'>Reset the comparison list</span></div>", unsafe_allow_html=True)
            if st.button("Clear Selection"):
                st.session_state.compare_countries = []
                st.success("Comparison list cleared.")
    with col3:
        with st.container():
            st.markdown("<div class='tooltip'>Remove Country<span class='tooltiptext'>Remove a specific country from the comparison list</span></div>", unsafe_allow_html=True)
            remove_country = st.selectbox("Select Country to Remove", st.session_state.compare_countries, index=0 if st.session_state.compare_countries else None, key="remove_country")
            if st.button("Remove") and remove_country:
                st.session_state.compare_countries.remove(remove_country)
                st.success(f"{remove_country} removed from comparison.")
    
    st.markdown("**Countries Selected for Comparison:**")
    st.write(", ".join(st.session_state.compare_countries) if st.session_state.compare_countries else "None")
    
    compare_indicators = st.multiselect(
        "Select Indicators for Comparison",
        list(indicator_map.keys()),
        default=[indicator]
    )
    
    # Toggle for showing comparison charts
    show_charts = st.checkbox("Show Comparison Charts", value=True)
    
    if st.button("Compare Selected Countries") and st.session_state.compare_countries and compare_indicators:
        with st.spinner("Generating comparison..."):
            st.markdown("<div class='progress-bar'><div class='progress-fill'></div></div>", unsafe_allow_html=True)
            # Fetch data for selected indicators and years
            all_data = pd.DataFrame()
            for ind in compare_indicators:
                col, code, unit = indicator_map[ind]
                for y in [2020, 2021, 2022]:
                    temp_df = fetch_worldbank_data(code, y, col) if ind != "Inflation" else fetch_inflation_data(y)
                    if ind == "Mortality Rate":
                        temp_df = fetch_mortality_data(y)
                    if not temp_df.empty:
                        temp_df["indicator"] = ind
                        temp_df["unit"] = unit
                        all_data = pd.concat([all_data, temp_df], ignore_index=True)
            
            # Filter for selected countries
            compare_df = all_data[all_data["country"].isin(st.session_state.compare_countries)]
            if not compare_df.empty:
                # Pivot table for comparison
                pivot_table = pd.pivot_table(
                    compare_df,
                    index="country",
                    columns=["indicator", "year"],
                    values=compare_df["indicator"].map(lambda x: indicator_map[x][0]),
                    aggfunc="first"
                ).reset_index()
                pivot_table.columns = ["_".join([str(c) for c in col]).strip("_") for col in pivot_table.columns]
                
                # Sort table
                sort_column = st.selectbox(
                    "Sort Table By",
                    ["country"] + [col for col in pivot_table.columns if col != "country"],
                    index=0
                )
                sort_ascending = st.checkbox("Sort Ascending", value=True)
                pivot_table = pivot_table.sort_values(by=sort_column, ascending=sort_ascending)
                
                # Display comparison table
                st.markdown("<div class='comparison-table'>", unsafe_allow_html=True)
                st.subheader("Comparison Table")
                
                # Custom formatter for numeric columns
                def format_value(val, fmt):
                    if pd.isna(val) or isinstance(val, str):
                        return val
                    try:
                        return fmt.format(val)
                    except (ValueError, TypeError):
                        return val
                
                format_dict = {
                    col: lambda x: format_value(x, "{:,.2f}" if any(k in col for k in ["GDP", "Military Expenditure"]) else "{:,.1f}")
                    for col in pivot_table.columns if col != "country"
                }
                
                st.dataframe(
                    pivot_table.style.format(format_dict),
                    use_container_width=True
                )
                
                # Export comparison table
                csv = pivot_table.to_csv(index=False).encode('utf-8')
                st.download_button("Download Comparison as CSV", csv, f"comparison_{year}.csv", "text/csv")
                st.markdown("</div>", unsafe_allow_html=True)
                
                if show_charts:
                    # Line chart for primary indicator
                    line_df = compare_df[compare_df["indicator"] == indicator][["country", "year", indicator_col]]
                    if not line_df.empty:
                        fig_line = px.line(
                            line_df,
                            x="year",
                            y=indicator_col,
                            color="country",
                            title=f"{indicator} Comparison Over Time ({indicator_unit})"
                        )
                        fig_line.update_layout(
                            paper_bgcolor="rgba(0,0,0,0)",
                            plot_bgcolor="rgba(0,0,0,0)",
                            font=dict(color="Helvetica", family="Orbitron"),
                            xaxis=dict(showgrid=False),
                            yaxis=dict(showgrid=False)
                        )
                        st.plotly_chart(fig_line, use_container_width=True)
                    
                    # Bar chart for selected indicators in the current year
                    bar_df = compare_df[(compare_df["year"] == year) & (compare_df["indicator"].isin(compare_indicators))]
                    if not bar_df.empty:
                        fig_bar = px.bar(
                            bar_df,
                            x="country",
                            y=bar_df["indicator"].map(lambda x: indicator_map[x][0]),
                            color="indicator",
                            title=f"Indicator Comparison for {year}",
                            barmode="group"
                        )
                        fig_bar.update_layout(
                            paper_bgcolor="rgba(0,0,0,0)",
                            plot_bgcolor="rgba(0,0,0,0)",
                            font=dict(color="Helvetica", family="Orbitron"),
                            xaxis=dict(showgrid=False),
                            yaxis=dict(showgrid=False)
                        )
                        st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.warning("No data available for selected countries or indicators.")

# Data table
if not df.empty:
    st.markdown(f"### {indicator} Data Matrix")
    display_cols = ["country", indicator_col]
    if secondary_indicator != "None" and secondary_col in df.columns:
        display_cols.append(secondary_col)
    if show_military:
        display_cols.extend(["military_personnel", "tanks", "aircraft", "naval_vessels", "missiles"])
    if highlight_conflicts:
        conflict_cols = ["conflict", "intensity", "sentiment"]
        if show_death_ratio:
            conflict_cols.append("death_ratio")
        display_cols.extend(conflict_cols)
    
    rename_dict = {
        indicator_col: f"{indicator} ({indicator_unit})",
        "military_personnel": "Personnel",
        "tanks": "Tanks",
        "aircraft": "Aircraft",
        "naval_vessels": "Naval Vessels",
        "missiles": "Missiles",
        "intensity": "Conflict Intensity",
        "sentiment": "Public Sentiment",
        "death_ratio": "Conflict Death Ratio (per million)"
    }
    if secondary_indicator != "None" and secondary_col in df.columns:
        rename_dict[secondary_col] = f"{secondary_indicator} ({secondary_unit})"
    
    format_dict = {
        f"{indicator} ({indicator_unit})": f"{{:,.{'2f' if indicator != 'Inflation' else '1f'}}}" ,
        "Personnel": "{:.0f}",
        "Tanks": "{:.0f}",
        "Aircraft": "{:.0f}",
        "Naval Vessels": "{:.0f}",
        "Missiles": "{:.0f}",
        "Conflict Intensity": "{:.0f}",
        "Conflict Death Ratio (per million)": "{:.1f}"
    }
    if secondary_indicator != "None" and secondary_col in df.columns:
        format_dict[f"{secondary_indicator} ({secondary_unit})"] = f"{{:,.{'2f' if secondary_indicator != 'Inflation' else '1f'}}}"

    st.dataframe(
        df[display_cols].rename(columns=rename_dict).style.format(format_dict),
        use_container_width=True
    )

# Export options
if not df.empty:
    st.markdown("### Data Export")
    if not kaleido_available:
        st.warning("Kaleido package not found. PNG export disabled. Install it using: `pip install --upgrade kaleido`")
    csv = df[display_cols].to_csv(index=False).encode('utf-8')
    st.download_button("Download Data as CSV", csv, f"{indicator}_{year}.csv", "text/csv")
    if kaleido_available:
        st.download_button("Download Visualization as PNG", data=create_visualization().to_image(format="png"), file_name=f"{indicator}_{year}.png", mime="image/png")

# Collaboration features
st.markdown("### Neural Collaboration Hub")
comment = st.text_input("Add Annotation")
if st.button("Submit Annotation"):
    st.session_state.comments.append({"user": user_role, "comment": comment, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
    st.success("Annotation added.")
for c in st.session_state.comments:
    st.markdown(f"**{c['user']}** ({c['timestamp']}): {c['comment']}")

# Footer
st.markdown(f"""
    <div class='footer'>
        <p>Data Sources: World Bank, WorldData.info, Neural Conflict Network | Last Updated: {datetime.now().strftime('%B %d, %Y %I:%M %p IST')} | Powered by Quantum Streamlit</p>
    </div>
""", unsafe_allow_html=True)

# WebSocket for live reloading
st.markdown("""
    <script>
    if ('WebSocket' in window) {
        (function () {
            function refreshCSS() {
                var sheets = [].slice.call(document.getElementsByTagName("link"));
                var head = document.getElementsByTagName("head")[0];
                for (var i = 0; i < sheets.length; ++i) {
                    var elem = sheets[i];
                    var parent = elem.parentElement || head;
                    parent.removeChild(elem);
                    var rel = elem.rel;
                    if (elem.href && typeof rel != "string" || rel.length == 0 || rel.toLowerCase() == "stylesheet") {
                        var url = elem.href.replace(/(&|\\?)_cacheOverride=\\d+', '')
                        elem.href = url + (url.indexOf('?') >= 0 ? '&' : '?') + '_cacheOverride=' + (new Date().valueOf());
                    }
                    parent.appendChild(elem);
                }
            }
            var protocol = window.location.protocol === 'http:' ? 'ws://' : 'wss://';
            var address = protocol + window.location.host + window.location.pathname + '/ws';
            var socket = new WebSocket(address);
            socket.onmessage = function (msg) {
                if (msg.data == 'reload') window.location.reload();
                else if (msg.data == 'refreshcss') refreshCSS();
            };
            if (sessionStorage && !sessionStorage.getItem('IsThisFirstTime_Log_From_LiveServer')) {
                console.log('Live reload enabled.');
                sessionStorage.setItem('IsThisFirstTime_Log_From_LiveServer', true);
            }
        })();
    } else {
        console.error('Upgrade your browser. This Browser is NOT supported WebSocket for Live-Reloading.');
    }
    </script>
""", unsafe_allow_html=True)
