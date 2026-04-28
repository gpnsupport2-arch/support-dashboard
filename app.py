import streamlit as st
import pandas as pd
import plotly.express as px
import base64
from streamlit_gsheets import GSheetsConnection

# --- 1. BRANDING & THEME ---
st.set_page_config(page_title="Primarc Pecan | Operations Portal", layout="wide")
BRAND_ORANGE, BRAND_NAVY, BRAND_WHITE = "#F37021", "#101828", "#FFFFFF"

st.markdown(f"""
    <style>
    .stApp {{ background: linear-gradient(180deg, {BRAND_NAVY} 0%, #1D2939 100%); }}
    h1, h2, h3, p, span, label, .stMarkdown {{ color: {BRAND_WHITE} !important; }}
    .logo-container {{ display: flex; justify-content: center; padding: 20px; background-color: rgba(255, 255, 255, 0.05); border-radius: 0 0 20px 20px; margin-bottom: 20px; }}
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
def aht_to_minutes(time_str):
    try:
        if pd.isna(time_str) or str(time_str).strip() == "" or time_str == "0": return 0
        parts = str(time_str).split(':')
        if len(parts) == 3: return int(parts[0])*60 + int(parts[1]) + int(parts[2])/60
        elif len(parts) == 2: return int(parts[0]) + int(parts[1])/60
        return 0
    except: return 0

def find_col(targets, df):
    if df is None: return None
    for t in targets:
        for col in df.columns:
            if t.lower() in str(col).lower(): return col
    return None

# --- 4. DATA LOADER ---
st.sidebar.header("🔌 Data Sources")
def load_data_source(label, key_id):
    st.sidebar.subheader(f"📂 {label}")
    mode = st.sidebar.radio(f"Input for {label}", ["Excel/CSV", "Google Sheet"], key=f"mode_{key_id}")
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

df_s = load_data_source("Call Tracker", "support")

if df_s is not None:
    df_s.columns = [str(c).strip() for c in df_s.columns]
    
    # Map Columns
    agent_col = find_col(['agent', 'executive'], df_s)
    csat_col = find_col(['csat', 'rating'], df_s)
    aht_col = find_col(['aht', 'handling time'], df_s)
    ticket_col = find_col(['ticket', 'id'], df_s)

    # --- 5. TOP KPI ROW ---
    k1, k2, k3, k4 = st.columns(4)
    total_calls = len(df_s)
    k1.metric("Total Calls Received", total_calls)

    # AHT Calculation
    if aht_col:
        df_s['AHT_Mins'] = df_s[aht_col].apply(aht_to_minutes)
        avg_aht = df_s[df_s['AHT_Mins'] > 0]['AHT_Mins'].mean()
        k2.metric("Avg Handling Time", f"{avg_aht:.2f} min")
    
    # CSAT Collection %
    if csat_col:
        valid_csats = df_s[df_s[csat_col].notna() & ~df_s[csat_col].astype(str).str.contains('Unanswered', case=False)]
        csat_total = len(valid_csats)
        coll_rate = (csat_total / total_calls * 100) if total_calls > 0 else 0
        k3.metric("Total CSAT Collected", csat_total)
        k4.metric("CSAT Collection %", f"{coll_rate:.1f}%")

    st.markdown("---")

    # --- 6. TABS ---
    t1, t2 = st.tabs(["📊 Performance Overview", "🕵️ Audit Tracker"])

    with t1:
        if agent_col:
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("Call Volume Share")
                fig1 = px.pie(df_s, names=agent_col, hole=0.4, color_discrete_sequence=px.colors.sequential.Oranges_r)
                fig1.update_layout(paper_bgcolor='rgba(0,0,0,0)', font=dict(color="white"))
                st.plotly_chart(fig1, use_container_width=True)
            with c2:
                st.subheader("Agent Distribution")
                fig_bar = px.bar(df_s[agent_col].value_counts().reset_index(), x='index', y=agent_col, color_discrete_sequence=[BRAND_ORANGE])
                st.plotly_chart(fig_bar, use_container_width=True)

    with t2:
        st.subheader("🕵️ Agent Quality & CSAT Performance")
        if agent_col and csat_col:
            # Sentiment Logic: 4-5 Positive, 3-Below Negative
            def get_sentiment(val):
                v = str(val).lower()
                if any(x in v for x in ['5', '4', 'excellent', 'good']): return "Positive"
                if any(x in v for x in ['1', '2', '3', 'poor', 'average']): return "Negative"
                return "None"

            df_s['Sentiment'] = df_s[csat_col].apply(get_sentiment)

            # Performance Summary Table
            summary = df_s.groupby(agent_col).agg(
                calls_taken=(ticket_col if ticket_col else df_s.columns[0], 'count'),
                csat_collected=('Sentiment', lambda x: (x != "None").sum()),
                positives=('Sentiment', lambda x: (x == "Positive").sum()),
                negatives=('Sentiment', lambda x: (x == "Negative").sum())
            ).reset_index()

            summary['Collection %'] = (summary['csat_collected'] / summary['calls_taken'] * 100).round(1)
            summary.columns = ['Executive Name', 'Calls Taken', 'CSAT Collected', 'Positive (4-5)', 'Negative (<=3)', 'Collection %']
            
            st.dataframe(summary.sort_values(by='Calls Taken', ascending=False), use_container_width=True)

            # Sentiment Chart
            sent_df = df_s[df_s['Sentiment'] != "None"]['Sentiment'].value_counts().reset_index()
            st.plotly_chart(px.pie(sent_df, names='index', values='Sentiment', hole=0.4, 
                                   color_discrete_map={'Positive': '#22C55E', 'Negative': '#EF4444'}), use_container_width=True)

# --- 7. PREDICTIONS ---
st.markdown("---")
st.subheader("🔮 Operations Insights")
p1, p2 = st.columns(2)
with p1:
    st.markdown('<div class="insight-card"><b>📅 Volume Forecast</b><br>Daily trends suggest workload is stable.</div>', unsafe_allow_html=True)
with p2:
    st.markdown('<div class="insight-card"><b>🚀 CSAT Strategy</b><br>Focus on increasing collection rates for agents below 20%.</div>', unsafe_allow_html=True)
