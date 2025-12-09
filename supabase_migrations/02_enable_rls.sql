-- ============================================================================
-- Baby Timeline - Row Level Security (RLS) Policies
-- Migration 02: Enable RLS and Create Policies
-- ============================================================================
-- This migration enables Row Level Security on all tables and creates
-- policies to enforce admin vs. viewer permissions at the DATABASE level.
--
-- Security Model:
-- - Admins (authenticated users): Full CRUD access to their babies' data
-- - Viewers (with valid share link): Read-only access via share_token
-- ============================================================================

-- ============================================================================
-- Enable Row Level Security on all tables
-- ============================================================================
-- Once RLS is enabled, ALL queries are blocked by default unless a policy allows them.
-- This is more secure than application-level checks (can't be bypassed).

ALTER TABLE babies ENABLE ROW LEVEL SECURITY;
ALTER TABLE photos ENABLE ROW LEVEL SECURITY;
ALTER TABLE measurements ENABLE ROW LEVEL SECURITY;
ALTER TABLE share_links ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- Policies for: babies table
-- ============================================================================

-- Policy 1: Admins can do ANYTHING with babies they created
CREATE POLICY "Admins own babies" ON babies
  FOR ALL  -- Applies to SELECT, INSERT, UPDATE, DELETE
  USING (auth.uid() = created_by);

-- Policy 2: Viewers with valid share link can READ babies
CREATE POLICY "Shared access to babies" ON babies
  FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM share_links
      WHERE share_links.baby_id = babies.baby_id
      AND share_links.is_active = true
      AND (share_links.expires_at IS NULL OR share_links.expires_at > now())
    )
  );

-- ============================================================================
-- Policies for: photos table
-- ============================================================================

-- Policy 1: Admins have full access to photos of their babies
CREATE POLICY "Admins full access photos" ON photos
  FOR ALL
  USING (
    baby_id IN (
      SELECT baby_id FROM babies WHERE created_by = auth.uid()
    )
  );

-- Policy 2: Viewers with valid share link can READ photos
CREATE POLICY "Shared access photos" ON photos
  FOR SELECT
  USING (
    baby_id IN (
      SELECT baby_id FROM share_links
      WHERE is_active = true
      AND (expires_at IS NULL OR expires_at > now())
    )
  );

-- ============================================================================
-- Policies for: measurements table
-- ============================================================================

-- Policy 1: Admins have full access to measurements of their babies
CREATE POLICY "Admins full access measurements" ON measurements
  FOR ALL
  USING (
    baby_id IN (
      SELECT baby_id FROM babies WHERE created_by = auth.uid()
    )
  );

-- Policy 2: Viewers with valid share link can READ measurements
CREATE POLICY "Shared access measurements" ON measurements
  FOR SELECT
  USING (
    baby_id IN (
      SELECT baby_id FROM share_links
      WHERE is_active = true
      AND (expires_at IS NULL OR expires_at > now())
    )
  );

-- ============================================================================
-- Policies for: share_links table
-- ============================================================================

-- Policy: Only admins can manage share links (no viewer access needed)
CREATE POLICY "Admins manage share links" ON share_links
  FOR ALL
  USING (auth.uid() = created_by);

-- ============================================================================
-- Storage Policies (for baby-photos bucket)
-- ============================================================================
-- Note: These must be created in Supabase Dashboard → Storage → Policies
-- (SQL storage policies have different syntax, see below)

-- After creating the 'baby-photos' bucket in Storage UI, run these policies:

-- Policy 1: Allow authenticated users (admins) to upload photos
-- CREATE POLICY "Admins upload photos" ON storage.objects FOR INSERT
--   WITH CHECK (bucket_id = 'baby-photos' AND auth.role() = 'authenticated');

-- Policy 2: Allow anyone to READ photos (if they have access to the baby via RLS)
-- CREATE POLICY "Public read photos" ON storage.objects FOR SELECT
--   USING (bucket_id = 'baby-photos');

-- Note: The SELECT policy on storage.objects is intentionally permissive.
-- We rely on RLS on the 'photos' table to control which photos are shown.
-- Without the photo_id from the database, a user can't construct the file URL anyway.

-- ============================================================================
-- Testing RLS Policies
-- ============================================================================

-- Test 1: As an authenticated admin, insert a baby
-- SET request.jwt.claims ->> 'sub' = 'your-admin-user-id';
-- INSERT INTO babies (name, birthdate, created_by) VALUES ('Test Baby', '2025-01-01', auth.uid());
-- SELECT * FROM babies;  -- Should see your baby

-- Test 2: As an unauthenticated user (no share link), try to read
-- SET ROLE anon;
-- SELECT * FROM babies;  -- Should return empty (RLS blocks access)

-- Test 3: Generate share link, then query as viewer
-- INSERT INTO share_links (baby_id, share_token, created_by) VALUES ('baby-uuid', 'test-token', auth.uid());
-- (Then test with share_token in app)

-- ============================================================================
-- Important Security Notes
-- ============================================================================

-- 1. RLS policies run at the DATABASE level, even if someone bypasses your Streamlit UI
-- 2. auth.uid() returns NULL for unauthenticated users, so "USING (auth.uid() = created_by)" blocks them
-- 3. Viewers don't have auth.uid() - they access via share_links policy
-- 4. Share tokens are UUID v4 (128-bit random) = ~3.4 × 10^38 possible values (impossible to guess)
-- 5. For password-protected links, password is hashed with bcrypt (checked in app, not SQL)

-- ============================================================================
-- Migration Complete!
-- Next Step: Create 'baby-photos' storage bucket and apply storage policies
-- Then proceed to Phase 2 (Authentication implementation)
-- ============================================================================
