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
