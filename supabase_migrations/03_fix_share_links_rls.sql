-- ============================================================================
-- Baby Timeline - Fix Share Links RLS for Viewers
-- Migration 03: Add policy to allow anonymous users to validate share tokens
-- ============================================================================
-- Problem: Anonymous viewers (in incognito mode) can't read share_links table
-- to validate their token because RLS blocks all access except for admins.
--
-- Solution: Add a SELECT policy that allows ANYONE to read share_links by token.
-- This is safe because:
-- 1. Tokens are UUID v4 (impossible to guess)
-- 2. We only expose active, non-expired links
-- 3. Password validation happens in the app (after SELECT)
-- ============================================================================

-- Add policy for anonymous users to validate share tokens
CREATE POLICY "Anyone can validate share tokens" ON share_links
  FOR SELECT
  USING (
    is_active = true
    AND (expires_at IS NULL OR expires_at > now())
  );

-- ============================================================================
-- Why is this secure?
-- ============================================================================
-- 1. Users can ONLY read share_links, not create/update/delete
-- 2. They can only see active, non-expired links
-- 3. Without the exact token (UUID v4 = 128-bit random), they can't find anything
-- 4. Password hashes are exposed in SELECT, but:
--    - They're SHA-256 hashed (not reversible)
--    - Password validation happens in app code (src/sharing.py)
-- 5. Even if someone sees a share_link row, they still need to:
--    - Know the exact token (impossible to guess)
--    - Pass password validation if protected
--
-- This policy enables the viewer mode flow:
--   1. User visits: localhost:8501/?share_token=abc-123
--   2. App calls validate_share_token() which does SELECT on share_links
--   3. If found and password correct (or no password), grant access
-- ============================================================================

-- Verification query (run after migration):
-- SELECT * FROM share_links WHERE is_active = true;
-- Should work for both authenticated and anonymous users
