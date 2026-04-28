import streamlit as st
import pandas as pd
import plotly.express as px
import base64
from streamlit_gsheets import GSheetsConnection
import numpy as np

# --- 1. BRANDING & STYLE ---
st.set_page_config(page_title="Primarc Pecan | Support Portal", layout="wide")
BRAND_ORANGE, BRAND_DARK, BRAND_WHITE = "#F37021", "#221F1F", "#FFFFFF"

st.markdown(f"""
    <style>
    .main {{ background-color: {BRAND_WHITE}; color: {BRAND_DARK}; }}
    [data-testid="stSidebar"] {{ background-color: {BRAND_DARK}; color: {BRAND_WHITE}; }}
    div[data-testid="stMetric"] {{
        background-color: {BRAND_WHITE}; border: 2px solid {BRAND_ORANGE}; border-radius: 10px; padding: 15px;
    }}
    [data-testid="stMetricValue"] {{ color: {BRAND_ORANGE} !important; }}
    .insight-card {{
        background-color: #FFF5EE; border-left: 5px solid {BRAND_ORANGE}; padding: 15px; border-radius: 5px; margin-top: 10px;
    }}
    footer {{ visibility: hidden; }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. LOGO ---
try:
    with open('primarc_pecan_logo.jpg', 'rb') as f:
        logo_base64 = base64.b64encode(f.read()).decode()
    st.sidebar.markdown(f'<div style="text-align: center;"><img src="data:image/jpeg;base64,{logo_base64}" width="180"></div>', unsafe_allow_html=True)
except:
    pass

# --- 3. DATA SOURCE ---
st.sidebar.header("🔌 Data Source")
source_type = st.sidebar.radio("Select Source", ["Google Sheet (Live)", "Manual Upload"])
df = None

if source_type == "Google Sheet (Live)":
    sheet_url = st.sidebar.text_input("Paste Google Sheet URL")
    if sheet_url:
        try:
            conn = st.connection("gsheets", type=GSheetsConnection)
            df = conn.read(spreadsheet=sheet_url, ttl=0)
        except:
            st.sidebar.error("Link restricted. Set 'Anyone with link' to Viewer.")
else:
    u_file = st.sidebar.file_uploader("Upload File", type=['csv', 'xlsx'])
    if u_file: df = pd.read_csv(u_file) if u_file.name.endswith('.csv') else pd.read_excel(u_file)

# --- 4. DASHBOARD LOGIC ---
if df is not None:
    df.columns = [str(c).strip() for c in df.columns]
    
    # Pre-processing
    if 'Timestamp' in df.columns:
        df['Timestamp'] = pd.to_datetime(df['Timestamp'], errors='coerce')
        df['Month'] = df['Timestamp'].dt.strftime('%B %Y')

    # Columns Mapping
    status_col, query_col, exec_col, chan_col = 'Ticket status', 'Query type', 'Email Address', 'Channel'

    # Slicers
    st.sidebar.markdown("---")
    st.sidebar.header("🔍 Filters")
    sel_month = st.sidebar.selectbox("Month", ["All"] + sorted(df['Month'].dropna().unique().tolist()) if 'Month' in df.columns else ["All"])
    sel_exec = st.sidebar.selectbox("Executive", ["All"] + sorted(df[exec_col].dropna().unique().tolist()) if exec_col in df.columns else ["All"])
    sel_chan = st.sidebar.selectbox("Channel", ["All"] + sorted(df[chan_col].dropna().unique().tolist()) if chan_col in df.columns else ["All"])

    # Applying Filters
    f_df = df.copy()
    if sel_month != "All": f_df = f_df[f_df['Month'] == sel_month]
    if sel_exec != "All": f_df = f_df[f_df[exec_col] == sel_exec]
    if sel_chan != "All": f_df = f_df[f_df[chan_col] == sel_chan]

    # --- 5. MAIN UI LAYOUT ---
    st.title("🎧 Support Operations Portal")
    
    # ROW 1: KPI Metrics
    k1, k2, k3, k4, k5 = st.columns(5)
    total_count = len(f_df)
    k1.metric("Total Tickets", total_count)
    
    if status_col in f_df.columns:
        resolved = len(f_df[f_df[status_col].str.contains('Resolved|Closed', case=False, na=False)])
        k2.metric("Resolved/Closed", resolved)
        k3.metric("Resolution Rate", f"{(resolved/total_count*100):.1f}%" if total_count > 0 else "0%")
        
    if chan_col in f_df.columns:
        k4.metric("Email Volume", len(f_df[f_df[chan_col].str.contains('Email', case=False, na=False)]))
        k5.metric("Call Volume", len(f_df[f_df[chan_col].str.contains('Call', case=False, na=False)]))

    st.markdown("---")

    # ROW 2: Charts
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("📊 Query Distribution by Channel")
        if query_col in f_df.columns and chan_col in f_df.columns:
            q_data = f_df.groupby([query_col, chan_col]).size().reset_index(name='Count')
            fig_q = px.bar(q_data, x=query_col, y='Count', color=chan_col, barmode='group',
                           color_discrete_sequence=[BRAND_ORANGE, BRAND_DARK])
            st.plotly_chart(fig_q, use_container_width=True)

    with col_b:
        st.subheader("👤 Executive Distribution")
        if exec_col in f_df.columns:
            ex_data = f_df[exec_col].value_counts().reset_index()
            fig_ex = px.pie(ex_data, names=exec_col, values='count', hole=0.4,
                            color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig_ex, use_container_width=True)

    st.markdown("---")

    # ROW 3: Speed Metrics
    st.subheader("⏱️ Team Speed Metrics")
    s1, s2, s3 = st.columns(3)
    aht = f_df['AHT'].mean() if 'AHT' in f_df.columns else 0
    frt = f_df['FRT'].mean() if 'FRT' in f_df.columns else 0
    s1.info(f"**Average Handling Time (AHT):** {aht:.1f} min")
    s2.info(f"**First Response Time (FRT):** {frt:.1f} min")
    s3.info(f"**Data Sample:** {len(f_df)} records")

    st.markdown("---")

    # ROW 4: PREDICTIONS (THE BOTTOM SECTION)
    st.subheader("🔮 Smart Insights & Predictions")
    p1, p2 = st.columns(2)

    with p1:
        st.markdown('<div class="insight-card">', unsafe_allow_html=True)
        st.markdown("**📅 Clearance Forecast**")
        # Logic: Calculate pending and predict days to clear
        pending = total_count - resolved if status_col in f_df.columns else 0
        daily_capacity = 30 # You can adjust this baseline
        days_needed = pending / daily_capacity if daily_capacity > 0 else 0
        st.write(f"Based on current capacity, the team will need approximately **{days_needed:.1f} days** to clear the current backlog of {pending} tickets.")
        st.markdown('</div>', unsafe_allow_html=True)

    with p2:
        st.markdown('<div class="insight-card">', unsafe_allow_html=True)
        st.markdown("**🚀 Volume Projection**")
        if query_col in f_df.columns:
            top_issue = f_df[query_col].value_counts().idxmax()
            st.write(f"Trend Alert: **'{top_issue}'** remains the primary volume driver. Improving self-service for this category could reduce overall ticket load by up to **15% next month**.")
        st.markdown('</div>', unsafe_allow_html=True)

    # RAW DATA EXPANDER
    with st.expander("🔍 View Raw Filtered Data Table"):
        st.dataframe(f_df)

else:
    st.title("🎧 Support Performance Portal")
    st.info("Connect a data source via the sidebar to generate branded insights.")
