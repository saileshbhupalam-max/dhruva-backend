-- ==========================================
-- DHRUVA PGRS - COMPLETE SEED DATA
-- ==========================================
-- Seeds 13 districts, 26 departments, and 5 test users
-- Run: psql -U postgres -d dhruva_pgrs -f backend/db/seeds/seed_data.sql

-- ==========================================
-- 1. SEED DISTRICTS (13 Andhra Pradesh Districts)
-- ==========================================

INSERT INTO districts (code, name, created_at, updated_at) VALUES
    ('01', 'Anantapur', NOW(), NOW()),
    ('02', 'Chittoor', NOW(), NOW()),
    ('03', 'East Godavari', NOW(), NOW()),
    ('04', 'Guntur', NOW(), NOW()),
    ('05', 'Krishna', NOW(), NOW()),
    ('06', 'Kurnool', NOW(), NOW()),
    ('07', 'Prakasam', NOW(), NOW()),
    ('08', 'Nellore', NOW(), NOW()),
    ('09', 'Srikakulam', NOW(), NOW()),
    ('10', 'Visakhapatnam', NOW(), NOW()),
    ('11', 'Vizianagaram', NOW(), NOW()),
    ('12', 'West Godavari', NOW(), NOW()),
    ('13', 'YSR Kadapa', NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- ==========================================
-- 2. SEED DEPARTMENTS (26 Government Departments)
-- ==========================================

INSERT INTO departments (code, name, name_telugu, description, sla_days, created_at, updated_at) VALUES
    -- Critical Priority (SLA: 1-7 days)
    ('POL', 'Police', 'పోలీసు', 'Law and order, crime prevention, public safety', 1, NOW(), NOW()),
    ('HLTH', 'Health Department', 'ఆరోగ్య శాఖ', 'Public health, hospitals, medical services', 7, NOW(), NOW()),
    ('PENS', 'Pensions Department', 'పెన్షన్ల శాఖ', 'Pension disbursement and management', 7, NOW(), NOW()),
    ('FOOD', 'Food & Civil Supplies', 'ఆహార & పౌర సరఫరాల శాఖ', 'Ration cards, PDS, food distribution', 7, NOW(), NOW()),
    ('ELEC', 'Electricity', 'విద్యుత్ శాఖ', 'Power supply, electricity complaints', 7, NOW(), NOW()),

    -- High Priority (SLA: 30 days)
    ('REV', 'Revenue Department', 'రెవిన్యూ శాఖ', 'Land records, certificates, revenue administration', 30, NOW(), NOW()),
    ('EDU', 'Education Department', 'విద్యా శాఖ', 'Schools, teachers, education infrastructure', 30, NOW(), NOW()),
    ('PWD', 'Public Works Department', 'ప్రజా పనుల శాఖ', 'Roads, bridges, public infrastructure', 30, NOW(), NOW()),
    ('WATR', 'Water Resources', 'నీటి వనరుల శాఖ', 'Water supply, irrigation, drainage', 30, NOW(), NOW()),
    ('TRANS', 'Transport', 'రవాణా శాఖ', 'RTO, vehicle registration, driving licenses', 30, NOW(), NOW()),
    ('HOUS', 'Housing', 'గృహనిర్మాణ శాఖ', 'Government housing schemes, allotment', 30, NOW(), NOW()),
    ('AGRI', 'Agriculture', 'వ్యవసాయ శాఖ', 'Farming support, crop insurance, subsidies', 30, NOW(), NOW()),
    ('ANIM', 'Animal Husbandry', 'పశుపోషణ శాఖ', 'Livestock, veterinary services', 30, NOW(), NOW()),
    ('FISH', 'Fisheries', 'మత్స్య శాఖ', 'Fishing licenses, coastal management', 30, NOW(), NOW()),
    ('FOR', 'Forest', 'అటవీ శాఖ', 'Forest conservation, wildlife protection', 30, NOW(), NOW()),
    ('INDS', 'Industries', 'పరిశ్రమల శాఖ', 'Industrial licenses, MSME support', 30, NOW(), NOW()),
    ('LABR', 'Labour', 'కార్మిక శాఖ', 'Worker welfare, labor disputes', 30, NOW(), NOW()),
    ('LAW', 'Law & Justice', 'చట్ట & న్యాయ శాఖ', 'Legal aid, court matters', 30, NOW(), NOW()),
    ('MUNI', 'Municipal Administration', 'మునిసిపల్ పరిపాలన', 'Urban services, sanitation, drainage', 30, NOW(), NOW()),
    ('PANC', 'Panchayati Raj', 'పంచాయతీరాజ్', 'Village administration, gram panchayats', 30, NOW(), NOW()),
    ('RURD', 'Rural Development', 'గ్రామీణాభివృద్ధి శాఖ', 'Rural infrastructure, NREGA', 30, NOW(), NOW()),
    ('SCWF', 'Social Welfare', 'సంఘక్షేమ శాఖ', 'SC/ST welfare, scholarships', 30, NOW(), NOW()),
    ('TOUR', 'Tourism', 'పర్యాటక శాఖ', 'Tourism development, heritage sites', 30, NOW(), NOW()),
    ('URBAN', 'Urban Development', 'పట్టణాభివృద్ధి శాఖ', 'Urban planning, smart cities', 30, NOW(), NOW()),
    ('WMCH', 'Women & Child Welfare', 'మహిళా & శిశు సంక్షేమ శాఖ', 'Women safety, child welfare, Anganwadi', 30, NOW(), NOW()),
    ('MISC', 'Miscellaneous', 'ఇతరాలు', 'Other grievances not covered above', 30, NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- ==========================================
-- 3. SEED TEST USERS (5 Users for Development/Testing)
-- ==========================================
-- ALL USERS PASSWORD: password123
-- Bcrypt hash: $2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYFZYlZBWZC

INSERT INTO users (
    id,
    username,
    email,
    password_hash,
    full_name,
    phone,
    role,
    department_id,
    district_id,
    is_active,
    created_at,
    updated_at
) VALUES
    -- Admin User
    (
        gen_random_uuid(),
        'admin',
        'admin@dhruva.ap.gov.in',
        '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYFZYlZBWZC',
        'System Administrator',
        '+919876543210',
        'admin',
        NULL,
        NULL,
        true,
        NOW(),
        NOW()
    ),

    -- Revenue Officer (Krishna District - Vijayawada)
    (
        gen_random_uuid(),
        'officer_vijayawada',
        'officer.vijayawada@dhruva.ap.gov.in',
        '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYFZYlZBWZC',
        'Ramesh Kumar',
        '+919876543211',
        'officer',
        (SELECT id FROM departments WHERE code = 'REV'),
        (SELECT id FROM districts WHERE code = '05'),
        true,
        NOW(),
        NOW()
    ),

    -- Revenue Supervisor (Krishna District - Vijayawada)
    (
        gen_random_uuid(),
        'supervisor_vijayawada',
        'supervisor.vijayawada@dhruva.ap.gov.in',
        '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYFZYlZBWZC',
        'Lakshmi Devi',
        '+919876543212',
        'supervisor',
        (SELECT id FROM departments WHERE code = 'REV'),
        (SELECT id FROM districts WHERE code = '05'),
        true,
        NOW(),
        NOW()
    ),

    -- Health Officer (Visakhapatnam District)
    (
        gen_random_uuid(),
        'officer_health',
        'officer.health@dhruva.ap.gov.in',
        '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYFZYlZBWZC',
        'Dr. Suresh Reddy',
        '+919876543213',
        'officer',
        (SELECT id FROM departments WHERE code = 'HLTH'),
        (SELECT id FROM districts WHERE code = '10'),
        true,
        NOW(),
        NOW()
    ),

    -- Police Officer (Visakhapatnam District)
    (
        gen_random_uuid(),
        'officer_police',
        'officer.police@dhruva.ap.gov.in',
        '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYFZYlZBWZC',
        'Inspector Mahesh',
        '+919876543214',
        'officer',
        (SELECT id FROM departments WHERE code = 'POL'),
        (SELECT id FROM districts WHERE code = '10'),
        true,
        NOW(),
        NOW()
    )
ON CONFLICT (username) DO NOTHING;

-- ==========================================
-- 4. VERIFY SEED DATA
-- ==========================================

-- Show counts
SELECT 'Districts seeded:' as message, COUNT(*) as count FROM districts
UNION ALL
SELECT 'Departments seeded:', COUNT(*) FROM departments
UNION ALL
SELECT 'Users seeded:', COUNT(*) FROM users;

-- ==========================================
-- TEST CREDENTIALS SUMMARY
-- ==========================================
--
-- Username: admin | Password: password123 | Role: admin
-- Username: officer_vijayawada | Password: password123 | Role: officer (Revenue, Krishna)
-- Username: supervisor_vijayawada | Password: password123 | Role: supervisor (Revenue, Krishna)
-- Username: officer_health | Password: password123 | Role: officer (Health, Visakhapatnam)
-- Username: officer_police | Password: password123 | Role: officer (Police, Visakhapatnam)
