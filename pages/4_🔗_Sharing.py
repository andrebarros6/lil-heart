"""
Family Sharing Page - Baby Timeline
Generate and manage share links for family members to view timeline read-only.
"""

import streamlit as st
from datetime import datetime
import os
from src.auth import require_auth, get_supabase_client
from src.sharing import (
    generate_share_link,
    get_active_share_link,
    revoke_share_link
)
from src.validators import validate_password

# ============================================================================
# Page Configuration
# ============================================================================
st.set_page_config(
    page_title="Family Sharing - Baby Timeline",
    page_icon="🔗",
    layout="wide"
)

# Require authentication (admin only)
require_auth()

# ============================================================================
# Main Page
# ============================================================================

st.title("🔗 Family Sharing")
st.write("Generate a private link to share your baby's timeline with family")

try:
    supabase = get_supabase_client()

    # ========================================================================
    # Step 1: Get baby info
    # ========================================================================
    babies = supabase.table("babies").select("*").execute()

    if not babies.data:
        st.error("❌ No baby profile found. Please create one from the main page.")
        st.page_link("Timeline.py", label="← Back to Main Page", icon="🏠")
        st.stop()

    baby = babies.data[0]
    baby_id = baby["baby_id"]
    baby_name = baby["name"]

    # ========================================================================
    # Step 2: Check for existing active link
    # ========================================================================
    active_link = get_active_share_link(supabase, baby_id)

    if active_link:
        # ==================== Display Active Link ====================
        st.success("✅ **Active share link found**")

        # Build shareable URL
        share_token = active_link["share_token"]

        # Get base URL from environment variable or use placeholder
        base_url = os.getenv("BASE_URL", "")

        if base_url:
            # Full URL is available
            share_url = f"{base_url}/?share_token={share_token}"
            st.markdown("**Your share link:**")
            st.code(share_url, language=None)
            st.caption("📋 Copy the link above and share via WhatsApp, Email, etc.")
        else:
            # No BASE_URL configured - show token and instructions
            st.warning("⚠️ **BASE_URL not configured** - Set this in Streamlit Secrets to generate full share links")

            st.markdown("**Share Token:**")
            st.code(share_token, language=None)

            st.info(f"""
**To share your timeline:**

**Option 1: Manual URL (Quick Fix)**
1. Copy the token above
2. Construct your share link:
   ```
   https://your-app-name.streamlit.app/?share_token={share_token}
   ```
3. Replace `your-app-name.streamlit.app` with your actual Streamlit Cloud URL
   (Look at your browser's address bar to find your app's URL)

**Option 2: Configure BASE_URL (Permanent Fix)**
1. Go to your Streamlit Cloud dashboard
2. Open **Settings** → **Secrets**
3. Add this line:
   ```
   BASE_URL = "https://your-app-name.streamlit.app"
   ```
4. Replace with your actual URL (without trailing slash)
5. Save and the app will automatically generate full links
            """)

        col_copy, col_preview, col_revoke = st.columns(3)

        with col_copy:
            if base_url:
                st.caption("✅ Ready to share")
            else:
                st.caption("⚠️ Configure BASE_URL")

        with col_preview:
            if st.button("👀 Preview (View Only Mode)", use_container_width=True):
                st.info("💡 Open the link above in an incognito/private browser window to test viewer mode")

        with col_revoke:
            if st.button("🗑️ Revoke Link", type="secondary", use_container_width=True):
                success, message = revoke_share_link(supabase, baby_id)
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)

        # Link details
        st.divider()

        col_created, col_protected = st.columns(2)

        with col_created:
            created_at = datetime.fromisoformat(active_link["created_at"].replace("Z", "+00:00"))
            st.caption(f"**Created:** {created_at.strftime('%b %d, %Y at %I:%M %p')}")

        with col_protected:
            if active_link["password_hash"]:
                st.caption("**Protection:** 🔒 Password required")
            else:
                st.caption("**Protection:** 🔓 Anyone with link can view")

        st.divider()

        # Instructions for sharing
        with st.expander("📱 How to Share This Link"):
            st.markdown("""
            ### Sharing Options

            **Via WhatsApp:**
            1. Copy the link above
            2. Open WhatsApp
            3. Paste and send to family members

            **Via Email:**
            1. Copy the link above
            2. Compose email with subject: "{baby_name}'s Baby Timeline"
            3. Paste link in email body
            4. If password-protected, include the password in the email

            **Via Text Message:**
            1. Copy the link above
            2. Send via SMS to family members
            3. Send password separately if protected

            ---

            ### What Can Viewers See?

            ✅ **Viewers can:**
            - View all photos in the timeline
            - See measurements and growth charts
            - Browse timeline history

            ❌ **Viewers cannot:**
            - Upload new photos
            - Add or delete measurements
            - Generate new share links
            - See admin controls or settings

            ---

            ### Security Tips

            - Only share with trusted family members
            - Use password protection for extra security
            - Revoke and regenerate link if accidentally shared publicly
            - Check who you're sending to before hitting send!
            """.replace("{baby_name}", baby_name))

    else:
        # ==================== No Active Link - Show Generator ====================
        st.info("📭 **No active share link**")
        st.write("Generate a link below to share your baby's timeline with family members.")

    # ========================================================================
    # Step 3: Link generator form
    # ========================================================================

    st.divider()
    st.subheader("🔗 Generate New Share Link")

    if active_link:
        st.warning("⚠️ **Note:** Generating a new link will revoke the existing link above. Old link will stop working.")

    with st.form("generate_link_form"):
        # Password protection toggle
        use_password = st.checkbox(
            "🔒 Require password for viewers",
            help="Add a password that viewers must enter before seeing the timeline"
        )

        password = None
        password_confirm = None

        if use_password:
            col_pass1, col_pass2 = st.columns(2)
            with col_pass1:
                password = st.text_input(
                    "Set password",
                    type="password",
                    placeholder="Enter password",
                    help="Choose something family can remember (e.g., baby's birthdate)"
                )
            with col_pass2:
                password_confirm = st.text_input(
                    "Confirm password",
                    type="password",
                    placeholder="Re-enter password"
                )

        # Tips
        if not use_password:
            st.info("💡 **Without password:** Anyone with the link can view the timeline. Only share with trusted family.")
        else:
            st.info("💡 **With password:** Viewers must enter the password you set. More secure, but family needs to remember it.")

        # Generate button
        submitted = st.form_submit_button(
            "✨ Generate Share Link",
            type="primary",
            use_container_width=True
        )

    # Handle form submission OUTSIDE form
    if submitted:
        # Validation
        if use_password:
            if not password or not password_confirm:
                st.error("❌ Please enter and confirm the password")
            elif password != password_confirm:
                st.error("❌ Passwords don't match. Please try again.")
            else:
                # Validate password length
                is_valid, error_msg = validate_password(password)
                if not is_valid:
                    st.error(error_msg)
                else:
                    # Generate link with password
                    with st.spinner("Generating secure link..."):
                        success, result, token = generate_share_link(
                            supabase,
                            baby_id,
                            password=password
                        )

                    if success:
                        st.success("✅ Share link generated successfully!")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error(result)
        else:
            # Generate link without password
            with st.spinner("Generating link..."):
                success, result, token = generate_share_link(
                    supabase,
                    baby_id,
                    password=None
                )

            if success:
                st.success("✅ Share link generated successfully!")
                st.balloons()
                st.rerun()
            else:
                st.error(result)

    # ========================================================================
    # Step 4: FAQs and help
    # ========================================================================

    st.divider()

    with st.expander("❓ Frequently Asked Questions"):
        st.markdown("""
        ### What happens if I generate a new link?

        The old link will **immediately stop working**. This is by design for security:
        - Only one active link per baby at a time
        - If old link was leaked, generate new one to revoke access
        - Family members with old link will need the new one

        ---

        ### Can I have multiple links with different passwords?

        Not in the MVP version. Future enhancement: create multiple links with different permissions.

        Current workaround: Generate one link, share password with trusted family only.

        ---

        ### How long do links last?

        Links are **permanent** (never expire) as long as they're active.

        You can revoke a link anytime by clicking "🗑️ Revoke Link" above.

        ---

        ### What if I forget the password I set?

        Generate a new link with a new password. The old link (and password) will stop working.

        ---

        ### Can viewers see future photos/measurements?

        Yes! The link gives access to the entire timeline, including:
        - All past photos and measurements
        - Any new content you add in the future

        This is intentional - family can check back regularly for updates.

        ---

        ### Is it safe to share via WhatsApp/Email?

        **With password:** Yes, very safe. Even if the link leaks, viewers need the password.

        **Without password:** Reasonably safe if sent via private channels (WhatsApp, Email to specific people).
        Don't post the link publicly (Facebook, Twitter, etc.).

        The share token is a UUID (128-bit random) - virtually impossible to guess without the link.

        ---

        ### Can I see who viewed the timeline?

        Not yet. Future enhancement: viewer analytics (who viewed, when, how often).

        ---

        ### What about sharing videos?

        MVP doesn't support video uploads (storage intensive).

        Workaround: Upload videos to YouTube/Google Photos, share those links separately.
        """)

except ValueError as e:
    # Environment not configured
    st.error(str(e))
    st.info("👉 **Setup required:** Follow the guide in `SUPABASE_SETUP.md`")

except Exception as e:
    st.error(f"❌ Error loading sharing page: {str(e)}")
    st.exception(e)  # Show full error in development

# ============================================================================
# Footer
# ============================================================================

st.divider()
st.caption("🔗 **Tip:** Use password protection for sensitive family photos. Revoke and regenerate links if they're accidentally shared.")
