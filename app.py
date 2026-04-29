import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection

# --- 1. UI BRANDING & SETTINGS ---
st.set_page_config(page_title="Primarc Pecan | Master Operations Dashboard", layout="wide")
ORANGE, NAVY = "#F37021", "#101828"

st.markdown(f"""
    <style>
    .stApp {{ background: linear-gradient(180deg, {NAVY} 0%, #1D2939 100%); }}
    h1, h2, h3, p, label {{ color: white !important; font-family: 'Segoe UI', sans-serif; }}
    div[data-testid="stMetric"] {{ 
        background-color: #1D2939; border: 1px solid {ORANGE}; 
        border-radius: 12px; padding: 20px; box-shadow: 2px 2px 10px rgba(0,0,0,0.5);
    }}
    [data-testid="stMetricValue"] {{ color: {ORANGE} !important; font-size: 32px !important; font-weight: bold; }}
    .stTabs [aria-selected="true"] {{ background-color: {ORANGE} !important; border-radius: 5px; color: white !important; }}
    .stDataFrame {{ background-color: white; border-radius: 8px; }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. ENGINE HELPERS ---
def find_col(targets, df):
    if df is None: return None
    cols = {c.strip().lower(): c for c in df.columns}
    for t in targets:
        if t.lower() in cols: return cols[t.lower()]
    return None

def parse_month(val):
    try: return pd.to_datetime(val, errors='coerce').strftime('%B')
    except: return "Unknown"

# --- 3. SIDEBAR CONTROLS ---
st.sidebar.title("🚀 Dashboard Control")

def load_data(label, key):
    st.sidebar.subheader(f"📂 {label}")
    src = st.sidebar.radio(f"Format: {label}", ["Excel/CSV", "Google Sheet"], key=f"src_{key}")
    if src == "Google Sheet":
        url = st.sidebar.text_input(f"Link: {label}", key=f"url_{key}")
        if url:
            try: return st.connection("gsheets", type=GSheetsConnection).read(spreadsheet=url, ttl=0)
            except: return None
    else:
        file = st.sidebar.file_uploader(f"Upload: {label}", type=['csv', 'xlsx'], key=f"file_{key}")
        if file: return pd.read_csv(file) if file.name.endswith('.csv') else pd.read_excel(file)
    return None

# Load Raw Data
df_perf_raw = load_data("Performance (CS Productivity)", "perf")
df_audit_raw = load_data("Audit (Call Tracker)", "audit")

# Global Month Filter in Sidebar
selected_months = []
all_months = []

if df_perf_raw is not None:
    t_col = find_col(['Timestamp', 'Created date'], df_perf_raw)
    if t_col:
        df_perf_raw['Month_Name'] = pd.to_datetime(df_perf_raw[t_col], errors='coerce').dt.strftime('%B')
        all_months = sorted(df_perf_raw['Month_Name'].dropna().unique().tolist())
        selected_months = st.sidebar.multiselect("🗓️ Select Month (Global Filter)", options=all_months, default=all_months)

# --- 4. MAIN DASHBOARD TABS ---
tab1, tab2 = st.tabs(["📊 Performance Overview", "🕵️ Audit Tracker"])

# --- TAB 1: PERFORMANCE OVERVIEW ---
with tab1:
    if df_perf_raw is not None:
        # Apply Sidebar Filter
        dfp = df_perf_raw[df_perf_raw['Month_Name'].isin(selected_months)] if selected_months else df_perf_raw
        
        # Mapping
        chan_col = find_col(['Channel'], dfp)
        stat_col = find_col(['Ticket status'], dfp)
        cat_col = find_col(['Query type'], dfp)
        email_col = find_col(['Email Address'], dfp)

        st.title("🎧 Support Operations Performance")
        
        # KPI ROW
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Ticket Count", len(dfp))
        if chan_col:
            m2.metric("Email Ticket Count", len(dfp[dfp[chan_col].str.contains('Email', na=False, case=False)]))
            m3.metric("Call Ticket Count", len(dfp[dfp[chan_col].str.contains('Call', na=False, case=False)]))
        if stat_col:
            resolved = len(dfp[dfp[stat_col].isin(['Closed', 'Resolved'])])
            m4.metric("Resolved & Closed", resolved)

        # PRODUCTIVITY TABLE
        st.subheader("📧 Email Address Productivity & Segment Contribution")
        if email_col and chan_col:
            prod_table = dfp.groupby([email_col, chan_col]).size().unstack(fill_value=0).reset_index()
            st.dataframe(prod_table, use_container_width=True)

        # CHARTS
        c1, c2 = st.columns(2)
        with c1:
            if chan_col:
                fig_pie = px.pie(dfp, names=chan_col, hole=0.4, title="Segment Contribution", color_discrete_sequence=[ORANGE, "#0047AB"])
                fig_pie.update_layout(paper_bgcolor='rgba(0,0,0,0)', font=dict(color="white"))
                st.plotly_chart(fig_pie, use_container_width=True)
        with c2:
            if cat_col:
                # Grouped by month logic for query frequency
                top_cats = dfp[cat_col].value_counts().nlargest(10).index
                fig_bar = px.bar(dfp[dfp[cat_col].isin(top_cats)], x=cat_col, color='Month_Name' if 'Month_Name' in dfp else None,
                                 title="Top Queries by Frequency", barmode='group', color_discrete_sequence=px.colors.qualitative.Prism)
                fig_bar.update_layout(paper_bgcolor='rgba(0,0,0,0)', font=dict(color="white"))
                st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("👋 Upload the 'CS - SOS.xlsx' file in the sidebar to begin.")

# --- TAB 2: AUDIT TRACKER ---
with tab2:
    if df_audit_raw is not None:
        dfa = df_audit_raw.copy()
        # Apply Sidebar Filter to Audit if timestamp exists
        at_col = find_col(['Created date', 'Timestamp'], dfa)
        if at_col:
            dfa['Month_Name'] = pd.to_datetime(dfa[at_col], errors='coerce').dt.strftime('%B')
            if selected_months:
                dfa = dfa[dfa['Month_Name'].isin(selected_months)]

        # Mapping
        exec_col = find_col(['Executive Name', 'Agent'], dfa)
        csat_col = find_col(['Csat'], dfa)

        st.title("🕵️ Quality Audit & CSAT Tracker")
        st.metric("Total Audit Calls", len(dfa))

        if exec_col and csat_col:
            # Sentiment Rule: 4-5 stars = Positive, 1-3 = Negative
            def get_sentiment(v):
                v = str(v).lower()
                if any(x in v for x in ['5', '4', 'positive', 'excellent', 'good']): return "Positive"
                if any(x in v for x in ['1', '2', '3', 'negative', 'poor', 'bad', 'average']): return "Negative"
                return "Not Rated"

            dfa['Sentiment'] = dfa[csat_col].apply(get_sentiment)

            # THE REQUESTED TABLE
            audit_summary = dfa.groupby(exec_col).agg(
                Total_Calls_Taken=(dfa.columns[0], 'count'),
                CSAT_Collected=('Sentiment', lambda x: (x != "Not Rated").sum()),
                Positive_CSAT=('Sentiment', lambda x: (x == "Positive").sum()),
                Negative_CSAT=('Sentiment', lambda x: (x == "Negative").sum())
            ).reset_index()

            # Percentage Calculations
            audit_summary['Pos CSAT % (vs Collected)'] = (audit_summary['Positive_CSAT'] / audit_summary['CSAT_Collected'] * 100).fillna(0).round(1).astype(str) + '%'
            audit_summary['Collection % (vs Total)'] = (audit_summary['CSAT_Collected'] / audit_summary['Total_Calls_Taken'] * 100).fillna(0).round(1).astype(str) + '%'

            st.subheader("Executive Performance Audit Table")
            st.dataframe(audit_summary, use_container_width=True)

            # Quality Chart
            valid = dfa[dfa['Sentiment'] != "Not Rated"]
            if not valid.empty:
                st.plotly_chart(px.pie(valid, names='Sentiment', hole=0.4, title="Overall CSAT Sentiment Split", color_discrete_map={'Positive':'#22C55E','Negative':'#EF4444'}), use_container_width=True)
        else:
            st.error("Audit File missing 'Executive Name' or 'Csat' columns.")
    else:
        st.info("👋 Upload the 'Mar'26 - Call.xlsx' file in the sidebar to begin.")
