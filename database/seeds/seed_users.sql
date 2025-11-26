-- ==========================================
-- DHRUVA PGRS - SEED DATA: USERS
-- ==========================================
-- 5 Sample Users (1 citizen, 2 officers, 1 supervisor, 1 admin)
--
-- Usage:
--   psql -U postgres -d dhruva_pgrs -f backend/database/seeds/seed_users.sql
--
-- PASSWORD GENERATION:
-- All test users use password: "password123"
-- Bcrypt hash: $2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYFZYlZBWZC
--
-- To generate new bcrypt hash in Python:
--   import bcrypt
--   bcrypt.hashpw(b'your_password', bcrypt.gensalt()).decode()
--
-- SECURITY WARNING:
-- These are TEST USERS ONLY. Never use in production!
-- Change passwords immediately in production environment.
-- ==========================================

INSERT INTO users (id, mobile_number, email, full_name, role, created_at, updated_at, deleted_at)
VALUES
    -- Test Citizen
    (
        gen_random_uuid(),
        '+919876543210',
        'citizen.test@example.com',
        'Test Citizen User',
        'citizen',
        NOW(),
        NOW(),
        NULL
    ),

    -- Test Officer 1 (Visakhapatnam District)
    (
        gen_random_uuid(),
        '+919876543211',
        'officer1@ap.gov.in',
        'Officer Rama Krishna',
        'officer',
        NOW(),
        NOW(),
        NULL
    ),

    -- Test Officer 2 (Guntur District)
    (
        gen_random_uuid(),
        '+919876543212',
        'officer2@ap.gov.in',
        'Officer Lakshmi Devi',
        'officer',
        NOW(),
        NOW(),
        NULL
    ),

    -- Test Supervisor (State Level)
    (
        gen_random_uuid(),
        '+919876543213',
        'supervisor@ap.gov.in',
        'Supervisor Venkat Rao',
        'supervisor',
        NOW(),
        NOW(),
        NULL
    ),

    -- Test Admin (System Administrator)
    (
        gen_random_uuid(),
        '+919876543214',
        'admin@ap.gov.in',
        'Admin Srinivas Reddy',
        'admin',
        NOW(),
        NOW(),
        NULL
    )
ON CONFLICT (mobile_number) DO NOTHING;

-- Verify insertion
SELECT COUNT(*) as total_users FROM users;
SELECT mobile_number, full_name, role FROM users ORDER BY role, full_name;

-- ==========================================
-- ADDITIONAL NOTES
-- ==========================================
--
-- Password Storage:
-- In production, passwords must be stored as bcrypt hashes
-- Never store plain text passwords
--
-- User Roles:
-- - citizen: Can submit grievances, track status
-- - officer: Can be assigned grievances, update status
-- - supervisor: Can assign grievances to officers, view all in district
-- - admin: Full system access, user management, reports
--
-- Mobile Number Format:
-- Must be E.164 format: +91 (country code) + 10 digits
-- Example: +919876543210
--
-- Email Validation:
-- Officers/Supervisors/Admins should use @ap.gov.in domain
-- Citizens can use any valid email
-- ==========================================
