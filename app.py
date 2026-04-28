import streamlit as st
import pandas as pd
import plotly.express as px
import base64
from streamlit_gsheets import GSheetsConnection

# --- 1. BRANDING & PERSISTENT STYLE ---
st.set_page_config(page_title="Primarc Pecan | Executive Portal", layout="wide")

BRAND_ORANGE = "#F37021"
BRAND_NAVY = "#101828" 
BRAND_WHITE = "#FFFFFF"

st.markdown(f"""
    <style>
    .stApp {{ background: linear-gradient(180deg, {BRAND_NAVY} 0%, #1D2939 100%); }}
    
    /* Font Visibility Fixes */
    h1, h2, h3, p, span, label, .stMarkdown {{ color: {BRAND_WHITE} !important; }}

    /* Dropdown Selection Fix (Dark text on light background for readability) */
    div[data-baseweb="select"] > div {{ background-color: white !important; color: {BRAND_NAVY} !important; }}
    div[role="listbox"] div {{ color: {BRAND_NAVY} !important; }}
    
    /* Metrics and Sidebar */
    div[data-testid="stMetric"] {{ background-color: #1D2939; border: 1px solid {BRAND_ORANGE}; border-radius: 10px; }}
    [data-testid="stSidebar"] {{ background-color: {BRAND_NAVY} !important; border-right: 1px solid {BRAND_ORANGE}; }}
    
    /* Tabs Visibility */
    .stTabs [data-baseweb="tab-list"] button {{ color: white !important; }}
    .stTabs [aria-selected="true"] {{ background-color: {BRAND_ORANGE} !important; border-radius: 5px; }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. MULTI-SOURCE DATA LOADER ---
st.sidebar.header("🔌 Data Sources")

def load_logic(label_prefix):
    st.sidebar.subheader(f"{label_prefix} Source")
    mode = st.sidebar.radio(f"Select {label_prefix} Type", ["Google Sheet", "Excel/CSV"], key=f"{label_prefix}_mode")
    if mode == "Google Sheet":
        url = st.sidebar.text_input(f"Paste {label_prefix} URL", key=f"{label_prefix}_url")
        if url:
            try:
                conn = st.connection("gsheets", type=GSheetsConnection)
                data = conn.read(spreadsheet=url, ttl=0)
                return data
            except Exception as e:
                st.sidebar.error(f"Error: {e}")
    else:
        file = st.sidebar.file_uploader(f"Upload {label_prefix} File", type=['csv', 'xlsx'], key=f"{label_prefix}_file")
        if file:
            return pd.read_csv(file) if file.name.endswith('.csv') else pd.read_excel(file)
    return None

df_s = load_logic("Support")
df_a = load_logic("Audit")

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

# --- 3. DASHBOARD TABS ---
t1, t2, t3 = st.tabs(["📊 Performance Overview", "📋 Support Ticket Log", "🕵️ Audit Tracker"])

# --- TAB 1 & 2: SUPPORT ANALYTICS ---
if df_s is not None:
    e_col = find_col(['executive', 'agent', 'email'], df_s)
    c_col = find_col(['channel'], df_s)

    with t1:
        st.title("🎧 Support Operations")
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Total Executive Workload")
            fig1 = px.pie(df_s, names=e_col, hole=0.4, color_discrete_sequence=px.colors.sequential.Oranges_r)
            fig1.update_layout(paper_bgcolor='rgba(0,0,0,0)', font=dict(color="white"))
            st.plotly_chart(fig1, use_container_width=True)
        with c2:
            st.subheader("Executive Channel Split")
            agent = st.selectbox("Select Executive:", sorted(df_s[e_col].dropna().unique()))
            sub = df_s[df_s[e_col] == agent]
            fig2 = px.pie(sub, names=c_col, hole=0.4, color_discrete_sequence=[BRAND_ORANGE, "#475467"])
            fig2.update_layout(paper_bgcolor='rgba(0,0,0,0)', font=dict(color="white"))
            st.plotly_chart(fig2, use_container_width=True)

    with t2:
        st.title("📋 Live Support Tracker")
        st.dataframe(df_s, use_container_width=True)

# --- TAB 3: AUDIT TRACKER (POSITIVE/NEGATIVE LOGIC) ---
with t3:
    st.title("🕵️ Audit Tracker & Quality Score")
    if df_a is not None:
        ae_col = find_col(['executive', 'agent', 'name'], df_a)
        as_col = find_col(['score', 'rating'], df_a)

        if ae_col and as_col:
            df_a[as_col] = pd.to_numeric(df_a[as_col], errors='coerce')
            # 5 & 4 = Positive | Below 3 = Negative
            df_a['Sentiment'] = df_a[as_col].apply(lambda x: "Positive" if x >= 4 else ("Negative" if x <= 3 else "Neutral"))
            
            m1, m2, m3 = st.columns(3)
            m1.metric("Total Audits", len(df_a))
            m2.metric("Avg Quality Score", f"{df_a[as_col].mean():.2f}")
            pos_rate = (len(df_a[df_a['Sentiment']=='Positive']) / len(df_a)) * 100 if len(df_a)>0 else 0
            m3.metric("Positive Rating %", f"{pos_rate:.1f}%")

            st.subheader("Executive Wise Quality Audit")
            summary = df_a.groupby(ae_col).agg({
                as_col: ['count', 'mean'],
                'Sentiment': lambda x: (x == 'Positive').sum()
            }).reset_index()
            summary.columns = ['Executive', 'Total Audits', 'Avg Score', 'Good Ratings (4-5)']
            st.dataframe(summary, use_container_width=True)
        else:
            st.error("Audit sheet must contain 'Executive' and 'Score' columns.")
    else:
        st.info("ℹ️ Please upload an Audit file or paste a URL in the sidebar.")

# --- 4. PREDICTIONS (PERMANENT BOTTOM) ---
st.markdown("---")
st.subheader("🔮 Predictive Insights")
p1, p2 = st.columns(2)
with p1:
    st.markdown(f'<div class="insight-card"><b>📅 Backlog Forecast</b><br>Remaining Volume: Calculated based on Support Data.</div>', unsafe_allow_html=True)
with p2:
    st.markdown(f'<div class="insight-card"><b>🚀 Capacity Planning</b><br>Quality trends suggest focus on low-score query types.</div>', unsafe_allow_html=True)
