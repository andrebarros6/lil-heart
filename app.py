"""
Baby Development Timeline - Main Application
A digital family photo album to document baby's growth with photos and measurements.
"""

import streamlit as st

# Page configuration - must be the first Streamlit command
st.set_page_config(
    page_title="Baby Timeline",
    page_icon="👶",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    """Main application entry point"""

    # Welcome message
    st.title("👶 Baby Development Timeline")
    st.write("Welcome to your baby's digital memory book!")

    st.info("""
    🚀 **MVP Development in Progress**

    This application will help you:
    - 📸 Upload and organize baby photos with captions
    - 📏 Track growth measurements (height & weight)
    - 📊 Visualize growth with interactive charts
    - 🔗 Share memories with family via private links

    **Next Steps:**
    1. Set up Supabase project
    2. Configure authentication
    3. Implement photo upload
    4. Add measurements tracking
    5. Create growth charts
    6. Enable family sharing
    """)

    # Show project structure
    with st.expander("📁 Project Structure"):
        st.code("""
lil_heart/
├── app.py                      ← You are here!
├── requirements.txt
├── .env (create this next)
├── .streamlit/config.toml
├── src/
│   ├── __init__.py
│   ├── auth.py                 ← Authentication logic
│   ├── database.py             ← Database operations
│   ├── storage.py              ← Photo storage
│   ├── sharing.py              ← Family sharing
│   └── utils.py                ← Helper functions
├── pages/
│   ├── 1_📸_Upload_Photo.py
│   ├── 2_📏_Add_Measurement.py
│   ├── 3_📊_Growth_Chart.py
│   └── 4_🔗_Sharing.py
└── supabase_migrations/
    ├── 01_create_tables.sql
    └── 02_enable_rls.sql
        """, language="text")

    # Setup instructions
    with st.expander("⚙️ Setup Instructions"):
        st.markdown("""
        ### 1. Create Supabase Project
        - Go to [https://supabase.com/dashboard](https://supabase.com/dashboard)
        - Create new project: "baby-timeline-prod"
        - Choose region: Europe (Frankfurt or Ireland)
        - Save your database password securely

        ### 2. Get API Keys
        - Go to Project Settings → API
        - Copy `URL` and `anon` key
        - Copy `service_role` key (keep this secret!)

        ### 3. Create `.env` File
        ```env
        SUPABASE_URL=https://xxxxx.supabase.co
        SUPABASE_ANON_KEY=your_anon_key_here
        SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here
        ```

        ### 4. Install Dependencies
        ```bash
        python -m venv venv
        source venv/bin/activate  # Windows: venv\\Scripts\\activate
        pip install -r requirements.txt
        ```

        ### 5. Run the App
        ```bash
        streamlit run app.py
        ```
        """)

if __name__ == "__main__":
    main()
