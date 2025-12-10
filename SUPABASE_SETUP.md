# 🗄️ Supabase Setup Guide

This guide walks you through setting up your Supabase project for the Baby Timeline app.

## Step 1: Create Supabase Project

1. **Go to Supabase Dashboard:**
   - Visit [https://supabase.com/dashboard](https://supabase.com/dashboard)
   - Sign in or create a free account

2. **Create New Project:**
   - Click "New Project"
   - **Organization:** Create a new organization or use existing
   - **Project Name:** `baby-timeline-prod`
   - **Database Password:** Generate a strong password (save it securely!)
   - **Region:** Choose closest to you:
     - Europe: Frankfurt (`eu-central-1`) or Ireland (`eu-west-1`)
     - US: North Virginia (`us-east-1`)
   - **Pricing Plan:** Free tier is sufficient for MVP
   - Click "Create new project" (takes ~2 minutes)

## Step 2: Get API Credentials

1. **Navigate to Settings:**
   - In your project dashboard, click **Settings** (gear icon in left sidebar)
   - Go to **API** section

2. **Copy these credentials:**
   - **Project URL:** `https://xxxxx.supabase.co`
   - **anon (public)** key: `eyJhbGciOi...` (long string)
   - **service_role (secret)** key: `eyJhbGciOi...` (long string)

3. **Create `.env` file:**
   ```bash
   cd lil_heart
   cp .env.example .env
   ```

4. **Edit `.env` with your credentials:**
   ```env
   SUPABASE_URL=https://xxxxx.supabase.co
   SUPABASE_ANON_KEY=your_anon_key_here
   SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here
   ```

   ⚠️ **Security Note:** Never commit `.env` to Git! (already in `.gitignore`)

## Step 3: Run Database Migrations

1. **Open SQL Editor:**
   - In Supabase dashboard, click **SQL Editor** in left sidebar
   - Click **New query**

2. **Run Migration 1 - Create Tables:**
   - Copy entire contents of `supabase_migrations/01_create_tables.sql`
   - Paste into SQL Editor
   - Click **Run** (bottom right)
   - ✅ Should see: "Success. No rows returned"

3. **Run Migration 2 - Enable RLS:**
   - Click **New query** again
   - Copy entire contents of `supabase_migrations/02_enable_rls.sql`
   - Paste into SQL Editor
   - Click **Run**
   - ✅ Should see: "Success. No rows returned"

4. **Verify tables created:**
   - Go to **Table Editor** in left sidebar
   - You should see: `babies`, `photos`, `measurements`, `share_links`

## Step 4: Create Storage Bucket

1. **Navigate to Storage:**
   - Click **Storage** in left sidebar
   - Click **New bucket**

2. **Create bucket:**
   - **Name:** `baby-photos`
   - **Public:** ❌ **Uncheck this!** (keep bucket private for security)
   - Click **Create bucket**

3. **Set Storage Policies:**
   - Click on `baby-photos` bucket
   - Go to **Policies** tab
   - Click **New policy**

   **Policy 1: Allow authenticated uploads**
   - Click **For full customization**
   - **Policy name:** `Admins upload photos`
   - **Policy command:** `INSERT`
   - **Policy definition:**
     ```sql
     bucket_id = 'baby-photos' AND auth.role() = 'authenticated'
     ```
   - Click **Review** → **Save policy**

   **Policy 2: Allow authenticated reads**
   - Click **New policy** again
   - **Policy name:** `Authenticated read photos`
   - **Policy command:** `SELECT`
   - **Policy definition:**
     ```sql
     bucket_id = 'baby-photos' AND auth.role() = 'authenticated'
     ```
   - Click **Review** → **Save policy**

   **Why private bucket?**
   - Better security: Only authenticated users can access storage
   - We use signed URLs (expire in 10 years) for long-term access
   - Even if URLs leak, they're tied to specific files, not entire bucket

## Step 5: Create First Admin User

1. **Navigate to Authentication:**
   - Click **Authentication** in left sidebar
   - Go to **Users** tab

2. **Add User:**
   - Click **Add user** → **Create new user**
   - **Email:** Your email (or your brother's)
   - **Password:** Click "Generate a random password" or create a strong one
   - **Auto Confirm User:** ✅ Check this (skip email verification for MVP)
   - Click **Create user**

3. **Save credentials securely:**
   - Email: `_______________`
   - Password: `_______________`
   - (Send these to the admin user via secure channel like WhatsApp/Signal)

## Step 6: Test Database Connection

1. **Create test script:**
   ```bash
   cd lil_heart
   ```

   Create `test_supabase.py`:
   ```python
   from supabase import create_client
   import os
   from dotenv import load_dotenv

   load_dotenv()

   supabase = create_client(
       os.getenv("SUPABASE_URL"),
       os.getenv("SUPABASE_ANON_KEY")
   )

   # Test query
   result = supabase.table("babies").select("*").execute()
   print(f"✅ Connected to Supabase!")
   print(f"Found {len(result.data)} babies in database")
   ```

2. **Run test:**
   ```bash
   python test_supabase.py
   ```

   Expected output:
   ```
   ✅ Connected to Supabase!
   Found 0 babies in database
   ```

## Step 7: Configure Email (Optional)

For password reset emails to work:

1. **Navigate to Authentication → Settings:**
   - Click **Authentication** → **Email Templates**

2. **Configure SMTP (optional):**
   - Default: Supabase sends emails (limited to 3/hour on free tier)
   - Custom SMTP: Use Gmail, SendGrid, etc. for more emails

3. **Test password reset:**
   - In your app, click "Forgot password?"
   - Enter admin email
   - Check inbox for reset link (may take 1-2 minutes)

## Troubleshooting

### "relation 'babies' does not exist"
- ✅ Solution: Run migration 01_create_tables.sql again
- Check **SQL Editor → Query History** to see if previous run succeeded

### "new row violates row-level security policy"
- ✅ Solution: Run migration 02_enable_rls.sql
- Verify in **Table Editor** → (select table) → **RLS Policies** shows policies

### "permission denied for table babies"
- ✅ Solution: Ensure you're authenticated (logged in as admin)
- In test script, try: `supabase.auth.sign_in_with_password({...})`

### Storage upload fails: "new row violates row-level security policy"
- ✅ Solution: Check storage policies in Storage → baby-photos → Policies
- Ensure "Admins upload photos" policy exists with `INSERT` command

### Can't connect from Python: "invalid API key"
- ✅ Double-check `.env` file:
  - No spaces around `=`
  - No quotes around keys
  - Keys copied completely (they're long!)

## Next Steps

✅ **Phase 1 Complete!** Your database is ready.

**Next:** Phase 2 - Implement authentication in `src/auth.py`

---

## Supabase Free Tier Limits

Keep these in mind as you develop:

- **Database:** 500MB (enough for ~5,000 photos' metadata)
- **Storage:** 1GB (enough for ~1,000 optimized photos)
- **Bandwidth:** 2GB/month
- **API Requests:** 50,000/month
- **Auth users:** Unlimited
- **Row Level Security:** ✅ Included

**Monitoring:**
- Check usage: Supabase Dashboard → **Reports**
- Set up alerts: Settings → **Billing** → **Usage alerts**

---

## Quick Reference

**Supabase Dashboard:** https://supabase.com/dashboard
**Project URL:** (saved in `.env`)
**Admin Email:** (created in Step 5)
**Storage Bucket:** `baby-photos` (private, with signed URLs)

**Tables:**
- `babies` - Baby profiles
- `photos` - Photo metadata
- `measurements` - Height/weight data
- `share_links` - Family sharing tokens

**Key Concepts:**
- **RLS (Row Level Security):** Database-level permissions
- **UUID:** Unique identifiers (e.g., `550e8400-e29b-41d4-a716-446655440000`)
- **JWT (JSON Web Token):** Auth tokens (what `auth.uid()` reads)
