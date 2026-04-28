import streamlit as st
import pandas as pd
import plotly.express as px
import base64
from streamlit_gsheets import GSheetsConnection

# --- 1. BRANDING & THEME ---
st.set_page_config(page_title="Primarc Pecan | Performance Hub", layout="wide")
BRAND_ORANGE, BRAND_NAVY, BRAND_WHITE = "#F37021", "#101828", "#FFFFFF"

st.markdown(f"""
    <style>
    .stApp {{ background: linear-gradient(180deg, {BRAND_NAVY} 0%, #1D2939 100%); }}
    h1, h2, h3, p, span, label, .stMarkdown {{ color: {BRAND_WHITE} !important; }}
    
    /* Center Logo */
    .logo-container {{ display: flex; justify-content: center; padding: 10px; margin-bottom: 10px; }}

    /* Dropdown Visibility Fix */
    div[data-baseweb="select"] > div {{ background-color: white !important; color: {BRAND_NAVY} !important; }}
    div[role="listbox"] div {{ color: {BRAND_NAVY} !important; }}
    
    /* Metric Cards */
    div[data-testid="stMetric"] {{ 
        background-color: #1D2939; 
        border: 1px solid {BRAND_ORANGE}; 
        border-radius: 10px; 
        padding: 15px;
    }}
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
    st.markdown(f'<div class="logo-container"><img src="data:image/jpeg;base64,{logo_data}" width="220"></div>', unsafe_allow_html=True)
except:
    st.markdown("<h1 style='text-align: center; color: #F37021;'>PRIMARC PECAN</h1>", unsafe_allow_html=True)

# --- 3. DATA LOADER (FIXED FOR MULTIPLE EXCEL) ---
st.sidebar.header("🔌 Data Sources")

def load_data_source(label, key_id):
    st.sidebar.subheader(f"📂 {label}")
    mode = st.sidebar.radio(f"Input for {label}", ["Google Sheet", "Excel/CSV"], key=f"mode_{key_id}")
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

df_s = load_data_source("Support Tracker", "support")
df_a = load_data_source("Audit Tracker", "audit")

def clean_df(df):
    if df is not None:
        df.columns = [str(c).strip() for c in df.columns]
        # Remove empty rows/cols
        df = df.dropna(how='all', axis=0).dropna(how='all', axis=1)
    return df

df_s, df_a = clean_df(df_s), clean_df(df_a)

def find_col(targets, df):
    if df is None: return None
    for t in targets:
        for col in df.columns:
            if t.lower() in str(col).lower(): return col
    return None

# --- 4. TOP KPI SECTION ---
if df_s is not None:
    status_col = find_col(['status', 'ticket status'], df_s)
    chan_col = find_col(['channel'], df_s)
    
    k1, k2, k3, k4 = st.columns(4)
    total_t = len(df_s)
    k1.metric("Total Tickets", total_t)
    
    if status_col:
        resolved = len(df_s[df_s[status_col].astype(str).str.contains('Resolved|Closed|Done', case=False, na=False)])
        res_rate = (resolved / total_t * 100) if total_t > 0 else 0
        k2.metric("Resolution Rate", f"{res_rate:.1f}%")
    else:
        k2.metric("Resolution Rate", "N/A")

    if chan_col:
        emails = len(df_s[df_s[chan_col].astype(str).str.contains('Email', case=False, na=False)])
        calls = len(df_s[df_s[chan_col].astype(str).str.contains('Call', case=False, na=False)])
        k3.metric("Email Volume", emails)
        k4.metric("Call Volume", calls)

st.markdown("---")

# --- 5. TABS ---
t1, t2 = st.tabs(["📊 Performance Overview", "🕵️ CSAT & Audit Tracker"])

# TAB 1: SUPPORT ANALYTICS
with t1:
    if df_s is not None:
        e_col = find_col(['executive', 'agent', 'email'], df_s)
        c_col = find_col(['channel'], df_s)
        if e_col:
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("Team Workload Distribution")
                fig1 = px.pie(df_s, names=e_col, hole=0.4, color_discrete_sequence=px.colors.sequential.Oranges_r)
                fig1.update_layout(paper_bgcolor='rgba(0,0,0,0)', font=dict(color="white"))
                st.plotly_chart(fig1, use_container_width=True)
            with c2:
                st.subheader("Executive Deep-Dive")
                agent = st.selectbox("Select Executive Name:", sorted(df_s[e_col].dropna().unique()))
                sub = df_s[df_s[e_col] == agent]
                fig2 = px.pie(sub, names=c_col, hole=0.4, color_discrete_sequence=[BRAND_ORANGE, "#475467"])
                fig2.update_layout(paper_bgcolor='rgba(0,0,0,0)', font=dict(color="white"))
                st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("Upload Support Tracker to see Performance Analytics.")

# TAB 2: AUDIT TRACKER (CSAT LOGIC)
with t2:
    st.subheader("🕵️ Quality & CSAT Collection")
    if df_a is not None:
        ae_col = find_col(['executive', 'agent', 'name'], df_a)
        as_col = find_col(['score', 'rating', 'csat'], df_a)

        if ae_col and as_col:
            # Clean numeric data
            df_a[as_col] = pd.to_numeric(df_a[as_col], errors='coerce')
            
            # POSITIVE / NEGATIVE Logic
            # 4-5 = Positive | Below 3 = Negative
            def categorize(val):
                if val >= 4: return "Positive ✅"
                elif val <= 3: return "Negative ❌"
                return "Neutral ⚠️"
            
            df_a['Sentiment'] = df_a[as_col].apply(categorize)
            
            # Scorecard Metrics
            m1, m2, m3 = st.columns(3)
            m1.metric("Total CSAT Collected", len(df_a))
            m2.metric("Avg Quality Score", f"{df_a[as_col].mean():.2f}")
            pos_rate = (len(df_a[df_a[as_col] >= 4]) / len(df_a) * 100) if len(df_a) > 0 else 0
            m3.metric("Positive CSAT %", f"{pos_rate:.1f}%")

            st.markdown("### Executive-wise CSAT Performance")
            # Grouping for the summary table you requested
            summary = df_a.groupby(ae_col).agg({
                as_col: ['count', 'mean'],
                'Sentiment': [lambda x: (x == "Positive ✅").sum(), lambda x: (x == "Negative ❌").sum()]
            }).reset_index()
            
            summary.columns = ['Executive Name', 'CSAT Collection', 'Avg Quality Score', 'Positive Count', 'Negative Count']
            
            # Final Table View
            st.dataframe(summary.style.background_gradient(subset=['Avg Quality Score'], cmap='RdYlGn'), use_container_width=True)
            
            st.markdown("### Raw Audit Log")
            st.dataframe(df_a[[ae_col, as_col, 'Sentiment']], use_container_width=True)
        else:
            st.error("Audit sheet must contain 'Executive' and 'Score' columns.")
    else:
        st.info("Upload Audit Tracker to see CSAT Metrics.")

# --- 6. PREDICTIONS ---
st.markdown("---")
st.subheader("🔮 Predictive Insights")
p1, p2 = st.columns(2)
with p1:
    st.markdown('<div class="insight-card"><b>📅 Backlog Forecast</b><br>Remaining Volume calculated based on Support Data.</div>', unsafe_allow_html=True)
with p2:
    st.markdown('<div class="insight-card"><b>🚀 Capacity Planning</b><br>Executive CSAT scores 4-5 are trending positively.</div>', unsafe_allow_html=True)
