with tab2:
    if df_audit_raw is not None:
        st.title("🕵️ Quality Audit Summary")
        df_a = df_audit_raw.copy()
        
        # The Logic: Mapping Star Ratings to Sentiments
        def get_sent(v):
            v = str(v).lower()
            if any(x in v for x in ['5', '4', 'excellent', 'good']): return "Positive"
            if any(x in v for x in ['1', '2', '3', 'bad', 'poor', 'average']): return "Negative"
            return "No Rating"
        
        df_a['Sentiment'] = df_a['Csat'].apply(get_sent)
        
        # UI: Detailed Audit Table
        summary = df_a.groupby('Agent').agg(
            Calls=('Agent', 'count'),
            CSATs=('Sentiment', lambda x: (x != "No Rating").sum()),
            Positives=('Sentiment', lambda x: (x == "Positive").sum()),
            Negatives=('Sentiment', lambda x: (x == "Negative").sum())
        ).reset_index()
        
        # Formula for Collection Rate
        summary['Collection %'] = (summary['CSATs'] / summary['Calls'] * 100).round(1)
        st.dataframe(summary, use_container_width=True)
