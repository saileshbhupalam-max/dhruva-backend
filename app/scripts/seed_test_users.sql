-- Seed data for test users
-- Sample citizens and officials for testing

INSERT INTO users (id, mobile_number, email, full_name, role, created_at, updated_at)
VALUES
    -- Test Citizens
    (gen_random_uuid(), '9876543210', 'citizen1@example.com', 'Ramesh Kumar', 'citizen', NOW(), NOW()),
    (gen_random_uuid(), '9876543211', 'citizen2@example.com', 'Lakshmi Devi', 'citizen', NOW(), NOW()),
    (gen_random_uuid(), '9876543212', 'citizen3@example.com', 'Venkat Rao', 'citizen', NOW(), NOW()),
    (gen_random_uuid(), '9876543213', 'citizen4@example.com', 'Sita Reddy', 'citizen', NOW(), NOW()),
    (gen_random_uuid(), '9876543214', 'citizen5@example.com', 'Krishna Murthy', 'citizen', NOW(), NOW()),

    -- Test Officials
    (gen_random_uuid(), '9999999901', 'official1@ap.gov.in', 'Prasad Admin', 'admin', NOW(), NOW()),
    (gen_random_uuid(), '9999999902', 'official2@ap.gov.in', 'Madhavi Officer', 'officer', NOW(), NOW()),
    (gen_random_uuid(), '9999999903', 'official3@ap.gov.in', 'Suresh Manager', 'manager', NOW(), NOW())
ON CONFLICT (mobile_number) DO NOTHING;

-- Verification query
-- Run this to verify all users were inserted:
-- SELECT role, COUNT(*) as count
-- FROM users
-- WHERE deleted_at IS NULL
-- GROUP BY role
-- ORDER BY role;
-- Expected: 5 citizens, 1 admin, 1 officer, 1 manager
