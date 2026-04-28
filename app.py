import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import base64
import logging
from datetime import datetime
from typing import Optional, List, Tuple, Dict, Any
from streamlit_gsheets import GSheetsConnection

# ============================================================================
# CONFIGURATION & LOGGING
# ============================================================================

# Configure logging for debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Brand Colors - Consistent across app
BRAND_ORANGE = "#F37021"
BRAND_NAVY = "#101828"
BRAND_WHITE = "#FFFFFF"
BRAND_DARK_GRAY = "#1D2939"
BRAND_LIGHT_GRAY = "#475467"
POSITIVE_GREEN = "#22C55E"
NEGATIVE_RED = "#EF4444"

# Page Configuration
st.set_page_config(
    page_title="Primarc Pecan | Operations Portal",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# 1. BRANDING & THEME STYLING
# ============================================================================

def apply_theme():
    """Apply consistent branding and styling across the application."""
    st.markdown(f"""
        <style>
        /* Main App Background */
        .stApp {{ 
            background: linear-gradient(180deg, {BRAND_NAVY} 0%, {BRAND_DARK_GRAY} 100%); 
        }}
        
        /* Text Elements */
        h1, h2, h3, h4, h5, h6, p, span, label, .stMarkdown {{ 
            color: {BRAND_WHITE} !important; 
        }}
        
        /* Logo Container */
        .logo-container {{ 
            display: flex; 
            justify-content: center; 
            padding: 20px; 
            background-color: rgba(255, 255, 255, 0.05); 
            border-radius: 0 0 20px 20px; 
            margin-bottom: 20px; 
        }}
        
        /* Dropdown/Select Elements */
        div[data-baseweb="select"] > div {{ 
            background-color: white !important; 
            color: {BRAND_NAVY} !important; 
            border-radius: 5px;
        }}
        div[role="listbox"] div {{ 
            color: {BRAND_NAVY} !important; 
        }}
        
        /* Metric Cards */
        div[data-testid="stMetric"] {{ 
            background-color: {BRAND_DARK_GRAY}; 
            border: 2px solid {BRAND_ORANGE}; 
            border-radius: 10px; 
            padding: 20px;
        }}
        [data-testid="stMetricValue"] {{ 
            color: {BRAND_ORANGE} !important; 
            font-size: 32px !important; 
        }}
        [data-testid="stMetricLabel"] {{ 
            color: {BRAND_WHITE} !important; 
        }}
        
        /* Sidebar */
        [data-testid="stSidebar"] {{ 
            background-color: {BRAND_NAVY} !important; 
            border-right: 2px solid {BRAND_ORANGE}; 
        }}
        
        /* Tabs */
        .stTabs [aria-selected="true"] {{ 
            background-color: {BRAND_ORANGE} !important; 
            border-radius: 5px; 
        }}
        
        /* Insight Cards */
        .insight-card {{ 
            background-color: rgba(255, 255, 255, 0.08); 
            border-left: 5px solid {BRAND_ORANGE}; 
            padding: 20px; 
            border-radius: 8px;
            margin: 10px 0;
        }}
        
        /* Dataframe styling */
        .stDataFrame, .stDataframe {{
            background-color: {BRAND_DARK_GRAY} !important;
        }}
        </style>
        """, unsafe_allow_html=True)

# ============================================================================
# 2. LOGO PLACEMENT
# ============================================================================

def display_logo():
    """Display company logo at the top of the page with fallback."""
    try:
        with open('primarc_pecan_logo.jpg', 'rb') as f:
            logo_data = base64.b64encode(f.read()).decode()
        st.markdown(
            f'<div class="logo-container"><img src="data:image/jpeg;base64,{logo_data}" width="250"></div>', 
            unsafe_allow_html=True
        )
    except FileNotFoundError:
        logger.warning("Logo file not found. Using fallback text.")
        st.markdown(
            f"<h1 style='text-align: center; color: {BRAND_ORANGE};'>PRIMARC PECAN</h1>",
            unsafe_allow_html=True
        )
    except Exception as e:
        logger.error(f"Error loading logo: {e}")
        st.markdown(
            f"<h1 style='text-align: center; color: {BRAND_ORANGE};'>PRIMARC PECAN</h1>",
            unsafe_allow_html=True
        )

# ============================================================================
# 3. UTILITY FUNCTIONS - TIME & DATA CONVERSION
# ============================================================================

def aht_to_minutes(time_str: str) -> float:
    """
    Convert Average Handle Time string to minutes.
    
    Handles formats: HH:MM:SS, MM:SS, or numeric values
    
    Args:
        time_str: Time string in format HH:MM:SS or MM:SS
        
    Returns:
        float: Total time in minutes
    """
    try:
        if pd.isna(time_str) or str(time_str).strip() == "" or str(time_str) == "0":
            return 0
        
        parts = str(time_str).split(':')
        
        if len(parts) == 3:  # HH:MM:SS
            return int(parts[0]) * 60 + int(parts[1]) + int(parts[2]) / 60
        elif len(parts) == 2:  # MM:SS
            return int(parts[0]) + int(parts[1]) / 60
        else:
            return float(time_str) if time_str else 0
    except (ValueError, TypeError):
        logger.warning(f"Could not convert AHT value: {time_str}")
        return 0

def find_column(targets: List[str], dataframe: Optional[pd.DataFrame]) -> Optional[str]:
    """
    Intelligently find a column in DataFrame by multiple possible names.
    
    Case-insensitive search. Returns first match found.*
