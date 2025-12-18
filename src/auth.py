"""
Authentication Module for Baby Timeline
Handles user login, logout, and session management using Supabase Auth.
"""

import streamlit as st
from supabase import Client, create_client
import os
from dotenv import load_dotenv
from typing import Tuple, Optional

# Load environment variables from .env file (local development only)
# On Streamlit Cloud, use the Secrets management in dashboard instead
load_dotenv(override=False)


def init_supabase() -> Client:
    """
    Initialize Supabase client (cached per session)

    Returns:
        Client: Authenticated Supabase client

    Raises:
        ValueError: If environment variables are not set
    """
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")

    if not url or not key:
        raise ValueError(
            "❌ Supabase credentials not found!\n\n"
            "Local development: Create a `.env` file with:\n"
            "  SUPABASE_URL=your_url\n"
            "  SUPABASE_ANON_KEY=your_key\n\n"
            "Streamlit Cloud: Add secrets in your app dashboard:\n"
            "  Settings → Secrets → Add the same variables\n\n"
            "See SUPABASE_SETUP.md for details."
        )

    # Create client with explicit named parameters (compatible with supabase-py 2.7+)
    return create_client(
        supabase_url=url,
        supabase_key=key
    )


def login(email: str, password: str) -> Tuple[bool, str]:
    """
    Authenticate user with Supabase Auth

    Args:
        email: User's email address
        password: User's password

    Returns:
        Tuple of (success: bool, message: str)
        - If success: (True, "Welcome, email!")
        - If failure: (False, "Error message")

    Side Effects:
        On success, stores in st.session_state:
        - authenticated: bool
        - user: Supabase User object
        - access_token: JWT token
        - supabase: Authenticated Supabase client
    """
    try:
        supabase = init_supabase()

        # Attempt sign in
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })

        # Validate response
        if not response.user:
            return False, "Login failed: No user returned"

        # Store session data
        st.session_state["authenticated"] = True
        st.session_state["user"] = response.user
        st.session_state["access_token"] = response.session.access_token
        st.session_state["supabase"] = supabase

        # Get user metadata for display
        user_email = response.user.email

        return True, f"Welcome, {user_email}!"

    except Exception as e:
        error_message = str(e)

        # Provide friendly error messages for common issues
        if "Invalid login credentials" in error_message:
            return False, "❌ Invalid email or password. Please try again."
        elif "Email not confirmed" in error_message:
            return False, "❌ Please confirm your email address before logging in."
        elif "Too many requests" in error_message:
            return False, "❌ Too many login attempts. Please wait a few minutes."
        else:
            return False, f"❌ Login error: {error_message}"


def logout():
    """
    Log out current user and clear session state

    Side Effects:
        - Calls Supabase Auth sign_out
        - Clears all st.session_state keys
        - Triggers Streamlit rerun to refresh UI
    """
    try:
        # Sign out from Supabase if client exists
        if "supabase" in st.session_state:
            st.session_state["supabase"].auth.sign_out()
    except Exception as e:
        # Log error but don't block logout
        print(f"Logout error (non-fatal): {e}")

    finally:
        # Clear all session state (ensures clean logout even if sign_out fails)
        for key in list(st.session_state.keys()):
            del st.session_state[key]

        # Refresh page to show login screen
        st.rerun()


def is_authenticated() -> bool:
    """
    Check if user is currently logged in

    Returns:
        bool: True if user is authenticated, False otherwise

    Note:
        Checks st.session_state for "authenticated" flag.
        This is set by login() and cleared by logout().
    """
    return st.session_state.get("authenticated", False)


def get_current_user():
    """
    Get currently logged-in user object

    Returns:
        Supabase User object or None if not authenticated

    User object contains:
        - id: UUID (user ID)
        - email: str
        - created_at: timestamp
        - user_metadata: dict (custom fields)
    """
    return st.session_state.get("user", None)


def get_user_id() -> Optional[str]:
    """
    Get current user's ID (UUID)

    Returns:
        str: User UUID or None if not authenticated

    Usage:
        Used for foreign key relationships (created_by, uploaded_by, etc.)
    """
    user = get_current_user()
    return user.id if user else None


def require_auth():
    """
    Decorator-like function to protect pages (admin-only)

    Usage:
        Call this at the top of any page that requires authentication:

        ```python
        from src.auth import require_auth

        require_auth()  # Stops execution if not logged in

        # Rest of your page code (only runs if authenticated)
        st.title("Admin Dashboard")
        ```

    Side Effects:
        If not authenticated:
        - Shows error message
        - Stops script execution with st.stop()
    """
    if not is_authenticated():
        st.error("🔒 **Access Denied**")
        st.warning("Please log in to access this page.")

        # Provide link to main page (login screen)
        st.page_link("Timeline.py", label="← Go to Login", icon="🔐")

        st.stop()


def get_supabase_client() -> Client:
    """
    Get authenticated Supabase client from session state

    Returns:
        Client: Supabase client with user's auth token

    Raises:
        RuntimeError: If called before authentication

    Note:
        This client includes the user's JWT token, so RLS policies
        will enforce permissions based on auth.uid().
    """
    if "supabase" not in st.session_state:
        # Try to initialize fresh client (for first run)
        try:
            return init_supabase()
        except Exception:
            raise RuntimeError(
                "Supabase client not initialized. "
                "Please call login() first or check .env configuration."
            )

    return st.session_state["supabase"]


# ============================================================================
# Helper Functions for Password Reset (Future Enhancement)
# ============================================================================

def request_password_reset(email: str) -> Tuple[bool, str]:
    """
    Send password reset email to user

    Args:
        email: User's email address

    Returns:
        Tuple of (success: bool, message: str)

    Note:
        This uses Supabase's built-in password reset flow.
        User will receive an email with a magic link to reset password.
    """
    try:
        supabase = init_supabase()

        # Request password reset
        supabase.auth.reset_password_for_email(email)

        return True, (
            "✅ Password reset email sent!\n\n"
            "Check your inbox and click the link to reset your password."
        )

    except Exception as e:
        return False, f"❌ Error sending reset email: {str(e)}"


def update_password(new_password: str) -> Tuple[bool, str]:
    """
    Update current user's password

    Args:
        new_password: New password (min 6 characters)

    Returns:
        Tuple of (success: bool, message: str)

    Note:
        User must be authenticated to change password.
    """
    if not is_authenticated():
        return False, "❌ Please log in first"

    try:
        supabase = get_supabase_client()

        # Update password
        supabase.auth.update_user({
            "password": new_password
        })

        return True, "✅ Password updated successfully!"

    except Exception as e:
        return False, f"❌ Error updating password: {str(e)}"


# ============================================================================
# Session State Debugging (Development Only)
# ============================================================================

def debug_session_state():
    """
    Print current session state (for development/debugging)

    Usage:
        Add to any page during development:
        ```python
        from src.auth import debug_session_state
        with st.expander("Debug: Session State"):
            debug_session_state()
        ```
    """
    import json

    st.write("**Session State Keys:**")
    st.write(list(st.session_state.keys()))

    st.write("**User Info:**")
    if is_authenticated():
        user = get_current_user()
        st.json({
            "id": user.id,
            "email": user.email,
            "created_at": str(user.created_at)
        })
    else:
        st.write("Not authenticated")
