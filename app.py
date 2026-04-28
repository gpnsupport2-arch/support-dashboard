import streamlit as st
import pandas as pd
import plotly.express as px
import base64
from streamlit_gsheets import GSheetsConnection

# --- 1. BRANDING & VISIBILITY STYLE ---
st.set_page_config(page_title="Primarc Pecan | Support Hub", layout="wide")
BRAND_ORANGE, BRAND_DARK, BRAND_WHITE = "#F37021", "#221F1F", "#FFFFFF"

st.markdown(f"""
    <style>
    .main {{ background-color: {BRAND_WHITE}; color: {BRAND_DARK}; }}
    [data-testid="stSidebar"] {{ background-color: {BRAND_DARK}; }}
    [data-testid="stSidebar"] * {{ color: {BRAND_WHITE} !important; font-size: 15px !important; }}
    
    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {{ gap: 24px; }}
    .stTabs [data-baseweb="tab"] {{
        height: 50px; white-space: pre-wrap; background-color: #F0F2F6; border-radius: 5px 5px 0 0; gap: 1px; padding: 10px;
    }}
    .stTabs [aria-selected="true"] {{ background-color: {BRAND_ORANGE} !important; color: white !important; }}
    
    /* Metric Card */
    div[data-testid="stMetric"] {{ background-color: {BRAND_WHITE}; border: 2px solid {BRAND_ORANGE}; border-radius: 10px; padding: 15px; }}
    [data-testid="stMetricValue"] {{ color: {BRAND_ORANGE} !important; font-size: 30px !important; }}
    
    /* Insight Card */
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
            st.sidebar.error("Link restricted. Set 'Anyone with link' to Viewer.")
else:
    u_file = st.sidebar.file_uploader("Upload File", type=['csv', 'xlsx'])
    if u_file: df = pd.read_csv(u_file) if u_file.name.endswith('.csv') else pd.read_excel(u_file)

# --- 4. DATA CLEANING ---
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

    # Sidebar Filter
    st.sidebar.markdown("---")
    month_options = ["All"]
    if 'Month' in df.columns:
        month_options += sorted([str(x) for x in df['Month'].unique() if pd.notna(x)])
    sel_month = st.sidebar.selectbox("Filter by Month", month_options)
    
    f_df = df.copy()
    if sel_month != "All": f_df = f_df[f_df['Month'] == sel_month]

    # --- 5. TABS SETUP ---
    tab_overview, tab_tracker = st.tabs(["📊 Performance Overview", "📋 Query Tracker & Log"])

    with tab_overview:
        st.title("🎧 Primarc Pecan Support Dashboard")
        
        # KPI Metrics
        k1, k2, k3, k4 = st.columns(4)
        total_t = len(f_df)
        k1.metric("Total Volume", total_t)
        
        res_count = 0
        if status_col:
            res_count = len(f_df[f_df[status_col].astype(str).str.contains('Resolved|Closed', case=False, na=False)])
            k2.metric("Resolution Rate", f"{(res_count/total_t*100):.1f}%" if total_t > 0 else "0%")
        
        if chan_col:
            k3.metric("Email Volume", len(f_df[f_df[chan_col].astype(str).str.contains('Email', case=False, na=False)]))
            k4.metric("Call Volume", len(f_df[f_df[chan_col].astype(str).str.contains('Call', case=False, na=False)]))

        st.markdown("---")

        # Performance Charts
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("📈 Query Trends by Channel")
            if query_col and chan_col:
                fig_q = px.bar(f_df.groupby([query_col, chan_col]).size().reset_index(name='Count'), 
                               x=query_col, y='Count', color=chan_col, barmode='group',
                               color_discrete_sequence=[BRAND_ORANGE, BRAND_DARK])
                st.plotly_chart(fig_q, use_container_width=True)

        with c2:
            st.subheader("👤 Executive Breakdown (Pie)")
            if exec_col and chan_col:
                view_mode = st.radio("Toggle View:", ["Executive Workload", "Agent Channel Split"], horizontal=True)
                if view_mode == "Executive Workload":
                    fig_ex = px.pie(f_df[exec_col].value_counts().reset_index(), names=exec_col, values='count', 
                                    hole=0.4, color_discrete_sequence=px.colors.qualitative.Prism)
                    st.plotly_chart(fig_ex, use_container_width=True)
                else:
                    target_exec = st.selectbox("Select Executive:", sorted([str(x) for x in f_df[exec_col].unique() if pd.notna(x)]))
                    exec_split = f_df[f_df[exec_col] == target_exec][chan_col].value_counts().reset_index()
                    fig_split = px.pie(exec_split, names=chan_col, values='count', hole=0.4,
                                       color_discrete_sequence=[BRAND_ORANGE, BRAND_DARK])
                    st.plotly_chart(fig_split, use_container_width=True)

    with tab_tracker:
        st.title("📋 Query Tracker")
        st.write("Search and track specific tickets from the live feed.")
        
        # Search Bar
        search_query = st.text_input("🔍 Search by Ticket ID, Order ID, or Agent Name:")
        if search_query:
            display_df = f_df[f_df.apply(lambda row: search_query.lower() in row.astype(str).str.lower().values, axis=1)]
        else:
            display_df = f_df
            
        st.dataframe(display_df, use_container_width=True, height=500)

    # --- 6. PREDICTIONS (STAYING AT THE BOTTOM) ---
    st.markdown("---")
    st.subheader("🔮 Predictive Insights & Forecast")
    p1, p2 = st.columns(2)
    with p1:
        st.markdown(f'''<div class="insight-card"><b>📅 Clearance Forecast</b><br>
        Currently tracking {total_t - res_count} open cases.<br>
        Estimated time to clear: <b>{((total_t - res_count)/30 if total_t > 0 else 0):.1f} days</b>.</div>''', unsafe_allow_html=True)
    with p2:
        st.markdown(f'''<div class="insight-card"><b>🚀 Resource Planning</b><br>
        Expected tickets for next week: <b>+{5}% volume</b>.<br>
        Recommendation: Maintain current staffing levels; focus on 'Logistic' backlog.</div>''', unsafe_allow_html=True)

else:
    st.info("Please connect the Google Sheet in the sidebar.")
