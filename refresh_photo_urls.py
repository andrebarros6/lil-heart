"""
URL Refresh Utility - Baby Timeline
Regenerates signed URLs for all existing photos in the database.

Use this script when:
- Switching from public bucket to private bucket
- Signed URLs are expiring (e.g., after 1 year)
- Photos showing "Bucket not found" errors

Usage:
    python refresh_photo_urls.py
"""

import os
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()

def refresh_all_photo_urls():
    """
    Fetch all photos from database and regenerate signed URLs.
    Updates the database with new URLs.
    """
    print("🔄 Starting URL refresh process...\n")

    # Initialize Supabase client
    supabase = create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_SERVICE_ROLE_KEY")  # Use service role for admin access
    )

    # Step 1: Fetch all photos
    print("📥 Fetching all photos from database...")
    photos_response = supabase.table("photos").select("*").execute()
    photos = photos_response.data

    if not photos:
        print("✅ No photos found in database. Nothing to refresh.")
        return

    print(f"Found {len(photos)} photos to process.\n")

    # Step 2: Process each photo
    success_count = 0
    error_count = 0

    for i, photo in enumerate(photos, 1):
        photo_id = photo["photo_id"]
        old_url = photo["file_url"]

        print(f"[{i}/{len(photos)}] Processing photo {photo_id[:8]}...")

        try:
            # Extract file path from old URL
            # URL format: https://xxx.supabase.co/storage/v1/object/public/baby-photos/path/to/file.jpg
            # OR: https://xxx.supabase.co/storage/v1/object/sign/baby-photos/path/to/file.jpg?token=...

            # Find the bucket name and extract path after it
            if "/baby-photos/" in old_url:
                file_path = old_url.split("/baby-photos/")[1].split("?")[0]  # Remove query params if any
            else:
                print(f"  ⚠️  Skipping - couldn't parse URL: {old_url}")
                error_count += 1
                continue

            # Generate new signed URL (10 years expiration)
            signed_url_response = supabase.storage.from_("baby-photos").create_signed_url(
                file_path,
                expires_in=315360000  # 10 years in seconds
            )
            new_url = signed_url_response.get("signedURL") or signed_url_response.get("signedUrl")

            if not new_url:
                print(f"  ❌ Failed to generate signed URL")
                error_count += 1
                continue

            # Update database with new URL
            supabase.table("photos").update({
                "file_url": new_url
            }).eq("photo_id", photo_id).execute()

            print(f"  ✅ Updated successfully")
            success_count += 1

        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            error_count += 1

    # Step 3: Summary
    print("\n" + "=" * 50)
    print("📊 Refresh Summary:")
    print(f"   ✅ Successfully updated: {success_count} photos")
    if error_count > 0:
        print(f"   ❌ Errors: {error_count} photos")
    print(f"   📁 Total processed: {len(photos)} photos")
    print("=" * 50)

    if success_count > 0:
        print("\n✨ URL refresh complete! Your photos should now display correctly.")
    if error_count > 0:
        print("\n⚠️  Some photos had errors. Check the logs above for details.")


def verify_bucket_access():
    """
    Verify that the bucket exists and is accessible.
    """
    print("🔍 Verifying bucket access...\n")

    supabase = create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    )

    try:
        # Try to list files in bucket (even if empty)
        result = supabase.storage.from_("baby-photos").list()
        print(f"✅ Bucket 'baby-photos' is accessible")
        print(f"   Found {len(result)} items in root directory\n")
        return True
    except Exception as e:
        print(f"❌ Bucket access error: {str(e)}\n")
        print("Please ensure:")
        print("  1. Bucket 'baby-photos' exists in Supabase Storage")
        print("  2. You're using SUPABASE_SERVICE_ROLE_KEY (not ANON_KEY)")
        print("  3. Storage policies allow authenticated reads\n")
        return False


if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("🔄 Photo URL Refresh Utility")
    print("=" * 50 + "\n")

    # Check environment variables
    if not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_SERVICE_ROLE_KEY"):
        print("❌ Error: Missing environment variables")
        print("Please ensure .env file contains:")
        print("  - SUPABASE_URL")
        print("  - SUPABASE_SERVICE_ROLE_KEY")
        exit(1)

    # Verify bucket access before proceeding
    if not verify_bucket_access():
        print("❌ Cannot proceed without bucket access. Please fix the issues above.")
        exit(1)

    # Confirm with user
    print("⚠️  This will regenerate signed URLs for ALL photos in the database.")
    print("   Old URLs will be replaced with new ones (expires in 10 years).\n")

    response = input("Continue? (yes/no): ").strip().lower()

    if response in ["yes", "y"]:
        print()
        refresh_all_photo_urls()
    else:
        print("\n❌ Refresh cancelled by user.")
