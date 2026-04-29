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
