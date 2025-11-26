-- ==========================================
-- DHRUVA PGRS - SEED DATA: DISTRICTS
-- ==========================================
-- 13 Districts of Andhra Pradesh
-- Source: Official AP Government administrative divisions
--
-- Usage:
--   psql -U postgres -d dhruva_pgrs -f backend/database/seeds/seed_districts.sql
--
-- Note: Uses gen_random_uuid() from pgcrypto extension
-- ==========================================

INSERT INTO districts (id, district_code, district_name, created_at, updated_at)
VALUES
    (gen_random_uuid(), 'VZG', 'Visakhapatnam', NOW(), NOW()),
    (gen_random_uuid(), 'VZN', 'Vizianagaram', NOW(), NOW()),
    (gen_random_uuid(), 'SKL', 'Srikakulam', NOW(), NOW()),
    (gen_random_uuid(), 'EG', 'East Godavari', NOW(), NOW()),
    (gen_random_uuid(), 'WG', 'West Godavari', NOW(), NOW()),
    (gen_random_uuid(), 'KRS', 'Krishna', NOW(), NOW()),
    (gen_random_uuid(), 'GNT', 'Guntur', NOW(), NOW()),
    (gen_random_uuid(), 'PKM', 'Prakasam', NOW(), NOW()),
    (gen_random_uuid(), 'SPSR', 'Sri Potti Sriramulu Nellore', NOW(), NOW()),
    (gen_random_uuid(), 'CTR', 'Chittoor', NOW(), NOW()),
    (gen_random_uuid(), 'KDP', 'Kadapa', NOW(), NOW()),
    (gen_random_uuid(), 'ATP', 'Anantapur', NOW(), NOW()),
    (gen_random_uuid(), 'KNL', 'Kurnool', NOW(), NOW())
ON CONFLICT (district_code) DO NOTHING;

-- Verify insertion
SELECT COUNT(*) as total_districts FROM districts;
SELECT district_code, district_name FROM districts ORDER BY district_name;
