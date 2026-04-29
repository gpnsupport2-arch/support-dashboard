import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection

# --- 1. CONFIGURATION & BRANDING (Primarc Pecan Theme) ---
st.set_page_config(page_title="Primarc Pecan | Master Ops Dashboard", layout="wide")
ORANGE, NAVY = "#F37021", "#101828"

st.markdown(f"""
    <style>
    .stApp {{ background: linear-gradient(180deg, {NAVY} 0%, #1D2939 100%); }}
    h1, h2, h3, p, label, .stMarkdown {{ color: white !important; font-family: 'Segoe UI', sans-serif; }}
    div[data-testid="stMetric"] {{ 
        background-color: #1D2939; border: 1px solid {ORANGE}; 
        border-radius: 12px; padding: 20px; box-shadow: 4px 4px 15px rgba(0,0,0,0.5);
    }}
    [data-testid="stMetricValue"] {{ color: {ORANGE} !important; font-size: 36px !important; font-weight: 800 !important; }}
    .stTabs [aria-selected="true"] {{ background-color: {ORANGE} !important; border-radius: 8px; color: white !important; font-weight: bold; }}
    .stDataFrame {{ background-color: white; border-radius: 8px; }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. THE ENGINE (Helper Functions) ---
def find_col(targets, df):
    """Fuzzy column matching to handle case and spaces."""
    if df is None: return None
    cols = {c.strip().lower(): c for c in df.columns}
    for t in targets:
        if t.lower() in cols: return cols[t.lower()]
    return None

def get_sentiment(v):
    """Maps 4-5 stars to Positive and 1-3 to Negative."""
    v = str(v).lower()
    if any(x in v for x in ['5', '4', 'excellent', 'good', 'positive']): return "Positive"
    if any(x in v for x in ['1', '2', '3', 'poor', 'bad', 'negative']): return "Negative"
    return "Not Rated"

# --- 3. SIDEBAR (Data Connectors & Global Filter) ---
st.sidebar.title("🛠️ Control Center")

def load_data(label, key_id):
    st.sidebar.subheader(f"📂 {label}")
    src = st.sidebar.radio(f"Select Source: {label}", ["Upload File", "Google Sheet"], key=f"src_{key_id}")
    if src == "Google Sheet":
        url = st.sidebar.text_input(f"Sheet URL: {label}", key=f"url_{key_id}")
        if url:
            try: return st.connection("gsheets", type=GSheetsConnection).read(spreadsheet=url, ttl=0)
            except: return None
    else:
        file = st.sidebar.file_uploader(f"Upload: {label}", type=['csv', 'xlsx'], key=f"f_{key_id}")
        if file: return pd.read_csv(file) if file.name.endswith('.csv') else pd.read_excel(file)
    return None

df_p_raw = load_data("Performance Tracker (CS Productivity)", "perf")
df_a_raw = load_data("Audit Tracker (Call Tracker)", "audit")

# Global Month Filter logic
selected_months = []
if df_p_raw is not None:
    t_col = find_col(['Timestamp', 'Created date'], df_p_raw)
    if t_col:
        df_p_raw['Month_Name'] = pd.to_datetime(df_p_raw[t_col], errors='coerce').dt.strftime('%B')
        all_months = sorted(df_p_raw['Month_Name'].dropna().unique().tolist())
        selected_months = st.sidebar.multiselect("🗓️ Global Month Slicer", options=all_months, default=all_months)

# --- 4. TABS ---
tab1, tab2 = st.tabs(["📊 Performance Overview", "🕵️ Audit Tracker"])

# --- PERFORMANCE OVERVIEW (Tab 1) ---
with tab1:
    if df_p_raw is not None:
        # Filter Logic
        dfp = df_p_raw[df_p_raw['Month_Name'].isin(selected_months)] if selected_months else df_p_raw
        
        # Columns Mapping
        chan_col = find_col(['Channel'], dfp)
        stat_col = find_col(['Ticket status'], dfp)
        cat_col = find_col(['Query type', 'Category'], dfp)
        mail_col = find_col(['Email Address', 'Agent'], dfp)
        time_col = find_col(['Timestamp', 'Created date'], dfp)

        st.title("🎧 Operations Performance Overview")

        # KPI Metrics
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Ticket Count", f"{len(dfp):,}")
        if chan_col:
            m2.metric("Email Tickets", f"{len(dfp[dfp[chan_col].str.contains('Email', na=False, case=False)]):,}")
            m3.metric("Call Tickets", f"{len(dfp[dfp[chan_col].str.contains('Call', na=False, case=False)]):,}")
        if stat_col:
            resolved = len(dfp[dfp[stat_col].isin(['Closed', 'Resolved'])])
            m4.metric("Resolved & Closed", f"{resolved:,}")

        # NEW: Daily Productivity Pivot
        st.subheader("🗓️ Daily Productivity by Email Address")
        if mail_col and time_col:
            dfp['Date'] = pd.to_datetime(dfp[time_col], errors='coerce').dt.date
            daily_pivot = dfp.groupby(['Date', mail_col]).size().unstack(fill_value=0).T
            st.dataframe(daily_pivot, use_container_width=True)

        # Contribution & Categories
        st.subheader("📈 Productivity & Query Insights")
        c1, c2 = st.columns(2)
        with c1:
            if chan_col:
                st.plotly_chart(px.pie(dfp, names=chan_col, hole=0.4, title="Contribution by Segment", 
                                      color_discrete_sequence=[ORANGE, "#0047AB", "#777"]), use_container_width=True)
        with c2:
            if cat_col:
                # Top Queries bar chart
                q_data = dfp[cat_col].value_counts().nlargest(10).reset_index()
                st.plotly_chart(px.bar(q_data, x='index', y=cat_col, title="Top Query Categories", 
                                      labels={'index': 'Category', cat_col: 'Count'},
                                      color_discrete_sequence=[ORANGE]), use_container_width=True)
        
        # Email Productivity Summary
        if mail_col and chan_col:
            st.subheader("👨‍💻 Productivity by Segment")
            prod_summary = dfp.groupby([mail_col, chan_col]).size().unstack(fill_value=0).reset_index()
            st.dataframe(prod_summary, use_container_width=True)
    else:
        st.info("👋 To start, upload your Performance file (CS Productivity) in the sidebar.")

# --- AUDIT TRACKER (Tab 2) ---
with tab2:
    if df_a_raw is not None:
        dfa = df_a_raw.copy()
        # Shared Month Slicer Logic for Audits
        at_col = find_col(['Created date', 'Timestamp', 'Month'], dfa)
        if at_col and selected_months:
            dfa['Month_Name'] = pd.to_datetime(dfa[at_col], errors='coerce').dt.strftime('%B')
            dfa = dfa[dfa['Month_Name'].isin(selected_months)]

        exec_col = find_col(['Executive Name', 'Agent'], dfa)
        csat_col = find_col(['Csat'], dfa)

        st.title("🕵️ Quality Audit Tracker")
        st.metric("Total Calls Audited", len(dfa))

        if exec_col and csat_col:
            dfa['Sentiment'] = dfa[csat_col].apply(get_sentiment)

            # THE REQUESTED MASTER AUDIT TABLE
            audit_summary = dfa.groupby(exec_col).agg(
                Total_Calls_Taken=(dfa.columns[0], 'count'),
                CSAT_Collected=('Sentiment', lambda x: (x != "Not Rated").sum()),
                Positive_CSAT=('Sentiment', lambda x: (x == "Positive").sum()),
                Negative_CSAT=('Sentiment', lambda x: (x == "Negative").sum())
            ).reset_index()

            # Precision % Calculations
            audit_summary['Positive % (vs CSAT)'] = (audit_summary['Positive_CSAT'] / audit_summary['CSAT_Collected'] * 100).fillna(0).round(1).astype(str) + '%'
            audit_summary['Collection % (vs Total)'] = (audit_summary['CSAT_Collected'] / audit_summary['Total_Calls_Taken'] * 100).fillna(0).round(1).astype(str) + '%'

            st.subheader("Executive Performance Scorecard")
            st.dataframe(audit_summary, use_container_width=True)

            # Quality Distribution Chart
            valid = dfa[dfa['Sentiment'] != "Not Rated"]
            if not valid.empty:
                st.plotly_chart(px.pie(valid, names='Sentiment', hole=0.5, title="Overall CSAT Quality Mix", 
                                      color_discrete_map={'Positive': '#22C55E', 'Negative': '#EF4444'}), use_container_width=True)
        else:
            st.error("Audit File is missing 'Executive Name' or 'Csat' columns.")
    else:
        st.info("👋 To start, upload your Audit file (Call Tracker) in the sidebar.")
