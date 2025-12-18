"""
Baby Development Timeline - Main Application
A digital family photo album to document baby's growth with photos and measurements.
"""

import streamlit as st
from datetime import datetime
from src.auth import (
    login,
    logout,
    is_authenticated,
    get_current_user,
    get_supabase_client,
    init_supabase
)
from src.sharing import validate_share_token
from src.ui_helpers import load_css

# ============================================================================
# Page Configuration (MUST be first Streamlit command)
# ============================================================================
st.set_page_config(
    page_title="👶 Timeline",
    page_icon="👶",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# Load Custom Styles
# ============================================================================
load_css()

# ============================================================================
# Main Application
# ============================================================================

def show_login_page():
    """Display login page for admin users"""

    # Center-aligned login form
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.title("🔐 Baby Timeline Login")
        st.write("Sign in to manage your baby's timeline")

        # Login form
        with st.form("login_form", clear_on_submit=True):
            email = st.text_input(
                "Email",
                placeholder="parent@example.com",
                help="Use the email you created in Supabase Dashboard"
            )
            password = st.text_input(
                "Password",
                type="password",
                help="Your secure password"
            )

            # Submit button
            col_a, col_b = st.columns(2)
            with col_a:
                submit = st.form_submit_button("🔓 Log In", use_container_width=True)
            with col_b:
                forgot = st.form_submit_button("Forgot Password?", use_container_width=True)

            if submit:
                if not email or not password:
                    st.error("❌ Please enter both email and password")
                else:
                    with st.spinner("Logging in..."):
                        success, message = login(email, password)

                    if success:
                        st.success(message)
                        st.balloons()
                        # Wait a moment for user to see success message
                        import time
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error(message)

            if forgot:
                st.info("💡 Contact your administrator to reset your password")

        # Setup instructions for first-time users
        with st.expander("ℹ️ First time here?"):
            st.markdown("""
            **Setting up your account:**

            1. **Create Supabase Account**
               - Visit [https://supabase.com/dashboard](https://supabase.com/dashboard)
               - Create a new project

            2. **Run Database Migrations**
               - See `SUPABASE_SETUP.md` for detailed instructions
               - Run `01_create_tables.sql` and `02_enable_rls.sql`

            3. **Create Admin User**
               - In Supabase Dashboard → Authentication → Users
               - Click "Add user" → Create new user
               - Use that email/password to log in here

            4. **Configure Environment**
               - Copy `.env.example` to `.env`
               - Add your Supabase URL and API keys

            **Need help?** Check the README.md file in the project directory.
            """)


def show_sidebar():
    """Display sidebar with navigation and user info"""

    with st.sidebar:
        # User info at top
        user = get_current_user()
        if user:
            st.markdown(f"**Logged in as:**")
            st.code(user.email, language=None)

        st.divider()

        # Navigation info
        st.markdown("### 📱 Navigation")
        st.info("""
        Use the pages in the sidebar to:
        - 📸 Upload photos
        - 📏 Add measurements
        - 📊 View growth charts
        - 🔗 Share with family
        """)

        st.divider()

        # Logout button at bottom
        if st.button("🚪 Logout", use_container_width=True, type="secondary"):
            logout()


def show_timeline():
    """Display main timeline view with photos and measurements"""

    st.title("👶 Baby Development Timeline")

    try:
        supabase = get_supabase_client()

        # ========================================================================
        # Step 1: Check if baby profile exists (MVP: single baby support)
        # ========================================================================
        babies = supabase.table("babies").select("*").execute()

        if not babies.data:
            # No baby profile yet - show setup prompt
            st.warning("👋 **Welcome!** Let's set up your baby's profile first.")

            with st.form("create_baby_profile"):
                st.markdown("### Create Baby Profile")

                col1, col2 = st.columns(2)
                with col1:
                    baby_name = st.text_input(
                        "Baby's Name",
                        placeholder="e.g., Emma",
                        help="First name or nickname"
                    )
                with col2:
                    birthdate = st.date_input(
                        "Birthdate",
                        value=datetime.now(),
                        max_value=datetime.now(),
                        help="When was your baby born?"
                    )

                submitted = st.form_submit_button("✨ Create Profile", use_container_width=True)

                if submitted:
                    if not baby_name:
                        st.error("❌ Please enter a name")
                    else:
                        try:
                            from src.auth import get_user_id

                            # Insert baby profile
                            supabase.table("babies").insert({
                                "name": baby_name,
                                "birthdate": str(birthdate),
                                "created_by": get_user_id()
                            }).execute()

                            st.success(f"✅ Profile created for {baby_name}!")
                            st.balloons()
                            st.rerun()

                        except Exception as e:
                            st.error(f"❌ Error creating profile: {str(e)}")

            st.stop()

        # Get baby info
        baby = babies.data[0]
        baby_id = baby["baby_id"]
        baby_name = baby["name"]

        # ========================================================================
        # Step 2: Fetch photos and measurements for timeline
        # ========================================================================

        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.markdown(f"### {baby_name}'s Timeline")
        with col2:
            sort_order = st.selectbox(
                "Sort",
                ["Oldest First", "Newest First"],
                label_visibility="collapsed",
                key="timeline_sort_order"
            )
        with col3:
            filter_option = st.selectbox(
                "Filter",
                ["All", "Photos Only", "Measurements Only"],
                label_visibility="collapsed"
            )

        # Fetch data
        with st.spinner("Loading timeline..."):
            photos_response = supabase.table("photos") \
                .select("*") \
                .eq("baby_id", baby_id) \
                .order("photo_date", desc=True) \
                .limit(50) \
                .execute()

            measurements_response = supabase.table("measurements") \
                .select("*") \
                .eq("baby_id", baby_id) \
                .order("measurement_date", desc=True) \
                .limit(50) \
                .execute()

            photos = photos_response.data if photos_response.data else []
            measurements = measurements_response.data if measurements_response.data else []

        # ========================================================================
        # Step 3: Combine and sort timeline items
        # ========================================================================

        timeline_items = []

        # Add photos
        if filter_option in ["All", "Photos Only"]:
            for photo in photos:
                timeline_items.append({
                    "type": "photo",
                    "date": photo["photo_date"],
                    "data": photo
                })

        # Add measurements
        if filter_option in ["All", "Measurements Only"]:
            for measurement in measurements:
                timeline_items.append({
                    "type": "measurement",
                    "date": measurement["measurement_date"],
                    "data": measurement
                })

        # Sort by date based on user preference
        reverse_sort = (sort_order == "Newest First")
        timeline_items.sort(key=lambda x: x["date"], reverse=reverse_sort)

        # ========================================================================
        # Step 4: Display timeline
        # ========================================================================

        if not timeline_items:
            st.info("""
            📸 **No timeline entries yet!**

            Get started by:
            1. **Upload a photo** → Use the "📸 Upload Photo" page
            2. **Add measurements** → Use the "📏 Add Measurement" page

            Your timeline will appear here once you add content.
            """)
        else:
            st.caption(f"Showing {len(timeline_items)} entries")

            # Display each timeline item
            for item in timeline_items:
                if item["type"] == "photo":
                    # ========== Photo Card ==========
                    photo_data = item["data"]

                    with st.container():
                        col_img, col_info = st.columns([1, 3])

                        with col_img:
                            # Display photo thumbnail
                            try:
                                # Build accessible alt text
                                alt_text = f"{baby_name}'s photo from {photo_data['photo_date']}"
                                if photo_data.get("caption"):
                                    alt_text += f": {photo_data['caption']}"

                                st.image(
                                    photo_data["file_url"],
                                    caption=alt_text,
                                    use_container_width=True
                                )
                            except Exception as e:
                                st.error(f"Could not load image")
                                with st.expander("Debug info"):
                                    st.write(f"URL: {photo_data['file_url']}")
                                    st.write(f"Error: {str(e)}")

                        with col_info:
                            # Photo date
                            st.markdown(f"**📅 {photo_data['photo_date']}**")

                            # Caption
                            if photo_data.get("caption"):
                                st.write(photo_data["caption"])
                            else:
                                st.caption("_No caption_")

                            # Metadata
                            upload_time = datetime.fromisoformat(
                                photo_data["upload_date"].replace("Z", "+00:00")
                            )
                            st.caption(f"Uploaded: {upload_time.strftime('%b %d, %Y at %I:%M %p')}")

                        st.divider()

                else:
                    # ========== Measurement Card ==========
                    measurement_data = item["data"]

                    with st.container():
                        st.markdown(f"**📏 {measurement_data['measurement_date']}**")

                        col_weight, col_height, col_notes = st.columns([1, 1, 2])

                        with col_weight:
                            if measurement_data.get("weight_kg"):
                                st.metric("Weight", f"{measurement_data['weight_kg']} kg")
                            else:
                                st.caption("_No weight recorded_")

                        with col_height:
                            if measurement_data.get("height_cm"):
                                st.metric("Height", f"{measurement_data['height_cm']} cm")
                            else:
                                st.caption("_No height recorded_")

                        with col_notes:
                            if measurement_data.get("notes"):
                                st.write(f"📝 {measurement_data['notes']}")

                        st.divider()

    except ValueError as e:
        # Environment not configured
        st.error(str(e))
        st.info("👉 **Next Steps:** Follow the setup guide in `SUPABASE_SETUP.md`")
        st.stop()

    except Exception as e:
        st.error(f"❌ Error loading timeline: {str(e)}")
        st.exception(e)  # Show full stack trace in development


def show_viewer_login(share_token: str):
    """Display password prompt for password-protected share links"""

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.title("🔒 Password Required")
        st.write("This timeline is password-protected")

        # Password form
        with st.form("viewer_password_form"):
            password = st.text_input(
                "Enter password",
                type="password",
                placeholder="Ask the family for the password",
                help="Password was set by the timeline admin"
            )

            submitted = st.form_submit_button("🔓 View Timeline", use_container_width=True)

            if submitted:
                if not password:
                    st.error("❌ Please enter the password")
                else:
                    with st.spinner("Validating..."):
                        supabase = init_supabase()
                        is_valid, result = validate_share_token(supabase, share_token, password)

                    if is_valid:
                        # Store validated session
                        st.session_state["viewer_authenticated"] = True
                        st.session_state["viewer_baby_id"] = result
                        st.session_state["viewer_mode"] = True
                        st.success("✅ Access granted!")
                        st.balloons()
                        import time
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error(result)

        st.divider()
        st.caption("💡 Don't have the password? Ask the family member who shared this link with you.")


def show_viewer_sidebar(baby_name: str):
    """Display sidebar for viewer mode (read-only)"""

    with st.sidebar:
        # Viewer status
        st.markdown("### 👀 View-Only Mode")
        st.caption(f"Viewing: **{baby_name}'s Timeline**")

        st.divider()

        # Limited navigation info
        st.markdown("### 📱 Available Views")
        st.info("""
        You can:
        - 📸 View photos
        - 📏 See measurements
        - 📊 Check growth charts

        _(Upload and edit disabled)_
        """)

        st.divider()

        # Exit viewer mode
        if st.button("🚪 Exit Viewer Mode", use_container_width=True, type="secondary"):
            # Clear viewer session
            for key in ["viewer_authenticated", "viewer_baby_id", "viewer_mode"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()


def main():
    """Main application entry point"""

    # ========================================================================
    # Step 1: Check for share token (viewer mode)
    # ========================================================================
    query_params = st.query_params
    share_token = query_params.get("share_token")

    if share_token:
        # ==================== Viewer Mode ====================
        # Check if already validated
        if st.session_state.get("viewer_authenticated") and \
           st.session_state.get("viewer_baby_id"):
            # Viewer is authenticated - show read-only timeline
            baby_id = st.session_state["viewer_baby_id"]

            try:
                supabase = init_supabase()

                # Fetch baby info
                baby_result = supabase.table("babies").select("*").eq("baby_id", baby_id).execute()

                if not baby_result.data:
                    st.error("❌ Timeline not found or access has been revoked")
                    st.info("The share link may have been deactivated by the family. Please ask for a new link.")
                    st.stop()

                baby = baby_result.data[0]
                baby_name = baby["name"]

                # Show viewer sidebar and timeline (read-only)
                show_viewer_sidebar(baby_name)

                # Show timeline with viewer mode flag
                st.session_state["viewer_mode"] = True
                show_timeline()

            except Exception as e:
                st.error(f"❌ Error loading timeline: {str(e)}")
                st.info("Please try refreshing the page. If the problem persists, ask for a new share link.")

        else:
            # Token exists but not validated yet
            # Check if password is required
            supabase = init_supabase()
            is_valid, result = validate_share_token(supabase, share_token, password=None)

            if is_valid:
                # No password required - grant access
                st.session_state["viewer_authenticated"] = True
                st.session_state["viewer_baby_id"] = result
                st.session_state["viewer_mode"] = True
                st.rerun()
            elif result == "password_required":
                # Password required - show password form
                show_viewer_login(share_token)
            else:
                # Invalid or expired token
                st.error(result)
                st.info("💡 The share link may be invalid or expired. Please ask the family for a new link.")
                st.stop()

    # ========================================================================
    # Step 2: Normal admin authentication flow
    # ========================================================================
    elif not is_authenticated():
        # Show login page for admins
        show_login_page()
    else:
        # Admin authenticated - show full app
        show_sidebar()
        show_timeline()


if __name__ == "__main__":
    main()
