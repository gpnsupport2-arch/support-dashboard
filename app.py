import streamlit as st
import pandas as pd
import plotly.express as px
import base64
from streamlit_gsheets import GSheetsConnection

# --- 1. BRANDING & BLUE THEME STYLE ---
st.set_page_config(page_title="Primarc Pecan | Support Hub", layout="wide")

# Colors
BRAND_ORANGE = "#F37021"
BRAND_DARK_BLUE = "#101828"  # Deep Navy Blue Background
BRAND_LIGHT_BLUE = "#1D2939" # Slightly lighter blue for contrast
BRAND_WHITE = "#FFFFFF"

st.markdown(f"""
    <style>
    /* Main Background */
    .stApp {{
        background-color: {BRAND_ORANGE}; /* Fallback */
        background: linear-gradient(180deg, {BRAND_DARK_BLUE} 0%, {BRAND_LIGHT_BLUE} 100%);
    }}
    
    /* Global Text Color */
    h1, h2, h3, p, span, label {{
        color: {BRAND_WHITE} !important;
    }}

    /* Sidebar Styling */
    [data-testid="stSidebar"] {{
        background-color: {BRAND_DARK_BLUE};
        border-right: 1px solid {BRAND_ORANGE};
    }}
    [data-testid="stSidebar"] * {{
        color: {BRAND_WHITE} !important;
    }}

    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {{ gap: 24px; }}
    .stTabs [data-baseweb="tab"] {{
        height: 50px; background-color: {BRAND_LIGHT_BLUE}; border-radius: 5px 5px 0 0; padding: 10px;
        color: {BRAND_WHITE} !important;
    }}
    .stTabs [aria-selected="true"] {{
        background-color: {BRAND_ORANGE} !important;
        border-bottom: 2px solid {BRAND_WHITE} !important;
    }}

    /* Metric Cards */
    div[data-testid="stMetric"] {{
        background-color: {BRAND_LIGHT_BLUE};
        border: 1px solid rgba(243, 112, 33, 0.4);
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }}
    [data-testid="stMetricValue"] {{ color: {BRAND_ORANGE} !important; font-size: 32px !important; }}
    [data-testid="stMetricLabel"] {{ color: #98A2B3 !important; }}

    /* Insight Card Styling at Bottom */
    .insight-card {{
        background-color: rgba(255, 255, 255, 0.05);
        border-left: 5px solid {BRAND_ORANGE};
        padding: 20px;
        border-radius: 8px;
        margin-top: 10px;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. LOGO ---
try:
    with open('primarc_pecan_logo.jpg', 'rb') as f:
        logo_base64 = base64.b64encode(f.read()).decode()
    st.sidebar.markdown(f'<div style="text-align: center;"><img src="data:image/jpeg;base64,{logo_base64}" width="180"></div>', unsafe_allow_html=True)
except:
    pass

# --- 3. DATA CONNECTION ---
st.sidebar.header("🔌 Data Connection")
source_type = st.sidebar.radio("Select Source", ["Google Sheet (Live)", "Manual Upload"])
df = None

if source_type == "Google Sheet (Live)":
    sheet_url = st.sidebar.text_input("Paste Google Sheet URL")
    if sheet_url:
        try:
            conn = st.connection("gsheets", type=GSheetsConnection)
            df = conn.read(spreadsheet=sheet_url, ttl=0)
        except:
            st.sidebar.error("Access Denied. Ensure Sheet is 'Anyone with link can view'.")
else:
    u_file = st.sidebar.file_uploader("Upload File", type=['csv', 'xlsx'])
    if u_file: df = pd.read_csv(u_file) if u_file.name.endswith('.csv') else pd.read_excel(u_file)

# --- 4. DATA PROCESSING ---
if df is not None:
    df.columns = [str(c).strip() for c in df.columns if c is not None]
    
    def find_col(target_names, current_cols):
        for name in target_names:
            for col in current_cols:
                if str(name).lower() == str(col).lower(): return col
        return None

    status_col = find_col(['Ticket status', 'Status'], df.columns)
    query_col = find_col(['Query type', 'Query'], df.columns)
    exec_col = find_col(['Email Address', 'Executive', 'Agent'], df.columns)
    chan_col = find_col(['Channel'], df.columns)
    date_col = find_col(['Timestamp', 'Date'], df.columns)

    if date_col:
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        df['Month'] = df[date_col].dt.strftime('%B %Y')

    # Sidebar Month Slicer
    st.sidebar.markdown("---")
    month_options = ["All"]
    if 'Month' in df.columns:
        month_options += sorted([str(x) for x in df['Month'].unique() if pd.notna(x)])
    sel_month = st.sidebar.selectbox("Filter by Month", month_options)
    
    f_df = df.copy()
    if sel_month != "All": f_df = f_df[f_df['Month'] == sel_month]

    # --- 5. TABS ---
    tab_overview, tab_tracker = st.tabs(["📊 Performance Overview", "📋 Query Tracker Log"])

    with tab_overview:
        st.title("🎧 Support Operations Hub")
        
        # KPI ROW
        k1, k2, k3, k4 = st.columns(4)
        total_t = len(f_df)
        k1.metric("Total Tickets", total_t)
        
        res_count = 0
        if status_col:
            res_count = len(f_df[f_df[status_col].astype(str).str.contains('Resolved|Closed', case=False, na=False)])
            k2.metric("Resolution Rate", f"{(res_count/total_t*100):.1f}%" if total_t > 0 else "0%")
        
        if chan_col:
            k3.metric("Email Count", len(f_df[f_df[chan_col].astype(str).str.contains('Email', case=False, na=False)]))
            k4.metric("Call Count", len(f_df[f_df[chan_col].astype(str).str.contains('Call', case=False, na=False)]))

        st.markdown("---")

        # CHARTS ROW
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("📈 Channel Wise Query Trends")
            if query_col and chan_col:
                fig_q = px.bar(f_df.groupby([query_col, chan_col]).size().reset_
