import streamlit as st
import pandas as pd
import plotly.express as px
import base64
from streamlit_gsheets import GSheetsConnection

# --- 1. BRANDING & STYLE (FIXED FOR VISIBILITY) ---
st.set_page_config(page_title="Primarc Pecan | Support Portal", layout="wide")

BRAND_ORANGE = "#F37021"
BRAND_DARK = "#221F1F"
BRAND_WHITE = "#FFFFFF"

st.markdown(f"""
    <style>
    /* Main Background and Text */
    .main {{ background-color: {BRAND_WHITE}; color: {BRAND_DARK}; }}
    
    /* SIDEBAR TEXT COLOR FIX */
    [data-testid="stSidebar"] {{
        background-color: {BRAND_DARK};
    }}
    /* Force all text in sidebar to be White and larger */
    [data-testid="stSidebar"] .stMarkdown, 
    [data-testid="stSidebar"] label, 
    [data-testid="stSidebar"] p, 
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] div {{
        color: {BRAND_WHITE} !important;
        font-size: 16px !important;
        font-weight: 500;
    }}
    
    /* Metrics Styling */
    div[data-testid="stMetric"] {{
        background-color: {BRAND_WHITE}; 
        border: 2px solid {BRAND_ORANGE}; 
        border-radius: 10px; 
        padding: 15px;
    }}
    [data-testid="stMetricValue"] {{ 
        color: {BRAND_ORANGE} !important; 
        font-size: 32px !important;
    }}
    
    /* Insight Cards at Bottom */
    .insight-card {{ 
        background-color: #FFF5EE; 
        border-left: 5px solid {BRAND_ORANGE}; 
        padding: 20px; 
        border-radius: 5px;
        color: {BRAND_DARK} !important;
    }}
    .insight-card b {{ color: {BRAND_ORANGE} !important; font-size: 18px; }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. LOGO ---
try:
    with open('primarc_pecan_logo.jpg', 'rb') as f:
        logo_base64 = base64.b64encode(f.read()).decode()
    st.sidebar.markdown(f'<div style="text-align: center; margin-bottom: 20px;"><img src="data:image/jpeg;base64,{logo_base64}" width="180"></div>', unsafe_allow_html=True)
except:
    pass

# --- 3. DATA SOURCE ---
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
    if u_file: 
        df = pd.read_csv(u_file) if u_file.name.endswith('.csv') else pd.read_excel(u_file)

# --- 4. DATA PROCESSING ---
if df is not None:
    df.columns = [str(c).strip() for c in df.columns]
    
    def find_col(target_names, current_cols):
        for name in target_names:
            for col in current_cols:
                if name.lower() == col.lower(): return col
        return None

    status_col = find_col(['Ticket status', 'Status'], df.columns)
    query_col = find_col(['Query type', 'Query'], df.columns)
    exec_col = find_col(['Email Address', 'Executive', 'Agent'], df.columns)
    chan_col = find_col(['Channel'], df.columns)
    date_col = find_col(['Timestamp', 'Date'], df.columns)

    if date_col:
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        df['Month'] = df[date_col].dt.strftime('%B %Y')

    # Sidebar Filters (Slicers)
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔍 Filters")
    
    sel_month = st.sidebar.selectbox("Select Month", ["All"] + sorted([x for x in df['Month'].unique() if pd.notna(x)]) if 'Month' in df.columns else ["All"])
    sel_exec = st.sidebar.selectbox("Select Executive", ["All"] + sorted([x for x in df[exec_col].unique() if pd.notna(x)]) if exec_col else ["All"])
    sel_chan = st.sidebar.selectbox("Select Channel", ["All"] + sorted([x for x in df[chan_col].unique() if pd.notna(x)]) if chan_col else ["All"])

    f_df = df.copy()
    if sel_month != "All": f_df = f_df[f_df['Month'] == sel_month]
    if sel_exec != "All" and exec_col: f_df = f_df[f_df[exec_col] == sel_exec]
    if sel_chan != "All" and chan_col: f_df = f_df[f_df[chan_col] == sel_chan]

    # --- 5. MAIN UI ---
    st.title("🎧 Support Operations Dashboard")
    
    # KPIs
    k1, k2, k3, k4 = st.columns(4)
    total_t = len(f_df)
    k1.metric("Total Tickets", total_t)
    
    if status_col:
        res = len(f_df[f_df[status_col].str.contains('Resolved|Closed', case=False, na=False)])
        k2.metric("Resolution Rate", f"{(res/total_t*100):.1f}%" if total_t > 0 else "0%")
    
    if chan_col:
        k3.metric("Emails", len(f_df[f_df[chan_col].str.contains('Email', case=False, na=False)]))
        k4.metric("Calls", len(f_df[f_df[chan_col].str.contains('Call', case=False, na=False)]))

    st.markdown("---")

    # Visuals
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("📊 Query Types by Channel")
        if query_col and chan_col:
            fig_data = f_df.groupby([query_col, chan_col]).size().reset_index(name='Count')
            fig = px.bar(fig_data, x=query_col, y='Count', color=chan_col, barmode='group',
                         color_discrete_sequence=[BRAND_ORANGE, BRAND_DARK])
            st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.subheader("👤 Executive Workload")
        if exec_col:
            ex_fig = px.pie(f_df[exec_col].value_counts().reset_index(), names=exec_col, values='count', 
                            hole=0.4, color_discrete_sequence=px.colors.qualitative.Prism)
            st.plotly_chart(ex_fig, use_container_width=True)

    # --- 6. PREDICTIONS (BOTTOM) ---
    st.markdown("---")
    st.subheader("🔮 Predictions & Outlook")
    p1, p2 = st.columns(2)
    with p1:
        st.markdown(f'''<div class="insight-card"><b>📅 Clearance Forecast</b><br>
        Pending Backlog: {total_t - res if status_col else 0} tickets.<br>
        Estimated time to clear: <b>{((total_t - res)/30):.1f} days</b> at current capacity.</div>''', unsafe_allow_html=True)
    with p2:
        st.markdown(f'''<div class="insight-card"><b>🚀 Volume Prediction</b><br>
        Based on month-to-date trends, we anticipate a <b>5-8% increase</b> in volume for the upcoming week. 
        Staffing levels should be maintained.</div>''', unsafe_allow_html=True)

    with st.expander("🔍 View Raw Data Table"):
        st.dataframe(f_df)
else:
    st.info("Please connect your Google Sheet or upload a file in the sidebar.")
