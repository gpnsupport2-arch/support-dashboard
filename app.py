import streamlit as st
import pandas as pd
import plotly.express as px
import base64
from streamlit_gsheets import GSheetsConnection

# --- 1. BRANDING & STYLE ---
st.set_page_config(page_title="Primarc Pecan | Support Portal", layout="wide")
BRAND_ORANGE, BRAND_DARK, BRAND_WHITE = "#F37021", "#221F1F", "#FFFFFF"

st.markdown(f"""
    <style>
    .main {{ background-color: {BRAND_WHITE}; color: {BRAND_DARK}; }}
    [data-testid="stSidebar"] {{ background-color: {BRAND_DARK}; }}
    [data-testid="stSidebar"] * {{ color: {BRAND_WHITE} !important; font-size: 15px !important; }}
    div[data-testid="stMetric"] {{ background-color: {BRAND_WHITE}; border: 2px solid {BRAND_ORANGE}; border-radius: 10px; padding: 15px; }}
    [data-testid="stMetricValue"] {{ color: {BRAND_ORANGE} !important; font-size: 30px !important; }}
    .insight-card {{ background-color: #FFF5EE; border-left: 5px solid {BRAND_ORANGE}; padding: 20px; border-radius: 5px; color: {BRAND_DARK} !important; }}
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
            st.sidebar.error("Please ensure the sheet is shared as 'Anyone with the link can view'.")
else:
    u_file = st.sidebar.file_uploader("Upload File", type=['csv', 'xlsx'])
    if u_file: 
        df = pd.read_csv(u_file) if u_file.name.endswith('.csv') else pd.read_excel(u_file)

# --- 4. DATA CLEANING (THE FIX) ---
if df is not None:
    # Remove any completely empty columns or rows first
    df = df.dropna(how='all', axis=1).dropna(how='all', axis=0)
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

    # Sidebar Filter
    st.sidebar.markdown("---")
    month_options = ["All"]
    if 'Month' in df.columns:
        month_options += sorted([str(x) for x in df['Month'].unique() if pd.notna(x)])
    sel_month = st.sidebar.selectbox("Filter by Month", month_options)
    
    f_df = df.copy()
    if sel_month != "All": f_df = f_df[f_df['Month'] == sel_month]

    # --- 5. MAIN DASHBOARD ---
    st.title("🎧 Primarc Pecan Support Portal")
    
    # KPI Metrics
    k1, k2, k3, k4 = st.columns(4)
    total_t = len(f_df)
    k1.metric("Total Volume", total_t)
    
    res_count = 0
    if status_col:
        res_count = len(f_df[f_df[status_col].astype(str).str.contains('Resolved|Closed', case=False, na=False)])
        k2.metric("Resolution Rate", f"{(res_count/total_t*100):.1f}%" if total_t > 0 else "0%")
    
    if chan_col:
        k3.metric("Email Count", len(f_df[f_df[chan_col].astype(str).str.contains('Email', case=False, na=False)]))
        k4.metric("Call Count", len(f_df[f_df[chan_col].astype(str).str.contains('Call', case=False, na=False)]))

    st.markdown("---")

    # --- 6. PIE CHART WITH TOGGLE ---
    st.subheader("👤 Executive Performance (Pie View)")
    if exec_col and chan_col:
        view_mode = st.radio("Select Pie Mode:", ["All Executives Workload", "Channel Split for One Executive"], horizontal=True)
        
        if view_mode == "All Executives Workload":
            pie_data = f_df[exec_col].value_counts().reset_index()
            fig_ex = px.pie(pie_data, names=exec_col, values='count', hole=0.4,
                            color_discrete_sequence=px.colors.qualitative.Prism)
            st.plotly_chart(fig_ex, use_container_width=True)
        else:
            agent_list = sorted([str(x) for x in f_df[exec_col].unique() if pd.notna(x)])
            target_exec = st.selectbox("Select Executive:", agent_list)
            exec_split = f_df[f_df[exec_col] == target_exec][chan_col].value_counts().reset_index()
            fig_split = px.pie(exec_split, names=chan_col, values='count', hole=0.4,
                               color_discrete_sequence=[BRAND_ORANGE, BRAND_DARK])
            st.plotly_chart(fig_split, use_container_width=True)

    # --- 7. PREDICTIONS (BOTTOM) ---
    st.markdown("---")
    st.subheader("🔮 Predictive Insights")
    p1, p2 = st.columns(2)
    with p1:
        st.markdown(f'''<div class="insight-card"><b>📅 Backlog Forecast</b><br>
        Tickets remaining: {total_t - res_count}<br>
        Est. clearance: <b>{((total_t - res_count)/25 if total_t > 0 else 0):.1f} days</b>.</div>''', unsafe_allow_html=True)
    with p2:
        st.markdown(f'''<div class="insight-card"><b>🚀 Capacity Note</b><br>
        Current trends suggest volume is stable. Focus on {f_df[query_col].mode()[0] if query_col in f_df.columns else "top queries"} 
        to improve efficiency next week.</div>''', unsafe_allow_html=True)

    with st.expander("🔍 Raw Data"):
        st.dataframe(f_df)
else:
    st.info("Awaiting data source from sidebar...")
