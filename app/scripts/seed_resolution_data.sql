-- Seed data for Smart Resolution Engine (Task 3B)
-- This script populates intervention_questions and resolution_templates

-- ============================================================================
-- INTERVENTION QUESTIONS
-- ============================================================================

-- WRONG_DEPARTMENT questions
INSERT INTO intervention_questions (root_cause, department, category, question_text_en, question_text_te, question_order, response_type, response_options, is_required) VALUES
('WRONG_DEPARTMENT', NULL, NULL,
 'Which government office did you visit for this issue?',
 'ఈ సమస్య కోసం మీరు ఏ ప్రభుత్వ కార్యాలయానికి వెళ్ళారు?',
 1, 'TEXT', NULL, TRUE),
('WRONG_DEPARTMENT', NULL, NULL,
 'What type of document or service were you seeking?',
 'మీరు ఏ రకమైన పత్రం లేదా సేవ కోరుతున్నారు?',
 2, 'SINGLE_CHOICE',
 '["Land Records", "Certificate", "Pension", "Ration Card", "License", "Other"]', TRUE);

-- MISSING_INFORMATION questions - Revenue
INSERT INTO intervention_questions (root_cause, department, category, question_text_en, question_text_te, question_order, response_type, response_options, is_required) VALUES
('MISSING_INFORMATION', 'Revenue', NULL,
 'Please provide your Survey Number',
 'దయచేసి మీ సర్వే నంబర్ అందించండి',
 1, 'TEXT', NULL, TRUE),
('MISSING_INFORMATION', 'Revenue', NULL,
 'Please provide the Village/Mandal name',
 'దయచేసి గ్రామం/మండల పేరు అందించండి',
 2, 'TEXT', NULL, TRUE);

-- MISSING_INFORMATION questions - Pension
INSERT INTO intervention_questions (root_cause, department, category, question_text_en, question_text_te, question_order, response_type, response_options, is_required) VALUES
('MISSING_INFORMATION', 'Pension', NULL,
 'Please provide your Pension ID or PPO Number',
 'దయచేసి మీ పెన్షన్ ID లేదా PPO నంబర్ అందించండి',
 1, 'TEXT', NULL, TRUE),
('MISSING_INFORMATION', 'Pension', NULL,
 'Please provide your Bank Account Number (last 4 digits)',
 'దయచేసి మీ బ్యాంక్ ఖాతా నంబర్ (చివరి 4 అంకెలు) అందించండి',
 2, 'NUMBER', NULL, TRUE);

-- CITIZEN_UNREACHABLE questions
INSERT INTO intervention_questions (root_cause, department, category, question_text_en, question_text_te, question_order, response_type, response_options, is_required) VALUES
('CITIZEN_UNREACHABLE', NULL, NULL,
 'Please provide an alternate phone number we can reach you at',
 'దయచేసి మిమ్మల్ని సంప్రదించగల ప్రత్యామ్నాయ ఫోన్ నంబర్ అందించండి',
 1, 'TEXT', NULL, TRUE),
('CITIZEN_UNREACHABLE', NULL, NULL,
 'What is the best time to call you?',
 'మీకు కాల్ చేయడానికి ఉత్తమ సమయం ఏది?',
 2, 'SINGLE_CHOICE',
 '["Morning (9-12)", "Afternoon (12-4)", "Evening (4-7)", "Any time"]', TRUE);

-- NEEDS_FIELD_VISIT questions
INSERT INTO intervention_questions (root_cause, department, category, question_text_en, question_text_te, question_order, response_type, response_options, is_required) VALUES
('NEEDS_FIELD_VISIT', NULL, NULL,
 'Please confirm your address for the field visit',
 'దయచేసి ఫీల్డ్ విజిట్ కోసం మీ చిరునామాను నిర్ధారించండి',
 1, 'TEXT', NULL, TRUE),
('NEEDS_FIELD_VISIT', NULL, NULL,
 'Any landmark near your location?',
 'మీ స్థానానికి దగ్గరలో ఏదైనా ల్యాండ్‌మార్క్ ఉందా?',
 2, 'TEXT', NULL, FALSE),
('NEEDS_FIELD_VISIT', NULL, NULL,
 'Preferred date for field visit',
 'ఫీల్డ్ విజిట్ కోసం ప్రాధాన్య తేదీ',
 3, 'DATE', NULL, TRUE);

