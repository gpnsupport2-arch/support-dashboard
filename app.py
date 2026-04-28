import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# --- PAGE CONFIG ---
st.set_page_config(page_title="Support Ops Dashboard", layout="wide", initial_sidebar_state="collapsed")

# --- ADVANCED CSS FOR MODERN UI ---
st.markdown("""
    <style>
    /* Main background */
    .stApp { background-color: #F8F9FA; }
    
    /* Custom Card Styling */
    .metric-card {
        background-color: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        border-top: 5px solid #FF6B00;
        text-align: center;
    }
    
    .metric-title { color: #6c757d; font-size: 14px; font-weight: 600; text-transform: uppercase; }
    .metric-value { color: #FF6B00; font-size: 32px; font-weight: 800; }
    
    /* Titles */
    h1, h2, h3 { color: #2D3436 !important; font-family: 'Inter', sans-serif; }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #eee; }
    </style>
    """, unsafe_allow_html=True)

# --- MOCK DATA GENERATOR ---
def load_data():
    agents = ['Sarah Jenkins', 'Mark Lohan', 'Elena Rodriguez', 'David Kim', 'Rachel Wong']
    data = {
        'Agent': agents,
        'Inbound Calls': [45, 32, 28, 50, 42],
        'Outbound Calls': [12, 25, 8, 15, 18],
        'Emails': [30, 20, 55, 25, 38],
        'Ticket AHT (min)': [4.2, 5.1, 4.8, 3.9, 4.5],
        'Call AHT (min)': [5.5, 6.2, 5.8, 5.1, 5.7],
        'Audit Score': [98, 88, 95, 91, 94],
        'CSAT': [4.9, 4.6, 4.8, 4.4, 4.9]
    }
    return pd.DataFrame(data)

df = load_data()
orange_shades = ['#FF6B00', '#FF8E3C', '#FFAE70', '#FFCDA3', '#FFEBD6']

# --- HEADER ---
st.title("🍊 OpsView | Support Intelligence")
st.markdown("Global Team Performance Metrics & Agent Audit Overview")
st.write("---")

# --- ROW 1: PROMINENT DATA PANELS ---
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown('<div class="metric-card"><p class="metric-title">Total Tickets</p><p class="metric-value">2,840</p></div>', unsafe_allow_html=True)
with col2:
    st.markdown('<div class="metric-card"><p class="metric-title">Tickets Resolved</p><p class="metric-value">2,105</p></div>', unsafe_allow_html=True)
with col3:
    st.markdown('<div class="metric-card"><p class="metric-title">Tickets Closed</p><p class="metric-value">1,980</p></div>', unsafe_allow_html=True)
with col4:
    st.markdown('<div class="metric-card"><p class="metric-title">Live CSAT</p><p class="metric-value">4.72</p></div>', unsafe_allow_html=True)

st.write("##")

# --- ROW 2: DYNAMIC CHARTS (AHT & CSAT) ---
c1, c2 = st.columns([2, 1])

with c1:
    st.subheader("⏱️ Handling Time Dynamics")
    fig_aht = go.Figure()
    fig_aht.add_trace(go.Bar(x=df['Agent'], y=df['Ticket AHT (min)'], name='Ticket AHT', marker_color='#FF6B00'))
    fig_aht.add_trace(go.Bar(x=df['Agent'], y=df['Call AHT (min)'], name='Call AHT', marker_color='#FFB380'))
    fig_aht.update_layout(barmode='group', plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', 
                          legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    st.plotly_chart(fig_aht, use_container_width=True)

with c2:
    st.subheader("⭐ CSAT Distribution (Emails)")
    fig_csat = px.line(df, x='Agent', y='CSAT', markers=True, color_discrete_sequence=['#FF6B00'])
    fig_csat.update_layout(yaxis_range=[0,5], plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig_csat, use_container_width=True)

# --- ROW 3: PRODUCTIVITY & CONTRIBUTION ---
st.write("---")
st.subheader("👥 Agent Contribution Breakdown")
tab1, tab2 = st.tabs(["Volume Analysis", "Call Audit Data"])

with tab1:
    # Stacked Bar for Contribution
    fig_contrib = px.bar(df, x="Agent", y=["Inbound Calls", "Outbound Calls", "Emails"],
                        title="Workload Distribution by Channel",
                        color_discrete_sequence=orange_shades)
    fig_contrib.update_layout(plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig_contrib, use_container_width=True)

with tab2:
    audit_col1, audit_col2 = st.columns([1, 2])
    with audit_col1:
        st.markdown("### Team Quality Avg")
        avg_audit = df['Audit_Score'].mean()
        st.metric("Overall Audit Score", f"{avg_audit}%", "+1.2%")
    with audit_col2:
        st.dataframe(df[['Agent', 'Audit_Score', 'CSAT']].style.background_gradient(cmap='Oranges'), use_container_width=True)

# --- FOOTER ---
st.markdown("<br><p style='text-align: center; color: #BDC3C7;'>OpsView Dashboard v2.0 | Powering Support Excellence</p>", unsafe_allow_html=True)
