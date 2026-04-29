import streamlit as st
import pandas as pd
import plotly.express as px
import base64
from streamlit_gsheets import GSheetsConnection

# --- 1. SETTINGS & BRANDING ---
st.set_page_config(page_title="Primarc Pecan | Executive Hub", layout="wide")
BRAND_ORANGE, BRAND_NAVY = "#F37021", "#101828"

st.markdown(f"""
    <style>
    .stApp {{ background: linear-gradient(180deg, {BRAND_NAVY} 0%, #1D2939 100%); }}
    h1, h2, h3, p, span, label, .stMarkdown {{ color: white !important; }}
    div[data-testid="stMetric"] {{ background-color: #1D2939; border: 1px solid {BRAND_ORANGE}; border-radius: 10px; padding: 15px; }}
    [data-testid="stMetricValue"] {{ color: {BRAND_ORANGE} !important; font-weight: bold !important; }}
    .stTabs [aria-selected="true"] {{ background-color: {BRAND_ORANGE} !important; border-radius: 5px; }}
    .stDataFrame {{ background-color: white; border-radius: 10px; }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. ENGINE HELPERS ---
def find_col(targets, df):
    if df is None or df.empty: return None
    cols = [str(c).strip().lower() for c in df.columns]
    for t in targets:
        if t.lower() in cols:
            return df.columns[cols.index(t.lower())]
    return None

def parse_aht(val):
    try:
        if pd.isna(val) or str(val).strip() in ["", "0", "nan"]: return 0
        s = str(val).strip().split(':')
        if len(s) == 3: return int(s[0])*60 + int(s[1]) + int(s[2])/60
        if len(s) == 2: return int(s[0]) + int(s[1])/60
        return float(val)
    except: return 0

# --- 3. SIDEBAR LOADERS ---
st.sidebar.title("🔌 Data Connectors")

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

df_p_raw = fetch_data("Performance Tracker")
st.sidebar.markdown("---")
df_a_raw = fetch_data("Audit Tracker")

# --- 4. TABS ---
tab1, tab2, tab3 = st.tabs(["📊 Performance Overview", "🕵️ Audit Tracker", "📋 Data Inspector"])

# --- TAB 1: PERFORMANCE OVERVIEW ---
with tab1:
    if df_p_raw is not None:
        df_p = df_p_raw.copy()
        df_p.columns = [str(c).strip() for c in df_p.columns]
        
        # Mapping from your specific file source
        ag = find_col(['agent', 'executive'], df_p)
        cat = find_col(['category'], df_p)
        aht = find_col(['aht'], df_p)

        st.title("🎧 Operations Performance")
        
        # Filtering out rows where Category/Agent are missing (the "Unanswered" rows)
        clean_df = df_p.dropna(subset=[cat, ag]) if cat and ag else df_p

        m1, m2, m3 = st.columns(3)
        m1.metric("Total Tickets Handled", len(clean_df))
        
        if aht:
            clean_df['mins'] = clean_df[aht].apply(parse_aht)
            avg_aht = clean_df[clean_df['mins'] > 0]['mins'].mean()
            m2.metric("Avg Handling Time", f"{avg_aht:.2f} min" if not pd.isna(avg_aht) else "0.00 min")
        
        if cat:
            m3.metric("Unique Categories", clean_df[cat].nunique())

        c1, c2 = st.columns(2)
        with c1:
            if ag:
                fig_ag = px.pie(clean_df, names=ag, hole=0.4, title="Ticket Share by Agent",
                                color_discrete_sequence=px.colors.sequential.Oranges_r)
                st.plotly_chart(fig_ag, use_container_width=True)
        with c2:
            if cat:
                fig_cat = px.bar(clean_df[cat].value_counts().reset_index(), x='index', y=cat, 
                                 title="Volume by Category", color_discrete_sequence=[BRAND_ORANGE])
                st.plotly_chart(fig_cat, use_container_width=True)
    else:
        st.info("👋 Use the sidebar to upload your 'Call Tracker' file.")

# --- TAB 2: AUDIT TRACKER ---
with tab2:
    if df_a_raw is not None:
        df_a = df_a_raw.copy()
        df_a.columns = [str(c).strip() for c in df_a.columns]
        
        ag_a = find_col(['agent', 'executive'], df_a)
        cs_a = find_col(['csat', 'rating'], df_a)

        st.title("🕵️ Quality Audit & CSAT Tracker")
        
        if ag_a and cs_a:
            # Rating Logic (4-5 = Positive, 1-3 = Negative)
            def get_sent(v):
                v = str(v).lower()
                if any(x in v for x in ['5', '4', 'excellent', 'good']): return "Positive"
                if any(x in v for x in ['1', '2', '3', 'bad', 'poor', 'average']): return "Negative"
                return "No Rating"

            df_a['Sentiment'] = df_a[cs_a].apply(get_sent)
            valid = df_a[df_a['Sentiment'] != "No Rating"]

            # Key Metrics
            k1, k2, k3 = st.columns(3)
            k1.metric("Total CSATs", len(valid))
            k2.metric("Collection Rate", f"{(len(valid)/len(df_a)*100):.1f}%")
            
            # Extract Score for average
            df_a['Score'] = pd.to_numeric(df_a[cs_a].astype(str).str.extract('(\d+)')[0], errors='coerce')
            k3.metric("Avg Quality Score", f"{df_a['Score'].mean():.2f}")

            # Agent Breakdown Table
            st.subheader("Agent Performance Metrics")
            summary = df_a.groupby(ag_a).agg(
                Calls_Taken=(df_a.columns[0], 'count'),
                CSATs_Collected=('Sentiment', lambda x: (x != "No Rating").sum()),
                Positives=('Sentiment', lambda x: (x == "Positive").sum()),
                Negatives=('Sentiment', lambda x: (x == "Negative").sum())
            ).reset_index()
            summary['Coll_Rate'] = (summary['CSATs_Collected'] / summary['Calls_Taken'] * 100).round(1)
            summary.columns = ['Agent Name', 'Calls Taken', 'CSAT Collected', 'Positive (4-5)', 'Negative (1-3)', 'Collection %']
            
            st.dataframe(summary.sort_values('Calls Taken', ascending=False), use_container_width=True)
            
            if not valid.empty:
                st.plotly_chart(px.pie(valid, names='Sentiment', hole=0.4, title="Overall Sentiment Split", 
                                       color_discrete_map={'Positive':'#22C55E','Negative':'#EF4444'}), use_container_width=True)
        else:
            st.error("Audit columns ('Agent' and 'Csat') not found in this file.")
    else:
        st.info("👋 Use the sidebar to upload your 'Audit Tracker' file.")

# --- TAB 3: DATA INSPECTOR ---
with tab3:
    st.subheader("System Data Diagnostics")
    c1, c2 = st.columns(2)
    with c1:
        st.write("Performance Data Preview")
        st.dataframe(df_p_raw)
    with c2:
        st.write("Audit Data Preview")
        st.dataframe(df_a_raw)
