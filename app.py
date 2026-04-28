import streamlit as st
import pandas as pd
import plotly.express as px

# --- AUDIT TRACKER MODULE ---
def show_audit_tracker(df):
    st.subheader("🕵️ Executive Quality & CSAT Performance")
    
    # 1. Identify Columns (Resilient Mapping)
    agent_col = next((c for c in df.columns if 'agent' in c.lower() or 'executive' in c.lower()), None)
    csat_col = next((c for c in df.columns if 'csat' in c.lower() or 'rating' in c.lower()), None)
    ticket_col = next((c for c in df.columns if 'ticket' in c.lower() or 'id' in c.lower()), df.columns[0])

    if agent_col and csat_col:
        # 2. Define Sentiment Logic (Instruction: 4-5 Pos, 1-3 Neg)
        def get_sentiment(val):
            v = str(val).lower()
            if any(x in v for x in ['5', '4', 'excellent', 'good']): 
                return "Positive"
            if any(x in v for x in ['1', '2', '3', 'poor', 'average']): 
                return "Negative"
            return "No Rating"

        df['Sentiment'] = df[csat_col].apply(get_sentiment)

        # 3. Top Row Metrics for Audits
        total_calls = len(df)
        valid_csats = df[df['Sentiment'] != "No Rating"]
        csat_count = len(valid_csats)
        coll_rate = (csat_count / total_calls * 100) if total_calls > 0 else 0

        m1, m2, m3 = st.columns(3)
        m1.metric("Total CSAT Collected", csat_count)
        m2.metric("Overall Collection %", f"{coll_rate:.1f}%")
        
        # Calculate Avg Score if numeric
        df['numeric_score'] = pd.to_numeric(df[csat_col].astype(str).str.extract('(\d+)')[0], errors='coerce')
        avg_score = df['numeric_score'].mean()
        m3.metric("Avg Quality Score", f"{avg_score:.2f}" if not pd.isna(avg_score) else "N/A")

        # 4. Executive Performance Table
        st.markdown("### Agent-wise Audit Summary")
        summary = df.groupby(agent_col).agg(
            calls_taken=(ticket_col, 'count'),
            csat_collected=('Sentiment', lambda x: (x != "No Rating").sum()),
            positives=('Sentiment', lambda x: (x == "Positive").sum()),
            negatives=('Sentiment', lambda x: (x == "Negative").sum())
        ).reset_index()

        # Calculate agent-specific collection percentage
        summary['Collection %'] = (summary['csat_collected'] / summary['calls_taken'] * 100).round(1)
        
        # Rename columns for the final display
        summary.columns = ['Executive Name', 'Calls Taken', 'CSAT Collected', 'Positive (4-5)', 'Negative (1-3)', 'Collection %']
        
        st.dataframe(summary.sort_values(by='Calls Taken', ascending=False), use_container_width=True)

        # 5. Visual Breakdown
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Sentiment Distribution")
            sent_counts = valid_csats['Sentiment'].value_counts().reset_index()
            fig_pie = px.pie(sent_counts, names='index', values='Sentiment', hole=0.4,
                             color_discrete_map={'Positive': '#22C55E', 'Negative': '#EF4444'})
            st.plotly_chart(fig_pie, use_container_width=True)
            
        with c2:
            st.subheader("Collection Rate by Agent")
            fig_bar = px.bar(summary, x='Executive Name', y='Collection %', 
                             color_discrete_sequence=['#F37021'])
            st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.error("Audit columns ('Agent' or 'Csat') not found in the file.")

# Usage Example (if df is your uploaded dataframe):
# show_audit_tracker(df)
