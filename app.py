import streamlit as st
import pandas as pd
import plotly.express as px
import base64
from streamlit_gsheets import GSheetsConnection

# --- 1. BRANDING & THEME ---
st.set_page_config(page_title="Primarc Pecan | Executive Portal", layout="wide")
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
    [data-testid="stSidebar"] {{ background-color: {BRAND_NAVY} !important; border-right: 1px solid {BRAND_ORANGE}; }}
    .stTabs [aria-selected="true"] {{ background-color: {BRAND_ORANGE} !important; border-radius: 5px; }}
    .insight-card {{ background-color: rgba(255, 255, 255, 0.08); border-left: 5px solid {BRAND_ORANGE}; padding: 20px; border-radius: 8px; }}
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
        if pd.isna(time_str) or str(time_str).strip() == "" or str(time_str) == "0": return 0
        parts = str(time_str).split(':')
        if len(parts) == 3: return int(parts[0])*60 + int(parts[1]) + int(parts[2])/60
        elif len(parts) == 2: return int(parts[0]) + int(parts[1])/60
        return 0
    except: return 0

# --- 4. DATA LOADER ---
st.sidebar.header("🔌 Data Sources")
def load_data(label):
    st.sidebar.subheader(f"{label} Source")
    mode = st.sidebar.radio(f"Select {label} Type", ["Excel/CSV", "Google Sheet"], key=f"{label}_m")
    if mode == "Google Sheet":
        url = st.sidebar.text_input(f"Paste {label} URL", key=f"{label}_u")
        if url:
            try:
                conn = st.connection("gsheets", type=GSheetsConnection)
                return conn.read(spreadsheet=url, ttl=0)
            except: return None
    else:
        file = st.sidebar.file_uploader(f"Upload {label} File", type=['csv', 'xlsx'], key=f"{label}_f")
        if file: return pd.read_csv(file) if file.name.endswith('.csv') else pd.read_excel(file)
    return None

df_main = load_data("Call/Audit")

# --- 5. MAIN DASHBOARD ---
if df_main is not None:
    df_main.columns = [str(c).strip() for c in df_main.columns]
    
    # Core Mapping
    agent_col = find_col(['agent', 'executive'], df_main)
    csat_col = find_col(['csat', 'rating'], df_main)
    aht_col = find_col(['aht'], df_main)
    cat_col = find_col(['category'], df_main)
    tk_col = find_col(['ticket', 'id'], df_main)

    t1, t2, t3 = st.tabs(["📊 Performance Overview", "📋 Call Tracker Log", "🕵️ Audit Tracker"])

    # --- TAB 1: PERFORMANCE ---
    with t1:
        st.title("🎧 Operations Performance")
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Calls", len(df_main))
        
        if aht_col:
            df_main['AHT_Mins'] = df_main[aht_col].apply(aht_to_minutes)
            avg_aht = df_main[df_main['AHT_Mins'] > 0]['AHT_Mins'].mean()
            m2.metric("Avg Handling Time", f"{avg_aht:.2f} min")
        
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Workload Share")
            if agent_col:
                st.plotly_chart(px.pie(df_main, names=agent_col, hole=0.4, color_discrete_sequence=px.colors.sequential.Oranges_r), use_container_width=True)
        with c2:
            st.subheader("Category Breakdown")
            if cat_col:
                st.plotly_chart(px.bar(df_main[cat_col].value_counts().reset_index(), x='index', y=cat_col, color_discrete_sequence=[BRAND_ORANGE]), use_container_width=True)

    # --- TAB 2: DATA LOG ---
    with t2:
        st.title("📋 Call Tracker Data")
        st.dataframe(df_main, use_container_width=True)

    # --- TAB 3: AUDIT TRACKER (FULLY RESTORED) ---
    with t3:
        st.title("🕵️ Executive Quality Audit")
        if agent_col and csat_col:
            # Logic: 4-5 Pos, 1-3 Neg
            def get_sentiment(val):
                v = str(val).lower()
                if any(x in v for x in ['5', '4', 'excellent', 'good']): return "Positive"
                if any(x in v for x in ['1', '2', '3', 'bad', 'poor', 'average']): return "Negative"
                return "No Rating"

            df_main['Sentiment'] = df_main[csat_col].apply(get_sentiment)
            valid_csats = df_main[df_main['Sentiment'] != "No Rating"]
            
            # Audit KPIs
            k1, k2, k3 = st.columns(3)
            k1.metric("CSATs Collected", len(valid_csats))
            k2.metric("Collection Rate", f"{(len(valid_csats)/len(df_main)*100):.1f}%")
            
            # Score Calculation (Extract digits)
            df_main['Score'] = pd.to_numeric(df_main[csat_col].astype(str).str.extract('(\d+)')[0], errors='coerce')
            k3.metric("Avg Quality Score", f"{df_main['Score'].mean():.2f}")

            # Performance Table
            st.subheader("Agent-wise CSAT Performance")
            audit_summary = df_main.groupby(agent_col).agg(
                Calls=(df_main.columns[0], 'count'),
                CSAT_Count=('Sentiment', lambda x: (x != "No Rating").sum()),
                Positive=('Sentiment', lambda x: (x == "Positive").sum()),
                Negative=('Sentiment', lambda x: (x == "Negative").sum())
            ).reset_index()
            
            audit_summary['Collection %'] = (audit_summary['CSAT_Count'] / audit_summary['Calls'] * 100).round(1)
            audit_summary.columns = ['Executive Name', 'Calls Taken', 'CSAT Collected', 'Positive (4-5)', 'Negative (1-3)', 'Collection %']
            
            st.dataframe(audit_summary.sort_values('Calls Taken', ascending=False), use_container_width=True)
            
            # Sentiment Split Pie
            st.plotly_chart(px.pie(valid_csats, names='Sentiment', hole=0.4, title="Overall Sentiment Split",
                                   color_discrete_map={'Positive':'#22C55E','Negative':'#EF4444'}), use_container_width=True)
        else:
            st.warning("Ensure your file has 'Agent' and 'Csat' columns for the Audit Tracker.")

    st.markdown("---")
    st.subheader("🔮 Operations Insights")
    p1, p2 = st.columns(2)
    with p1: st.markdown('<div class="insight-card"><b>📅 Forecast:</b> March 2026 volume is trending stable.</div>', unsafe_allow_html=True)
    with p2: st.markdown('<div class="insight-card"><b>🚀 Focus:</b> Target a 30% CSAT collection rate.</div>', unsafe_allow_html=True)

else:
    st.info("👋 Welcome! Please upload your Tracker file in the sidebar to populate the portal.")
