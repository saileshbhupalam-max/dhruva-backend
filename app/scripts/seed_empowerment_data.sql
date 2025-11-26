-- Seed data for Citizen Empowerment System (Task 3C)
-- Run this after the migration is applied

-- =====================================================
-- RIGHTS KNOWLEDGE BASE - Core Categories
-- =====================================================

-- PENSION DELAY - Level 1 (Basic Rights)
INSERT INTO rights_knowledge_base (department, category, disclosure_level, right_title, right_description_en, right_description_te, legal_reference, helpful_contact, priority_order) VALUES
('Pension', 'Pension Delay', 1, 'Resolution Timeline',
 'Your pension issue must be resolved within 7 days of complaint registration',
 'మీ పెన్షన్ సమస్య ఫిర్యాదు నమోదు అయిన 7 రోజుల్లో పరిష్కరించాలి',
 'Rule 12.3, AP Pension Rules', NULL, 1),

('Pension', 'Pension Delay', 1, 'Helpline Access',
 'Call Pension Helpline 1800-599-4422 for immediate assistance',
 'తక్షణ సహాయం కోసం పెన్షన్ హెల్ప్‌లైన్ 1800-599-4422 కు కాల్ చేయండి',
 NULL, '1800-599-4422', 2),

('Pension', 'Pension Delay', 1, 'Bank Complaint Option',
 'If Treasury delays, you can file complaint directly at your bank',
 'ట్రెజరీ ఆలస్యం చేస్తే, మీరు మీ బ్యాంక్ లో నేరుగా ఫిర్యాదు చేయవచ్చు',
 NULL, NULL, 3),

-- PENSION DELAY - Level 2 (Officer Details)
('Pension', 'Pension Delay', 2, 'Assigned Officer',
 'Your case is assigned to District Treasury Officer. You can visit treasury office.',
 'మీ కేసు జిల్లా ట్రెజరీ అధికారికి కేటాయించబడింది. మీరు ట్రెజరీ కార్యాలయాన్ని సందర్శించవచ్చు.',
 NULL, NULL, 1),

('Pension', 'Pension Delay', 2, 'Office Timings',
 'Treasury Office: Mon-Sat, 10 AM - 5 PM. Bring your PPO number.',
 'ట్రెజరీ కార్యాలయం: సోమ-శని, ఉదయం 10 - సాయంత్రం 5. మీ PPO నంబర్ తీసుకురండి.',
 NULL, NULL, 2),

-- PENSION DELAY - Level 3 (Legal Provisions)
('Pension', 'Pension Delay', 3, 'Legal Recourse',
 'Under AP Civil Services Rules, pension is a statutory right. Delay beyond 7 days can be reported to Lokayukta.',
 'AP సివిల్ సర్వీసెస్ నిబంధనల ప్రకారం, పెన్షన్ చట్టబద్ధమైన హక్కు. 7 రోజులకు మించి ఆలస్యం లోకాయుక్తకు రిపోర్ట్ చేయవచ్చు.',
 'AP Civil Services Rules Section 234', NULL, 1),

-- RATION CARD - Level 1
('Civil Supplies', 'Ration Card', 1, 'Issuance Timeline',
 'New ration card must be issued within 15 days of application',
 'దరఖాస్తు చేసిన 15 రోజుల్లో కొత్త రేషన్ కార్డు జారీ చేయాలి',
 'PDS Act Section 4', NULL, 1),

('Civil Supplies', 'Ration Card', 1, 'No Extra Documents',
 'Dealer cannot demand documents beyond Aadhaar and address proof',
 'డీలర్ ఆధార్ మరియు చిరునామా రుజువు మినహా పత్రాలు అడగలేరు',
 'PDS Guidelines 2023', NULL, 2),

('Civil Supplies', 'Ration Card', 1, 'Temporary Slip',
 'You can get temporary slip while card processes - ask at Fair Price Shop',
 'కార్డు ప్రాసెస్ అవుతున్నప్పుడు తాత్కాలిక స్లిప్ పొందవచ్చు - Fair Price Shop లో అడగండి',
 NULL, NULL, 3),

