"""
Storage Module for Baby Timeline
Handles photo upload, optimization, and retrieval from Supabase Storage.
"""

import os
from io import BytesIO
from PIL import Image
from datetime import datetime
import streamlit as st
from supabase import Client
from typing import Tuple, Optional


def optimize_image(uploaded_file, max_width: int = 1920, quality: int = 85) -> Tuple[BytesIO, dict]:
    """
    Resize image to max width and convert to JPEG for storage optimization.

    Args:
        uploaded_file: Streamlit UploadedFile object
        max_width: Maximum width in pixels (default 1920 for Full HD)
        quality: JPEG quality 0-100 (default 85 for good balance)

    Returns:
        Tuple of (BytesIO buffer with optimized image, metadata dict)

    Raises:
        ValueError: If file is not a valid image
        IOError: If image processing fails

    Storage Savings:
        - Original 5MB photo → ~1MB optimized
        - 1GB storage = ~1,000 photos (vs ~200 originals)
    """
    try:
        # Open image with PIL
        img = Image.open(uploaded_file)

        # Store original dimensions for metadata
        original_width = img.width
        original_height = img.height
        original_format = img.format or "UNKNOWN"

        # Resize if larger than max_width
        if img.width > max_width:
            ratio = max_width / img.width
            new_height = int(img.height * ratio)
            new_size = (max_width, new_height)

            # Use LANCZOS for high-quality downscaling
            img = img.resize(new_size, Image.Resampling.LANCZOS)

        # Convert to RGB (handles RGBA/PNG with transparency)
        if img.mode in ("RGBA", "P", "LA"):
            # Create white background for transparent images
            background = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P":
                img = img.convert("RGBA")
            background.paste(img, mask=img.split()[-1] if img.mode in ("RGBA", "LA") else None)
            img = background
        elif img.mode != "RGB":
            img = img.convert("RGB")

        # Save to buffer as optimized JPEG
        buffer = BytesIO()
        img.save(buffer, format="JPEG", quality=quality, optimize=True)
        buffer.seek(0)

        # Prepare metadata
        metadata = {
            "original_width": original_width,
            "original_height": original_height,
            "original_format": original_format,
            "optimized_width": img.width,
            "optimized_height": img.height,
            "optimized_format": "JPEG",
            "quality": quality
        }

        return buffer, metadata

    except Exception as e:
        raise ValueError(f"Failed to process image: {str(e)}")


def extract_exif_date(uploaded_file) -> Optional[datetime]:
    """
    Extract photo date from EXIF metadata (if available).

    Args:
        uploaded_file: Streamlit UploadedFile object

    Returns:
        datetime object or None if no EXIF date found

    Note:
        EXIF dates are in format: "YYYY:MM:DD HH:MM:SS"
        Common EXIF tags: DateTimeOriginal (photo taken), DateTime (file modified)
    """
    try:
        from PIL.ExifTags import TAGS

        img = Image.open(uploaded_file)
        exif_data = img._getexif()

        if not exif_data:
            return None

        # Look for DateTimeOriginal (when photo was taken)
        for tag_id, value in exif_data.items():
            tag_name = TAGS.get(tag_id, tag_id)

            if tag_name == "DateTimeOriginal":
                # Parse EXIF date format: "2025:12:09 14:30:45"
                date_str = value.split()[0].replace(":", "-")
                return datetime.strptime(date_str, "%Y-%m-%d")

        return None

    except Exception as e:
        # EXIF extraction is optional - fail silently
        print(f"EXIF extraction failed (non-fatal): {e}")
        return None


