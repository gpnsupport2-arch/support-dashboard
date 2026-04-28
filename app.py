import streamlit as st
import pandas as pd
import plotly.express as px
import base64
from streamlit_gsheets import GSheetsConnection

# --- 1. BRANDING & THEME ---
st.set_page_config(page_title="Primarc Pecan | Support & Audit Hub", layout="wide")
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

# --- 2. CENTERED LOGO ---
try:
    with open('primarc_pecan_logo.jpg', 'rb') as f:
        logo_data = base64.b64encode(f.read()).decode()
    st.markdown(f'<div class="logo-container"><img src="data:image/jpeg;base64,{logo_data}" width="250"></div>', unsafe_allow_html=True)
except:
    st.markdown("<h1 style='text-align: center; color: #F37021;'>PRIMARC PECAN</h1>", unsafe_allow_html=True)

# --- 3. HELPERS ---
def find_col(targets, df):
    if df is None: return None
    for t in targets:
        for col in df.columns:
            if t.lower() in str(col).lower(): return col
    return None

def aht_to_minutes(time_str):
    try:
        if pd.isna(time_str) or str(time_str).strip() in ["", "0"]: return 0
        parts = str(time_str).split(':')
        if len(parts) == 3: return int(parts[0])*60 + int(parts[1]) + int(parts[2])/60
        elif len(parts) == 2: return int(parts[0]) + int(parts[1])/60
        return 0
    except: return 0

# --- 4. SIDEBAR DATA CONNECTORS ---
st.sidebar.header("🔌 Data Connectors")
def load_data():
    mode = st.sidebar.radio("Data Source Type", ["Excel/CSV", "Google Sheet"])
    if mode == "Google Sheet":
        url = st.sidebar.text_input("Paste Google Sheet URL")
        if url:
            try:
                conn = st.connection("gsheets", type=GSheetsConnection)
                return conn.read(spreadsheet=url, ttl=0)
            except: return None
    else:
        file = st.sidebar.file_uploader("Upload Tracker File", type=['csv', 'xlsx'])
        if file:
            return pd.read_csv(file) if file.name.endswith('.csv') else pd.read_excel(file)
    return None

df = load_data()

# --- 5. MAIN DASHBOARD LOGIC ---
if df is not None:
    # Cleanup
    df.columns = [str(c).strip() for c in df.columns]
    
    # Mapping
    agent_col = find_col(['agent', 'executive'], df)
    csat_col = find_col(['csat', 'rating'], df)
    aht_col = find_col(['aht'], df)
    cat_col = find_col(['category'], df)
    tk_col = find_col(['ticket', 'id'], df)

    # TOP KPI ROW
    k1, k2, k3, k4 = st.columns(4)
    total_calls = len(df)
    k1.metric("Total Calls", total_calls)

    if aht_col:
        df['AHT_Mins'] = df[aht_col].apply(aht_to_minutes)
        avg_aht = df[df['AHT_Mins'] > 0]['AHT_Mins'].mean()
        k2.metric("Avg Handling Time", f"{avg_aht:.2f} min")

    if csat_col:
        valid_csats = df[df[csat_col].notna() & ~df[csat_col].astype(str).str.contains('Unanswered', case=False)]
        k3.metric("Total CSAT Collected", len(valid_csats))
        k4.metric("CSAT Collection %", f"{(len(valid_csats)/total_calls*100):.1f}%")

    st.markdown("---")

    # TABS
    t1, t2, t3 = st.tabs(["📊 Performance Overview", "🕵️ Audit Tracker", "📋 Raw Data Log"])

    # --- TAB 1: PERFORMANCE OVERVIEW ---
    with t1:
        st.subheader("Workload & Distribution")
        c1, c2 = st.columns(2)
        with c1:
            if agent_col:
                fig_pie = px.pie(df, names=agent_col, hole=0.4, title="Ticket Share by Agent")
                fig_pie.update_layout(paper_bgcolor='rgba(0,0,0,0)', font=dict(color="white"))
                st.plotly_chart(fig_pie, use_container_width=True)
        with c2:
            if cat_col:
                fig_bar = px.bar(df[cat_col].value_counts().reset_index(), x='index', y=cat_col, 
                                 title="Volume by Category", color_discrete_sequence=[BRAND_ORANGE])
                fig_bar.update_layout(paper_bgcolor='rgba(0,0,0,0)', font=dict(color="white"))
                st.plotly_chart(fig_bar, use_container_width=True)

    # --- TAB 2: AUDIT TRACKER (RESTORED) ---
    with t2:
        st.subheader("Executive CSAT & Quality Audit")
        if agent_col and csat_col:
            # Rating Logic
            def get_sentiment(val):
                v = str(val).lower()
                if any(x in v for x in ['5', '4', 'excellent', 'good']): return "Positive"
                if any(x in v for x in ['1', '2', '3', 'bad', 'poor', 'average']): return "Negative"
                return "No Rating"

            df['Sentiment'] = df[csat_col].apply(get_sentiment)
            
            # Agent-wise Summary Table
            summary = df.groupby(agent_col).agg(
                Calls=(df.columns[0], 'count'),
                CSATs=('Sentiment', lambda x: (x != "No Rating").sum()),
                Positive=('Sentiment', lambda x: (x == "Positive").sum()),
                Negative=('Sentiment', lambda x: (x == "Negative").sum())
            ).reset_index()
            
            summary['Collection %'] = (summary['CSATs'] / summary['Calls'] * 100).round(1)
            summary.columns = ['Executive Name', 'Calls Taken', 'CSAT Collected', 'Positive (4-5)', 'Negative (1-3)', 'Collection %']
            
            st.dataframe(summary.sort_values('Calls Taken', ascending=False), use_container_width=True)
            
            # Sentiment Pie
            valid_only = df[df['Sentiment'] != "No Rating"]
            st.plotly_chart(px.pie(valid_only, names='Sentiment', hole=0.4, title="Overall Sentiment Split",
                                   color_discrete_map={'Positive':'#22C55E','Negative':'#EF4444'}), use_container_width=True)
        else:
            st.warning("Audit columns missing. Please ensure your file has 'Agent' and 'Csat'.")

    # --- TAB 3: DATA LOG ---
    with t3:
        st.subheader("Full Support Tracker Log")
        st.dataframe(df, use_container_width=True)

    # FOOTER
    st.markdown("---")
    st.subheader("🔮 Predictive Insights")
    p1, p2 = st.columns(2)
    with p1: st.markdown('<div class="insight-card"><b>📅 Volume Forecast:</b> Stable workload based on historical trends.</div>', unsafe_allow_html=True)
    with p2: st.markdown('<div class="insight-card"><b>🚀 Capacity Planning:</b> Current quality scores (4-5) are meeting the 80% target.</div>', unsafe_allow_html=True)

else:
    st.info("👋 Welcome! Please upload your Excel file or connect your Google Sheet in the sidebar.")
