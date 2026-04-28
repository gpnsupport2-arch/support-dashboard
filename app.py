import streamlit as st
import pandas as pd
import plotly.express as px
import base64

# --- 1. BRANDING & THEME ---
st.set_page_config(page_title="Primarc Pecan | Performance Hub", layout="wide")
BRAND_ORANGE, BRAND_NAVY = "#F37021", "#101828"

st.markdown(f"""
    <style>
    .stApp {{ background: linear-gradient(180deg, {BRAND_NAVY} 0%, #1D2939 100%); }}
    h1, h2, h3, p, span, label, .stMarkdown {{ color: white !important; }}
    .logo-container {{ display: flex; justify-content: center; padding: 10px; }}
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

# --- 3. DATA HELPERS ---
def find_col(targets, df):
    for t in targets:
        for col in df.columns:
            if t.lower() in str(col).lower(): return col
    return None

def aht_to_minutes(time_str):
    try:
        if pd.isna(time_str) or str(time_str).strip() == "": return 0
        parts = str(time_str).split(':')
        if len(parts) == 3: return int(parts[0])*60 + int(parts[1]) + int(parts[2])/60
        if len(parts) == 2: return int(parts[0]) + int(parts[1])/60
        return float(time_str)
    except: return 0

# --- 4. DATA LOADING ---
st.sidebar.header("🔌 Data Sources")
file = st.sidebar.file_uploader("Upload 'Mar'26 - Call' File", type=['csv', 'xlsx'])

if file:
    df = pd.read_csv(file) if file.name.endswith('.csv') else pd.read_excel(file)
    df.columns = [str(c).strip() for c in df.columns]

    # Identify Columns
    agent_col = find_col(['agent', 'executive'], df)
    csat_col = find_col(['csat', 'rating'], df)
    aht_col = find_col(['aht', 'handling time'], df)

    # --- 5. TOP KPI ROW ---
    k1, k2, k3, k4 = st.columns(4)
    total_calls = len(df)
    k1.metric("Total Calls Received", total_calls)

    if aht_col:
        df['AHT_Mins'] = df[aht_col].apply(aht_to_minutes)
        avg_aht = df[df['AHT_Mins'] > 0]['AHT_Mins'].mean()
        k2.metric("Avg Handling Time", f"{avg_aht:.2f} min")

    if csat_col:
        # Filter valid CSATs (ignore 'Unanswered')
        valid_csats = df[df[csat_col].notna() & ~df[csat_col].astype(str).str.contains('Unanswered', case=False)]
        csat_count = len(valid_csats)
        k3.metric("Total CSAT Collected", csat_count)
        k4.metric("CSAT Collection %", f"{(csat_count/total_calls*100):.1f}%")

    st.markdown("---")

    # --- 6. EXECUTIVE PERFORMANCE TABLE ---
    if agent_col and csat_col:
        # Sentiment Logic
        def get_sentiment(val):
            v = str(val).lower()
            if any(x in v for x in ['5', '4', 'excellent', 'good']): return "Positive"
            if any(x in v for x in ['1', '2', '3', 'poor', 'average']): return "Negative"
            return "None"

        df['Sentiment'] = df[csat_col].apply(get_sentiment)

        st.subheader("🕵️ Executive Performance Table")
        summary = df.groupby(agent_col).agg(
            calls_taken=('Ticket', 'count'),
            csat_count=('Sentiment', lambda x: (x != "None").sum()),
            positives=('Sentiment', lambda x: (x == "Positive").sum()),
            negatives=('Sentiment', lambda x: (x == "Negative").sum())
        ).reset_index()

        summary['Collection %'] = (summary['csat_count'] / summary['calls_taken'] * 100).round(1)
        summary.columns = ['Executive Name', 'Calls Taken', 'CSAT Collected', 'Positive Ratings', 'Negative Ratings', 'Collection %']
        
        st.dataframe(summary.sort_values(by='Calls Taken', ascending=False), use_container_width=True)
else:
    st.info("Please upload your data file in the sidebar.")