-- LAND SURVEY - Level 1
('Revenue', 'Land Survey', 1, 'Survey Timeline',
 'Land survey must be completed within 30 days of request',
 'అభ్యర్థన చేసిన 30 రోజుల్లో భూమి సర్వే పూర్తి చేయాలి',
 'AP Survey Manual Rule 45', NULL, 1),

('Revenue', 'Land Survey', 1, 'Surveyor Obligations',
 'Surveyor must give you copy of measurements. Demand receipt for any payment.',
 'సర్వేయర్ మీకు కొలతల కాపీ ఇవ్వాలి. ఏదైనా చెల్లింపుకు రసీదు అడగండి.',
 NULL, NULL, 2),

('Revenue', 'Land Survey', 1, 'Standard Fees',
 'Survey fee is Rs.500 only for normal cases. Do not pay more without receipt.',
 'సాధారణ కేసులకు సర్వే ఫీజు Rs.500 మాత్రమే. రసీదు లేకుండా ఎక్కువ చెల్లించవద్దు.',
 'AP Revenue Fee Schedule 2024', NULL, 3),

-- BIRTH/DEATH CERTIFICATE - Level 1
('Municipal', 'Certificate', 1, 'Issuance Timeline',
 'Certificate must be issued within 21 days of application',
 'దరఖాస్తు చేసిన 21 రోజుల్లో సర్టిఫికేట్ జారీ చేయాలి',
 'Registration of Births and Deaths Act', NULL, 1),

('Municipal', 'Certificate', 1, 'Late Fee Waiver',
 'Late registration fee is waived if delay was due to hospital/office fault',
 'ఆస్పత్రి/కార్యాలయం తప్పు వల్ల ఆలస్యమైతే ఆలస్య రిజిస్ట్రేషన్ ఫీజు మినహాయించబడుతుంది',
 NULL, NULL, 2),

('Municipal', 'Certificate', 1, 'Online Application',
 'Online application is equally valid - no need to visit office',
 'ఆన్‌లైన్ దరఖాస్తు సమానంగా చెల్లుతుంది - కార్యాలయానికి వెళ్ళవలసిన అవసరం లేదు',
 'meeseva.ap.gov.in', NULL, 3),

-- GENERIC RIGHTS - Level 1 (Fallback for any category)
('General', 'All', 1, 'Right to Track',
 'You have the right to track your case status online or via SMS',
 'మీ కేసు స్థితిని ఆన్‌లైన్ లేదా SMS ద్వారా ట్రాక్ చేసే హక్కు మీకు ఉంది',
 NULL, NULL, 1),

('General', 'All', 1, 'Right to Escalate',
 'If not resolved within SLA, case auto-escalates to higher authority',
 'SLA లో పరిష్కరించకపోతే, కేసు ఆటోమేటిక్‌గా ఉన్నత అధికారికి escalate అవుతుంది',
 'PGRS Guidelines 2024', NULL, 2),

('General', 'All', 1, 'Right to Officer Info',
 'You can know the name of officer handling your case',
 'మీ కేసును హ్యాండిల్ చేస్తున్న అధికారి పేరు తెలుసుకోవచ్చు',
 'RTI Act 2005', NULL, 3),

-- =====================================================
-- AP WELFARE SCHEME SPECIFIC RIGHTS
-- =====================================================

-- YSR PENSION KANUKA
('Social Welfare', 'YSR Pension Kanuka', 1, 'Eligibility Check',
 'All citizens above 60 years with income below Rs.10,000/month are eligible',
 '10,000 రూ./నెల లోపు ఆదాయం ఉన్న 60 ఏళ్ల పైబడిన పౌరులందరూ అర్హులు',
 'GO MS 15, Social Welfare Dept', NULL, 1),

