-- Seed data for Andhra Pradesh districts
-- All 26 districts as per 2024 administrative divisions

INSERT INTO districts (id, district_code, district_name, created_at, updated_at)
VALUES
    (gen_random_uuid(), 'ANT', 'Anantapur', NOW(), NOW()),
    (gen_random_uuid(), 'CHT', 'Chittoor', NOW(), NOW()),
    (gen_random_uuid(), 'EG', 'East Godavari', NOW(), NOW()),
    (gen_random_uuid(), 'GNT', 'Guntur', NOW(), NOW()),
    (gen_random_uuid(), 'KDP', 'Kadapa', NOW(), NOW()),
    (gen_random_uuid(), 'KRS', 'Krishna', NOW(), NOW()),
    (gen_random_uuid(), 'KNL', 'Kurnool', NOW(), NOW()),
    (gen_random_uuid(), 'NLR', 'Nellore', NOW(), NOW()),
    (gen_random_uuid(), 'PKM', 'Prakasam', NOW(), NOW()),
    (gen_random_uuid(), 'SKM', 'Srikakulam', NOW(), NOW()),
    (gen_random_uuid(), 'VSP', 'Visakhapatnam', NOW(), NOW()),
    (gen_random_uuid(), 'VZG', 'Vizianagaram', NOW(), NOW()),
    (gen_random_uuid(), 'WG', 'West Godavari', NOW(), NOW()),
    (gen_random_uuid(), 'ARL', 'Alluri Sitharama Raju', NOW(), NOW()),
    (gen_random_uuid(), 'ANA', 'Anakapalli', NOW(), NOW()),
    (gen_random_uuid(), 'ANM', 'Annamaya', NOW(), NOW()),
    (gen_random_uuid(), 'BAP', 'Bapatla', NOW(), NOW()),
    (gen_random_uuid(), 'ELR', 'Eluru', NOW(), NOW()),
    (gen_random_uuid(), 'KKN', 'Kakinada', NOW(), NOW()),
    (gen_random_uuid(), 'KNR', 'Konaseema', NOW(), NOW()),
    (gen_random_uuid(), 'NTR', 'NTR District', NOW(), NOW()),
    (gen_random_uuid(), 'PLN', 'Palnadu', NOW(), NOW()),
    (gen_random_uuid(), 'PVT', 'Parvathipuram Manyam', NOW(), NOW()),
    (gen_random_uuid(), 'NAG', 'Sri Potti Sriramulu Nellore', NOW(), NOW()),
    (gen_random_uuid(), 'STY', 'Sri Satya Sai', NOW(), NOW()),
    (gen_random_uuid(), 'TPT', 'Tirupati', NOW(), NOW())
ON CONFLICT (district_code) DO NOTHING;

-- Verification query
-- Run this to verify all districts were inserted:
-- SELECT COUNT(*) as total_districts,
--        STRING_AGG(district_code, ', ' ORDER BY district_code) as codes
-- FROM districts;
-- Expected: 26 districts
