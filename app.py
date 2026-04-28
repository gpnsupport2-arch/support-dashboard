import streamlit as st
import pandas as pd
import plotly.express as px
import base64
from streamlit_gsheets import GSheetsConnection

# --- 1. BRANDING & PERSISTENT STYLE ---
st.set_page_config(page_title="Primarc Pecan | Support Portal", layout="wide")
BRAND_ORANGE, BRAND_NAVY, BRAND_WHITE = "#F37021", "#101828", "#FFFFFF"

st.markdown(f"""
    <style>
    .stApp {{ background: linear-gradient(180deg, {BRAND_NAVY} 0%, #1D2939 100%); }}
    h1, h2, h3, p, span, label, .stMarkdown {{ color: {BRAND_WHITE} !important; }}
    
    /* Dropdown Selection Fix */
    div[data-baseweb="select"] > div {{ background-color: white !important; color: {BRAND_NAVY} !important; }}
    div[role="listbox"] div {{ color: {BRAND_NAVY} !important; }}
    
    /* Metric Cards - Fixed for Visibility */
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

# --- 2. DATA LOADER ---
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

# Clean & Find Columns
def clean_df(df):
    if df is not None:
        df.columns = [str(c).strip() for c in df.columns]
    return df

df_s, df_a = clean_df(df_s), clean_df(df_a)

def find_col(targets, df):
    if df is None: return None
    for t in targets:
        for col in df.columns:
            if t.lower() in col.lower(): return col
    return None

# --- 3. TOP KPI SECTION (RESTORED) ---
st.title("🎧 Support Operations Portal")

if df_s is not None:
    # Identify critical columns for KPIs
    status_col = find_col(['status', 'ticket status'], df_s)
    chan_col = find_col(['channel'], df_s)
    
    k1, k2, k3, k4 = st.columns(4)
    total_t = len(df_s)
    
    # 1. Total Tickets
    k1.metric("Total Tickets", total_t)
    
    # 2. Resolved Tickets (Looking for "Resolved" or "Closed")
    if status_col:
        resolved_count = len(df_s[df_s[status_col].astype(str).str.contains('Resolved|Closed|Done', case=False, na=False)])
        res_rate = (resolved_count / total_t * 100) if total_t > 0 else 0
        k2.metric("Resolution Rate", f"{res_rate:.1f}%")
    else:
        k2.metric("Resolution Rate", "N/A")

    # 3. & 4. Channel Counts
    if chan_col:
        emails = len(df_s[df_s[chan_col].astype(str).str.contains('Email', case=False, na=False)])
        calls = len(df_s[df_s[chan_col].astype(str).str.contains('Call', case=False, na=False)])
        k3.metric("Email Volume", emails)
        k4.metric("Call Volume", calls)

st.markdown("---")

# --- 4. TABS SECTION ---
t1, t2, t3 = st.tabs(["📊 Performance Overview", "📋 Support Log", "🕵️ Audit Tracker"])

# SUPPORT ANALYTICS
if df_s is not None:
    e_col = find_col(['executive', 'agent', 'email'], df_s)
    c_col = find_col(['channel'], df_s)

    with t1:
        st.subheader("Executive Distribution & Deep-Dive")
        c1, c2 = st.columns(2)
        with c1:
            fig1 = px.pie(df_s, names=e_col, hole=0.4, color_discrete_sequence=px.colors.sequential.Oranges_r)
            fig1.update_layout(paper_bgcolor='rgba(0,0,0,0)', font=dict(color="white"))
            st.plotly_chart(fig1, use_container_width=True)
        with c2:
            agent = st.selectbox("Select Executive Name:", sorted(df_s[e_col].dropna().unique()), key="sel_agent_tab")
            sub = df_s[df_s[e_col] == agent]
            fig2 = px.pie(sub, names=c_col, hole=0.4, color_discrete_sequence=[BRAND_ORANGE, "#475467"])
            fig2.update_layout(paper_bgcolor='rgba(0,0,0,0)', font=dict(color="white"))
            st.plotly_chart(fig2, use_container_width=True)

    with t2:
        st.subheader("📋 Searchable Ticket Log")
        st.dataframe(df_s, use_container_width=True)

# AUDIT ANALYTICS
with t3:
    st.subheader("🕵️ Quality Audit & Ratings")
    if df_a is not None:
        ae_col = find_col(['executive', 'agent', 'name'], df_a)
        as_col = find_col(['score', 'rating'], df_a)

        if ae_col and as_col:
            df_a[as_col] = pd.to_numeric(df_a[as_col], errors='coerce')
            df_a['Sentiment'] = df_a[as_col].apply(lambda x: "Positive" if x >= 4 else ("Negative" if x <= 3 else "Neutral"))
            
            m1, m2, m3 = st.columns(3)
            m1.metric("Total Audits", len(df_a))
            m2.metric("Avg Quality Score", f"{df_a[as_col].mean():.2f}")
            pos_rate = (len(df_a[df_a['Sentiment']=='Positive']) / len(df_a)) * 100 if len(df_a)>0 else 0
            m3.metric("Positive Rating % (4-5 Star)", f"{pos_rate:.1f}%")

            st.dataframe(df_a.groupby(ae_col).agg({as_col: ['count', 'mean']}).reset_index(), use_container_width=True)
    else:
        st.info("ℹ️ Connect Audit Source in sidebar.")

# --- 5. PREDICTIONS (PERMANENT BOTTOM) ---
st.markdown("---")
st.subheader("🔮 Predictive Insights")
p1, p2 = st.columns(2)
with p1:
    st.markdown('<div class="insight-card"><b>📅 Backlog Forecast</b><br>Tickets remaining: Based on Support Tracker data.</div>', unsafe_allow_html=True)
with p2:
    st.markdown('<div class="insight-card"><b>🚀 Capacity Planning</b><br>Quality scores 4-5 are currently trending at a healthy rate.</div>', unsafe_allow_html=True)
