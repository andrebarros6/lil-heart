"""
Sharing Module for Baby Timeline
Handles share link generation, validation, and token-based access control.
"""

import uuid
import streamlit as st
from supabase import Client
from typing import Tuple, Optional
import bcrypt
import hmac
import os
from src.logger import setup_logger

logger = setup_logger(__name__)


def generate_share_link(
    supabase: Client,
    baby_id: str,
    password: Optional[str] = None
) -> Tuple[bool, str, Optional[str]]:
    """
    Generate a unique share token and save to database.

    Args:
        supabase: Authenticated Supabase client
        baby_id: UUID of the baby
        password: Optional password for additional security

    Returns:
        Tuple of (success: bool, share_url or error_message: str, token: str or None)

    Process:
        1. Generate random UUID token
        2. Hash password if provided (using SHA-256)
        3. Deactivate any existing active links for this baby
        4. Insert new share link to database
        5. Return full shareable URL

    Security:
        - Token is UUID v4 (128-bit random, virtually impossible to guess)
        - Password is hashed with bcrypt (never stored in plain text)
        - Only one active link per baby (regenerating revokes old links)
    """
    try:
        # Generate unique share token
        share_token = str(uuid.uuid4())

        # Hash password if provided
        password_hash = None
        if password:
            password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

        # Deactivate old links for this baby
        supabase.table("share_links").update({
            "is_active": False
        }).eq("baby_id", baby_id).execute()

        # Get current user ID
        user_id = st.session_state.get("user").id if st.session_state.get("user") else None

        # Insert new share link
        result = supabase.table("share_links").insert({
            "baby_id": baby_id,
            "share_token": share_token,
            "password_hash": password_hash,
            "created_by": user_id,
            "is_active": True
        }).execute()

        if not result.data:
            raise Exception("Database insert failed - no data returned")

        # Build shareable URL
        # Get base URL from environment variable
        # If not configured, return token with instructions (handled by UI)
        base_url = os.getenv("BASE_URL", "http://localhost:8501")
        share_url = f"{base_url}/?share_token={share_token}"

        return True, share_url, share_token

    except Exception as e:
        error_msg = str(e)

        if "violates row-level security" in error_msg.lower():
            return False, "❌ Permission denied. Please log in as admin.", None
        else:
            return False, f"❌ Failed to generate link: {error_msg}", None


def validate_share_token(
    supabase: Client,
    token: str,
    password: Optional[str] = None
) -> Tuple[bool, str]:
    """
    Validate share token and optional password.

    Args:
        supabase: Supabase client
        token: Share token from URL
        password: Password provided by viewer (if required)

    Returns:
        Tuple of (is_valid: bool, baby_id or error_message: str)

    Validation checks:
        1. Token exists in database
        2. Link is active (not revoked)
        3. Link hasn't expired (if expires_at is set)
        4. Password matches (if password protection enabled)

    Security:
        - Password is verified using bcrypt (never stored/transmitted in plain text)
        - Constant-time comparison prevents timing attacks
    """
    try:
        # Fetch share link from database
        result = supabase.table("share_links") \
            .select("*") \
            .eq("share_token", token) \
            .eq("is_active", True) \
            .execute()

        if not result.data:
            return False, "❌ Invalid or expired share link"

        link = result.data[0]

        # Check if link has expired
        if link.get("expires_at"):
            from datetime import datetime
            expires_at = datetime.fromisoformat(link["expires_at"].replace("Z", "+00:00"))
            if datetime.now(expires_at.tzinfo) > expires_at:
                return False, "❌ This share link has expired"

        # Check password if required
        if link["password_hash"]:
            if not password:
                return False, "password_required"  # Special code for UI handling

            # Verify password using bcrypt (constant-time comparison built-in)
            if not bcrypt.checkpw(password.encode(), link["password_hash"].encode()):
                return False, "❌ Incorrect password"

        # Validation successful - return baby_id
        return True, link["baby_id"]

    except Exception as e:
        return False, f"❌ Validation error: {str(e)}"


def revoke_share_link(supabase: Client, baby_id: str) -> Tuple[bool, str]:
    """
    Revoke (deactivate) all active share links for a baby.

    Args:
        supabase: Authenticated Supabase client
        baby_id: UUID of the baby

    Returns:
        Tuple of (success: bool, message: str)

    Use case:
        Admin wants to revoke family access (e.g., link was leaked)
    """
    try:
        result = supabase.table("share_links").update({
            "is_active": False
        }).eq("baby_id", baby_id).eq("is_active", True).execute()

        if not result.data:
            return False, "❌ No active links found to revoke"

        return True, f"✅ Revoked {len(result.data)} active link(s)"

    except Exception as e:
        return False, f"❌ Failed to revoke links: {str(e)}"


def get_active_share_link(supabase: Client, baby_id: str) -> Optional[dict]:
    """
    Get the currently active share link for a baby (if any).

    Args:
        supabase: Authenticated Supabase client
        baby_id: UUID of the baby

    Returns:
        Share link dict or None if no active link exists

    Use case:
        Display current share link in admin UI
    """
    try:
        result = supabase.table("share_links") \
            .select("*") \
            .eq("baby_id", baby_id) \
            .eq("is_active", True) \
            .execute()

        if result.data:
            return result.data[0]
        else:
            return None

    except Exception as e:
        logger.error(f"Error fetching active share link: {e}", exc_info=True)
        return None


def check_viewer_mode() -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Check if current session is in viewer mode (accessing via share link).

    Returns:
        Tuple of (is_viewer_mode: bool, baby_id: str or None, error_message: str or None)

    Use case:
        Called at app startup to determine if user is admin or viewer
    """
    # Check for share_token in URL query params
    query_params = st.query_params
    share_token = query_params.get("share_token")

    if not share_token:
        return False, None, None

    # Check if already validated in session
    if st.session_state.get("viewer_authenticated") and \
       st.session_state.get("viewer_baby_id"):
        return True, st.session_state["viewer_baby_id"], None

    # Token exists but not yet validated
    return True, None, None
