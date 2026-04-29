import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection

# --- 1. UI BRANDING & THEME ---
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
    .stTabs [aria-selected="true"] {{ background-color: {ORANGE} !important; border-radius: 5px; }}
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

# --- 3. SIDEBAR DATA CONNECTORS ---
st.sidebar.title("🔌 Data Sources")
def load_source(label):
    st.sidebar.subheader(f"📂 {label}")
    src = st.sidebar.radio(f"Format: {label}", ["Excel/CSV", "Google Sheet"], key=f"s_{label}")
    if src == "Google Sheet":
        url = st.sidebar.text_input(f"URL: {label}", key=f"u_{label}")
        if url:
            try: return st.connection("gsheets", type=GSheetsConnection).read(spreadsheet=url, ttl=0)
            except: return None
    else:
        file = st.sidebar.file_uploader(f"Upload: {label}", type=['csv', 'xlsx'], key=f"f_{label}")
        if file: return pd.read_csv(file) if file.name.endswith('.csv') else pd.read_excel(file)
    return None

df_prod_raw = load_source("Performance (CS SOS)")
df_audit_raw = load_source("Audit (Mar Call Tracker)")

# --- 4. MAIN DASHBOARD ---
tab1, tab2 = st.tabs(["📊 Performance Overview", "🕵️ Audit Tracker"])

# --- TAB 1: PERFORMANCE OVERVIEW (Using CS SOS Data) ---
with tab1:
    if df_prod_raw is not None:
        df_p = df_prod_raw.copy()
        df_p.columns = [str(c).strip() for c in df_p.columns]

        # Column Mapping
        email_col = find_col(['Email Address'], df_p)
        status_col = find_col(['Ticket status'], df_p)
        channel_col = find_col(['Channel'], df_p)
        cat_col = find_col(['Query type'], df_p)
        month_col = find_col(['Timestamp'], df_p)

        st.title("🚀 Operations Performance")
        
        # Slicer for Month (Derived from Timestamp)
        if month_col:
            df_p['Month'] = pd.to_datetime(df_p[month_col], errors='coerce').dt.strftime('%B')
            selected_month = st.multiselect("Filter by Month", options=df_p['Month'].unique().tolist(), default=df_p['Month'].unique().tolist())
            df_p = df_p[df_p['Month'].isin(selected_month)]

        # KPI Metrics
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Total Tickets", len(df_p))
        if channel_col:
            k2.metric("Email Tickets", len(df_p[df_p[channel_col] == 'Emails']))
            k3.metric("Call Tickets", len(df_p[df_p[channel_col] == 'Calls']))
        if status_col:
            closed_count = len(df_p[df_p[status_col].isin(['Closed', 'Resolved'])])
            k4.metric("Resolved/Closed", closed_count)

        # Productivity & Contribution Section
        st.subheader("📧 Email Address Productivity & Segment Contribution")
        if email_col and channel_col:
            prod = df_p.groupby([email_col, channel_col]).size().unstack(fill_value=0).reset_index()
            st.dataframe(prod, use_container_width=True)
            
            c1, c2 = st.columns(2)
            with c1:
                st.plotly_chart(px.pie(df_p, names=channel_col, hole=0.4, title="Contribution by Segment", color_discrete_sequence=[ORANGE, "#444"]), use_container_width=True)
            with c2:
                if cat_col:
                    st.plotly_chart(px.bar(df_p[cat_col].value_counts().head(10), title="Top Query Categories", color_discrete_sequence=[ORANGE]), use_container_width=True)
    else:
        st.info("Upload 'CS - SOS.xlsx' to see Performance metrics.")

# --- TAB 2: AUDIT TRACKER (Using Mar'26 Call Tracker Data) ---
with tab2:
    if df_audit_raw is not None:
        df_a = df_audit_raw.copy()
        df_a.columns = [str(c).strip() for c in df_a.columns]

        # Mapping for Audit Data
        ag_name = find_col(['Agent', 'Executive Name'], df_a)
        csat_col = find_col(['Csat'], df_a)
        
        st.title("🕵️ Quality Audit Tracker")
        
        if ag_name and csat_col:
            # Sentiment logic
            def get_val(v):
                v = str(v).lower()
                if any(x in v for x in ['5', '4', 'positive']): return "Positive"
                if any(x in v for x in ['1', '2', '3', 'negative']): return "Negative"
                return "Not Rated"
            
            df_a['Sentiment'] = df_a[csat_col].apply(get_val)
            
            # The Main Audit Table requested
            audit_summary = df_a.groupby(ag_name).agg(
                Total_Calls_Taken=(df_a.columns[0], 'count'),
                Calls_Audited=(df_a.columns[0], 'count'), # Assuming each row in this sheet is an audit
                CSAT_Collected=('Sentiment', lambda x: (x != "Not Rated").sum()),
                Positives=('Sentiment', lambda x: (x == "Positive").sum()),
                Negatives=('Sentiment', lambda x: (x == "Negative").sum())
            ).reset_index()

            audit_summary['Collection %'] = (audit_summary['CSAT_Collected'] / audit_summary['Total_Calls_Taken'] * 100).round(1)
            
            # Reorder for UI
            audit_summary = audit_summary[[ag_name, 'Total_Calls_Taken', 'Calls_Audited', 'CSAT_Collected', 'Collection %', 'Positives', 'Negatives']]
            
            st.metric("Total Audited Calls", len(df_a))
            st.dataframe(audit_summary, use_container_width=True)
            
            # Sentiment Breakdown Chart
            valid = df_a[df_a['Sentiment'] != "Not Rated"]
            if not valid.empty:
                st.plotly_chart(px.pie(valid, names='Sentiment', title="CSAT Quality Split", color_discrete_map={'Positive':'#22C55E','Negative':'#EF4444'}), use_container_width=True)
        else:
            st.error("Missing 'Agent' or 'Csat' columns in Audit file.")
    else:
        st.info("Upload 'Mar'26 - Call.xlsx' to see Audit metrics.")
