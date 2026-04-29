import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection

# --- 1. SETTINGS & BRANDING ---
st.set_page_config(page_title="Primarc Pecan | Executive Operations", layout="wide")
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
    .stTabs [aria-selected="true"] {{ background-color: {ORANGE} !important; border-radius: 5px; color: white !important; }}
    .stDataFrame {{ background-color: white; border-radius: 8px; }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA LOADING HELPERS ---
def load_source(label, key_id):
    st.sidebar.subheader(f"📂 {label}")
    src = st.sidebar.radio(f"Source: {label}", ["Upload File", "Google Sheet"], key=f"src_{key_id}")
    if src == "Google Sheet":
        url = st.sidebar.text_input(f"Sheet URL: {label}", key=f"url_{key_id}")
        if url:
            try: return st.connection("gsheets", type=GSheetsConnection).read(spreadsheet=url, ttl=0)
            except: return None
    else:
        file = st.sidebar.file_uploader(f"Upload: {label}", type=['csv', 'xlsx'], key=f"f_{key_id}")
        if file: return pd.read_csv(file) if file.name.endswith('.csv') else pd.read_excel(file)
    return None

st.sidebar.title("🚀 Control Center")
dfp_raw = load_source("Performance (CS Productivity)", "perf")
dfa_raw = load_source("Audit (Call Tracker)", "audit")

# --- 3. SHARED FILTERS ---
selected_months = []
if dfp_raw is not None:
    # Convert Timestamp to Month Name for the Slicer
    dfp_raw['Timestamp'] = pd.to_datetime(dfp_raw['Timestamp'], errors='coerce')
    dfp_raw['Month_Name'] = dfp_raw['Timestamp'].dt.strftime('%B')
    all_months = sorted(dfp_raw['Month_Name'].dropna().unique().tolist())
    selected_months = st.sidebar.multiselect("🗓️ Global Month Slicer", options=all_months, default=all_months)

# --- 4. MAIN DASHBOARD ---
tab1, tab2 = st.tabs(["📊 Performance Overview", "🕵️ Audit Tracker"])

# --- TAB 1: PERFORMANCE ---
with tab1:
    if dfp_raw is not None:
        # Filter by selected month
        dfp = dfp_raw[dfp_raw['Month_Name'].isin(selected_months)] if selected_months else dfp_raw
        
        st.title("🎧 Operations Performance")

        # KPI Row
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Ticket Count", f"{len(dfp):,}")
        
        # Email vs Call Count
        email_tickets = len(dfp[dfp['Channel'].str.contains('Email', na=False, case=False)])
        call_tickets = len(dfp[dfp['Channel'].str.contains('Call', na=False, case=False)])
        m2.metric("Email Ticket Count", f"{email_tickets:,}")
        m3.metric("Call Ticket Count", f"{call_tickets:,}")
        
        # Resolved/Closed
        res_closed = len(dfp[dfp['Ticket status'].isin(['Closed', 'Resolved'])])
        m4.metric("Resolved & Closed", f"{res_closed:,}")

        # NEW: Daily Productivity Pivot
        st.subheader("🗓️ Daily Productivity by Email Address")
        dfp['Date'] = dfp['Timestamp'].dt.date
        if 'Email Address' in dfp.columns:
            daily_pivot = dfp.groupby(['Date', 'Email Address']).size().unstack(fill_value=0).T
            st.dataframe(daily_pivot, use_container_width=True)

        # Charts
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(px.pie(dfp, names='Channel', hole=0.4, title="Contribution by Segment", 
                                  color_discrete_sequence=[ORANGE, "#0047AB"]), use_container_width=True)
        with c2:
            top_q = dfp['Query type'].value_counts().nlargest(10).reset_index()
            st.plotly_chart(px.bar(top_q, x='index', y='Query type', title="Top Query Categories", 
                                  color_discrete_sequence=[ORANGE]), use_container_width=True)
            
        # Segment Contribution Table
        st.subheader("👨‍💻 Productivity & Segment Contribution")
        segment_table = dfp.groupby(['Email Address', 'Channel']).size().unstack(fill_value=0).reset_index()
        st.dataframe(segment_table, use_container_width=True)
    else:
        st.info("Please upload Performance Data in the Sidebar.")

# --- TAB 2: AUDIT TRACKER ---
with tab2:
    if dfa_raw is not None:
        dfa = dfa_raw.copy()
        
        # Sync with Month Filter
        dfa['Created date'] = pd.to_datetime(dfa['Created date'], errors='coerce')
        dfa['Month_Name'] = dfa['Created date'].dt.strftime('%B')
        if selected_months:
            dfa = dfa[dfa['Month_Name'].isin(selected_months)]

        st.title("🕵️ Quality Audit Tracker")
        st.metric("Total Calls Audited", len(dfa))

        # Sentiment Logic (4-5 = Positive)
        def get_sentiment(v):
            v = str(v).lower()
            if any(x in v for x in ['5', '4', 'positive']): return "Positive"
            if any(x in v for x in ['1', '2', '3', 'negative']): return "Negative"
            return "No Rating"
        
        dfa['Sentiment'] = dfa['Csat'].apply(get_sentiment)

        # TABLE: Executive Name, Total Calls, CSAT Collected, Pos, Neg, Percentages
        audit_summary = dfa.groupby('Executive Name').agg(
            Total_Calls_Taken=('Ticket', 'count'),
            CSAT_Collected=('Sentiment', lambda x: (x != "No Rating").sum()),
            Positive_CSAT=('Sentiment', lambda x: (x == "Positive").sum()),
            Negative_CSAT=('Sentiment', lambda x: (x == "Negative").sum())
        ).reset_index()

        # Percentages
        audit_summary['Positive % (vs CSAT)'] = (audit_summary['Positive_CSAT'] / audit_summary['CSAT_Collected'] * 100).fillna(0).round(1).astype(str) + '%'
        audit_summary['Collection % (vs Total)'] = (audit_summary['CSAT_Collected'] / audit_summary['Total_Calls_Taken'] * 100).fillna(0).round(1).astype(str) + '%'

        st.subheader("Executive Quality Metrics")
        st.dataframe(audit_summary, use_container_width=True)
        
        # Visual Split
        valid_csat = dfa[dfa['Sentiment'] != "No Rating"]
        if not valid_csat.empty:
            st.plotly_chart(px.pie(valid_csat, names='Sentiment', hole=0.5, title="CSAT Quality Split", 
                                  color_discrete_map={'Positive': '#22C55E', 'Negative': '#EF4444'}), use_container_width=True)
    else:
        st.info("Please upload Audit Data in the Sidebar.")
