import streamlit as st
import pandas as pd
import plotly.express as px
import base64
from streamlit_gsheets import GSheetsConnection

# --- 1. BRANDING & STYLE ---
st.set_page_config(page_title="Primarc Pecan | Live Dash", layout="wide")

BRAND_ORANGE = "#F37021"
BRAND_DARK = "#221F1F"
BRAND_WHITE = "#FFFFFF"

st.markdown(f"""
    <style>
    .main {{ background-color: {BRAND_WHITE}; color: {BRAND_DARK}; }}
    [data-testid="stSidebar"] {{ background-color: {BRAND_DARK}; color: {BRAND_WHITE}; }}
    [data-testid="stSidebar"] .stMarkdown, [data-testid="stSidebar"] label, [data-testid="stSidebar"] p {{ color: {BRAND_WHITE} !important; }}
    div[data-testid="stMetric"] {{
        background-color: {BRAND_WHITE};
        border: 2px solid {BRAND_ORANGE};
        border-radius: 10px;
        padding: 15px;
    }}
    [data-testid="stMetricValue"] {{ color: {BRAND_ORANGE} !important; }}
    footer {{ visibility: hidden; }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. LOGO LOGIC ---
logo_filename = 'primarc_pecan_logo.jpg'
try:
    with open(logo_filename, 'rb') as f:
        data = f.read()
        logo_base64 = base64.b64encode(data).decode()
    st.sidebar.markdown(f'<div style="text-align: center;"><img src="data:image/jpeg;base64,{logo_base64}" width="180"></div>', unsafe_allow_html=True)
except:
    st.sidebar.info("Upload 'primarc_pecan_logo.jpg' to GitHub.")

# --- 3. LIVE CONNECTION SETUP ---
st.sidebar.header("🔌 Data Source")
source_type = st.sidebar.radio("Select Source", ["Google Sheet (Live)", "Manual Upload (Excel/CSV)"])

df = None

if source_type == "Google Sheet (Live)":
    sheet_url = st.sidebar.text_input("Paste Google Sheet URL", help="Ensure the sheet is 'Anyone with link can view'")
    if sheet_url:
        try:
            # Connect to Google Sheets
            conn = st.connection("gsheets", type=GSheetsConnection)
            df = conn.read(spreadsheet=sheet_url)
            st.sidebar.success("Connected to Live Data!")
        except Exception as e:
            st.sidebar.error(f"Connection Error: {e}")
    else:
        st.info("Please paste your Google Sheet URL in the sidebar to begin.")

else:
    uploaded_file = st.sidebar.file_uploader("Upload 'CS - SOS' File", type=['csv', 'xlsx'])
    if uploaded_file:
        df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)

# --- 4. DASHBOARD LOGIC (If data is loaded) ---
if df is not None:
    # Standardize columns
    df.columns = [str(c).strip() for c in df.columns]

    # Process Dates
    if 'Timestamp' in df.columns:
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        df['Month'] = df['Timestamp'].dt.strftime('%B %Y')
    
    # Define Column Names
    exec_col, chan_col, query_col, status_col = 'Email Address', 'Channel', 'Query type', 'Ticket status'

    # Slicers (Monthly / Executive / Channel)
    st.sidebar.markdown("---")
    st.sidebar.header("🔍 Filters")
    
    sel_month = st.sidebar.selectbox("Month", ["All Months"] + sorted(df['Month'].unique().tolist()) if 'Month' in df.columns else ["N/A"])
    sel_exec = st.sidebar.selectbox("Executive", ["All Executives"] + sorted(df[exec_col].dropna().unique().tolist()) if exec_col in df.columns else ["N/A"])
    sel_chan = st.sidebar.selectbox("Channel", ["All Channels"] + sorted(df[chan_col].dropna().unique().tolist()) if chan_col in df.columns else ["N/A"])

    # Filtering Logic
    f_df = df.copy()
    if sel_month != "All Months": f_df = f_df[f_df['Month'] == sel_month]
    if sel_exec != "All Executives": f_df = f_df[f_df[exec_col] == sel_exec]
    if sel_chan != "All Channels": f_df = f_df[f_df[chan_col] == sel_chan]

    # --- MAIN UI ---
    st.title("🎧 Primarc Pecan Live Support Dash")
    
    # KPI Row
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Total Tickets", len(f_df))
    if status_col in f_df.columns:
        k2.metric("Resolved", len(f_df[f_df[status_col].str.contains('Resolved', case=False, na=False)]))
        k3.metric("Closed", len(f_df[f_df[status_col].str.contains('Closed', case=False, na=False)]))
    if chan_col in f_df.columns:
        k4.metric("Email Vol", len(f_df[f_df[chan_col].str.contains('Email', case=False, na=False)]))
        k5.metric("Call Vol", len(f_df[f_df[chan_col].str.contains('Call', case=False, na=False)]))

    st.markdown("---")

    # Trend 1: Query by Channel
    st.subheader("📊 Query Distribution by Channel (Email vs Call)")
    if query_col in f_df.columns and chan_col in f_df.columns:
        q_chan_df = f_df.groupby([query_col, chan_col]).size().reset_index(name='Count')
        fig_q_chan = px.bar(q_chan_df, x=query_col, y='Count', color=chan_col, 
                             barmode='group', color_discrete_sequence=[BRAND_ORANGE, BRAND_DARK])
        st.plotly_chart(fig_q_chan, use_container_width=True)

    # Performance Section
    c_left, c_right = st.columns(2)
    with c_left:
        st.subheader("👤 Executive Workload")
        if exec_col in f_df.columns:
            exec_data = f_df[exec_col].value_counts().reset_index()
            fig_ex = px.pie(exec_data, names=exec_col, values='count', hole=0.4, 
                            color_discrete_sequence=px.colors.qualitative.Prism)
            st.plotly_chart(fig_ex, use_container_width=True)

    with c_right:
        st.subheader("⏱️ Speed Metrics (AHT/FRT)")
        aht = f"{f_df['AHT'].mean():.1f}m" if 'AHT' in f_df.columns else "Pending"
        frt = f"{f_df['FRT'].mean():.1f}m" if 'FRT' in f_df.columns else "Pending"
        st.info(f"**Avg Call Handling Time (AHT):** {aht}")
        st.info(f"**First Response Time (FRT):** {frt}")

    with st.expander("🔍 Filtered Data Table"):
        st.dataframe(f_df)
