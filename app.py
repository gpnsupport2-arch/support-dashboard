import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection

# UI Configuration: Sets the page to Wide Mode and Dark Theme
st.set_page_config(page_title="Primarc Pecan Portal", layout="wide")
BRAND_ORANGE, BRAND_NAVY = "#F37021", "#101828"

st.markdown(f"""
    <style>
    /* Dark background gradient */
    .stApp {{ background: linear-gradient(180deg, {BRAND_NAVY} 0%, #1D2939 100%); }}
    /* Metric Card Styling */
    div[data-testid="stMetric"] {{ 
        background-color: #1D2939; 
        border: 1px solid {BRAND_ORANGE}; 
        border-radius: 10px; 
        padding: 15px; 
    }}
    /* Tab Styling */
    .stTabs [aria-selected="true"] {{ 
        background-color: {BRAND_ORANGE} !important; 
        color: white !important;
        border-radius: 5px; 
    }}
    </style>
    """, unsafe_allow_html=True)

# Create the Tabs in the UI
tab1, tab2, tab3 = st.tabs(["📊 Performance Overview", "🕵️ Audit Tracker", "📋 Data Logs"])
with tab1:
    if df_perf_raw is not None:
        st.title("🎧 Operations Performance")
        df_p = df_perf_raw.copy()
        
        # UI Metrics Row
        m1, m2 = st.columns(2)
        m1.metric("Total Tickets Handled", len(df_p))
        
        # AHT Calculation Logic
        if 'AHT' in df_p.columns:
            # Converts HH:MM:SS to numeric minutes
            df_p['mins'] = df_p['AHT'].apply(parse_aht) 
            avg_val = df_p[df_p['mins'] > 0]['mins'].mean()
            m2.metric("Avg Handling Time", f"{avg_val:.2f} min")

        # Visualization UI
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(px.pie(df_p, names='Agent', hole=0.4, title="Agent Share"), use_container_width=True)
        with c2:
            st.plotly_chart(px.bar(df_p['Category'].value_counts().reset_index(), 
                                  x='index', y='Category', title="Volume by Category"), use_container_width=True)
            with tab2:
    if df_audit_raw is not None:
        st.title("🕵️ Quality Audit Summary")
        df_a = df_audit_raw.copy()
        
        # The Logic: Mapping Star Ratings to Sentiments
        def get_sent(v):
            v = str(v).lower()
            if any(x in v for x in ['5', '4', 'excellent', 'good']): return "Positive"
            if any(x in v for x in ['1', '2', '3', 'bad', 'poor', 'average']): return "Negative"
            return "No Rating"
        
        df_a['Sentiment'] = df_a['Csat'].apply(get_sent)
        
        # UI: Detailed Audit Table
        summary = df_a.groupby('Agent').agg(
            Calls=('Agent', 'count'),
            CSATs=('Sentiment', lambda x: (x != "No Rating").sum()),
            Positives=('Sentiment', lambda x: (x == "Positive").sum()),
            Negatives=('Sentiment', lambda x: (x == "Negative").sum())
        ).reset_index()
        
        # Formula for Collection Rate
        summary['Collection %'] = (summary['CSATs'] / summary['Calls'] * 100).round(1)
        st.dataframe(summary, use_container_width=True)
        st.sidebar.title("🔌 Data Connectors")

# UI for Performance Uploader
st.sidebar.subheader("📂 Performance Tracker")
src_p = st.sidebar.radio("Format", ["Excel/CSV", "Google Sheet"], key="src_p")
if src_p == "Google Sheet":
    url_p = st.sidebar.text_input("Link", key="url_p")
else:
    file_p = st.sidebar.file_uploader("Upload", type=['xlsx', 'csv'], key="file_p")

# UI for Audit Uploader
st.sidebar.subheader("📂 Audit Tracker")
src_a = st.sidebar.radio("Format", ["Excel/CSV", "Google Sheet"], key="src_a")
# ... similar logic for Audit ...
