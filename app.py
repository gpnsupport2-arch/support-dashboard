import streamlit as st
import pandas as pd
import plotly.express as px
import base64
from streamlit_gsheets import GSheetsConnection

# --- 1. BRANDING & VISIBILITY (FIXED SELECTBOX FONT) ---
st.set_page_config(page_title="Primarc Pecan | Multi-Sheet Portal", layout="wide")

BRAND_ORANGE, BRAND_NAVY, BRAND_WHITE = "#F37021", "#101828", "#FFFFFF"

st.markdown(f"""
    <style>
    .stApp {{ background: linear-gradient(180deg, {BRAND_NAVY} 0%, #1D2939 100%); }}
    
    /* Global White Text */
    h1, h2, h3, p, span, label, div {{ color: {BRAND_WHITE} !important; }}

    /* CRITICAL FIX: DROPDOWN MENU VISIBILITY */
    div[data-baseweb="select"] * {{ color: {BRAND_NAVY} !important; }} 
    div[role="listbox"] * {{ color: {BRAND_NAVY} !important; }}
    .stSelectbox label {{ color: {BRAND_WHITE} !important; }}

    /* Sidebar & Metrics */
    [data-testid="stSidebar"] {{ background-color: {BRAND_NAVY} !important; border-right: 1px solid {BRAND_ORANGE}; }}
    div[data-testid="stMetric"] {{ background-color: #1D2939; border: 1px solid {BRAND_ORANGE}; border-radius: 12px; }}
    [data-testid="stMetricValue"] {{ color: {BRAND_ORANGE} !important; }}
    
    /* Tabs */
    .stTabs [aria-selected="true"] {{ background-color: {BRAND_ORANGE} !important; }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA CONNECTIONS (SIDEBAR) ---
st.sidebar.header("🔌 Data Connections")

# Connection 1: Support Tracker
st.sidebar.subheader("1. Support Data")
support_url = st.sidebar.text_input("Paste Support Sheet URL")

# Connection 2: Audit Tracker
st.sidebar.subheader("2. Audit Data")
audit_url = st.sidebar.text_input("Paste Audit Sheet URL")

conn = st.connection("gsheets", type=GSheetsConnection)

def load_data(url):
    if url:
        try: return conn.read(spreadsheet=url, ttl=0)
        except: return None
    return None

df_support = load_data(support_url)
df_audit = load_data(audit_url)

# --- 3. PROCESSING ---
# Find columns for Audit logic
def find_col(target_names, current_cols):
    for name in target_names:
        for col in current_cols:
            if str(name).lower() == str(col).lower(): return col
    return None

# --- 4. TABS ---
tab1, tab2, tab3 = st.tabs(["📊 Performance Overview", "📋 Support Log", "🕵️ Audit Tracker"])

# --- TAB 1 & 2: SUPPORT DATA ---
if df_support is not None:
    df_support.columns = [str(c).strip() for c in df_support.columns]
    exec_col = find_col(['Email Address', 'Executive', 'Agent'], df_support.columns)
    chan_col = find_col(['Channel'], df_support.columns)

    with tab1:
        st.title("🎧 Support Performance")
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Executive Distribution")
            fig = px.pie(df_support[exec_col].value_counts().reset_index(), names=exec_col, values='count', hole=0.4, color_discrete_sequence=px.colors.sequential.Oranges_r)
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            st.subheader("Individual Channel Split")
            agent = st.selectbox("Select Agent for Split:", sorted(df_support[exec_col].dropna().unique()), key="agent_split")
            split_data = df_support[df_support[exec_col] == agent][chan_col].value_counts().reset_index()
            fig2 = px.pie(split_data, names=chan_col, values='count', hole=0.4, color_discrete_sequence=[BRAND_ORANGE, "#475467"])
            st.plotly_chart(fig2, use_container_width=True)

    with tab2:
        st.title("📋 Support Ticket Log")
        st.dataframe(df_support, use_container_width=True)

# --- TAB 3: AUDIT TRACKER ---
with tab3:
    st.title("🕵️ Quality Audit Tracker")
    if df_audit is not None:
        df_audit.columns = [str(c).strip() for c in df_audit.columns]
        
        # Identify Audit Columns
        a_exec_col = find_col(['Executive Name', 'Exe Name', 'Agent'], df_audit.columns)
        score_col = find_col(['Score', 'Audit Score', 'Rating'], df_audit.columns)

        if a_exec_col and score_col:
            # Audit Logic: 4-5 is Positive, <3 is Negative
            df_audit[score_col] = pd.to_numeric(df_audit[score_col], errors='coerce')
            df_audit['Sentiment'] = df_audit[score_col].apply(lambda x: "Positive" if x >= 4 else ("Negative" if x <= 3 else "Neutral"))

            # Summary Table
            audit_summary = df_audit.groupby(a_exec_col).agg({
                score_col: ['count', 'mean'],
                'Sentiment': lambda x: (x == 'Positive').sum()
            }).reset_index()
            audit_summary.columns = ['Executive Name', 'Total Audits', 'Avg Score', 'Positive Count']
            
            # Display Metrics
            m1, m2, m3 = st.columns(3)
            m1.metric("Total Audits Conducted", len(df_audit))
            m2.metric("Avg Quality Score", round(df_audit[score_col].mean(), 2))
            m3.metric("Overall CSAT %", f"{(len(df_audit[df_audit['Sentiment']=='Positive'])/len(df_audit)*100):.1f}%")

            st.subheader("Executive Audit Summary")
            st.dataframe(audit_summary.style.background_gradient(subset=['Avg Score'], cmap='RdYlGn'), use_container_width=True)
            
            st.subheader("Detailed Audit Feed")
            st.dataframe(df_audit, use_container_width=True)
        else:
            st.warning("Could not find 'Executive Name' or 'Score' columns in the Audit sheet.")
    else:
        st.info("Please paste the Audit Sheet URL in the sidebar to view quality analytics.")
