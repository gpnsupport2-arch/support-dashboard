import streamlit as st
import pandas as pd
import plotly.express as px
import base64
from streamlit_gsheets import GSheetsConnection

# --- 1. SETTINGS & BRANDING ---
st.set_page_config(page_title="Primarc Pecan Portal", layout="wide")
BRAND_ORANGE, BRAND_NAVY = "#F37021", "#101828"

st.markdown(f"""
    <style>
    .stApp {{ background: linear-gradient(180deg, {BRAND_NAVY} 0%, #1D2939 100%); }}
    h1, h2, h3, p, span, label, .stMarkdown {{ color: white !important; }}
    div[data-testid="stMetric"] {{ background-color: #1D2939; border: 1px solid {BRAND_ORANGE}; border-radius: 10px; padding: 15px; }}
    [data-testid="stMetricValue"] {{ color: {BRAND_ORANGE} !important; font-weight: bold !important; }}
    .stTabs [aria-selected="true"] {{ background-color: {BRAND_ORANGE} !important; border-radius: 5px; }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. ENGINE HELPERS ---
def find_col(targets, df):
    """Aggressively finds columns even with trailing spaces or different casing."""
    if df is None or df.empty: return None
    cols = [str(c).strip().lower() for c in df.columns]
    for t in targets:
        if t.lower() in cols:
            return df.columns[cols.index(t.lower())]
    return None

def parse_aht(val):
    """Converts 00:04:22 or 04:22 to decimal minutes."""
    try:
        if pd.isna(val) or str(val).strip() in ["", "0", "nan"]: return 0
        s = str(val).strip().split(':')
        if len(s) == 3: return int(s[0])*60 + int(s[1]) + int(s[2])/60
        if len(s) == 2: return int(s[0]) + int(s[1])/60
        return float(val)
    except: return 0

# --- 3. SIDEBAR LOADERS ---
st.sidebar.title("🔌 Data Sources")

def fetch_data(label):
    st.sidebar.subheader(f"📂 {label}")
    src = st.sidebar.radio(f"Source: {label}", ["Excel/CSV", "Google Sheet"], key=f"src_{label}")
    if src == "Google Sheet":
        url = st.sidebar.text_input(f"Link: {label}", key=f"url_{label}")
        if url:
            try:
                conn = st.connection("gsheets", type=GSheetsConnection)
                return conn.read(spreadsheet=url, ttl=0)
            except: return None
    else:
        file = st.sidebar.file_uploader(f"Upload: {label}", type=['csv', 'xlsx'], key=f"file_{label}")
        if file:
            return pd.read_csv(file) if file.name.endswith('.csv') else pd.read_excel(file)
    return None

# Load Independent Dataframes
df_perf_raw = fetch_data("Performance Tracker")
st.sidebar.markdown("---")
df_audit_raw = fetch_data("Audit Tracker")

# --- 4. TABS ---
tab1, tab2, tab3 = st.tabs(["📊 Performance Overview", "🕵️ Audit Tracker", "📋 System Logs"])

# --- TAB 1: PERFORMANCE ---
with tab1:
    if df_perf_raw is not None:
        df_p = df_perf_raw.copy()
        # Mapping
        ag = find_col(['agent', 'executive'], df_p)
        cat = find_col(['category'], df_p)
        aht = find_col(['aht', 'handling time'], df_p)

        st.title("🎧 Operations Overview")
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Tickets", len(df_p))
        
        if aht:
            df_p['mins'] = df_p[aht].apply(parse_aht)
            avg_val = df_p[df_p['mins'] > 0]['mins'].mean()
            col2.metric("Avg Handling Time", f"{avg_val:.2f} min" if not pd.isna(avg_val) else "0.00 min")
        
        if cat:
            col3.metric("Ticket Categories", df_p[cat].nunique())

        # Charts
        c1, c2 = st.columns(2)
        with c1:
            if ag: st.plotly_chart(px.pie(df_p, names=ag, hole=0.4, title="Agent Workload Share"), use_container_width=True)
        with c2:
            if cat: st.plotly_chart(px.bar(df_p[cat].value_counts().reset_index(), x='index', y=cat, 
                                          title="Volume by Category", color_discrete_sequence=[BRAND_ORANGE]), use_container_width=True)
    else:
        st.info("👋 Upload Performance Data in the sidebar to begin.")

# --- TAB 2: AUDIT TRACKER ---
with tab2:
    if df_audit_raw is not None:
        df_a = df_audit_raw.copy()
        ag_a = find_col(['agent', 'executive'], df_a)
        cs_a = find_col(['csat', 'rating'], df_a)

        st.title("🕵️ Quality Audit Summary")
        if ag_a and cs_a:
            # Sentiment Logic
            def get_sent(v):
                v = str(v).lower()
                if any(x in v for x in ['5', '4', 'excellent', 'good']): return "Positive"
                if any(x in v for x in ['1', '2', '3', 'bad', 'poor', 'average']): return "Negative"
                return "No Rating"

            df_a['Sentiment'] = df_a[cs_a].apply(get_sent)
            valid = df_a[df_a['Sentiment'] != "No Rating"]

            k1, k2 = st.columns(2)
            k1.metric("Total CSAT Collected", len(valid))
            k2.metric("Collection %", f"{(len(valid)/len(df_a)*100):.1f}%")

            # Agent Performance Table
            st.subheader("Executive Deep-Dive")
            summary = df_a.groupby(ag_a).agg(
                Calls=(df_a.columns[0], 'count'),
                CSATs=('Sentiment', lambda x: (x != "No Rating").sum()),
                Positives=('Sentiment', lambda x: (x == "Positive").sum()),
                Negatives=('Sentiment', lambda x: (x == "Negative").sum())
            ).reset_index()
            summary['Coll %'] = (summary['CSATs'] / summary['Calls'] * 100).round(1)
            summary.columns = ['Agent', 'Total Calls', 'CSATs', 'Positive(4-5)', 'Negative(1-3)', 'Coll %']
            st.dataframe(summary.sort_values('Total Calls', ascending=False), use_container_width=True)
            
            if not valid.empty:
                st.plotly_chart(px.pie(valid, names='Sentiment', hole=0.4, title="Overall Quality Score", 
                                       color_discrete_map={'Positive':'#22C55E','Negative':'#EF4444'}), use_container_width=True)
        else:
            st.error("Audit File Missing: Ensure it has 'Agent' and 'Csat' columns.")
    else:
        st.info("👋 Upload Audit Tracker Data in the sidebar to begin.")

# --- TAB 3: SYSTEM LOGS ---
with tab3:
    st.subheader("Data Inspector")
    if df_perf_raw is not None: 
        st.write("Current Performance Data Headers:", list(df_perf_raw.columns))
        st.dataframe(df_perf_raw.head(5))
    if df_audit_raw is not None:
        st.write("Current Audit Data Headers:", list(df_audit_raw.columns))
        st.dataframe(df_audit_raw.head(5))
