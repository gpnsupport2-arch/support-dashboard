import streamlit as st
import pandas as pd
import plotly.express as px
import base64
from streamlit_gsheets import GSheetsConnection

# --- 1. BRANDING & CRITICAL VISIBILITY FIXES ---
st.set_page_config(page_title="Primarc Pecan | Executive Portal", layout="wide")

BRAND_ORANGE = "#F37021"
BRAND_NAVY = "#101828" 

st.markdown(f"""
    <style>
    /* Main Background */
    .stApp {{ background: linear-gradient(180deg, {BRAND_NAVY} 0%, #1D2939 100%); }}
    
    /* FORCE TEXT COLOR */
    h1, h2, h3, p, span, label, .stMarkdown {{ color: white !important; }}

    /* FIX DROPDOWN (SELECTBOX) CONTRAST */
    /* This makes the menu background white and text dark so you can read names */
    div[data-baseweb="select"] > div {{
        background-color: white !important;
        color: {BRAND_NAVY} !important;
    }}
    div[data-baseweb="popover"] div {{
        color: {BRAND_NAVY} !important;
    }}
    
    /* Metrics and Sidebar */
    div[data-testid="stMetric"] {{ background-color: #1D2939; border: 1px solid {BRAND_ORANGE}; border-radius: 10px; }}
    [data-testid="stSidebar"] {{ background-color: {BRAND_NAVY} !important; border-right: 1px solid {BRAND_ORANGE}; }}
    
    /* Tabs Visibility */
    .stTabs [data-baseweb="tab-list"] button {{ color: white !important; }}
    .stTabs [aria-selected="true"] {{ background-color: {BRAND_ORANGE} !important; border-radius: 5px; }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA LOADING LOGIC ---
st.sidebar.header("🔌 Data Sources")
support_url = st.sidebar.text_input("1. Support Google Sheet URL")
audit_url = st.sidebar.text_input("2. Audit Google Sheet URL")

conn = st.connection("gsheets", type=GSheetsConnection)

def get_data(url):
    if not url: return None
    try:
        data = conn.read(spreadsheet=url, ttl=0)
        data.columns = [str(c).strip() for c in data.columns]
        return data
    except Exception as e:
        st.sidebar.error(f"Error loading sheet: {e}")
        return None

df_s = get_data(support_url)
df_a = get_data(audit_url)

# Helper to find columns regardless of exact naming
def find_col(targets, df):
    if df is None: return None
    for t in targets:
        for col in df.columns:
            if t.lower() in col.lower(): return col
    return None

# --- 3. DASHBOARD TABS ---
t1, t2, t3 = st.tabs(["📊 Performance", "📋 Support Log", "🕵️ Audit Tracker"])

# --- TAB 1 & 2: SUPPORT ANALYTICS ---
if df_s is not None:
    e_col = find_col(['executive', 'agent', 'email'], df_s)
    c_col = find_col(['channel'], df_s)

    with t1:
        st.title("🎧 Executive Workload")
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Team Distribution")
            fig1 = px.pie(df_s, names=e_col, hole=0.4, color_discrete_sequence=px.colors.sequential.Oranges_r)
            st.plotly_chart(fig1, use_container_width=True)
        with c2:
            st.subheader("Agent Deep-Dive")
            # The dropdown here is now fixed with CSS to be readable
            agent = st.selectbox("Choose Executive:", sorted(df_s[e_col].dropna().unique()))
            sub = df_s[df_s[e_col] == agent]
            fig2 = px.pie(sub, names=c_col, hole=0.4, color_discrete_sequence=[BRAND_ORANGE, "#475467"])
            st.plotly_chart(fig2, use_container_width=True)

    with t2:
        st.subheader("Full Support Ticket Log")
        st.dataframe(df_s, use_container_width=True)

# --- TAB 3: AUDIT ANALYTICS (THE NEW ROOM) ---
with t3:
    st.title("🕵️ Quality Audit Tracker")
    if df_a is not None:
        # Find columns for Audit
        ae_col = find_col(['executive', 'agent', 'name'], df_a)
        as_col = find_col(['score', 'rating'], df_a)

        if ae_col and as_col:
            # Audit Logic: Score >= 4 is Positive, <= 3 is Negative
            df_a[as_col] = pd.to_numeric(df_a[as_col], errors='coerce')
            df_a['Sentiment'] = df_a[as_col].apply(lambda x: "Positive" if x >= 4 else ("Negative" if x <= 3 else "Neutral"))
            
            # Metrics
            m1, m2, m3 = st.columns(3)
            m1.metric("Total Audits", len(df_a))
            m2.metric("Average Score", f"{df_a[as_col].mean():.2f}")
            pos_rate = (len(df_a[df_a['Sentiment']=='Positive']) / len(df_a)) * 100
            m3.metric("Quality Pass Rate", f"{pos_rate:.1f}%")

            # Summary Table
            st.subheader("Executive Audit Summary")
            summary = df_a.groupby(ae_col).agg({as_col: ['count', 'mean']}).reset_index()
            summary.columns = ['Executive', 'Total Audits', 'Avg Score']
            st.table(summary) # Table is often more readable than Dataframe in dark mode

            st.subheader("Audit Raw Data")
            st.dataframe(df_a, use_container_width=True)
        else:
            st.error("Audit sheet missing 'Executive' or 'Score' columns.")
    else:
        st.info("ℹ️ Connect Audit Sheet in sidebar to view Quality metrics.")
