import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Page Config
st.set_page_config(page_title="CS Performance Dashboard", layout="wide", initial_sidebar_state="expanded")

# Custom Styling
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border: 1px solid #e6e9ef; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎧 Customer Support Executive Performance")

uploaded_file = st.file_uploader("Upload your CS - SOS Excel/CSV file", type=['csv', 'xlsx'])

if uploaded_file:
    # Load Data
    df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
    
    # 2. Data Cleaning
    if 'Timestamp' in df.columns:
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        df['Month'] = df['Timestamp'].dt.strftime('%B %Y')
        df['Date'] = df['Timestamp'].dt.date
    else:
        df['Month'] = "Unknown"

    # 3. Sidebar Slicers (Filters)
    st.sidebar.header("🔍 Filter Dashboard")
    
    # Month Filter
    months = ["All Months"] + sorted(df['Month'].unique().tolist())
    selected_month = st.sidebar.selectbox("Select Month", months)
    
    # Executive Filter
    exec_col = 'Email Address' if 'Email Address' in df.columns else df.columns[0]
    executives = ["All Executives"] + sorted(df[exec_col].dropna().unique().tolist())
    selected_exec = st.sidebar.selectbox("Select Executive", executives)

    # Apply Filters
    filtered_df = df.copy()
    if selected_month != "All Months":
        filtered_df = filtered_df[filtered_df['Month'] == selected_month]
    if selected_exec != "All Executives":
        filtered_df = filtered_df[filtered_df[exec_col] == selected_exec]

    # 4. Top KPI Row
    st.markdown("### 📊 Overview Metrics")
    m1, m2, m3, m4 = st.columns(4)
    
    total_received = len(filtered_df)
    m1.metric("Tickets Received", total_received)

    if 'Ticket status' in df.columns:
        res_count = len(filtered_df[filtered_df['Ticket status'].str.contains('Resolved', case=False, na=False)])
        closed_count = len(filtered_df[filtered_df['Ticket status'].str.contains('Closed', case=False, na=False)])
        m2.metric("Resolved", res_count)
        m3.metric("Closed", closed_count)
    
    # Future-proof for AHT (Handling Time)
    aht_val = f"{filtered_df['AHT'].mean():.1f}m" if 'AHT' in filtered_df.columns else "Pending"
    m4.metric("Avg Handling Time", aht_val)

    st.markdown("---")

    # 5. Trends and Performance Rows
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🔥 Top 10 Query Trends")
        if 'Query type' in filtered_df.columns:
            q_trends = filtered_df['Query type'].value_counts().reset_index().head(10)
            q_trends.columns = ['Query', 'Count']
            fig_q = px.bar(q_trends, x='Count', y='Query', orientation='h', 
                           color='Count', color_continuous_scale='Blues', template="plotly_white")
            st.plotly_chart(fig_q, use_container_width=True)

    with col2:
        st.subheader("👤 Executive Performance")
        if exec_col in filtered_df.columns:
            perf = filtered_df[exec_col].value_counts().reset_index()
            perf.columns = ['Executive', 'Tickets']
            fig_p = px.pie(perf, names='Executive', values='Tickets', hole=0.5, 
                           color_discrete_sequence=px.colors.qualitative.Safe)
            st.plotly_chart(fig_p, use_container_width=True)

    # 6. Monthly/Daily Volume Trend
    st.subheader("📅 Ticket Volume Trend")
    if 'Date' in filtered_df.columns:
        daily_trend = filtered_df.groupby('Date').size().reset_index(name='Tickets')
        fig_t = px.line(daily_trend, x='Date', y='Tickets', markers=True, template="plotly_white")
        fig_t.update_traces(line_color='#1f77b4', line_width=3)
        st.plotly_chart(fig_t, use_container_width=True)

    # 7. Raw Data
    with st.expander("📂 View Filtered Data Table"):
        st.dataframe(filtered_df)

else:
    st.info("👋 Ready for your presentation! Please upload the 'CS - SOS' file to see the live analytics.")
