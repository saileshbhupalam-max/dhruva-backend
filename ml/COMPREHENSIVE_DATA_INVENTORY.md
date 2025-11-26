# Comprehensive Data Inventory for ML Training - DHRUVA PGRS

**Generated**: 2025-11-25
**Purpose**: Complete inventory of ALL available training data before model training

---

## 📊 EXECUTIVE SUMMARY

We have **MASSIVE government data** that was already extracted but NOT YET USED for training:

| Data Source | Records | Status | Location |
|-------------|---------|--------|----------|
| **Guntur Audit** | 2,298 cases, 13 lapse categories | ✅ Extracted | `audit_reports.json` |
| **PGRS Keywords** | 30 depts, 709 bilingual keywords | ✅ Extracted | `pgrs_book_keywords.json` |
| **Call Center 1100** | 93,892 feedback records, 31 depts | ✅ In docs | `STATE CALL CENTER 1100 FEEDBACK REPORT.md` |
| **Officer Performance** | 490 officers, 34 depts | ✅ Extracted | `officer_performance.json` |
| **Message Templates** | 54 official SMS/WhatsApp templates | ✅ Extracted | `message_templates.json` |
| **Audio Transcriptions** | 46 Telugu voice samples | ✅ Extracted | `audio_transcriptions.json` |
| **Constituency Pre-Audit** | 243,133 cases, 26 districts | ✅ In JSON | Part of `audit_reports.json` |
| **Lapse Definitions** | 12 official lapse categories | ✅ In docs | `Improper Redressal lapses.md` |

**Total Raw Data**: ~340,000+ records across multiple sources

---

## 🎯 DATA SOURCES - DETAILED BREAKDOWN

### 1. GUNTUR DISTRICT AUDIT (Primary Training Data for Lapse Model)

**Location**: `backend/ml/data/extracted/audit_reports.json`
**Records**: 2,298 audited cases

**13 Lapse Categories with Exact Percentages**:

| # | Lapse Category | Count | % | Type | Severity |
|---|----------------|-------|---|------|----------|
| 1 | GRA did not speak to citizen directly | 970 | 42.19% | Procedural | High |
| 2 | Not visited site / No field verification | 364 | 15.83% | Procedural | High |
| 3 | Wrong/Blank/Not related comments | 286 | 12.44% | Procedural | Critical |
| 4 | GRA did not speak properly/scolded | 201 | 8.75% | Behavioral | Critical |
| 5 | Wrong department assignment | 157 | 6.83% | Procedural | Medium |
| 6 | Improper enquiry photo/report | 143 | 6.22% | Procedural | High |
| 7 | GRA did not provide endorsement | 139 | 6.05% | Procedural | Medium |
| 8 | GRA did not explain to applicant | 139 | 6.05% | Procedural | Medium |
| 9 | Forwarded to lower official | 86 | 3.74% | Procedural | High |
| 10 | GRA intentionally avoided work | 81 | 3.52% | Behavioral | Critical |
| 11 | GRA threatened/pleaded applicant | 39 | 1.70% | Behavioral | Critical |
| 12 | GRA involved political persons | 15 | 0.65% | Behavioral | Critical |
| 13 | GRA took/asked for bribe | 10 | 0.44% | Behavioral | Critical |

**Department Breakdown** (20 departments with full metrics):
- Revenue (CCLA): 12.39% improper
- Police: 21.20% improper
- Survey & Land Records: 7.71% improper
- Municipal Administration: 15.56% improper
- Panchayati Raj: 17.26% improper
- APCRDA: **50.51% improper** (highest)
- Medical Education: 23.91% improper

**Mandal Breakdown** (9 mandals with full metrics):
- Pedakakani: 34.48% improper (highest)
- Medikonduru: 40.00% improper
- Ponnur: 30.83% improper

**Officer Performance** (Top 5 poor performers):
- Commissioner CRDA: 60.94% improper
- SDPO North Sub Division: 34.64% improper
- Tahsildar Mangalagiri: 32.56% improper

---

### 2. PGRS BOOK KEYWORDS (Primary Training Data for Telugu Classifier)

**Location**: `backend/ml/data/extracted/pgrs_book_keywords.json`

**Summary**:
- **30 Departments** with full hierarchy
- **106 Subjects** per department
- **138 Sub-subjects**
- **709 Keywords** (354 Telugu, 355 English)

**Top Departments by Keyword Count**:
1. Revenue (CCLA): 98 keywords - handles 67% of grievances
2. Municipal Administration: 34 keywords
3. Agriculture: 32 keywords
4. Transport, Roads & Buildings: 29 keywords
5. Animal Husbandry: 29 keywords

