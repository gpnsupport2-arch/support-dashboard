import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection

# --- 1. SETTINGS & BRANDING ---
st.set_page_config(page_title="Primarc Pecan Operations", layout="wide")
ORANGE, NAVY = "#F37021", "#101828"

st.markdown(f"""
    <style>
    .stApp {{ background: linear-gradient(180deg, {NAVY} 0%, #1D2939 100%); }}
    h1, h2, h3, p, label {{ color: white !important; font-family: 'Segoe UI', sans-serif; }}
    div[data-testid="stMetric"] {{ 
        background-color: #1D2939; border: 1px solid {ORANGE}; 
        border-radius: 12px; padding: 20px; 
    }}
    [data-testid="stMetricValue"] {{ color: {ORANGE} !important; font-size: 32px !important; }}
    .stTabs [aria-selected="true"] {{ background-color: {ORANGE} !important; border-radius: 5px; color: white !important; }}
    /* Styling for the tables to make them white and readable */
    .stDataFrame {{ background-color: white; border-radius: 8px; padding: 5px; }}
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
dfp_raw = load_source("Performance Data", "perf")
dfa_raw = load_source("Audit Data", "audit")

# --- 3. SHARED MONTH FILTER ---
selected_months = []
if dfp_raw is not None:
    dfp_raw['Timestamp'] = pd.to_datetime(dfp_raw['Timestamp'], errors='coerce')
    dfp_raw['Month_Name'] = dfp_raw['Timestamp'].dt.strftime('%B')
    all_months = sorted(dfp_raw['Month_Name'].dropna().unique().tolist())
    selected_months = st.sidebar.multiselect("🗓️ Global Month Slicer", options=all_months, default=all_months)

# --- 4. MAIN DASHBOARD ---
tab1, tab2 = st.tabs(["📊 Performance Overview", "🕵️ Audit Tracker"])

# --- TAB 1: PERFORMANCE OVERVIEW ---
with tab1:
    if dfp_raw is not None:
        dfp = dfp_raw[dfp_raw['Month_Name'].isin(selected_months)].copy() if selected_months else dfp_raw.copy()
        
        st.title("🎧 Support Operations Performance")

        # KPI Row
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Tickets", f"{len(dfp):,}")
        m2.metric("Email Tickets", f"{len(dfp[dfp['Channel'].str.contains('Email', na=False, case=False)]):,}")
        m3.metric("Call Tickets", f"{len(dfp[dfp['Channel'].str.contains('Call', na=False, case=False)]):,}")
        res_count = len(dfp[dfp['Ticket status'].isin(['Closed', 'Resolved'])])
        m4.metric("Resolved/Closed", f"{res_count:,}")

        st.subheader("👨‍💻 Executive Performance & Highlighted Daily Productivity")
        if 'Email Address' in dfp.columns and not dfp.empty:
            # 1. Base Summary
            base_summary = dfp.groupby(['Email Address', 'Channel']).size().unstack(fill_value=0)
            
            # 2. Daily Pivot (Converted to String for Table/JSON safety)
            dfp['Date_Str'] = dfp['Timestamp'].dt.strftime('%d-%b') 
            daily_pivot = dfp.groupby(['Email Address', 'Date_Str']).size().unstack(fill_value=0)
            
            # 3. Merge
            final_perf_table = base_summary.join(daily_pivot, how='left').reset_index()
            
            # --- HIGHLIGHTING LOGIC ---
            def highlight_productivity(s):
                # Colors the background of the date columns to make them stand out
                return ['background-color: #fdf2e9; font-weight: bold' if '-' in str(col) else '' for col in final_perf_table.columns]

            st.dataframe(final_perf_table.style.apply(highlight_productivity, axis=1), use_container_width=True)

        # Charts
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(px.pie(dfp, names='Channel', hole=0.4, title="Segment Split", color_discrete_sequence=[ORANGE, "#444"]), use_container_width=True)
        with c2:
            top_q = dfp['Query type'].value_counts().nlargest(10).reset_index()
            st.plotly_chart(px.bar(top_q, x='index', y='Query type', title="Top Queries", color_discrete_sequence=[ORANGE]), use_container_width=True)
    else:
        st.info("Upload Performance Data to begin.")

# --- TAB 2: AUDIT TRACKER ---
with tab2:
    if dfa_raw is not None:
        dfa = dfa_raw.copy()
        dfa['Created date'] = pd.to_datetime(dfa['Created date'], errors='coerce')
        dfa['Month_Name'] = dfa['Created date'].dt.strftime('%B')
        if selected_months:
            dfa = dfa[dfa['Month_Name'].isin(selected_months)]

        st.title("🕵️ Quality Audit Deep-Dive")
        
        def get_sent(v):
            v = str(v).lower()
            if any(x in v for x in ['5', '4', 'positive']): return "Positive"
            if any(x in v for x in ['1', '2', '3', 'negative']): return "Negative"
            return "No Rating"
        
        dfa['Sentiment'] = dfa['Csat'].apply(get_sent)

        audit_table = dfa.groupby('Executive Name').agg(
            Total_Calls_Taken=('Ticket', 'count'),
            CSAT_Collected=('Sentiment', lambda x: (x != "No Rating").sum()),
            Positive_CSAT=('Sentiment', lambda x: (x == "Positive").sum()),
            Negative_CSAT=('Sentiment', lambda x: (x == "Negative").sum())
        ).reset_index()

        # Fix Collection % logic
        audit_table['Positive % (vs CSAT)'] = (audit_table['Positive_CSAT'] / audit_table['CSAT_Collected'] * 100).fillna(0).round(1).astype(str) + '%'
        audit_table['Collection % (vs Total)'] = (audit_table['CSAT_Collected'] / audit_table['Total_Calls_Taken'] * 100).fillna(0).round(1).astype(str) + '%'

        # Style Audit Table
        st.dataframe(audit_table.style.highlight_max(subset=['Positive_CSAT'], color='#d4edda'), use_container_width=True)
        
        valid = dfa[dfa['Sentiment'] != "No Rating"]
        if not valid.empty:
            st.plotly_chart(px.pie(valid, names='Sentiment', hole=0.5, title="Quality Split", color_discrete_map={'Positive':'#22C55E','Negative':'#EF4444'}), use_container_width=True)