-- EXTERNAL_DEPENDENCY questions
INSERT INTO intervention_questions (root_cause, department, category, question_text_en, question_text_te, question_order, response_type, response_options, is_required) VALUES
('EXTERNAL_DEPENDENCY', NULL, NULL,
 'Which external department/agency is the issue pending with?',
 'సమస్య ఏ బాహ్య డిపార్ట్‌మెంట్/ఏజెన్సీలో పెండింగ్‌లో ఉంది?',
 1, 'TEXT', NULL, TRUE),
('EXTERNAL_DEPENDENCY', NULL, NULL,
 'Do you have any reference number for the pending item?',
 'పెండింగ్ అంశం కోసం మీ వద్ద ఏదైనా రిఫరెన్స్ నంబర్ ఉందా?',
 2, 'TEXT', NULL, FALSE);

-- OUTSIDE_JURISDICTION questions
INSERT INTO intervention_questions (root_cause, department, category, question_text_en, question_text_te, question_order, response_type, response_options, is_required) VALUES
('OUTSIDE_JURISDICTION', NULL, NULL,
 'Please provide your complete address',
 'దయచేసి మీ పూర్తి చిరునామా అందించండి',
 1, 'TEXT', NULL, TRUE),
('OUTSIDE_JURISDICTION', NULL, NULL,
 'Which district/mandal does your issue belong to?',
 'మీ సమస్య ఏ జిల్లా/మండలానికి చెందినది?',
 2, 'TEXT', NULL, TRUE);


-- ============================================================================
-- RESOLUTION TEMPLATES
-- ============================================================================

-- Pension templates
INSERT INTO resolution_templates (template_key, department, category, root_cause, template_title, template_description, action_steps, success_rate, avg_resolution_hours, similar_cases_resolved) VALUES
('pension_bank_mismatch_fix', 'Pension', 'Pension Delay', 'MISSING_INFORMATION',
 'Update Bank Account from Aadhaar',
 'Fix pension delay caused by bank account mismatch by fetching correct account from Aadhaar-linked database',
 '[
   {"step": 1, "action": "VERIFY_AADHAAR", "description": "Verify citizen Aadhaar number"},
   {"step": 2, "action": "FETCH_BANK_DETAILS", "description": "Fetch Aadhaar-linked bank account"},
   {"step": 3, "action": "UPDATE_PENSION_RECORD", "description": "Update pension disbursement record"},
   {"step": 4, "action": "TRIGGER_PAYMENT", "description": "Trigger next-cycle payment"},
   {"step": 5, "action": "NOTIFY_CITIZEN", "description": "Send SMS notification to citizen"}
 ]',
 95.20, 4, 2847),

('pension_verification_pending', 'Pension', 'Pension Delay', 'EXTERNAL_DEPENDENCY',
 'Fast-track Verification',
 'Expedite pending verification by routing to senior verifier',
 '[
   {"step": 1, "action": "IDENTIFY_BLOCKER", "description": "Identify which verification is pending"},
   {"step": 2, "action": "ESCALATE_TO_SENIOR", "description": "Route to senior verifier"},
   {"step": 3, "action": "SET_PRIORITY", "description": "Mark as high priority"},
   {"step": 4, "action": "NOTIFY_CITIZEN", "description": "Inform citizen of expedited processing"}
 ]',
 87.50, 24, 1523);

-- Revenue templates
INSERT INTO resolution_templates (template_key, department, category, root_cause, template_title, template_description, action_steps, success_rate, avg_resolution_hours, similar_cases_resolved) VALUES
('land_survey_schedule', 'Revenue', 'Land Survey', 'NEEDS_FIELD_VISIT',
 'Schedule Surveyor Visit',
 'Schedule field visit by assigning surveyor and notifying citizen',
 '[
   {"step": 1, "action": "CHECK_SURVEYOR_AVAILABILITY", "description": "Check available surveyors in mandal"},
   {"step": 2, "action": "ASSIGN_SURVEYOR", "description": "Assign surveyor to case"},
   {"step": 3, "action": "SCHEDULE_VISIT", "description": "Schedule visit within 7 days"},
   {"step": 4, "action": "NOTIFY_CITIZEN", "description": "Send SMS with date, time, and surveyor contact"},
   {"step": 5, "action": "CREATE_REMINDER", "description": "Set reminder for surveyor 1 day before"}
 ]',
 91.30, 168, 3421),

('land_wrong_dept_reclassify', 'Revenue', 'Land Records', 'WRONG_DEPARTMENT',
 'Reclassify to Correct Department',
 'Re-route grievance to correct department based on clarification',
 '[
   {"step": 1, "action": "ANALYZE_CLARIFICATION", "description": "Review citizen responses"},
   {"step": 2, "action": "IDENTIFY_CORRECT_DEPT", "description": "Determine correct department"},
   {"step": 3, "action": "TRANSFER_CASE", "description": "Transfer to correct department"},
   {"step": 4, "action": "NOTIFY_CITIZEN", "description": "Inform citizen of transfer"},
   {"step": 5, "action": "RESET_SLA", "description": "Reset SLA from transfer date"}
 ]',
 88.90, 2, 892);

