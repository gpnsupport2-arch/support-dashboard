import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection

# --- 1. UI BRANDING ---
st.set_page_config(page_title="Primarc Pecan | Executive Portal", layout="wide")
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

df_prod_raw = load_source("Performance (CS Productivity)")
df_audit_raw = load_source("Audit (Call Tracker)")

# --- 4. MAIN DASHBOARD ---
tab1, tab2 = st.tabs(["📊 Performance Overview", "🕵️ Audit Tracker"])

# --- TAB 1: PERFORMANCE OVERVIEW ---
with tab1:
    if df_prod_raw is not None:
        df_p = df_prod_raw.copy()
        df_p.columns = [str(c).strip() for c in df_p.columns]
        
        # Mapping
        time_col = find_col(['Timestamp'], df_p)
        chan_col = find_col(['Channel'], df_p)
        stat_col = find_col(['Ticket status'], df_p)
        cat_col = find_col(['Query type'], df_p)
        email_addr = find_col(['Email Address'], df_p)

        # 📅 GLOBAL MONTH SLICER FOR ALL CHARTS
        if time_col:
            df_p['Month'] = pd.to_datetime(df_p[time_col], errors='coerce').dt.strftime('%B')
            all_months = sorted(df_p['Month'].dropna().unique().tolist())
            selected_months = st.multiselect("🗓️ Select Month Filter (Applies to all Charts)", options=all_months, default=all_months)
            # Apply filter
            df_filtered = df_p[df_p['Month'].isin(selected_months)]
        else:
            df_filtered = df_p

        st.title("🎧 Operations Performance")
        
        # Metrics Row
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Total Tickets", len(df_filtered))
        if chan_col:
            k2.metric("Email Tickets", len(df_filtered[df_filtered[chan_col] == 'Emails']))
            k3.metric("Call Tickets", len(df_filtered[df_filtered[chan_col] == 'Calls']))
        if stat_col:
            res = len(df_filtered[df_filtered[stat_col].isin(['Closed', 'Resolved'])])
            k4.metric("Resolved/Closed", res)

        # Productivity Slicer Logic
        st.subheader("📧 Productivity & Contribution")
        if email_addr and chan_col:
            prod_table = df_filtered.groupby([email_addr, chan_col]).size().unstack(fill_value=0).reset_index()
            st.dataframe(prod_table, use_container_width=True)

        c1, c2 = st.columns(2)
        with c1:
            if chan_col:
                st.plotly_chart(px.pie(df_filtered, names=chan_col, hole=0.4, title="Contribution by Segment", color_discrete_sequence=[ORANGE, "#444"]), use_container_width=True)
        with c2:
            if cat_col:
                st.plotly_chart(px.bar(df_filtered[cat_col].value_counts().head(10), title="Top Queries (Filtered)", color_discrete_sequence=[ORANGE]), use_container_width=True)
    else:
        st.info("Upload 'CS Productivity' source.")

# --- TAB 2: AUDIT TRACKER ---
with tab2:
    if df_audit_raw is not None:
        df_a = df_audit_raw.copy()
        df_a.columns = [str(c).strip() for c in df_a.columns]
        
        # Mapping
        exec_col = find_col(['Executive Name', 'Agent'], df_a)
        csat_col = find_col(['Csat'], df_a)
        
        st.title("🕵️ Quality Audit Deep-Dive")
        
        if exec_col and csat_col:
            # Logic: 4-5 stars = Positive, 1-3 = Negative
            def get_sent(v):
                v = str(v).lower()
                if any(x in v for x in ['5', '4', 'positive']): return "Positive"
                if any(x in v for x in ['1', '2', '3', 'negative']): return "Negative"
                return "Not Rated"
            
            df_a['Sentiment'] = df_a[csat_col].apply(get_sent)
            
            # --- THE REQUESTED AUDIT TABLE ---
            audit_table = df_a.groupby(exec_col).agg(
                Total_Calls_Taken=(df_a.columns[0], 'count'),
                CSAT_Collected=('Sentiment', lambda x: (x != "Not Rated").sum()),
                Positive_CSAT=('Sentiment', lambda x: (x == "Positive").sum()),
                Negative_CSAT=('Sentiment', lambda x: (x == "Negative").sum())
            ).reset_index()

            # Percentage Calculations
            # % of positive CSAT against total CSAT collected
            audit_table['Positive % (vs CSAT)'] = (audit_table['Positive_CSAT'] / audit_table['CSAT_Collected'] * 100).fillna(0).round(1)
            # % of total CSAT collected against total calls taken
            audit_table['Collection % (vs Total)'] = (audit_table['CSAT_Collected'] / audit_table['Total_Calls_Taken'] * 100).fillna(0).round(1)

            # Display Table
            st.subheader("Executive Quality Metrics")
            st.dataframe(audit_table, use_container_width=True)
            
            # Sentiment Pie Chart
            valid_only = df_a[df_a['Sentiment'] != "Not Rated"]
            if not valid_only.empty:
                st.plotly_chart(px.pie(valid_only, names='Sentiment', hole=0.4, title="Overall Sentiment Split", color_discrete_map={'Positive':'#22C55E','Negative':'#EF4444'}), use_container_width=True)
        else:
            st.error("Audit File missing 'Executive Name' or 'Csat' columns.")
    else:
        st.info("Upload Audit Tracker source.")