def generate_filename(baby_id: str, photo_date: datetime, original_filename: str) -> str:
    """
    Generate organized filename for storage.

    Args:
        baby_id: UUID of the baby
        photo_date: Date the photo was taken
        original_filename: Original uploaded filename

    Returns:
        Path string: "baby_id/YYYY/MM/YYYYMMDD_HHMMSS_original.jpg"

    Example:
        "550e8400-.../2025/12/20251209_143045_first_smile.jpg"

    Storage Organization:
        /baby-photos/
        ├── baby-uuid-1/
        │   ├── 2025/
        │   │   ├── 01/
        │   │   │   ├── 20250115_120000_newborn.jpg
        │   │   │   └── 20250120_140000_first_bath.jpg
        │   │   └── 06/
        │   │       └── 20250601_100000_6months.jpg
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Clean original filename (remove extension, sanitize)
    base_name = os.path.splitext(original_filename)[0]
    base_name = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in base_name)
    base_name = base_name[:50]  # Limit length

    # Build path: baby_id/year/month/timestamp_original.jpg
    year = photo_date.strftime("%Y")
    month = photo_date.strftime("%m")
    filename = f"{timestamp}_{base_name}.jpg"

    return f"{baby_id}/{year}/{month}/{filename}"


def upload_photo(
    supabase: Client,
    baby_id: str,
    uploaded_file,
    photo_date: datetime,
    caption: str = "",
    user_id: str = None
) -> Tuple[bool, str, Optional[str]]:
    """
    Upload photo to Supabase Storage and save metadata to database.

    Args:
        supabase: Authenticated Supabase client
        baby_id: UUID of the baby
        uploaded_file: Streamlit UploadedFile object
        photo_date: Date the photo was taken
        caption: Optional caption (max 500 chars)
        user_id: User ID of uploader

    Returns:
        Tuple of (success: bool, message: str, photo_id: str or None)

    Process:
        1. Optimize image (resize, compress)
        2. Upload to Supabase Storage bucket
        3. Save metadata to photos table
        4. Return success with photo_id

    Storage Path:
        bucket: baby-photos
        path: baby_id/YYYY/MM/timestamp_filename.jpg
    """
    try:
        # Step 1: Validate file size (before optimization)
        file_size_mb = uploaded_file.size / (1024 * 1024)
        if file_size_mb > 10:
            return False, f"❌ File too large: {file_size_mb:.1f}MB (max 10MB)", None

        # Step 2: Optimize image
        uploaded_file.seek(0)  # Reset file pointer
        optimized_buffer, metadata = optimize_image(uploaded_file)

        optimized_size_mb = optimized_buffer.getbuffer().nbytes / (1024 * 1024)

        # Step 3: Generate filename and path
        uploaded_file.seek(0)
        file_path = generate_filename(baby_id, photo_date, uploaded_file.name)

        # Step 4: Upload to Supabase Storage
        supabase.storage.from_("baby-photos").upload(
            path=file_path,
            file=optimized_buffer.getvalue(),  # Convert BytesIO to bytes
            file_options={
                "content-type": "image/jpeg",
                "upsert": "false"  # Don't overwrite existing files
            }
        )

        # Step 5: Create signed URL (works with private buckets, expires in 1 year)
        # Note: For production, consider making bucket public or regenerating signed URLs periodically
        signed_url_response = supabase.storage.from_("baby-photos").create_signed_url(
            file_path,
            expires_in=31536000  # 1 year in seconds
        )
        file_url = signed_url_response.get("signedURL") or signed_url_response.get("signedUrl")

        # Step 6: Save metadata to database
        photo_data = {
            "baby_id": baby_id,
            "file_url": file_url,
            "caption": caption[:500] if caption else None,  # Enforce 500 char limit
            "photo_date": photo_date.strftime("%Y-%m-%d"),
            "uploaded_by": user_id,
            "exif_data": metadata  # Store optimization metadata
        }

        result = supabase.table("photos").insert(photo_data).execute()

        if not result.data:
            raise Exception("Database insert failed - no data returned")

        photo_id = result.data[0]["photo_id"]

        # Success message with optimization stats
        success_msg = (
            f"✅ Photo uploaded successfully!\n\n"
            f"📊 **Optimization:**\n"
            f"- Original: {file_size_mb:.1f}MB ({metadata['original_width']}x{metadata['original_height']}px)\n"
            f"- Optimized: {optimized_size_mb:.1f}MB ({metadata['optimized_width']}x{metadata['optimized_height']}px)\n"
            f"- Saved: {(file_size_mb - optimized_size_mb):.1f}MB ({((file_size_mb - optimized_size_mb) / file_size_mb * 100):.0f}% smaller)"
        )

        return True, success_msg, photo_id

    except Exception as e:
        error_msg = str(e)

        # Provide helpful error messages
        if "already exists" in error_msg.lower():
            return False, "❌ A photo with this name already exists. Try renaming the file.", None
        elif "quota" in error_msg.lower() or "storage" in error_msg.lower():
            return False, "❌ Storage quota exceeded. Consider upgrading your Supabase plan.", None
        elif "permission" in error_msg.lower() or "policy" in error_msg.lower():
            return False, "❌ Permission denied. Check storage bucket policies in Supabase Dashboard.", None
        else:
            return False, f"❌ Upload failed: {error_msg}", None


def delete_photo(supabase: Client, photo_id: str, baby_id: str) -> Tuple[bool, str]:
    """
    Delete photo from storage and database.

    Args:
        supabase: Authenticated Supabase client
        photo_id: UUID of the photo
        baby_id: UUID of the baby (for permission check)

    Returns:
        Tuple of (success: bool, message: str)

    Process:
        1. Get photo metadata from database
        2. Delete file from storage
        3. Delete database record
    """
    try:
        # Step 1: Get photo metadata
        result = supabase.table("photos") \
            .select("file_url, baby_id") \
            .eq("photo_id", photo_id) \
            .execute()

        if not result.data:
            return False, "❌ Photo not found"

        photo = result.data[0]

        # Permission check (RLS should handle this, but double-check)
        if photo["baby_id"] != baby_id:
            return False, "❌ Permission denied"

        # Step 2: Extract file path from URL
        # URL format: https://xxx.supabase.co/storage/v1/object/public/baby-photos/path/to/file.jpg
        file_url = photo["file_url"]
        file_path = file_url.split("/baby-photos/")[-1]

        # Step 3: Delete from storage
        supabase.storage.from_("baby-photos").remove([file_path])

        # Step 4: Delete from database
        supabase.table("photos").delete().eq("photo_id", photo_id).execute()

        return True, "✅ Photo deleted successfully"

    except Exception as e:
        return False, f"❌ Delete failed: {str(e)}"


def get_storage_usage(supabase: Client, baby_id: str) -> dict:
    """
    Get storage usage statistics for a baby.

    Args:
        supabase: Authenticated Supabase client
        baby_id: UUID of the baby

    Returns:
        dict with keys:
        - photo_count: Number of photos
        - total_size_mb: Estimated total size in MB
        - storage_limit_mb: Free tier limit (1000 MB)
        - percentage_used: Percentage of limit used

    Note:
        Size is estimated based on average optimized photo size (~1MB)
        For exact size, would need to query storage bucket metadata
    """
    try:
        # Count photos
        result = supabase.table("photos") \
            .select("photo_id", count="exact") \
            .eq("baby_id", baby_id) \
            .execute()

        photo_count = result.count or 0

        # Estimate size (avg optimized photo = 1MB)
        estimated_size_mb = photo_count * 1.0

        # Free tier limit
        storage_limit_mb = 1000  # 1GB

        # Calculate percentage
        percentage_used = (estimated_size_mb / storage_limit_mb) * 100

        return {
            "photo_count": photo_count,
            "total_size_mb": estimated_size_mb,
            "storage_limit_mb": storage_limit_mb,
            "percentage_used": percentage_used
        }

    except Exception as e:
        print(f"Error getting storage usage: {e}")
        return {
            "photo_count": 0,
            "total_size_mb": 0,
            "storage_limit_mb": 1000,
            "percentage_used": 0
        }