('Social Welfare', 'YSR Pension Kanuka', 1, 'Monthly Amount',
 'Current pension amount is Rs.2,750/month. Paid every month through bank.',
 'ప్రస్తుత పెన్షన్ మొత్తం నెలకు Rs.2,750. ప్రతి నెలా బ్యాంక్ ద్వారా చెల్లిస్తారు.',
 NULL, NULL, 2),

('Social Welfare', 'YSR Pension Kanuka', 1, 'Complaint Helpline',
 'Call 1902 (toll-free) for pension complaints. Lodge complaint on Spandana portal.',
 'పెన్షన్ ఫిర్యాదులకు 1902 (టోల్-ఫ్రీ) కాల్ చేయండి. స్పందన పోర్టల్‌లో ఫిర్యాదు చేయండి.',
 NULL, '1902', 3),

-- AMMA VODI
('Education', 'Amma Vodi', 1, 'Eligibility',
 'Mother/guardian of children studying in govt/aided schools with BPL card eligible',
 'BPL కార్డు ఉన్న ప్రభుత్వ/సహాయిత పాఠశాలల్లో చదువుతున్న పిల్లల తల్లి/సంరక్షకులు అర్హులు',
 'GO MS 4, Education Dept', NULL, 1),

('Education', 'Amma Vodi', 1, 'Annual Amount',
 'Rs.15,000 per year per child. Credited to mother bank account in January.',
 'ఏడాదికి బిడ్డకు Rs.15,000. జనవరిలో తల్లి బ్యాంక్ ఖాతాకు జమ అవుతుంది.',
 NULL, NULL, 2),

('Education', 'Amma Vodi', 1, 'Grievance Portal',
 'Apply for Amma Vodi issues on VSP portal or contact school headmaster',
 'అమ్మ వొడి సమస్యలకు VSP పోర్టల్‌లో దరఖాస్తు చేయండి లేదా పాఠశాల ప్రధానోపాధ్యాయుడిని సంప్రదించండి',
 'vsp.ap.gov.in', NULL, 3),

-- RYTHU BHAROSA
('Agriculture', 'Rythu Bharosa', 1, 'Eligibility',
 'All farmers with cultivable land (own or lease) are eligible',
 'సాగు భూమి (సొంత లేదా లీజు) ఉన్న రైతులందరూ అర్హులు',
 'GO MS 16, Agriculture Dept', NULL, 1),

('Agriculture', 'Rythu Bharosa', 1, 'Benefit Amount',
 'Rs.13,500 per year in 3 installments (Rabi, Kharif seasons)',
 'సంవత్సరానికి Rs.13,500, 3 విడతల్లో (రబీ, ఖరీఫ్ సీజన్లు)',
 NULL, NULL, 2),

('Agriculture', 'Rythu Bharosa', 1, 'Contact',
 'Contact Agricultural Officer at Mandal or call 1800-599-7766',
 'మండల వ్యవసాయ అధికారిని సంప్రదించండి లేదా 1800-599-7766 కు కాల్ చేయండి',
 NULL, '1800-599-7766', 3),

-- VIDYA DEEVENA
('Education', 'Vidya Deevena', 1, 'Eligibility',
 'Students in ITI/Polytechnic/Degree/PG with parent income below Rs.2.5 lakh eligible',
 'Rs.2.5 లక్షల లోపు తల్లిదండ్రుల ఆదాయం ఉన్న ITI/పాలిటెక్నిక్/డిగ్రీ/PG విద్యార్థులు అర్హులు',
 'GO MS 18, Higher Education', NULL, 1),

('Education', 'Vidya Deevena', 1, 'Fee Reimbursement',
 'Complete tuition fee reimbursement paid directly to college',
 'పూర్తి ట్యూషన్ ఫీజు రీఎంబర్స్‌మెంట్ నేరుగా కళాశాలకు చెల్లించబడుతుంది',
 NULL, NULL, 2),

