-- Seed data for Government Departments
-- Major departments handling public grievances in Andhra Pradesh

INSERT INTO departments (id, dept_code, dept_name, name_telugu, sla_days, created_at, updated_at)
VALUES
    (gen_random_uuid(), 'RD', 'Rural Development', 'గ్రామీణాభివృద్ధి', 7, NOW(), NOW()),
    (gen_random_uuid(), 'MUNICIPAL', 'Municipal Administration', 'మునిసిపల్ పరిపాలన', 7, NOW(), NOW()),
    (gen_random_uuid(), 'REVENUE', 'Revenue Department', 'రెవెన్యూ శాఖ', 7, NOW(), NOW()),
    (gen_random_uuid(), 'ELECTRICITY', 'Energy Department', 'శక్తి శాఖ', 7, NOW(), NOW()),
    (gen_random_uuid(), 'WATER', 'Water Resources', 'నీటి వనరులు', 7, NOW(), NOW()),
    (gen_random_uuid(), 'EDUCATION', 'School Education', 'పాఠశాల విద్య', 7, NOW(), NOW()),
    (gen_random_uuid(), 'HEALTH', 'Health and Family Welfare', 'ఆరోగ్యం మరియు కుటుంబ సంక్షేమం', 7, NOW(), NOW()),
    (gen_random_uuid(), 'POLICE', 'Police Department', 'పోలీసు శాఖ', 7, NOW(), NOW()),
    (gen_random_uuid(), 'TRANSPORT', 'Transport Department', 'రవాణా శాఖ', 7, NOW(), NOW()),
    (gen_random_uuid(), 'AGRICULTURE', 'Agriculture Department', 'వ్యవసాయ శాఖ', 7, NOW(), NOW()),
    (gen_random_uuid(), 'PANCHAYAT', 'Panchayat Raj', 'పంచాయతీరాజ్', 7, NOW(), NOW()),
    (gen_random_uuid(), 'WELFARE', 'Social Welfare', 'సాంఘిక సంక్షేమం', 7, NOW(), NOW()),
    (gen_random_uuid(), 'PWD', 'Public Works Department', 'ప్రజా పనుల శాఖ', 7, NOW(), NOW()),
    (gen_random_uuid(), 'HOUSING', 'Housing Department', 'గృహ శాఖ', 7, NOW(), NOW()),
    (gen_random_uuid(), 'LABOUR', 'Labour Department', 'కార్మిక శాఖ', 7, NOW(), NOW())
ON CONFLICT (dept_code) DO NOTHING;

-- Verification query
-- Run this to verify all departments were inserted:
-- SELECT COUNT(*) as total_departments,
--        STRING_AGG(dept_code, ', ' ORDER BY dept_code) as codes
-- FROM departments;
-- Expected: 15 departments
