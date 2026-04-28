import streamlit as st
import pandas as pd
import plotly.express as px
import base64
from streamlit_gsheets import GSheetsConnection

# --- 1. BRANDING & THEME ---
st.set_page_config(page_title="Primarc Pecan | Performance Hub", layout="wide")
BRAND_ORANGE, BRAND_NAVY, BRAND_WHITE = "#F37021", "#101828", "#FFFFFF"

st.markdown(f"""
    <style>
    .stApp {{ background: linear-gradient(180deg, {BRAND_NAVY} 0%, #1D2939 100%); }}
    h1, h2, h3, p, span, label, .stMarkdown {{ color: {BRAND_WHITE} !important; }}
    .logo-container {{ display: flex; justify-content: center; padding: 10px; }}
    div[data-baseweb="select"] > div {{ background-color: white !important; color: {BRAND_NAVY} !important; }}
    div[data-testid="stMetric"] {{ background-color: #1D2939; border: 1px solid {BRAND_ORANGE}; border-radius: 10px; padding: 15px; }}
    [data-testid="stMetricValue"] {{ color: {BRAND_ORANGE} !important; font-size: 32px !important; }}
    .stTabs [aria-selected="true"] {{ background-color: {BRAND_ORANGE} !important; border-radius: 5px; }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. LOGO ---
try:
    with open('primarc_pecan_logo.jpg', 'rb') as f:
        logo_data = base64.b64encode(f.read()).decode()
    st.markdown(f'<div class="logo-container"><img src="data:image/jpeg;base64,{logo_data}" width="220"></div>', unsafe_allow_html=True)
except:
    st.markdown("<h1 style='text-align: center; color: #F37021;'>PRIMARC PECAN</h1>", unsafe_allow_html=True)

# --- 3. DATA LOADING ---
st.sidebar.header("🔌 Data Sources")

def load_data_source(label, key_id):
    st.sidebar.subheader(f"📂 {label}")
    mode = st.sidebar.radio(f"Input for {label}", ["Google Sheet", "Excel/CSV"], key=f"mode_{key_id}")
    if mode == "Google Sheet":
        url = st.sidebar.text_input(f"Paste {label} URL", key=f"url_{key_id}")
        if url:
            try:
                conn = st.connection("gsheets", type=GSheetsConnection)
                return conn.read(spreadsheet=url, ttl=0)
            except: return None
    else:
        file = st.sidebar.file_uploader(f"Upload {label} File", type=['csv', 'xlsx'], key=f"file_{key_id}")
        if file:
            return pd.read_csv(file) if file.name.endswith('.csv') else pd.read_excel(file)
    return None

df_s = load_data_source("Support Tracker", "support")
df_a = load_data_source("Audit Tracker", "audit")

def find_col(targets, df):
    if df is None: return None
    for t in targets:
        for col in df.columns:
            if t.lower() in str(col).lower(): return col
    return None

# --- 4. TOP KPI SECTION (AHT & VOLUMES) ---
if df_s is not None:
    df_s.columns = [str(c).strip() for c in df_s.columns]
    status_col = find_col(['status'], df_s)
    chan_col = find_col(['channel'], df_s)
    aht_col = find_col(['handling time', 'aht', 'duration'], df_s)
    
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Tickets", len(df_s))
    
    # AHT Calculation
    if aht_col:
        avg_aht = pd.to_numeric(df_s[aht_col], errors='coerce').mean()
        k2.metric("Avg Handling Time", f"{avg_aht:.2f} min")
    else:
        k2.metric("Avg Handling Time", "N/A")

    # Email/Call Split
    if chan_col:
        calls = len(df_s[df_s[chan_col].astype(str).str.contains('Call', case=False, na=False)])
        emails = len(df_s[df_s[chan_col].astype(str).str.contains('Email', case=False, na=False)])
        k3.metric("Total Calls Received", calls)
        k4.metric("Total Emails", emails)

st.markdown("---")

# --- 5. TABS ---
t1, t2 = st.tabs(["📊 Performance Overview", "🕵️ CSAT & Audit Tracker"])

with t1:
    if df_s is not None:
        e_col = find_col(['executive', 'agent'], df_s)
        if e_col:
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("Workload Distribution")
                st.plotly_chart(px.pie(df_s, names=e_col, hole=0.4), use_container_width=True)
            with c2:
                st.subheader("Executive Call vs Email")
                agent = st.selectbox("Select Executive:", sorted(df_s[e_col].dropna().unique()))
                agent_data = df_s[df_s[e_col] == agent]
                st.plotly_chart(px.pie(agent_data, names=chan_col, hole=0.4), use_container_width=True)

# --- TAB 2: THE FIXED AUDIT TRACKER ---
with t2:
    st.subheader("🕵️ Quality Audit & CSAT Deep-Dive")
    if df_a is not None and df_s is not None:
        df_a.columns = [str(c).strip() for c in df_a.columns]
        ae_col = find_col(['executive', 'agent'], df_a)
        as_col = find_col(['score', 'rating', 'csat'], df_a)

        if ae_col and as_col:
            # Force numeric for score
            df_a[as_col] = pd.to_numeric(df_a[as_col], errors='coerce').fillna(0)
            
            # KPI Scorecard
            m1, m2, m3 = st.columns(3)
            total_calls = len(df_s[df_s[chan_col].astype(str).str.contains('Call', case=False, na=False)]) if chan_col else 1
            total_csat = len(df_a)
            csat_coll_perc = (total_csat / total_calls * 100) if total_calls > 0 else 0
            
            m1.metric("Total CSAT Collected", total_csat)
            m2.metric("CSAT Collection %", f"{csat_coll_perc:.1f}%")
            m3.metric("Avg Quality Score", f"{df_a[as_col].mean():.2f}")

            # Summary Table Logic
            # 1. Get Call Counts from Support Tracker
            call_counts = df_s[df_s[chan_col].astype(str).str.contains('Call', case=False, na=False)].groupby(e_col).size().reset_index(name='Calls Taken')
            
            # 2. Get Audit Data
            audit_counts = df_a.groupby(ae_col).agg(
                csat_count=(as_col, 'count'),
                avg_score=(as_col, 'mean'),
                positives=(as_col, lambda x: (x >= 4).sum()),
                negatives=(as_col, lambda x: (x <= 3).sum())
            ).reset_index()

            # 3. Merge both for the final view
            final_summary = pd.merge(call_counts, audit_counts, left_on=e_col, right_on=ae_col, how='outer').fillna(0)
            
            # Add Collection % per agent
            final_summary['Collection %'] = (final_summary['csat_count'] / final_summary['Calls Taken'] * 100).replace([float('inf'), -float('inf')], 0).fillna(0)
            
            final_summary = final_summary[['Executive Name' if 'Executive Name' in final_summary else e_col, 'Calls Taken', 'csat_count', 'Collection %', 'avg_score', 'positives', 'negatives']]
            final_summary.columns = ['Executive', 'Calls Taken', 'CSAT Collected', 'Collection %', 'Avg Quality Score', 'Positive (4-5)', 'Negative (<3)']
            
            st.markdown("### Executive-wise Call vs CSAT Performance")
            st.dataframe(final_summary, use_container_width=True)
    else:
        st.info("Please upload BOTH Support Tracker and Audit Tracker to see these metrics.")