**Example Keywords by Department**:

**Revenue (రెవెన్యూ)**:
- English: land, patta, survey, record, title, mutation, certificate, income, caste, residence
- Telugu: భూమి, పట్టా, సర్వే, రికార్డు, మ్యూటేషన్, సర్టిఫికేట్, ఆదాయం, కులం, నివాసం

**Agriculture (వ్యవసాయం)**:
- English: crop, insurance, fertilizer, subsidy, loan, farmer, damage
- Telugu: పంట, బీమా, ఎరువులు, సబ్సిడీ, రుణం, రైతు, నష్టం

**Health (ఆరోగ్యం)**:
- English: hospital, doctor, treatment, medicine, emergency, ambulance
- Telugu: ఆసుపత్రి, డాక్టర్, చికిత్స, మందు, అత్యవసరం, అంబులెన్స్

---

### 3. CALL CENTER 1100 FEEDBACK (Risk Scoring Features)

**Location**: `docs/reference/markdown/STATE CALL CENTER 1100 FEEDBACK REPORT (1).md`

**Summary**: 93,892 feedback records across 31 departments

**Department-wise Satisfaction Scores** (31 departments):

| Department | Total | Satisfaction Score | Dissatisfaction % |
|------------|-------|-------------------|-------------------|
| Agriculture | 1357 | 2.58 | 10.83% |
| Civil Supplies | 983 | 2.48 | 8.75% |
| Revenue (CCLA) | 31627 | 2.04 | 11.36% |
| Police | 11989 | 1.57 | 14.98% |
| Social Welfare | 321 | 1.60 | 14.33% |
| Registration & Stamps | 651 | 1.51 | 19.20% |
| APSRTC | 454 | 1.34 | 20.26% |

**District-wise Satisfaction** (26 districts):
- Best: Kakinada (2.61), Konaseema (2.42)
- Worst: Ananthapur (1.49), Visakhapatnam (1.54), West Godavari (1.55)

**Source-wise Analysis** (18 sources):
- Revenue-Sadassulu: 2.46 satisfaction
- PGRS-PR: 2.22 satisfaction
- Call Center 1100: 2.16 satisfaction

---

### 4. LAPSE DEFINITIONS (Ground Truth Labels)

**Location**: `docs/reference/markdown/Improper Redressal lapses.md`

**12 Official Lapse Categories** (Government-defined):

**Behavioral Lapses (5)**:
1. GRA did not speak properly / scolded / used abusive language
2. GRA threatened / pleaded / persuaded the applicant
3. GRA took a bribe / asked for a bribe / stopped work for not paying
4. GRA did not work and involved political persons
5. GRA intentionally avoided doing work

**Procedural Lapses (7)**:
6. GRA did not speak directly with the citizen
7. GRA did not provide the endorsement personally
8. GRA did not spend time explaining the issue
9. GRA gave WRONG/BLANK/NOT RELATED endorsement
10. GRA uploaded improper enquiry photo/report
11. GRA closed by forwarding to lower-level official
12. GRA closed stating not under jurisdiction

---

### 5. MESSAGE TEMPLATES (Telugu Text Training)

**Location**: `backend/ml/data/extracted/message_templates.json`

**Summary**: 54 official SMS/WhatsApp templates (44 unique after dedup)

**Template Categories**:
- Grievance Registration confirmations
- Grievance Resolved notifications
- GRA Communication messages
- Feedback request messages
- Court case notifications

**Sample Telugu Text**:
- "మీ ఫిర్యాదు నమోదు చేయబడింది" (Your complaint has been registered)
- "మీ సమస్య పరిష్కరించబడింది" (Your issue has been resolved)

---

### 6. AUDIO TRANSCRIPTIONS (Telugu Voice Training)

**Location**: `backend/ml/data/extracted/audio_transcriptions.json`

**Summary**: 46 Telugu voice message samples

**Categories**:
- Grievance registration (3)
- Grievance resolved (3)
- Court case (1)
- GRA communication (3)
- Officer communication (2)
- Feedback (2)
- General scenarios (14+)

---

### 7. CONSTITUENCY PRE-AUDIT (Additional Training Data)

**Location**: Part of `backend/ml/data/extracted/audit_reports.json`

**Summary**: 243,133 cases audited across 26 districts

**District Highlights**:
- Ananthapur: 13,122 audited, 57.67% improper
- Visakhapatnam: 12,267 audited, 28.32% improper
- NTR: 10,635 audited, 35.98% improper
- YSR Kadapa: 10,444 audited, 40.59% improper