-- PEDALANDARIKI ILLU
('Housing', 'Pedalandariki Illu', 1, 'Eligibility',
 'Landless families living in huts/rented houses with white ration card eligible',
 'తెల్ల రేషన్ కార్డు ఉన్న గుడిసెలు/అద్దె ఇళ్ళలో నివసించే భూమిలేని కుటుంబాలు అర్హులు',
 'GO MS 12, Housing Dept', NULL, 1),

('Housing', 'Pedalandariki Illu', 1, 'House Details',
 'Free 365 sqft house with 2 rooms, kitchen, bathroom, and plot',
 'ఉచితంగా 365 చదరపు అడుగుల ఇల్లు, 2 గదులు, వంటగది, బాత్రూం మరియు ప్లాట్',
 NULL, NULL, 2),

('Housing', 'Pedalandariki Illu', 1, 'Application',
 'Apply through village/ward volunteer or Spandana portal',
 'గ్రామ/వార్డు వాలంటీర్ ద్వారా లేదా స్పందన పోర్టల్ ద్వారా దరఖాస్తు చేయండి',
 'spandana.ap.gov.in', NULL, 3),

-- AAROGYASRI
('Health', 'Aarogyasri', 1, 'Eligibility',
 'All white ration card holders eligible for free treatment up to Rs.5 lakh',
 'తెల్ల రేషన్ కార్డు హోల్డర్లందరికీ Rs.5 లక్షల వరకు ఉచిత వైద్యం',
 'Aarogyasri Health Care Trust', NULL, 1),

('Health', 'Aarogyasri', 1, 'Emergency',
 'In emergency, go directly to network hospital. Card not needed for first 48 hours.',
 'అత్యవసర పరిస్థితిలో నేరుగా నెట్‌వర్క్ ఆసుపత్రికి వెళ్ళండి. మొదటి 48 గంటలకు కార్డు అవసరం లేదు.',
 NULL, NULL, 2),

('Health', 'Aarogyasri', 1, 'Helpline',
 'Call 104 for Aarogyasri queries. 1902 for complaints.',
 'ఆరోగ్య శ్రీ సమస్యలకు 104 కు కాల్ చేయండి. ఫిర్యాదులకు 1902.',
 NULL, '104', 3);

-- =====================================================
-- PROACTIVE TRIGGER CONFIGURATION
-- =====================================================

INSERT INTO proactive_trigger_config (trigger_type, enabled, threshold_value, message_template_en, message_template_te) VALUES
('SLA_50_PERCENT', TRUE, 50,
 'Your case {case_id} is {days_elapsed} days old (50% of allowed time). Status: {status}. Need help tracking? Reply 1 for tips.',
 'మీ కేసు {case_id} {days_elapsed} రోజులు అయింది (అనుమతించిన సమయంలో 50%). స్థితి: {status}. ట్రాకింగ్ సహాయం కావాలా? చిట్కాల కోసం 1 రిప్లై చేయండి.'),

('SLA_APPROACHING', TRUE, 80,
 'ALERT: Your case {case_id} deadline is in {days_remaining} days. If not resolved, it will auto-escalate. Have you received any update? Reply: 1=Yes 2=No',
 'హెచ్చరిక: మీ కేసు {case_id} గడువు {days_remaining} రోజుల్లో ఉంది. పరిష్కారం లేకపోతే auto-escalate అవుతుంది. ఏదైనా అప్‌డేట్ వచ్చిందా? రిప్లై: 1=అవును 2=లేదు'),

('NO_UPDATE_7_DAYS', TRUE, 7,
 'Your case {case_id} has no update in 7 days. Want to know your rights? Reply 1. Contact officer? Reply 2.',
 'మీ కేసు {case_id} కు 7 రోజులుగా అప్‌డేట్ లేదు. మీ హక్కులు తెలుసుకోవాలా? 1 రిప్లై చేయండి. అధికారిని సంప్రదించాలా? 2 రిప్లై చేయండి.');
