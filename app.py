import streamlit as st
import pandas as pd
import plotly.express as px
import base64

# --- 1. BRANDING & STYLE CONFIG ---
st.set_page_config(page_title="Primarc Pecan | Support Dash", layout="wide")

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
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

logo_filename = 'primarc_pecan_logo.jpg'
try:
    logo_base64 = get_base64_of_bin_file(logo_filename)
    st.sidebar.markdown(f'<div style="text-align: center;"><img src="data:image/jpeg;base64,{logo_base64}" width="180"></div>', unsafe_allow_html=True)
except:
    st.sidebar.info("Upload 'primarc_pecan_logo.jpg' to GitHub.")

# --- 3. SIDEBAR FILTERS (SLICERS) ---
st.sidebar.header("🔍 Presentation Filters")
uploaded_file = st.sidebar.file_uploader("Upload 'CS - SOS' File", type=['csv', 'xlsx'])

if uploaded_file:
    # Load Data
    df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
    df.columns = [str(c).strip() for c in df.columns]

    # Process Date & Month
    if 'Timestamp' in df.columns:
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        df['Month'] = df['Timestamp'].dt.strftime('%B %Y')
    
    # Define Column Names based on your file
    exec_col = 'Email Address'
    chan_col = 'Channel'
    query_col = 'Query type'
    status_col = 'Ticket status'

    # Slicers
    months = ["All Months"] + sorted(df['Month'].unique().tolist()) if 'Month' in df.columns else ["N/A"]
    sel_month = st.sidebar.selectbox("Filter by Month", months)
    
    execs = ["All Executives"] + sorted(df[exec_col].dropna().unique().tolist()) if exec_col in df.columns else ["N/A"]
    sel_exec = st.sidebar.selectbox("Filter by Executive", execs)
    
    chans = ["All Channels"] + sorted(df[chan_col].dropna().unique().tolist()) if chan_col in df.columns else ["N/A"]
    sel_chan = st.sidebar.selectbox("Filter by Channel", chans)

    # Apply Logic
    f_df = df.copy()
    if sel_month != "All Months": f_df = f_df[f_df['Month'] == sel_month]
    if sel_exec != "All Executives": f_df = f_df[f_df[exec_col] == sel_exec]
    if sel_chan != "All Channels": f_df = f_df[f_df[chan_col] == sel_chan]

    # --- 4. TOP KPI ROW ---
    st.title("🎧 Primarc Pecan Support Performance")
    st.markdown(f"**Current View:** {sel_month} | {sel_exec} | {sel_chan}")
    
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Total Tickets", len(f_df))
    
    if status_col in f_df.columns:
        res = len(f_df[f_df[status_col].str.contains('Resolved', case=False, na=False)])
        cld = len(f_df[f_df[status_col].str.contains('Closed', case=False, na=False)])
        k2.metric("Resolved", res)
        k3.metric("Closed", cld)
    
    if chan_col in f_df.columns:
        email_v = len(f_df[f_df[chan_col].str.contains('Email', case=False, na=False)])
        call_v = len(f_df[f_df[chan_col].str.contains('Call', case=False, na=False)])
        k4.metric("Email Vol", email_v)
        k5.metric("Call Vol", call_v)

    st.markdown("---")

    # --- 5. QUERY TRENDS BY CHANNEL (NEW REQUIREMENT) ---
    st.subheader("📊 Query Distribution by Channel (Email vs Call)")
    if query_col in f_df.columns and chan_col in f_df.columns:
        q_chan_df = f_df.groupby([query_col, chan_col]).size().reset_index(name='Count')
        fig_q_chan = px.bar(q_chan_df, x=query_col, y='Count', color=chan_col, 
                             barmode='group', color_discrete_sequence=[BRAND_ORANGE, BRAND_DARK])
        st.plotly_chart(fig_q_chan, use_container_width=True)

    st.markdown("---")

    # --- 6. EXECUTIVE PERFORMANCE & SPEED ---
    c_left, c_right = st.columns(2)

    with c_left:
        st.subheader("👤 Executive Workload")
        if exec_col in f_df.columns:
            exec_data = f_df[exec_col].value_counts().reset_index()
            exec_data.columns = ['Executive', 'Count']
            fig_ex = px.pie(exec_data, names='Executive', values='Count', hole=0.4, 
                            color_discrete_sequence=px.colors.qualitative.Prism)
            st.plotly_chart(fig_ex, use_container_width=True)

    with c_right:
        st.subheader("⏱️ Speed Metrics (AHT/FRT)")
        aht = f"{f_df['AHT'].mean():.1f}m" if 'AHT' in f_df.columns else "Pending Data"
        frt = f"{f_df['FRT'].mean():.1f}m" if 'FRT' in f_df.columns else "Pending Data"
        st.info(f"**Avg Call Handling Time (AHT):** {aht}")
        st.info(f"**First Response Time (FRT):** {frt}")
        st.caption("Add columns 'AHT' and 'FRT' to your file to update these automatically.")

    # --- 7. DATA PREVIEW ---
    with st.expander("🔍 Filtered Data Table"):
        st.dataframe(f_df)

else:
    st.title("🎧 Primarc Pecan Support Portal")
    st.warning("Please upload your file in the sidebar to start.")
