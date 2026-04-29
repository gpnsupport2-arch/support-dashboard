import streamlit as st
import pandas as pd
import plotly.express as px
import base64
from streamlit_gsheets import GSheetsConnection

# --- 1. BRANDING & THEME ---
st.set_page_config(page_title="Primarc Pecan | Executive Portal", layout="wide")
BRAND_ORANGE, BRAND_NAVY = "#F37021", "#101828"

st.markdown(f"""
    <style>
    .stApp {{ background: linear-gradient(180deg, {BRAND_NAVY} 0%, #1D2939 100%); }}
    h1, h2, h3, p, span, label, .stMarkdown {{ color: white !important; }}
    div[data-testid="stMetric"] {{ background-color: #1D2939; border: 1px solid {BRAND_ORANGE}; border-radius: 10px; padding: 15px; }}
    [data-testid="stMetricValue"] {{ color: {BRAND_ORANGE} !important; }}
    .stTabs [aria-selected="true"] {{ background-color: {BRAND_ORANGE} !important; border-radius: 5px; }}
    .insight-card {{ background-color: rgba(255, 255, 255, 0.08); border-left: 5px solid {BRAND_ORANGE}; padding: 15px; border-radius: 8px; }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. HELPERS ---
def find_col(targets, df):
    if df is None or df.empty: return None
    for t in targets:
        for col in df.columns:
            if t.lower() in str(col).lower(): return col
    return None

def aht_to_minutes(time_str):
    try:
        if pd.isna(time_str) or str(time_str).strip() in ["", "0", "nan"]: return 0
        parts = str(time_str).split(':')
        if len(parts) == 3: return int(parts[0])*60 + int(parts[1]) + int(parts[2])/60
        if len(parts) == 2: return int(parts[0]) + int(parts[1])/60
        return 0
    except: return 0

# --- 3. DUAL DATA LOADERS (SIDEBAR) ---
st.sidebar.title("🔌 Data Connectors")

def load_data_source(label):
    st.sidebar.subheader(f"📂 {label} Data")
    mode = st.sidebar.radio(f"Format: {label}", ["Excel/CSV", "Google Sheet"], key=f"m_{label}")
    if mode == "Google Sheet":
        url = st.sidebar.text_input(f"URL: {label}", key=f"u_{label}")
        if url:
            try:
                conn = st.connection("gsheets", type=GSheetsConnection)
                return conn.read(spreadsheet=url, ttl=0)
            except: return None
    else:
        file = st.sidebar.file_uploader(f"Upload: {label}", type=['csv', 'xlsx'], key=f"f_{label}")
        if file:
            return pd.read_csv(file) if file.name.endswith('.csv') else pd.read_excel(file)
    return None

df_p_raw = load_data_source("Performance")
df_a_raw = load_data_source("Audit Tracker")

# --- 4. DASHBOARD TABS ---
t1, t2, t3 = st.tabs(["📊 Performance Overview", "🕵️ Audit Tracker", "📋 Raw Logs"])

# --- TAB 1: PERFORMANCE ---
with t1:
    if df_p_raw is not None:
        df_p = df_p_raw.copy()
        df_p.columns = [str(c).strip() for c in df_p.columns]
        
        ag_col = find_col(['agent', 'executive'], df_p)
        cat_col = find_col(['category'], df_p)
        aht_col = find_col(['aht'], df_p)

        st.title("🎧 Operations Performance")
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Tickets", len(df_p))
        
        if aht_col:
            df_p['mins'] = df_p[aht_col].apply(aht_to_minutes)
            avg = df_p[df_p['mins'] > 0]['mins'].mean()
            m2.metric("Avg Handling Time", f"{avg:.2f} min" if not pd.isna(avg) else "0.00 min")
        
        if cat_col:
            m3.metric("Categories", df_p[cat_col].nunique())

        c1, c2 = st.columns(2)
        with c1:
            if ag_col: st.plotly_chart(px.pie(df_p, names=ag_col, hole=0.4, title="Ticket Share"), use_container_width=True)
        with c2:
            if cat_col: st.plotly_chart(px.bar(df_p[cat_col].value_counts().reset_index(), x='index', y=cat_col, title="Volume by Category", color_discrete_sequence=[BRAND_ORANGE]), use_container_width=True)
    else:
        st.info("Please upload Performance Data in the sidebar to view this tab.")

# --- TAB 2: AUDIT TRACKER ---
with t2:
    if df_a_raw is not None:
        df_a = df_a_raw.copy()
        df_a.columns = [str(c).strip() for c in df_a.columns]
        
        ag_col = find_col(['agent', 'executive'], df_a)
        cs_col = find_col(['csat', 'rating'], df_a)

        if ag_col and cs_col:
            def get_sentiment(val):
                v = str(val).lower()
                if any(x in v for x in ['5', '4', 'excellent', 'good']): return "Positive"
                if any(x in v for x in ['1', '2', '3', 'bad', 'poor', 'average']): return "Negative"
                return "No Rating"

            df_a['Sentiment'] = df_a[cs_col].apply(get_sentiment)
            valid = df_a[df_a['Sentiment'] != "No Rating"]

            st.title("🕵️ Quality Audit Tracker")
            k1, k2, k3 = st.columns(3)
            k1.metric("CSATs Collected", len(valid))
            k2.metric("Collection %", f"{(len(valid)/len(df_a)*100):.1f}%" if len(df_a) > 0 else "0%")
            
            # Numeric Score
            df_a['Score'] = pd.to_numeric(df_a[cs_col].astype(str).str.extract('(\d+)')[0], errors='coerce')
            k3.metric("Avg Score", f"{df_a['Score'].mean():.2f}" if not pd.isna(df_a['Score'].mean()) else "N/A")

            # Agent Breakdown
            st.subheader("Agent Performance Details")
            summary = df_a.groupby(ag_col).agg(
                Calls=(df_a.columns[0], 'count'),
                CSATs=('Sentiment', lambda x: (x != "No Rating").sum()),
                Positives=('Sentiment', lambda x: (x == "Positive").sum()),
                Negatives=('Sentiment', lambda x: (x == "Negative").sum())
            ).reset_index()
            summary['Coll %'] = (summary['CSATs'] / summary['Calls'] * 100).round(1)
            summary.columns = ['Agent', 'Calls Taken', 'CSATs', 'Pos(4-5)', 'Neg(1-3)', 'Coll %']
            st.dataframe(summary.sort_values('Calls Taken', ascending=False), use_container_width=True)
            
            if not valid.empty:
                st.plotly_chart(px.pie(valid, names='Sentiment', hole=0.4, title="Overall Sentiment", color_discrete_map={'Positive':'#22C55E','Negative':'#EF4444'}), use_container_width=True)
        else:
            st.error("Audit File missing required columns: 'Agent' and 'Csat'.")
    else:
        st.info("Please upload Audit Tracker Data in the sidebar to view this tab.")

# --- TAB 3: DATA LOGS ---
with t3:
    st.subheader("Data Inspector")
    c1, c2 = st.columns(2)
    with c1: 
        st.write("Performance Data Preview")
        st.dataframe(df_p_raw)
    with c2: 
        st.write("Audit Data Preview")
        st.dataframe(df_a_raw)
