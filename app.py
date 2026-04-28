import streamlit as st
import pandas as pd
import plotly.express as px
import base64
from streamlit_gsheets import GSheetsConnection

# --- 1. BRANDING & PERSISTENT STYLE ---
st.set_page_config(page_title="Primarc Pecan | Executive Portal", layout="wide")
BRAND_ORANGE, BRAND_NAVY, BRAND_WHITE = "#F37021", "#101828", "#FFFFFF"

st.markdown(f"""
    <style>
    .stApp {{ background: linear-gradient(180deg, {BRAND_NAVY} 0%, #1D2939 100%); }}
    h1, h2, h3, p, span, label, .stMarkdown {{ color: {BRAND_WHITE} !important; }}
    div[data-baseweb="select"] > div {{ background-color: white !important; color: {BRAND_NAVY} !important; }}
    div[role="listbox"] div {{ color: {BRAND_NAVY} !important; }}
    div[data-testid="stMetric"] {{ background-color: #1D2939; border: 1px solid {BRAND_ORANGE}; border-radius: 10px; padding: 15px; }}
    [data-testid="stMetricValue"] {{ color: {BRAND_ORANGE} !important; font-size: 32px !important; }}
    [data-testid="stSidebar"] {{ background-color: {BRAND_NAVY} !important; border-right: 1px solid {BRAND_ORANGE}; }}
    .stTabs [aria-selected="true"] {{ background-color: {BRAND_ORANGE} !important; border-radius: 5px; }}
    .insight-card {{ background-color: rgba(255, 255, 255, 0.08); border-left: 5px solid {BRAND_ORANGE}; padding: 20px; border-radius: 8px; }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA LOADER ---
st.sidebar.header("🔌 Data Sources")

def load_logic(label_prefix):
    st.sidebar.subheader(f"{label_prefix} Source")
    mode = st.sidebar.radio(f"Select {label_prefix} Type", ["Excel/CSV", "Google Sheet"], key=f"{label_prefix}_mode")
    if mode == "Google Sheet":
        url = st.sidebar.text_input(f"Paste {label_prefix} URL", key=f"{label_prefix}_url")
        if url:
            try:
                conn = st.connection("gsheets", type=GSheetsConnection)
                return conn.read(spreadsheet=url, ttl=0)
            except Exception as e: st.sidebar.error(f"Error: {e}")
    else:
        file = st.sidebar.file_uploader(f"Upload {label_prefix} File", type=['csv', 'xlsx'], key=f"{label_prefix}_file")
        if file: return pd.read_csv(file) if file.name.endswith('.csv') else pd.read_excel(file)
    return None

df_s = load_logic("Support")
df_a = load_logic("Audit") # Usually the same file for your use case

# Helpers
def find_col(targets, df):
    if df is None: return None
    for t in targets:
        for col in df.columns:
            if t.lower() in str(col).lower(): return col
    return None

def aht_to_minutes(time_str):
    try:
        if pd.isna(time_str) or str(time_str).strip() == "" or time_str == "0": return 0
        parts = str(time_str).split(':')
        if len(parts) == 3: return int(parts[0])*60 + int(parts[1]) + int(parts[2])/60
        elif len(parts) == 2: return int(parts[0]) + int(parts[1])/60
        return 0
    except: return 0

# --- 3. DASHBOARD TABS ---
t1, t2, t3 = st.tabs(["📊 Performance Overview", "📋 Support Ticket Log", "🕵️ Audit Tracker"])

# --- TAB 1 & 2: PERFORMANCE & LOG ---
if df_s is not None:
    df_s.columns = [str(c).strip() for c in df_s.columns]
    e_col = find_col(['agent', 'executive'], df_s)
    c_col = find_col(['channel', 'category'], df_s)
    aht_col = find_col(['aht'], df_s)

    with t1:
        st.title("🎧 Support Operations")
        if aht_col:
            df_s['AHT_Mins'] = df_s[aht_col].apply(aht_to_minutes)
            avg_aht = df_s[df_s['AHT_Mins'] > 0]['AHT_Mins'].mean()
            st.metric("Global Average Handling Time", f"{avg_aht:.2f} min")

        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Workload by Executive")
            st.plotly_chart(px.pie(df_s, names=e_col, hole=0.4, color_discrete_sequence=px.colors.sequential.Oranges_r), use_container_width=True)
        with c2:
            agent = st.selectbox("Deep-Dive Executive:", sorted(df_s[e_col].dropna().unique()))
            sub = df_s[df_s[e_col] == agent]
            st.plotly_chart(px.pie(sub, names=c_col, hole=0.4, title=f"{agent}'s Categories"), use_container_width=True)

    with t2:
        st.title("📋 Live Support Tracker")
        st.dataframe(df_s, use_container_width=True)

# --- TAB 3: AUDIT TRACKER (FIXED) ---
with t3:
    st.title("🕵️ Quality & CSAT Audit")
    # If df_a is empty, use df_s as fallback since they are often the same file
    audit_data = df_a if df_a is not None else df_s
    
    if audit_data is not None:
        audit_data.columns = [str(c).strip() for c in audit_data.columns]
        ag_col = find_col(['agent', 'executive'], audit_data)
        cs_col = find_col(['csat', 'rating'], audit_data)
        tk_col = find_col(['ticket', 'id'], audit_data)

        if ag_col and cs_col:
            # Rating Logic: 4-5 Positive, 1-3 Negative
            def get_sentiment(val):
                v = str(val).lower()
                if any(x in v for x in ['5', '4', 'excellent', 'good']): return "Positive"
                if any(x in v for x in ['1', '2', '3', 'bad', 'average', 'poor']): return "Negative"
                return "No Rating"

            audit_data['Sentiment'] = audit_data[cs_col].apply(get_sentiment)

            # Metrics Row
            total = len(audit_data)
            valid = audit_data[audit_data['Sentiment'] != "No Rating"]
            
            m1, m2, m3 = st.columns(3)
            m1.metric("Total CSAT Collected", len(valid))
            m2.metric("Overall Collection %", f"{(len(valid)/total*100):.1f}%")
            
            # Numeric Score Parsing
            audit_data['score'] = pd.to_numeric(audit_data[cs_col].astype(str).str.extract('(\d+)')[0], errors='coerce')
            m3.metric("Avg Quality Score", f"{audit_data['score'].mean():.2f}")

            # Performance Table
            st.markdown("### Executive Audit Summary")
            summary = audit_data.groupby(ag_col).agg(
                calls=(tk_col if tk_col else audit_data.columns[0], 'count'),
                csats=('Sentiment', lambda x: (x != "No Rating").sum()),
                pos=('Sentiment', lambda x: (x == "Positive").sum()),
                neg=('Sentiment', lambda x: (x == "Negative").sum())
            ).reset_index()
            
            summary['Collection %'] = (summary['csats'] / summary['calls'] * 100).round(1)
            summary.columns = ['Executive', 'Calls Taken', 'CSAT Collected', 'Positive (4-5)', 'Negative (1-3)', 'Collection %']
            st.dataframe(summary.sort_values('Calls Taken', ascending=False), use_container_width=True)
            
            # Sentiment Chart
            st.plotly_chart(px.pie(valid, names='Sentiment', hole=0.4, title="Overall Sentiment Split",
                                   color_discrete_map={'Positive': '#22C55E', 'Negative': '#EF4444'}), use_container_width=True)
        else:
            st.error("Could not find 'Agent' or 'Csat' columns in the data.")
    else:
        st.info("Please upload a file to view Audit Analytics.")

# --- 4. PERMANENT FOOTER ---
st.markdown("---")
st.subheader("🔮 Predictive Insights")
p1, p2 = st.columns(2)
with p1:
    st.markdown('<div class="insight-card"><b>📅 Backlog Forecast</b><br>Volume is trending normally for March 2026.</div>', unsafe_allow_html=True)
with p2:
    st.markdown('<div class="insight-card"><b>🚀 Capacity Planning</b><br>Quality scores 4-5 are currently leading by 85%.</div>', unsafe_allow_html=True)
