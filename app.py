import streamlit as st
import pandas as pd
import plotly.express as px
import base64

# --- 1. Page Config & Brand Styling ---
st.set_page_config(page_title="Primarc Pecan | Support Dash", layout="wide", initial_sidebar_state="expanded")

# Define Brand Colors
BRAND_ORANGE = "#F37021"
BRAND_DARK = "#221F1F"
BRAND_WHITE = "#FFFFFF"

# Inject Custom CSS for Theme
st.markdown(f"""
    <style>
    /* Main Background and Text */
    .main .block-container {{ background-color: {BRAND_WHITE}; color: {BRAND_DARK}; }}
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] {{ background-color: {BRAND_DARK}; color: {BRAND_WHITE}; }}
    [data-testid="stSidebar"] .stMarkdown, [data-testid="stSidebar"] label, [data-testid="stSidebar"] p {{ color: {BRAND_WHITE} !important; }}
    
    /* Metric Boxes Styling */
    [data-testid="stMetricValue"] {{ color: {BRAND_ORANGE} !important; }}
    [data-testid="stMetricLabel"] {{ color: {BRAND_DARK} !important; }}
    div[data-testid="stMetric"] {{
        background-color: {BRAND_WHITE};
        border: 2px solid {BRAND_ORANGE};
        border-radius: 10px;
        padding: 15px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
    }}

    /* Buttons and Links */
    .stButton>button {{ background-color: {BRAND_ORANGE}; color: {BRAND_WHITE}; border-radius: 5px; }}
    a {{ color: {BRAND_ORANGE}; }}

    /* Streamlit footer */
    footer {{ visibility: hidden; }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. Logo Handling ---
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

# Try to load the logo if it's in the GitHub repo
logo_filename = 'primarc_pecan_logo.jpg'
try:
    logo_base64 = get_base64_of_bin_file(logo_filename)
    st.sidebar.markdown(
        f"""
        <div style="text-align: center; padding-bottom: 20px;">
            <img src="data:image/jpeg;base64,{logo_base64}" width="200">
        </div>
        """,
        unsafe_allow_html=True
    )
except FileNotFoundError:
    st.sidebar.warning("Note: To see the logo, upload 'primarc_pecan_logo.jpg' to your GitHub repository folder.")

# --- 3. Sidebar Filters (Slicers) ---
st.sidebar.header("🔍 Support Data Slicers")

uploaded_file = st.sidebar.file_uploader("Upload 'CS - SOS' Export", type=['csv', 'xlsx'])

if uploaded_file:
    # Load Data
    df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
    
    # Cleaning & Dates
    if 'Timestamp' in df.columns:
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        df['Month'] = df['Timestamp'].dt.strftime('%B %Y')
    
    # 3a. Monthly Filter
    months = ["All Months"] + sorted(df['Month'].unique().tolist())
    sel_month = st.sidebar.selectbox("Month", months)
    
    # 3b. Executive Filter
    exec_col = 'Email Address' if 'Email Address' in df.columns else None
    execs = ["All Executives"] + sorted(df[exec_col].dropna().unique().tolist()) if exec_col else ["N/A"]
    sel_exec = st.sidebar.selectbox("Executive", execs)
    
    # 3c. Channel Filter (Email/Call)
    chan_col = 'Channel' if 'Channel' in df.columns else None
    channels = ["All Channels"] + sorted(df[chan_col].dropna().unique().tolist()) if chan_col else ["N/A"]
    sel_chan = st.sidebar.selectbox("Channel", channels)

    # Apply Filters
    f_df = df.copy()
    if sel_month != "All Months":
        f_df = f_df[f_df['Month'] == sel_month]
    if exec_col and sel_exec != "All Executives":
        f_df = f_df[f_df[exec_col] == sel_exec]
    if chan_col and sel_chan != "All Channels":
        f_df = f_df[f_df[chan_col] == sel_chan]

    # --- 4. Main Dashboard UI ---
    st.title("🎧 Primarc Pecan Support Performance Portal")
    st.markdown(f"**Reporting Period:** {sel_month} | **Executive:** {sel_exec} | **Channel:** {sel_chan}")
    st.markdown("---")

    # 4a. Top KPI Scorecards
    st.markdown("### 🏆 Core Metrics")
    k1, k2, k3, k4, k5 = st.columns(5)
    
    k1.metric("Tickets Received", len(f_df))
    
    if 'Ticket status' in f_df.columns:
        res = len(f_df[f_df['Ticket status'].str.contains('Resolved', case=False, na=False)])
        cld = len(f_df[f_df['Ticket status'].str.contains('Closed', case=False, na=False)])
        k2.metric("Resolved", res)
        k3.metric("Closed", cld)
    
    # Channel Split Metrics
    if chan_col:
        email_cnt = len(f_df[f_df[chan_col].str.contains('Email', case=False, na=False)])
        call_cnt = len(f_df[f_df[chan_col].str.contains('Call', case=False, na=False)])
        k4.metric("Email Tickets", email_cnt)
        k5.metric("Call Tickets", call_cnt)

    # 4b. Presentation Charts Row 1
    st.markdown("---")
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("📬 Channel Split")
        if chan_col:
            # Using custom color sequence matching logo
            fig_chan = px.pie(f_df, names=chan_col, hole=0.4, 
                               color_discrete_sequence=[BRAND_ORANGE, BRAND_DARK, "#FFC09F"])
            fig_chan.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_chan, use_container_width=True)

    with c2:
        st.subheader("👤 Executive Workload")
        if exec_col:
            perf = f_df[exec_col].value_counts().reset_index()
            perf.columns = ['Executive', 'Tickets']
            # Branded bar chart
            fig_exec = px.bar(perf.head(10), x='Tickets', y='Executive', orientation='h', 
                               color_discrete_sequence=[BRAND_ORANGE])
            fig_exec.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                                    xaxis=dict(gridcolor='#e6e9ef'), yaxis=dict(gridcolor='#e6e9ef'))
            st.plotly_chart(fig_exec, use_container_width=True)

    # 4c. Presentation Charts Row 2 (Trends)
    st.markdown("---")
    st.subheader("❓ Top 10 Query Trends (Most Common Issues)")
    if 'Query type' in f_df.columns:
        q_counts = f_df['Query type'].value_counts().reset_index().head(10)
        q_counts.columns = ['Query', 'Count']
        fig_q = px.bar(q_counts, x='Count', y='Query', orientation='h', color='Count', 
                        color_continuous_scale=[BRAND_DARK, BRAND_ORANGE])
        fig_q.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                                xaxis=dict(gridcolor='#e6e9ef'), yaxis=dict(gridcolor='#e6e9ef'))
        st.plotly_chart(fig_q, use_container_width=True)

    # 4d. Data Explorer
    with st.expander("🔍 Search Full Branded Dataset"):
        st.dataframe(f_df)

else:
    st.title("🎧 Primarc Pecan Support Portal")
    st.info("👋 Presentation Ready! Please upload your 'CS - SOS' file via the sidebar to view the live branded dashboard.")
    # Show large logo on home screen if file not found
    try:
        logo_base64_main = get_base64_of_bin_file(logo_filename)
        st.markdown(
            f"""
            <div style="text-align: center; padding-top: 50px;">
                <img src="data:image/jpeg;base64,{logo_base64_main}" width="400">
            </div>
            """,
            unsafe_allow_html=True
        )
    except:
        pass
