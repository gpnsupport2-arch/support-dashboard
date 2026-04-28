import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Page Config
st.set_page_config(page_title="Support Ops Dashboard", layout="wide")

st.title("📊 Customer Support Performance Portal")

uploaded_file = st.file_uploader("Upload your 'CS - SOS' file", type=['csv', 'xlsx'])

if uploaded_file:
    # Load Data
    df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
    
    # 2. Data Cleaning & Dates
    if 'Timestamp' in df.columns:
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        df['Month'] = df['Timestamp'].dt.strftime('%B %Y')
        df['Date'] = df['Timestamp'].dt.date
    
    # 3. Sidebar Filters (Slicers)
    st.sidebar.header("🔍 Dashboard Filters")
    
    # Month Filter
    months = ["All Months"] + sorted(df['Month'].unique().tolist())
    sel_month = st.sidebar.selectbox("Filter by Month", months)
    
    # Executive Filter
    exec_col = 'Email Address' if 'Email Address' in df.columns else None
    execs = ["All Executives"] + sorted(df[exec_col].dropna().unique().tolist()) if exec_col else ["N/A"]
    sel_exec = st.sidebar.selectbox("Filter by Executive", execs)
    
    # Channel Filter (New!)
    chan_col = 'Channel' if 'Channel' in df.columns else None
    channels = ["All Channels"] + sorted(df[chan_col].dropna().unique().tolist()) if chan_col else ["N/A"]
    sel_chan = st.sidebar.selectbox("Filter by Channel (Email/Call)", channels)

    # Applying Filters
    f_df = df.copy()
    if sel_month != "All Months":
        f_df = f_df[f_df['Month'] == sel_month]
    if exec_col and sel_exec != "All Executives":
        f_df = f_df[f_df[exec_col] == sel_exec]
    if chan_col and sel_chan != "All Channels":
        f_df = f_df[f_df[chan_col] == sel_chan]

    # 4. KPI Scorecards
    st.markdown("### 📈 Core Metrics")
    k1, k2, k3, k4, k5 = st.columns(5)
    
    k1.metric("Total Tickets", len(f_df))
    
    if 'Ticket status' in f_df.columns:
        res = len(f_df[f_df['Ticket status'].str.contains('Resolved', case=False, na=False)])
        cld = len(f_df[f_df['Ticket status'].str.contains('Closed', case=False, na=False)])
        k2.metric("Resolved", res)
        k3.metric("Closed", cld)
    
    # Channel Split Metrics
    if chan_col:
        email_cnt = len(f_df[f_df[chan_col].str.contains('Email', case=False, na=False)])
        call_cnt = len(f_df[f_df[chan_col].str.contains('Call', case=False, na=False)])
        k4.metric("Email Tickets", email_cnt)
        k5.metric("Call Tickets", call_cnt)

    # 5. Presentation Charts
    st.markdown("---")
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("📬 Channel Distribution")
        if chan_col:
            fig_chan = px.pie(f_df, names=chan_col, hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig_chan, use_container_width=True)

    with c2:
        st.subheader("👤 Executive Performance")
        if exec_col:
            perf = f_df[exec_col].value_counts().reset_index()
            perf.columns = ['Executive', 'Tickets']
            fig_exec = px.bar(perf.head(10), x='Tickets', y='Executive', orientation='h', color='Tickets')
            st.plotly_chart(fig_exec, use_container_width=True)

    st.markdown("---")
    c3, c4 = st.columns(2)

    with c3:
        st.subheader("❓ Query Trends (Top Issues)")
        if 'Query type' in f_df.columns:
            q_counts = f_df['Query type'].value_counts().reset_index().head(10)
            q_counts.columns = ['Query', 'Count']
            fig_q = px.bar(q_counts, x='Count', y='Query', orientation='h', color_discrete_sequence=['#FF4B4B'])
            st.plotly_chart(fig_q, use_container_width=True)

    with c4:
        st.subheader("⏱️ Speed Metrics (AHT & FRT)")
        # Placeholders for your future columns
        aht = f"{f_df['AHT'].mean():.1f}m" if 'AHT' in f_df.columns else "No Data"
        frt = f"{f_df['FRT'].mean():.1f}m" if 'FRT' in f_df.columns else "No Data"
        
        st.info(f"**Average Call Handling Time (AHT):** {aht}")
        st.info(f"**First Response Time (FRT):** {frt}")
        st.caption("Note: Add 'AHT' and 'FRT' columns to your file to update these automatically.")

    # 6. Data Explorer
    with st.expander("🔍 Search & Filter Raw Data"):
        st.dataframe(f_df)

else:
    st.info("Upload your Excel/CSV file to view the Presentation Dashboard.")
