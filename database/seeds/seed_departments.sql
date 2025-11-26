-- ==========================================
-- DHRUVA PGRS - SEED DATA: DEPARTMENTS
-- ==========================================
-- 26 Government Departments of Andhra Pradesh
-- Source: AP Government official department list
--
-- Usage:
--   psql -U postgres -d dhruva_pgrs -f backend/database/seeds/seed_departments.sql
--
-- Note: Uses gen_random_uuid() from pgcrypto extension
-- ==========================================

INSERT INTO departments (id, dept_code, dept_name, created_at, updated_at)
VALUES
    (gen_random_uuid(), 'PWD', 'Public Works Department', NOW(), NOW()),
    (gen_random_uuid(), 'MEPMA', 'Municipal Administration & Urban Development', NOW(), NOW()),
    (gen_random_uuid(), 'RWS', 'Rural Water Supply', NOW(), NOW()),
    (gen_random_uuid(), 'ENERGY', 'Energy Department', NOW(), NOW()),
    (gen_random_uuid(), 'HEALTH', 'Health, Medical & Family Welfare', NOW(), NOW()),
    (gen_random_uuid(), 'EDUCATION', 'School Education', NOW(), NOW()),
    (gen_random_uuid(), 'POLICE', 'Police Department', NOW(), NOW()),
    (gen_random_uuid(), 'REVENUE', 'Revenue Department', NOW(), NOW()),
    (gen_random_uuid(), 'PANCHAYAT', 'Panchayat Raj & Rural Development', NOW(), NOW()),
    (gen_random_uuid(), 'TRANSPORT', 'Transport, Roads & Buildings', NOW(), NOW()),
    (gen_random_uuid(), 'AGRICULTURE', 'Agriculture Department', NOW(), NOW()),
    (gen_random_uuid(), 'ANIMAL', 'Animal Husbandry', NOW(), NOW()),
    (gen_random_uuid(), 'FISHERIES', 'Fisheries Department', NOW(), NOW()),
    (gen_random_uuid(), 'FOREST', 'Forest Department', NOW(), NOW()),
    (gen_random_uuid(), 'LABOUR', 'Labour Department', NOW(), NOW()),
    (gen_random_uuid(), 'SOCIAL', 'Social Welfare', NOW(), NOW()),
    (gen_random_uuid(), 'WOMEN', 'Women & Child Welfare', NOW(), NOW()),
    (gen_random_uuid(), 'HOUSING', 'Housing Department', NOW(), NOW()),
    (gen_random_uuid(), 'FINANCE', 'Finance Department', NOW(), NOW()),
    (gen_random_uuid(), 'COMMERCIAL', 'Commercial Taxes', NOW(), NOW()),
    (gen_random_uuid(), 'EXCISE', 'Excise Department', NOW(), NOW()),
    (gen_random_uuid(), 'FIRE', 'Fire Services', NOW(), NOW()),
    (gen_random_uuid(), 'TOURISM', 'Tourism & Culture', NOW(), NOW()),
    (gen_random_uuid(), 'INDUSTRIES', 'Industries & Commerce', NOW(), NOW()),
    (gen_random_uuid(), 'IT', 'Information Technology', NOW(), NOW()),
    (gen_random_uuid(), 'LEGAL', 'Legal Affairs & Law', NOW(), NOW())
ON CONFLICT (dept_code) DO NOTHING;

-- Verify insertion
SELECT COUNT(*) as total_departments FROM departments;
SELECT dept_code, dept_name FROM departments ORDER BY dept_name;
