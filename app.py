import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection

# --- 1. UI BRANDING ---
st.set_page_config(page_title="Primarc Pecan | Performance & Audit", layout="wide")
ORANGE, NAVY = "#F37021", "#101828"

st.markdown(f"""
    <style>
    .stApp {{ background: linear-gradient(180deg, {NAVY} 0%, #1D2939 100%); }}
    h1, h2, h3, p, label {{ color: white !important; }}
    div[data-testid="stMetric"] {{ 
        background-color: #1D2939; border: 1px solid {ORANGE}; 
        border-radius: 12px; padding: 20px; 
    }}
    [data-testid="stMetricValue"] {{ color: {ORANGE} !important; font-size: 32px !important; }}
    .stTabs [aria-selected="true"] {{ background-color: {ORANGE} !important; border-radius: 5px; }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. ENGINE HELPERS ---
def find_col(targets, df):
    if df is None: return None
    cols = {c.strip().lower(): c for c in df.columns}
    for t in targets:
        if t.lower() in cols: return cols[t.lower()]
    return None

# --- 3. DATA LOADING & SIDEBAR FILTERS ---
st.sidebar.title("🚀 Control Panel")

def load_source(label, key_suffix):
    st.sidebar.subheader(f"📂 {label}")
    src = st.sidebar.radio(f"Format: {label}", ["Excel/CSV", "Google Sheet"], key=f"s_{key_suffix}")
    if src == "Google Sheet":
        url = st.sidebar.text_input(f"URL: {label}", key=f"u_{key_suffix}")
        if url:
            try: return st.connection("gsheets", type=GSheetsConnection).read(spreadsheet=url, ttl=0)
            except: return None
    else:
        file = st.sidebar.file_uploader(f"Upload: {label}", type=['csv', 'xlsx'], key=f"f_{key_suffix}")
        if file: return pd.read_csv(file) if file.name.endswith('.csv') else pd.read_excel(file)
    return None

dfp_raw = load_source("Performance Data", "p")
dfa_raw = load_source("Audit Data", "a")

# Create a Shared Filter in Sidebar
selected_months = []
if dfp_raw is not None:
    t_col = find_col(['Timestamp', 'Created date', 'Month'], dfp_raw)
    if t_col:
        # Standardize month names
        dfp_raw['Month_Label'] = pd.to_datetime(dfp_raw[t_col], errors='coerce').dt.strftime('%B')
        months = sorted(dfp_raw['Month_Label'].dropna().unique().tolist())
        selected_months = st.sidebar.multiselect("🗓️ Global Month Filter", options=months, default=months)

# --- 4. MAIN DASHBOARD ---
tab1, tab2 = st.tabs(["📊 Performance Overview", "🕵️ Audit Tracker"])

# --- TAB 1: PERFORMANCE OVERVIEW ---
with tab1:
    if dfp_raw is not None:
        # Filter data based on sidebar
        dfp = dfp_raw[dfp_raw['Month_Label'].isin(selected_months)] if selected_months else dfp_raw
        
        # Mapping
        chan_col = find_col(['Channel'], dfp)
        stat_col = find_col(['Ticket status'], dfp)
        cat_col = find_col(['Query type', 'Category'], dfp)
        email_addr = find_col(['Email Address'], dfp)

        st.title("🎧 Support Operations")
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Tickets", len(dfp))
        if chan_col:
            m2.metric("Email Tickets", len(dfp[dfp[chan_col].str.contains('Email', na=False, case=False)]))
            m3.metric("Call Tickets", len(dfp[dfp[chan_col].str.contains('Call', na=False, case=False)]))
        if stat_col:
            res = len(dfp[dfp[stat_col].isin(['Closed', 'Resolved'])])
            m4.metric("Resolved/Closed", res)

        st.subheader("📧 Productivity per Email & Segment")
        if email_addr and chan_col:
            prod_table = dfp.groupby([email_addr, chan_col]).size().unstack(fill_value=0).reset_index()
            st.dataframe(prod_table, use_container_width=True)

        c1, c2 = st.columns(2)
        with c1:
            if chan_col:
                st.plotly_chart(px.pie(dfp, names=chan_col, hole=0.4, title="Segment Contribution", color_discrete_sequence=[ORANGE, "#444"]), use_container_width=True)
        with c2:
            if cat_col:
                st.plotly_chart(px.bar(dfp[cat_col].value_counts().head(10), title="Top Query Categories", color_discrete_sequence=[ORANGE]), use_container_width=True)
    else:
        st.info("Please upload Performance Data in the sidebar.")

# --- TAB 2: AUDIT TRACKER ---
with tab2:
    if dfa_raw is not None:
        # Use same month filter if possible
        dfa = dfa_raw.copy()
        t_col_a = find_col(['Timestamp', 'Month', 'Created date'], dfa)
        if t_col_a and selected_months:
            dfa['Month_Label'] = pd.to_datetime(dfa[t_col_a], errors='coerce').dt.strftime('%B')
            dfa = dfa[dfa['Month_Label'].isin(selected_months)]

        exec_col = find_col(['Executive Name', 'Agent'], dfa)
        csat_col = find_col(['Csat'], dfa)
        
        st.title("🕵️ Quality Metrics")
        
        if exec_col and csat_col:
            def get_sent(v):
                v = str(v).lower()
                if any(x in v for x in ['5', '4', 'positive']): return "Positive"
                if any(x in v for x in ['1', '2', '3', 'negative']): return "Negative"
                return "No Rating"
            
            dfa['Sentiment'] = dfa[csat_col].apply(get_sent)
            
            # --- THE FINAL REQUESTED TABLE ---
            summary = dfa.groupby(exec_col).agg(
                Total_Calls_Taken=(dfa.columns[0], 'count'),
                CSAT_Collected=('Sentiment', lambda x: (x != "No Rating").sum()),
                Positive_CSAT=('Sentiment', lambda x: (x == "Positive").sum()),
                Negative_CSAT=('Sentiment', lambda x: (x == "Negative").sum())
            ).reset_index()

            # % Calculations
            summary['Positive % (vs Collected)'] = (summary['Positive_CSAT'] / summary['CSAT_Collected'] * 100).fillna(0).round(1).astype(str) + '%'
            summary['Collection % (vs Total)'] = (summary['CSAT_Collected'] / summary['Total_Calls_Taken'] * 100).fillna(0).round(1).astype(str) + '%'

            st.dataframe(summary, use_container_width=True)
            
            valid = dfa[dfa['Sentiment'] != "No Rating"]
            if not valid.empty:
                st.plotly_chart(px.pie(valid, names='Sentiment', hole=0.4, title="Overall Quality Split", color_discrete_map={'Positive':'#22C55E','Negative':'#EF4444'}), use_container_width=True)
    else:
        st.info("Please upload Audit Data in the sidebar.")
