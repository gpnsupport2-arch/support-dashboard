st.sidebar.title("🔌 Data Connectors")

# UI for Performance Uploader
st.sidebar.subheader("📂 Performance Tracker")
src_p = st.sidebar.radio("Format", ["Excel/CSV", "Google Sheet"], key="src_p")
if src_p == "Google Sheet":
    url_p = st.sidebar.text_input("Link", key="url_p")
else:
    file_p = st.sidebar.file_uploader("Upload", type=['xlsx', 'csv'], key="file_p")

# UI for Audit Uploader
st.sidebar.subheader("📂 Audit Tracker")
src_a = st.sidebar.radio("Format", ["Excel/CSV", "Google Sheet"], key="src_a")
# ... similar logic for Audit ...
