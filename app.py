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
    import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Executive Support Dashboard", layout="wide")
st.title("📊 Customer Support Performance Dashboard")

uploaded_file = st.file_uploader("Upload Support Data", type=['csv', 'xlsx'])

if uploaded_file:
    # 1. Load Data
    df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
    
    # 2. Preparation: Convert timestamp to readable dates
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['Month'] = df['timestamp'].dt.strftime('%B %Y')

    # 3. Top Metrics Row
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Tickets", len(df))
    
    # Check for Resolution (Searching in 'crm_r...' or status column)
    # Adjust 'crm_status' below if your status column has a different name
    if 'status' in df.columns:
        resolved = len(df[df['status'].str.contains('Resolved|Closed', case=False, na=False)])
        col2.metric("Resolved Tickets", resolved)
        col3.metric("Open Tickets", len(df) - resolved)
    else:
        col2.info("Add a 'Status' column to see Resolution rates")

    st.markdown("---")

    # 4. Monthly Issue Analysis (Which issues are raised most)
    st.subheader("📈 Most Frequent Issues by Month")
    if 'query_type' in df.columns:
        # Filter for top issues
        issue_counts = df.groupby(['Month', 'query_type']).size().reset_index(name='Count')
        fig_issues = px.bar(issue_counts, x='Month', y='Count', color='query_type', barmark='group', title="Monthly Issue Volume")
        st.plotly_chart(fig_issues, use_container_width=True)

    # 5. Executive Performance (Performance by Email/Agent)
    st.subheader("👤 Executive Performance (Ticket Volume)")
    # Using email_address as a proxy for the executive/agent name
    agent_col = 'email_address' if 'email_address' in df.columns else None
    
    if agent_col:
        exec_perf = df[agent_col].value_counts().reset_index()
        exec_perf.columns = ['Executive', 'Tickets Handled']
        fig_exec = px.bar(exec_perf, x='Executive', y='Tickets Handled', color='Tickets Handled', title="Tickets per Executive")
        st.plotly_chart(fig_exec, use_container_width=True)

    # 6. Raw Data Search
    with st.expander("🔍 Search Full Data"):
        st.dataframe(df)
else:
    st.info("Please upload your Excel file to generate the performance report.")
