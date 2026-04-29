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
