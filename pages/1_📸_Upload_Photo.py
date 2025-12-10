"""
Upload Photo Page - Baby Timeline
Allows admins to upload photos with captions and dates.
"""

import streamlit as st
from datetime import datetime
from src.auth import require_auth, get_supabase_client, get_user_id
from src.storage import upload_photo, extract_exif_date, get_storage_usage

# ============================================================================
# Page Configuration
# ============================================================================
st.set_page_config(
    page_title="Upload Photo - Baby Timeline",
    page_icon="📸",
    layout="wide"
)

# Require authentication (admin only)
require_auth()

# ============================================================================
# Main Page
# ============================================================================

st.title("📸 Upload Photo")
st.write("Add a new photo to your baby's timeline")

try:
    supabase = get_supabase_client()

    # ========================================================================
    # Step 1: Get baby info
    # ========================================================================
    babies = supabase.table("babies").select("*").execute()

    if not babies.data:
        st.error("❌ No baby profile found. Please create one from the main page.")
        st.page_link("app.py", label="← Back to Main Page", icon="🏠")
        st.stop()

    baby = babies.data[0]
    baby_id = baby["baby_id"]
    baby_name = baby["name"]

    # ========================================================================
    # Step 2: Show storage usage
    # ========================================================================
    storage_info = get_storage_usage(supabase, baby_id)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Photos", storage_info["photo_count"])
    with col2:
        st.metric("Storage Used", f"{storage_info['total_size_mb']:.0f} MB")
    with col3:
        st.metric("Storage Limit", f"{storage_info['storage_limit_mb']} MB")

    # Show warning if storage is running low
    if storage_info["percentage_used"] > 80:
        st.warning(f"⚠️ Storage {storage_info['percentage_used']:.0f}% full - consider upgrading your Supabase plan")
    elif storage_info["percentage_used"] > 50:
        st.info(f"💡 Storage {storage_info['percentage_used']:.0f}% used")

    st.divider()

    # ========================================================================
    # Step 3: Upload form
    # ========================================================================

    st.subheader(f"Upload Photo for {baby_name}")

    # File uploader
    uploaded_file = st.file_uploader(
        "Choose a photo",
        type=["jpg", "jpeg", "png", "heic"],
        help="Supported formats: JPG, PNG, HEIC (iPhone photos)",
        accept_multiple_files=False
    )

    if uploaded_file:
        # Show preview
        col_preview, col_form = st.columns([1, 1])

        with col_preview:
            st.markdown("#### Preview")
            try:
                st.image(uploaded_file, caption="Photo preview", use_column_width=True)
            except Exception as e:
                st.error(f"❌ Could not display preview: {str(e)}")

            # Show file info
            file_size_mb = uploaded_file.size / (1024 * 1024)
            st.caption(f"📄 **File:** {uploaded_file.name}")
            st.caption(f"📊 **Size:** {file_size_mb:.2f} MB")

        with col_form:
            st.markdown("#### Photo Details")

            # Try to extract EXIF date
            uploaded_file.seek(0)
            exif_date = extract_exif_date(uploaded_file)
            uploaded_file.seek(0)  # Reset file pointer

            if exif_date:
                st.success(f"📅 Auto-detected date: {exif_date.strftime('%B %d, %Y')}")
                default_date = exif_date
            else:
                st.info("📅 No EXIF date found - using today's date")
                default_date = datetime.now()

            # Date picker
            photo_date = st.date_input(
                "Photo date",
                value=default_date,
                max_value=datetime.now(),
                help="When was this photo taken?"
            )

            # Caption
            caption = st.text_area(
                "Caption (optional)",
                max_chars=500,
                height=100,
                placeholder="e.g., First smile! 😊",
                help="Add a caption to remember this moment"
            )

            # Character counter
            if caption:
                char_count = len(caption)
                st.caption(f"{char_count}/500 characters")

            st.divider()

            # Upload button
            if st.button("📤 Upload Photo", type="primary", use_column_width=True):
                if file_size_mb > 10:
                    st.error("❌ File too large. Maximum size is 10 MB.")
                else:
                    with st.spinner("Optimizing and uploading..."):
                        uploaded_file.seek(0)  # Reset file pointer

                        success, message, photo_id = upload_photo(
                            supabase=supabase,
                            baby_id=baby_id,
                            uploaded_file=uploaded_file,
                            photo_date=photo_date,
                            caption=caption,
                            user_id=get_user_id()
                        )

                    if success:
                        st.success(message)
                        st.balloons()

                        # Show link to timeline
                        st.info("🎉 Photo added to timeline!")

                        col_a, col_b = st.columns(2)
                        with col_a:
                            if st.button("📸 Upload Another", use_column_width=True):
                                st.rerun()
                        with col_b:
                            st.page_link("app.py", label="👀 View Timeline", icon="🏠")

                    else:
                        st.error(message)

                        # Troubleshooting help
                        with st.expander("🔧 Troubleshooting"):
                            st.markdown("""
                            **Common issues:**

                            1. **Permission denied**
                               - Check storage bucket policies in Supabase Dashboard
                               - Ensure "Admins upload photos" policy exists

                            2. **Storage quota exceeded**
                               - Free tier: 1GB storage (~1,000 photos)
                               - Upgrade to Supabase Pro for more storage

                            3. **File already exists**
                               - Rename the file before uploading
                               - Or delete the existing photo first

                            4. **Invalid file format**
                               - Try converting to JPG
                               - HEIC files require pillow-heif library

                            **Still having issues?** Check the [SUPABASE_SETUP.md](SUPABASE_SETUP.md) guide.
                            """)

    else:
        # No file uploaded yet - show helpful instructions
        st.info("""
        📱 **Tips for uploading:**

        - **From phone:** Click "Browse files" and select from camera roll
        - **From computer:** Drag & drop or click to browse
        - **Best quality:** Upload original photos (they'll be optimized automatically)
        - **Supported formats:** JPG, PNG, HEIC (iPhone photos)
        - **File size limit:** 10 MB per photo

        **What happens to my photos?**
        - Photos are resized to 1920px width (Full HD quality)
        - Compressed to ~1MB (saves storage without visible quality loss)
        - Stored securely in Supabase Storage (private bucket)
        - Original EXIF date is preserved if available
        """)

    # ========================================================================
    # Step 4: Recent uploads (optional preview)
    # ========================================================================

    st.divider()

    with st.expander("📋 Recent Uploads", expanded=False):
        with st.spinner("Loading recent uploads..."):
            recent_photos = supabase.table("photos") \
                .select("*") \
                .eq("baby_id", baby_id) \
                .order("upload_date", desc=True) \
                .limit(5) \
                .execute()

        if recent_photos.data:
            st.caption(f"Last {len(recent_photos.data)} photos uploaded")

            for photo in recent_photos.data:
                col_thumb, col_info = st.columns([1, 4])

                with col_thumb:
                    # Build accessible alt text
                    alt_text = f"Recent upload from {photo['photo_date']}"
                    if photo.get("caption"):
                        alt_text += f": {photo['caption']}"

                    st.image(photo["file_url"], caption=alt_text, use_column_width=True)

                with col_info:
                    st.markdown(f"**📅 {photo['photo_date']}**")
                    if photo.get("caption"):
                        st.write(photo["caption"])

                    upload_time = datetime.fromisoformat(
                        photo["upload_date"].replace("Z", "+00:00")
                    )
                    st.caption(f"Uploaded: {upload_time.strftime('%b %d at %I:%M %p')}")

                st.divider()
        else:
            st.caption("No photos uploaded yet")

except ValueError as e:
    # Environment not configured
    st.error(str(e))
    st.info("👉 **Setup required:** Follow the guide in `SUPABASE_SETUP.md`")

except Exception as e:
    st.error(f"❌ Error loading upload page: {str(e)}")
    st.exception(e)  # Show full error in development

# ============================================================================
# Footer
# ============================================================================

st.divider()
st.caption("💡 **Tip:** Photos are automatically optimized to save storage space while maintaining quality.")
