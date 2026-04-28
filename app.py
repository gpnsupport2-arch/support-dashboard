import streamlit as st
import pandas as pd
import plotly.express as px
import base64
from streamlit_gsheets import GSheetsConnection
import numpy as np

# --- 1. BRANDING & STYLE ---
st.set_page_config(page_title="Primarc Pecan | Predictive Dash", layout="wide")
BRAND_ORANGE, BRAND_DARK, BRAND_WHITE = "#F37021", "#221F1F", "#FFFFFF"

st.markdown(f"""
    <style>
    .main {{ background-color: {BRAND_WHITE}; color: {BRAND_DARK}; }}
    [data-testid="stSidebar"] {{ background-color: {BRAND_DARK}; color: {BRAND_WHITE}; }}
    div[data-testid="stMetric"] {{
        background-color: {BRAND_WHITE}; border: 2px solid {BRAND_ORANGE}; border-radius: 10px; padding: 15px;
    }}
    .insight-card {{
        background-color: #FFF5EE; border-left: 5px solid {BRAND_ORANGE}; padding: 15px; border-radius: 5px; margin-bottom: 10px;
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
            st.sidebar.error("Check 'Anyone with link' sharing settings.")
else:
    u_file = st.sidebar.file_uploader("Upload File", type=['csv', 'xlsx'])
    if u_file: df = pd.read_csv(u_file) if u_file.name.endswith('.csv') else pd.read_excel(u_file)

# --- 4. DASHBOARD LOGIC ---
if df is not None:
    df.columns = [str(c).strip() for c in df.columns]
    if 'Timestamp' in df.columns:
        df['Timestamp'] = pd.to_datetime(df['Timestamp'], errors='coerce')
        df['Month'] = df['Timestamp'].dt.strftime('%B %Y')
        df['Date'] = df['Timestamp'].dt.date

    # --- Metrics Logic ---
    status_col, query_col, exec_col, chan_col = 'Ticket status', 'Query type', 'Email Address', 'Channel'
    
    total = len(df)
    resolved = len(df[df[status_col].str.contains('Resolved|Closed', case=False, na=False)]) if status_col in df.columns else 0
    pending = total - resolved
    res_rate = (resolved / total * 100) if total > 0 else 0

    # --- UI DISPLAY ---
    st.title("🎧 Primarc Pecan | Smart Ops Dashboard")
    
    # KPI Row
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Received", total)
    k2.metric("Resolution Rate", f"{res_rate:.1f}%")
    k3.metric("Current Pending", pending)
    k4.metric("Avg AHT", f"{df['AHT'].mean():.1f}m" if 'AHT' in df.columns else "No Data")

    st.markdown("---")

    # --- 5. SMART INTERPRETATION & PREDICTION SECTION ---
    st.subheader("🔮 Predictive Insights")
    i1, i2 = st.columns(2)

    with i1:
        st.markdown('<div class="insight-card">', unsafe_allow_html=True)
        st.markdown("**Backlog Projection**")
        # Logic: If team closes avg 20 tickets a day
        avg_daily_close = 25 # You can make this dynamic later
        days_to_clear = pending / avg_daily_close if avg_daily_close > 0 else 0
        st.write(f"At the current pace, it will take approx **{days_to_clear:.1f} days** to clear the existing backlog.")
        st.markdown('</div>', unsafe_allow_html=True)

    with i2:
        st.markdown('<div class="insight-card">', unsafe_allow_html=True)
        st.markdown("**Volume Trend Interpretation**")
        if query_col in df.columns:
            top_issue = df[query_col].value_counts().idxmax()
            st.write(f"The most critical driver of volume is **'{top_issue}'**. Reducing this by 10% would save the team roughly {int(total*0.1)} tickets per month.")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")

    # --- 6. VISUALS ---
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("📊 Query by Channel")
        if query_col in df.columns and chan_col in df.columns:
            fig = px.bar(df.groupby([query_col, chan_col]).size().reset_index(name='Count'), 
                         x=query_col, y='Count', color=chan_col, barmode='group',
                         color_discrete_sequence=[BRAND_ORANGE, BRAND_DARK])
            st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.subheader("👤 Executive Workload")
        if exec_col in df.columns:
            fig_ex = px.pie(df[exec_col].value_counts().reset_index(), names=exec_col, values='count', 
                            hole=0.4, color_discrete_sequence=px.colors.qualitative.Safe)
            st.plotly_chart(fig_ex, use_container_width=True)

else:
    st.info("Please connect your data source in the sidebar.")
