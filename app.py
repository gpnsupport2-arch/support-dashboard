import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Support Dashboard", layout="wide")
st.title("🎧 Support Team Presentation")

uploaded_file = st.file_uploader("Upload CSV or Excel", type=['csv', 'xlsx'])

if uploaded_file:
    # Load data
    df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
    
    # Clean column names (removes spaces and makes lowercase to prevent errors)
    df.columns = [c.strip().lower().replace(' ', '_') for c in df.columns]

    # --- KPI Row ---
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Tickets", len(df))

    # Safely calculate metrics
    if 'response_hours' in df.columns:
        col2.metric("Avg Response", f"{df['response_hours'].mean():.2f}h")
    else:
        col2.warning("Column 'response_hours' not found")

    if 'csat' in df.columns:
        col3.metric("Avg CSAT", f"{df['csat'].mean():.1f}/5")
    else:
        col3.warning("Column 'csat' not found")

    # Display the data so you can check headers during your presentation
    st.write("### Data Preview", df.head())
else:
    st.info("Please upload your support data file to begin.")
