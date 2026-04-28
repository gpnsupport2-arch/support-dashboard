import streamlit as st
import pandas as pd
import plotly.express as px
import base64
from streamlit_gsheets import GSheetsConnection

# --- 1. BRANDING & THEME ---
st.set_page_config(page_title="Primarc Pecan | Multi-Source Dashboard", layout="wide")
BRAND_ORANGE, BRAND_NAVY, BRAND_WHITE = "#F37021", "#101828", "#FFFFFF"

st.markdown(f"""
    <style>
    .stApp {{ background: linear-gradient(180deg, {BRAND_NAVY} 0%, #1D2939 100%); }}
    h1, h2, h3, p, span, label, .stMarkdown {{ color: {BRAND_WHITE} !important; }}
    .logo-container {{ display: flex; justify-content: center; padding: 20px; margin-bottom: 10px; }}
    div[data-baseweb="select"] > div {{ background-color: white !important; color: {BRAND_NAVY} !important; }}
    div[role="listbox"] div {{ color: {BRAND_NAVY} !important; }}
    div[data-testid="stMetric"] {{ background-color: #1D2939; border: 1px solid {BRAND_ORANGE}; border-radius: 10px; padding: 15px; }}
    [data-testid="stMetricValue"] {{ color: {BRAND_ORANGE} !important; font-size: 32px !important; }}
    [data-testid="stSidebar"] {{ background-color: {BRAND_NAVY} !important; border-right: 1px solid {BRAND_ORANGE}; padding-top: 20px; }}
    .stTabs [aria-selected="true"] {{ background-color: {BRAND_ORANGE} !important; border-radius: 5px; }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. LOGO ---
try:
    with open('primarc_pecan_logo.jpg', 'rb') as f:
        logo_data = base64.b64encode(f.read()).decode()
    st.markdown(f'<div class="logo-container"><img src="data:image/jpeg;base64,{logo_data}" width="250"></div>', unsafe_allow_html=True)
except:
    st.markdown("<h1 style='text-align: center; color: #F37021;'>PRIMARC PECAN</h1>", unsafe_allow_html=True)

# --- 3. DATA HELPERS ---
def find_col(targets, df):
    if df is None: return None
    for t in targets:
        for col in df.columns:
            if t.lower() in str(col).lower(): return col
    return None

def aht_to_minutes(time_str):
    try:
        if pd.isna(time_str) or str(time_str).strip() in ["", "0", "nan"]: return 0
        parts = str(time_str).split(':')
        if len(parts) == 3: return int(parts[0])*60 + int(parts[1]) + int(parts[2])/60
        elif len(parts) == 2: return int(parts[0]) + int(parts[1])/60
        return 0
    except: return 0

# --- 4. SEPARATE DATA LOADERS (SIDEBAR) ---
st.sidebar.title("🔌 Data Connectors")

def universal_loader(label):
    st.sidebar.subheader(f"📂 {label} Data")
    mode = st.sidebar.radio(f"Format for {label}", ["Excel/CSV", "Google Sheet"], key=f"mode_{label}")
    
    if mode == "Google Sheet":
        url = st.sidebar.text_input(f"Paste {label} URL", key=f"url_{label}")
        if url:
            try:
                conn = st.connection("gsheets", type=GSheetsConnection)
                return conn.read(spreadsheet=url, ttl=0)
            except Exception as e:
                st.sidebar.error(f"Link Error: {e}")
                return None
    else:
        file = st.sidebar.file_uploader(f"Upload {label} File", type=['csv', 'xlsx'], key=f"file_{label}")
        if file:
            if file.name.endswith('.csv'): return pd.read_csv(file)
            else: return pd.read_excel(file)
    return None

# Load two distinct dataframes
df_support = universal_loader("Performance")
st.sidebar.markdown("---")
df_audit = universal_loader("Audit Tracker")

# --- 5. DASHBOARD TABS ---
t1, t2, t3 = st.tabs(["📊 Performance Overview", "🕵️ Audit Tracker", "📋 Raw Data Logs"])

# --- PERFORMANCE TAB ---
with t1:
    st.title("🎧 Operations Performance")
    if df_support is not None:
        df_support.columns = [str(c).strip() for c in df_support.columns]
        ag_col = find_col(['agent', 'executive'], df_support)
        cat_col = find_col(['category'], df_support)
        aht_col = find_col(['aht'], df_support)

        m1, m2 = st.columns(2)
        m1.metric("Total Support Tickets", len(df_support))
        if aht_col:
            df_support['AHT_Mins'] = df_support[aht_col].apply(aht_to_minutes)
            avg_aht = df_support[df_support['AHT_Mins'] > 0]['AHT_Mins'].mean()
            m2.metric("Avg Handling Time", f"{avg_aht:.2f} min")

        c1, c2 = st.columns(2)
        with c1:
            if ag_col: st.plotly_chart(px.pie(df_support, names=ag_col, hole=0.4, title="Workload by Agent"), use_container_width=True)
        with c2:
            if cat_col: st.plotly_chart(px.bar(df_support[cat_col].value_counts().reset_index(), x='index', y=cat_col, title="Volume by Category", color_discrete_sequence=[BRAND_ORANGE]), use_container_width=True)
    else:
        st.info("Please upload Performance data in the sidebar.")

# --- AUDIT TRACKER TAB ---
with t2:
    st.title("🕵️ Quality Audit Tracker")
    if df_audit is not None:
        df_audit.columns = [str(c).strip() for c in df_audit.columns]
        ag_col_a = find_col(['agent', 'executive'], df_audit)
        cs_col_a = find_col(['csat', 'rating'], df_audit)

        if ag_col_a and cs_col_a:
            def get_sentiment(val):
                v = str(val).lower()
                if any(x in v for x in ['5', '4', 'excellent', 'good']): return "Positive"
                if any(x in v for x in ['1', '2', '3', 'bad', 'poor', 'average']): return "Negative"
                return "No Rating"

            df_audit['Sentiment'] = df_audit[cs_col_a].apply(get_sentiment)
            
            # Summary Metrics
            valid = df_audit[df_audit['Sentiment'] != "No Rating"]
            k1, k2 = st.columns(2)
            k1.metric("CSATs Collected", len(valid))
            k2.metric("Collection %", f"{(len(valid)/len(df_audit)*100):.1f}%")

            # Agent Table
            summary = df_audit.groupby(ag_col_a).agg(
                Calls=(df_audit.columns[0], 'count'),
                CSATs=('Sentiment', lambda x: (x != "No Rating").sum()),
                Positive=('Sentiment', lambda x: (x == "Positive").sum()),
                Negative=('Sentiment', lambda x: (x == "Negative").sum())
            ).reset_index()
            summary.columns = ['Agent', 'Total Calls', 'CSATs', 'Pos(4-5)', 'Neg(1-3)']
            st.dataframe(summary, use_container_width=True)
            
            st.plotly_chart(px.pie(valid, names='Sentiment', hole=0.4, title="Audit Sentiment Split", color_discrete_map={'Positive':'#22C55E','Negative':'#EF4444'}), use_container_width=True)
    else:
        st.info("Please upload Audit data in the sidebar.")

# --- LOGS TAB ---
with t3:
    st.subheader("Data Inspector")
    col_a, col_b = st.columns(2)
    with col_a:
        st.write("Performance Data Preview")
        st.dataframe(df_support, height=300)
    with col_b:
        st.write("Audit Data Preview")
        st.dataframe(df_audit, height=300)
