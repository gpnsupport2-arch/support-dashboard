import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Customer Support Dashboard", layout="wide")

st.title("🎧 Support Operations Dashboard")
st.markdown("Upload your support export (CSV/XLSX) to refresh the metrics.")

# File Uploader
uploaded_file = st.file_uploader("Choose a file", type=['csv', 'xlsx'])

if uploaded_file:
    # Load data
    df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
    
    # --- KPI Row ---
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Tickets", len(df))
    col2.metric("Avg. Response Time", f"{df['response_hours'].mean():.2f}h")
    col3.metric("CSAT Score", f"{df['csat'].mean():.1f}/5")

    # --- Charts ---
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("Tickets by Channel")
        fig_channel = px.pie(df, names='channel', hole=0.4)
        st.plotly_chart(fig_channel, use_container_width=True)
        
    with c2:
        st.subheader("Volume Trend")
        df['date'] = pd.to_datetime(df['date'])
        trend_data = df.groupby('date').size().reset_index(name='counts')
        fig_trend = px.line(trend_data, x='date', y='counts')
        st.plotly_chart(fig_trend, use_container_width=True)

else:
    st.info("Please upload a file to view the analysis.")