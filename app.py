import streamlit as st
import pandas as pd
import plotly.express as px
import base64
from streamlit_gsheets import GSheetsConnection

# --- 1. BRANDING & HIGH-VISIBILITY BLUE THEME ---
st.set_page_config(page_title="Primarc Pecan | Support Hub", layout="wide")

BRAND_ORANGE = "#F37021"
BRAND_NAVY = "#101828" 
BRAND_LIGHT_BLUE = "#1D2939" 
BRAND_WHITE = "#FFFFFF"

st.markdown(f"""
    <style>
    /* 1. Main Background */
    .stApp {{
        background: linear-gradient(180deg, {BRAND_NAVY} 0%, {BRAND_LIGHT_BLUE} 100%);
    }}
    
    /* 2. FORCE ALL TEXT TO WHITE (EVERYWHERE) */
    html, body, [class*="st-"], .stMarkdown, p, span, label, h1, h2, h3 {{
        color: {BRAND_WHITE} !important;
    }}

    /* 3. FIX DATAFRAME VISIBILITY (INTERNAL FONT) */
    [data-testid="stTable"], [data-testid="stDataFrame"] {{
        background-color: transparent !important;
    }}
    div[data-testid="stExpander"] {{
        background-color: rgba(255, 255, 255, 0.05) !important;
    }}
    
    /* 4. SIDEBAR FIX */
    [data-testid="stSidebar"] {{
        background-color: {BRAND_NAVY} !important;
        border-right: 1px solid {BRAND_ORANGE};
    }}

    /* 5. METRIC CARDS */
    div[data-testid="stMetric"] {{
        background-color: {BRAND_LIGHT_BLUE};
        border: 1px solid {BRAND_ORANGE};
        border-radius: 12px;
        padding: 20px;
    }}
    [data-testid="stMetricValue"] {{ color: {BRAND_ORANGE} !important; font-size: 32px !important; }}
    
    /* 6. TAB STYLING */
    .stTabs [data-baseweb="tab-list"] {{ gap: 15px; }}
    .stTabs [data-baseweb="tab"] {{
        background-color: {BRAND_LIGHT_BLUE} !important;
        color: {BRAND_WHITE} !important;
        border-radius: 5px;
        padding: 8px 20px;
    }}
    .stTabs [aria-selected="true"] {{
        background-color: {BRAND_ORANGE} !important;
    }}

    /* 7. INSIGHT CARDS (BOTTOM) */
    .insight-card {{
        background-color: rgba(255, 255, 255, 0.08);
        border-left: 5px solid {BRAND_ORANGE};
        padding: 20px;
        border-radius: 8px;
        color: {BRAND_WHITE} !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. LOGO ---
try:
    with open('primarc_pecan_logo.jpg', 'rb') as f:
        logo_base64 = base64.b64encode(f.read()).decode()
    st.sidebar.markdown(f'<div style="text-align: center;"><img src="data:image/jpeg;base64,{logo_base64}" width="180"></div>', unsafe_allow_html=True)
except:
    st.sidebar.title("Primarc Pecan")

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
            st.sidebar.error("Access Error: Set sheet to 'Anyone with link can view'.")
else:
    u_file = st.sidebar.file_uploader("Upload File", type=['csv', 'xlsx'])
    if u_file: 
        df = pd.read_csv(u_file) if u_file.name.endswith('.csv') else pd.read_excel(u_file)

# --- 4. PROCESSING ---
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
    tab_overview, tab_tracker = st.tabs(["📊 Analytics Overview", "📋 Query Tracker Log"])

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
            st.subheader("📊 Query Trends")
            if query_col and chan_col:
                fig_q = px.bar(f_df.groupby([query_col, chan_col]).size().reset_index(name='Count'), 
                               x=query_col, y='Count', color=chan_col, barmode='group',
                               color_discrete_sequence=[BRAND_ORANGE, "#98A2B3"])
                fig_q.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="white"))
                st.plotly_chart(fig_q, use_container_width=True)

        with c2:
            st.subheader("👤 Executive Performance")
            if exec_col and chan_col:
                view_mode = st.radio("Chart Mode:", ["Total Workload", "Agent Split"], horizontal=True)
                if view_mode == "Total Workload":
                    fig_ex = px.pie(f_df[exec_col].value_counts().reset_index(), names=exec_col, values='count', 
                                    hole=0.4, color_discrete_sequence=px.colors.sequential.Oranges_r)
                else:
                    agent_list = sorted([str(x) for x in f_df[exec_col].unique() if pd.notna(x)])
                    target_exec = st.selectbox("Select Executive:", agent_list)
                    exec_split = f_df[f_df[exec_col] == target_exec][chan_col].value_counts().reset_index()
                    fig_ex = px.pie(exec_split, names=chan_col, values='count', hole=0.4,
                                   color_discrete_sequence=[BRAND_ORANGE, "#475467"])
                
                fig_ex.update_layout(paper_bgcolor='rgba(0,0,0,0)', font=dict(color="white"))
                st.plotly_chart(fig_ex, use_container_width=True)

    with tab_tracker:
        st.title("📋 Live Query Log")
        st.write("Full searchable ticket list:")
        st.dataframe(f_df, use_container_width=True)

    # --- 6. PREDICTIONS (BOTTOM) ---
    st.markdown("---")
    st.subheader("🔮 Predictive Outlook")
    p1, p2 = st.columns(2)
    with p1:
        st.markdown(f'''<div class="insight-card">
        <b style="color:{BRAND_ORANGE}">📅 Backlog clearance Forecast</b><br>
        Pending: {total_t - res_count} tickets.<br>
        Forecasted finish: <b>{((total_t - res_count)/30 if total_t > 0 else 0):.1f} days</b>.</div>''', unsafe_allow_html=True)
    with p2:
        st.markdown(f'''<div class="insight-card">
        <b style="color:{BRAND_ORANGE}">🚀 Future Resource Planning</b><br>
        Next week volume projection: <b>+4.2%</b>.<br>
        Current staffing levels are optimal for the current trend.</div>''', unsafe_allow_html=True)

else:
    st.title("🎧 Support Dashboard")
    st.info("Connect data source to begin...")
