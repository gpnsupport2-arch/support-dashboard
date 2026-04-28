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

import streamlit as st
import pandas as pd
import plotly.express as px
import streamlit as st
import pandas as pd
import plotly.express as px

# --- AUDIT TRACKER MODULE ---
def show_audit_tracker(df):
    st.subheader("🕵️ Executive Quality & CSAT Performance")
    
    # 1. Identify Columns (Resilient Mapping)
    agent_col = next((c for c in df.columns if 'agent' in c.lower() or 'executive' in c.lower()), None)
    csat_col = next((c for c in df.columns if 'csat' in c.lower() or 'rating' in c.lower()), None)
    ticket_col = next((c for c in df.columns if 'ticket' in c.lower() or 'id' in c.lower()), df.columns[0])

    if agent_col and csat_col:
        # 2. Define Sentiment Logic (Instruction: 4-5 Pos, 1-3 Neg)
        def get_sentiment(val):
            v = str(val).lower()
            if any(x in v for x in ['5', '4', 'excellent', 'good']): 
                return "Positive"
            if any(x in v for x in ['1', '2', '3', 'poor', 'average']): 
                return "Negative"
            return "No Rating"

        df['Sentiment'] = df[csat_col].apply(get_sentiment)

        # 3. Top Row Metrics for Audits
        total_calls = len(df)
        valid_csats = df[df['Sentiment'] != "No Rating"]
        csat_count = len(valid_csats)
        coll_rate = (csat_count / total_calls * 100) if total_calls > 0 else 0

        m1, m2, m3 = st.columns(3)
        m1.metric("Total CSAT Collected", csat_count)
        m2.metric("Overall Collection %", f"{coll_rate:.1f}%")
        
        # Calculate Avg Score if numeric
        df['numeric_score'] = pd.to_numeric(df[csat_col].astype(str).str.extract('(\d+)')[0], errors='coerce')
        avg_score = df['numeric_score'].mean()
        m3.metric("Avg Quality Score", f"{avg_score:.2f}" if not pd.isna(avg_score) else "N/A")

        # 4. Executive Performance Table
        st.markdown("### Agent-wise Audit Summary")
        summary = df.groupby(agent_col).agg(
            calls_taken=(ticket_col, 'count'),
            csat_collected=('Sentiment', lambda x: (x != "No Rating").sum()),
            positives=('Sentiment', lambda x: (x == "Positive").sum()),
            negatives=('Sentiment', lambda x: (x == "Negative").sum())
        ).reset_index()

        # Calculate agent-specific collection percentage
        summary['Collection %'] = (summary['csat_collected'] / summary['calls_taken'] * 100).round(1)
        
        # Rename columns for the final display
        summary.columns = ['Executive Name', 'Calls Taken', 'CSAT Collected', 'Positive (4-5)', 'Negative (1-3)', 'Collection %']
        
        st.dataframe(summary.sort_values(by='Calls Taken', ascending=False), use_container_width=True)

        # 5. Visual Breakdown
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Sentiment Distribution")
            sent_counts = valid_csats['Sentiment'].value_counts().reset_index()
            fig_pie = px.pie(sent_counts, names='index', values='Sentiment', hole=0.4,
                             color_discrete_map={'Positive': '#22C55E', 'Negative': '#EF4444'})
            st.plotly_chart(fig_pie, use_container_width=True)
            
        with c2:
            st.subheader("Collection Rate by Agent")
            fig_bar = px.bar(summary, x='Executive Name', y='Collection %', 
                             color_discrete_sequence=['#F37021'])
            st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.error("Audit columns ('Agent' or 'Csat') not found in the file.")

# Usage Example (if df is your uploaded dataframe):
# show_audit_tracker(df)
        
        # 4. Executive Performance Table
        st.markdown("### Agent-wise Audit Summary")
        summary = df.groupby(agent_col).agg(
            calls_taken=(ticket_col, 'count'),
            csat_collected=('Sentiment', lambda x: (x != "No Rating").sum()),
            positives=('Sentiment', lambda x: (x == "Positive").sum()),
            negatives=('Sentiment', lambda x: (x == "Negative").sum())
        ).reset_index()

        # Calculate agent-specific collection percentage
        summary['Collection %'] = (summary['csat_collected'] / summary['calls_taken'] * 100).round(1)
        
        # Rename columns for the final display
        summary.columns = ['Executive Name', 'Calls Taken', 'CSAT Collected', 'Positive (4-5)', 'Negative (1-3)', 'Collection %']
        
        st.dataframe(summary.sort_values(by='Calls Taken', ascending=False), use_container_width=True)

        # 5. Visual Breakdown
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Sentiment Distribution")
            sent_counts = valid_csats['Sentiment'].value_counts().reset_index()
            fig_pie = px.pie(sent_counts, names='index', values='Sentiment', hole=0.4,
                             color_discrete_map={'Positive': '#22C55E', 'Negative': '#EF4444'})
            st.plotly_chart(fig_pie, use_container_width=True)
            
        with c2:
            st.subheader("Collection Rate by Agent")
            fig_bar = px.bar(summary, x='Executive Name', y='Collection %', 
                             color_discrete_sequence=['#F37021'])
            st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.error("Audit columns ('Agent' or 'Csat') not found in the file.")

# Usage Example (if df is your uploaded dataframe):
# show_audit_tracker(df)

# --- 4. PREDICTIONS (PERMANENT BOTTOM) ---
st.markdown("---")
st.subheader("🔮 Predictive Insights")
p1, p2 = st.columns(2)
with p1:
    st.markdown(f'<div class="insight-card"><b>📅 Backlog Forecast</b><br>Remaining Volume: Calculated based on Support Data.</div>', unsafe_allow_html=True)
with p2:
    st.markdown(f'<div class="insight-card"><b>🚀 Capacity Planning</b><br>Quality trends suggest focus on low-score query types.</div>', unsafe_allow_html=True)
