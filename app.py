import streamlit as st
import pandas as pd
import plotly.express as px
import base64

# --- 1. Page Config & Brand Styling ---
st.set_page_config(page_title="Primarc Pecan | Support Analytics", layout="wide")

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

# --- 2. Logo Logic ---
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

logo_filename = 'primarc_pecan_logo.jpg'
try:
    logo_base64 = get_base64_of_bin_file(logo_filename)
    st.sidebar.markdown(f'<div style="text-align: center;"><img src="data:image/jpeg;base64,{logo_base64}" width="180"></div>', unsafe_allow_html=True)
except:
    st.sidebar.info("Upload 'primarc_pecan_logo.jpg' to GitHub to see logo.")

# --- 3. Sidebar Slicers ---
st.sidebar.header("📊 Filter Dashboard")
uploaded_file = st.sidebar.file_uploader("Upload 'CS - SOS' File", type=['csv', 'xlsx'])

if uploaded_file:
    df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
    df.columns = [str(c).strip() for c in df.columns]

    # Date/Month Parsing
    if 'Timestamp' in df.columns:
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        df['Month'] = df['Timestamp'].dt.strftime('%B %Y')
    
    # Slicers
    sel_month = st.sidebar.selectbox("Select Month", ["All Months"] + sorted(df['Month'].unique().tolist()) if 'Month' in df.columns else ["N/A"])
    
    exec_col = 'Email Address' if 'Email Address' in df.columns else None
    sel_exec = st.sidebar.selectbox("Select Executive", ["All Executives"] + sorted(df[exec_col].dropna().unique().tolist()) if exec_col else ["N/A"])
    
    chan_col = 'Channel' if 'Channel' in df.columns else None
    sel_chan = st.sidebar.selectbox("Select Channel", ["All Channels"] + sorted(df[chan_col].dropna().unique().tolist()) if chan_col else ["N/A"])

    # Filtering Logic
    f_df = df.copy()
    if sel_month != "All Months": f_df = f_df[f_df['Month'] == sel_month]
    if exec_col and sel_exec != "All Executives": f_df = f_df[f_df[exec_col] == sel_exec]
    if chan_col and sel_chan != "All Channels": f_df = f_df[f_df[chan_col] == sel_chan]

    # --- 4. Main Dashboard ---
    st.title("🎧 Support Operations & Query Trends")
    
    # KPI Row
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Total Tickets", len(f_df))
    if 'Ticket status' in f_df.columns:
        k2.metric("Resolved", len(f_df[f_df['Ticket status'].str.contains('Resolved', case=False, na=False)]))
        k3.metric("Closed", len(f_df[f_df['Ticket status'].str.contains('Closed', case=False, na=False)]))
    if chan_col:
        k4.metric("Email Vol", len(f_df[f_df[chan_col].str.contains('Email', case=False, na=False)]))
        k5.metric("Call Vol", len(f_df[f_df[chan_col].str.contains('Call', case=False, na=False)]))

    st.markdown("---")

    # --- 5. New Trend Analysis: Query by Channel ---
    st.subheader("📈 Which Queries come from which Channel?")
    if 'Query type' in f_df.columns and chan_col:
        # Grouping query by channel
        q_chan_df = f_df.groupby(['Query type', chan_col]).size().reset_index(name='Ticket Count')
        # Showing top 15 queries for better visibility
        fig_q_chan = px.bar(q_chan_df, x='Query type', y='Ticket Count', color=chan_col, 
                             barmode='group', 
                             color_discrete_sequence=[BRAND_ORANGE, BRAND_DARK],
                             title="Query Volume: Email vs Call")
        fig_q_chan.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_q_chan, use_container_width=True)
    
    st.markdown("---")

    # --- 6. Executive & Productivity ---
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.subheader("👤 Executive Workload")
        if exec_col:
            exec_data = f_df[exec_col].value_counts().reset_index()
            exec_data.columns = ['Executive', 'Count']
            fig_ex = px.pie(exec_data, names='Executive', values='Count', hole=0.4, 
                            color_discrete_sequence=px.colors.qualitative.Bold)
            st.plotly_chart(fig_ex, use_container_width=True)

    with col_right:
        st.subheader("⏱️ Speed Metrics (AHT/FRT)")
        # Calculate if columns exist
        aht = f"{f_df['AHT'].mean():.1f}m" if 'AHT' in f_df.columns else "Waiting for Data"
        frt = f"{f_df['FRT'].mean():.1f}m" if 'FRT' in f_df.columns else "Waiting for Data"
        st.info(f"**Average Call Handling Time:** {aht}")
        st.info(f"**First Response Time:** {frt}")

    # 7. Data Preview
    with st.expander("🔍 View Raw Filtered Data"):
        st.dataframe(f_df)

else:
    st.title("🎧 Primarc Pecan Support Dashboard")
    st.warning("Please upload your CSV/Excel file in the sidebar to start the presentation.")