-- Municipal templates
INSERT INTO resolution_templates (template_key, department, category, root_cause, template_title, template_description, action_steps, success_rate, avg_resolution_hours, similar_cases_resolved) VALUES
('pothole_repair_schedule', 'Municipal', 'Road Repair', 'NEEDS_FIELD_VISIT',
 'Schedule Road Repair',
 'Schedule road repair work by assigning contractor',
 '[
   {"step": 1, "action": "VERIFY_LOCATION", "description": "Verify GPS coordinates of issue"},
   {"step": 2, "action": "ASSESS_SEVERITY", "description": "Categorize repair type"},
   {"step": 3, "action": "ASSIGN_CONTRACTOR", "description": "Assign to available contractor"},
   {"step": 4, "action": "SCHEDULE_WORK", "description": "Schedule repair within SLA"},
   {"step": 5, "action": "NOTIFY_CITIZEN", "description": "Send expected completion date"}
 ]',
 82.40, 120, 5678);

-- Generic templates
INSERT INTO resolution_templates (template_key, department, category, root_cause, template_title, template_description, action_steps, success_rate, avg_resolution_hours, similar_cases_resolved) VALUES
('duplicate_merge', 'General', 'All', 'DUPLICATE_CASE',
 'Merge Duplicate Cases',
 'Merge duplicate grievance into existing case',
 '[
   {"step": 1, "action": "IDENTIFY_ORIGINAL", "description": "Find original case"},
   {"step": 2, "action": "COMPARE_DETAILS", "description": "Verify cases are duplicates"},
   {"step": 3, "action": "MERGE_ATTACHMENTS", "description": "Add any new attachments to original"},
   {"step": 4, "action": "CLOSE_DUPLICATE", "description": "Close duplicate with reference to original"},
   {"step": 5, "action": "NOTIFY_CITIZEN", "description": "Inform citizen of merge"}
 ]',
 96.70, 1, 4521),

('officer_redistribute', 'General', 'All', 'OFFICER_OVERLOAD',
 'Redistribute to Available Officer',
 'Transfer case to officer with lower workload',
 '[
   {"step": 1, "action": "FIND_AVAILABLE_OFFICER", "description": "Find officer in same dept with <50 cases"},
   {"step": 2, "action": "TRANSFER_CASE", "description": "Reassign case to new officer"},
   {"step": 3, "action": "NOTIFY_OFFICERS", "description": "Notify both officers"},
   {"step": 4, "action": "UPDATE_WORKLOAD", "description": "Update workload counters"}
 ]',
 94.10, 1, 2134),

('community_verify', 'General', 'All', 'CITIZEN_UNREACHABLE',
 'Trigger Community Verification',
 'Send verification request to community verifier network',
 '[
   {"step": 1, "action": "FIND_VERIFIER", "description": "Find ASHA/SHG/Volunteer within 2km"},
   {"step": 2, "action": "SEND_VERIFICATION_REQUEST", "description": "Send verification task to verifier"},
   {"step": 3, "action": "SET_DEADLINE", "description": "Set 3-day deadline for verification"},
   {"step": 4, "action": "AWAIT_RESPONSE", "description": "Monitor for verifier response"}
 ]',
 78.50, 72, 1876),

('policy_explanation', 'General', 'All', 'POLICY_LIMITATION',
 'Explain Policy and Provide Alternatives',
 'Send detailed explanation of policy limitation with alternative options',
 '[
   {"step": 1, "action": "IDENTIFY_POLICY", "description": "Identify the specific policy/GO"},
   {"step": 2, "action": "PREPARE_EXPLANATION", "description": "Prepare citizen-friendly explanation"},
   {"step": 3, "action": "FIND_ALTERNATIVES", "description": "List alternative actions citizen can take"},
   {"step": 4, "action": "NOTIFY_CITIZEN", "description": "Send explanation and alternatives"},
   {"step": 5, "action": "CLOSE_WITH_INFO", "description": "Close case with informational resolution"}
 ]',
 85.00, 4, 1245);

-- Success message
SELECT 'Seed data inserted successfully. Totals:' AS message;
SELECT COUNT(*) AS question_count FROM intervention_questions;
SELECT COUNT(*) AS template_count FROM resolution_templates;
