-- ============================================================================
-- Baby Timeline - Database Schema
-- Migration 01: Create Tables
-- ============================================================================
-- This migration creates all core tables for the Baby Timeline application.
-- Run this in Supabase SQL Editor after creating your project.
-- ============================================================================

-- Enable UUID extension for generating unique IDs
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- Table: babies
-- Stores baby profiles (MVP supports single baby, but schema allows multiple)
-- ============================================================================
CREATE TABLE babies (
  baby_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name VARCHAR(100) NOT NULL,
  birthdate DATE NOT NULL,
  profile_photo_url TEXT,  -- URL to Supabase Storage
  created_by UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- Index for faster lookups by creator
CREATE INDEX idx_babies_created_by ON babies(created_by);

-- ============================================================================
-- Table: photos
-- Stores photo metadata (actual images stored in Supabase Storage)
-- ============================================================================
CREATE TABLE photos (
  photo_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  baby_id UUID REFERENCES babies(baby_id) ON DELETE CASCADE NOT NULL,
  file_url TEXT NOT NULL,  -- Supabase Storage URL
  thumbnail_url TEXT,      -- Optional: optimized thumbnail (future enhancement)
  caption TEXT,            -- Optional caption (max 500 chars enforced in app)
  photo_date DATE NOT NULL,  -- Date photo was taken (not uploaded)
  upload_date TIMESTAMPTZ DEFAULT now(),
  uploaded_by UUID REFERENCES auth.users(id),
  exif_data JSONB  -- Optional: camera metadata, GPS, etc.
);

-- Indexes for performance (timeline queries order by date DESC)
CREATE INDEX idx_photos_baby_id ON photos(baby_id);
CREATE INDEX idx_photos_date ON photos(photo_date DESC);
CREATE INDEX idx_photos_baby_date ON photos(baby_id, photo_date DESC);

-- ============================================================================
-- Table: measurements
-- Stores height and weight measurements over time
-- ============================================================================
CREATE TABLE measurements (
  measurement_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  baby_id UUID REFERENCES babies(baby_id) ON DELETE CASCADE NOT NULL,
  measurement_date DATE NOT NULL,
  weight_kg DECIMAL(4,2) CHECK (weight_kg > 0 AND weight_kg < 50),  -- 0.01 to 49.99 kg
  height_cm DECIMAL(5,2) CHECK (height_cm > 0 AND height_cm < 200), -- 0.01 to 199.99 cm
  notes TEXT,  -- Optional notes (e.g., "Measured at doctor's office")
  recorded_by UUID REFERENCES auth.users(id),
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Constraint: At least one of weight or height must be provided
ALTER TABLE measurements ADD CONSTRAINT check_one_measurement
  CHECK (weight_kg IS NOT NULL OR height_cm IS NOT NULL);

-- Indexes for performance (growth chart queries)
CREATE INDEX idx_measurements_baby_id ON measurements(baby_id);
CREATE INDEX idx_measurements_date ON measurements(measurement_date DESC);
CREATE INDEX idx_measurements_baby_date ON measurements(baby_id, measurement_date DESC);

-- ============================================================================
-- Table: share_links
-- Stores tokens for family viewing (no account required)
-- ============================================================================
CREATE TABLE share_links (
  link_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  baby_id UUID REFERENCES babies(baby_id) ON DELETE CASCADE NOT NULL,
  share_token VARCHAR(64) UNIQUE NOT NULL,  -- UUID v4 token
  password_hash VARCHAR(255),  -- NULL if no password protection
  created_by UUID REFERENCES auth.users(id),
  created_at TIMESTAMPTZ DEFAULT now(),
  expires_at TIMESTAMPTZ,  -- NULL = never expires (future enhancement)
  is_active BOOLEAN DEFAULT true  -- Admin can deactivate without deleting
);

-- Index for fast token lookups (only check active, non-expired links)
CREATE INDEX idx_share_links_token ON share_links(share_token)
  WHERE is_active = true;
CREATE INDEX idx_share_links_baby_id ON share_links(baby_id);

-- ============================================================================
-- Helpful Comments & Usage Examples
-- ============================================================================

-- Example: Insert a baby
-- INSERT INTO babies (name, birthdate, created_by)
-- VALUES ('Baby Name', '2025-01-15', auth.uid());

-- Example: Insert a photo
-- INSERT INTO photos (baby_id, file_url, caption, photo_date, uploaded_by)
-- VALUES ('uuid-here', 'https://supabase.co/storage/...', 'First smile!', '2025-06-01', auth.uid());

-- Example: Insert a measurement
-- INSERT INTO measurements (baby_id, measurement_date, weight_kg, height_cm, notes, recorded_by)
-- VALUES ('uuid-here', '2025-06-01', 8.2, 72.5, '6-month checkup', auth.uid());

-- Example: Generate share link
-- INSERT INTO share_links (baby_id, share_token, created_by)
-- VALUES ('uuid-here', uuid_generate_v4()::text, auth.uid());

-- ============================================================================
-- Migration Complete!
-- Next Step: Run 02_enable_rls.sql to set up Row Level Security
-- ============================================================================
