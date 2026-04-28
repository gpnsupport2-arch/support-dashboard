# --- TAB 1: PERFORMANCE OVERVIEW (FIXED) ---
with t1:
    st.title("🎧 Support Operations")
    
    if df_s is not None:
        df_s.columns = [str(c).strip() for c in df_s.columns]
        
        # 1. Smarter Column Mapping for your specific file
        e_col = find_col(['agent', 'executive'], df_s)
        cat_col = find_col(['category'], df_s)
        aht_col = find_col(['aht'], df_s)

        # 2. Key Metrics Row
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Tickets Handled", len(df_s))
        
        if aht_col:
            df_s['AHT_Mins'] = df_s[aht_col].apply(aht_to_minutes)
            avg_aht = df_s[df_s['AHT_Mins'] > 0]['AHT_Mins'].mean()
            m2.metric("Avg Handling Time", f"{avg_aht:.2f} min")
        
        # 3. Workload Charts
        c1, c2 = st.columns(2)
        
        with c1:
            st.subheader("Distribution by Executive")
            if e_col:
                fig_exec = px.pie(df_s, names=e_col, hole=0.4, 
                                 color_discrete_sequence=px.colors.sequential.Oranges_r)
                fig_exec.update_layout(paper_bgcolor='rgba(0,0,0,0)', font=dict(color="white"))
                st.plotly_chart(fig_exec, use_container_width=True)
            else:
                st.warning("Column 'Agent' not found for workload chart.")

        with c2:
            st.subheader("Executive Deep-Dive")
            if e_col:
                # Selectbox for agents found in your file (Faizan, Siddhi, etc.)
                agent_list = sorted(df_s[e_col].dropna().unique())
                selected_agent = st.selectbox("Select Executive to Analyze:", agent_list)
                
                # Filter data for selected agent
                agent_data = df_s[df_s[e_col] == selected_agent]
                
                # Show what categories this specific agent is handling
                if cat_col:
                    fig_sub = px.bar(agent_data[cat_col].value_counts().reset_index(), 
                                    x='index', y=cat_col, 
                                    labels={'index': 'Category', 'Category': 'Count'},
                                    title=f"Category Breakdown for {selected_agent}",
                                    color_discrete_sequence=[BRAND_ORANGE])
                    fig_sub.update_layout(paper_bgcolor='rgba(0,0,0,0)', font=dict(color="white"))
                    st.plotly_chart(fig_sub, use_container_width=True)
                else:
                    st.info("Upload file with a 'Category' column to see agent breakdown.")
    else:
        st.info("Waiting for data... Please upload your file in the sidebar.")