**Edge Cases Identified** (67 total):
- Extreme high improper: YSR Kadapa Proddatur (58.56%)
- Extreme low improper: Vizianagaram Nellimarla (5.31%)
- Behavioral hotspot: Ananthapur (10.91% behavioral)

---

### 8. OFFICER PERFORMANCE DATA

**Location**: `backend/ml/data/extracted/officer_performance.json`

**Summary**: 490 officers across 34 departments

**Use for ML**: Feature engineering for lapse prediction based on officer history

---

## 📁 FILE LOCATIONS SUMMARY

### Already Extracted (backend/ml/data/extracted/):
```
audit_reports.json          - 2,298+ cases with 13 lapse categories
pgrs_book_keywords.json     - 30 depts, 709 keywords (Telugu+English)
officer_performance.json    - 490 officers, 34 departments
message_templates.json      - 54 official templates
call_center_satisfaction.json - Department satisfaction metrics
audio_transcriptions.json   - 46 Telugu voice samples
```

### In Docs (need parsing):
```
docs/reference/markdown/
├── STATE CALL CENTER 1100 FEEDBACK REPORT (1).md  - 93,892 records
├── Improper Redressal lapses.md                   - 12 lapse definitions
├── Guntur District PGRS review meeting notes.md   - Full audit report
├── CONSTITUENCY PRE AUDIT REPORT.md               - 243,133 cases
├── Ananthapur district department audit.md        - Department breakdown
└── West Godavari Top 10 officers.md               - Officer performance
```

### Synthetic Data Generated:
```
backend/ml/data/synthetic/
├── synthetic_lapse_cases.json      - 1,000 synthetic cases
├── synthetic_telugu_grievances.json - 585 Telugu samples
```

### Research Data:
```
backend/ml/
├── TELUGU_GRIEVANCE_DATASET_RESEARCH.json   - 85 real Telugu samples
├── AP_GRIEVANCE_LAPSE_RESEARCH_FINDINGS.json - 8 documented cases
├── additional_lapse_cases_research.json      - 58 more cases
├── additional_telugu_samples_research.json   - 127 Telugu samples
```

---

## 🎯 ML TRAINING DATA SUMMARY

### For Lapse Prediction Model:

| Source | Records | Usable For Training |
|--------|---------|---------------------|
| Guntur Audit | 2,298 | ✅ Primary - labeled with 13 lapse types |
| Constituency Pre-Audit | 243,133 | ✅ Additional - needs parsing |
| Officer Performance | 490 | ✅ Feature engineering |
| Synthetic Data | 1,000 | ✅ Augmentation |
| Research Data | 66 | ✅ Additional labeled cases |

**Total Potential Training Samples**: ~246,000+

### For Telugu Department Classifier:

| Source | Records | Usable For Training |
|--------|---------|---------------------|
| PGRS Keywords | 709 keywords (354 Telugu) | ✅ Primary |
| Message Templates | 54 (44 unique) | ✅ Telugu text |
| Audio Transcriptions | 46 | ✅ Telugu voice text |
| Research Telugu Samples | 212 (85+127) | ✅ Labeled samples |
| Synthetic Telugu | 500 | ✅ Augmentation |

**Total Potential Training Samples**: ~1,500+ Telugu text samples

---

## ⚠️ CRITICAL INSIGHT

**We have NOT been using the massive government data that's already available!**

The `audit_reports.json` alone contains:
- 2,298 labeled cases with exact lapse categories
- 20 department breakdowns with improper percentages
- 9 mandal breakdowns
- 5 officer performance records
- Behavioral vs Procedural split

The `pgrs_book_keywords.json` contains:
- 709 bilingual keywords
- Perfect for Telugu → Department classification
- Already mapped to 30 departments and 106 subjects

**NEXT STEP**: Use this existing data to train models IMMEDIATELY.

---

## 📋 IMMEDIATE ACTION ITEMS

1. **Parse Call Center 1100 Data** - Extract 93,892 records from markdown
2. **Load Guntur Audit Data** - Already in JSON, ready to use
3. **Train Lapse Model** - Use 2,298 labeled cases + features
4. **Train Telugu Classifier** - Use 709 keywords + 212 research samples
5. **Validate with Synthetic** - Use 1,500 synthetic samples for testing

---

## 🔗 CROSS-REFERENCES

- Handoff Document: `backend/ml/ML_TRAINING_HANDOFF_DOCUMENT.md`
- Prevention Guide: `backend/ml/DATA_IMPORT_PREVENTION_GUIDE.md`
- Master Index: `docs/MASTER_INDEX.md`

---

**Document Status**: COMPLETE
**Next Action**: Train models using existing government data
