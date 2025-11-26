# DHRUVA Knowledge Base Quick Reference

**Created:** 2025-11-25
**Version:** 1.0
**Location:** `D:\projects\dhruva\backend\ml\data\knowledge_base\`

> **TL;DR:** This folder contains ALL the data you need for DHRUVA grievance processing. Start with `_INDEX.json` for navigation, then dive into `tier1_core/` for daily use, `tier2_training/` for ML models, `tier3_reference/` for supporting data, and `tier4_audit/` for analytics.

---

## What Data Do We Have?

### For Department Classification
- **709 bilingual keywords** (354 Telugu + 355 English) → `tier1_core/departments.json`
- **30 departments** with Telugu names and codes → same file
- **106 subdepartments** → same file
- **14,876 training samples** → `tier2_training/classification/muril_classification_training.json`
- **Source:** PGRS BOOK + MuRIL training data

### For Sentiment/Distress Detection
- **4 distress levels**: CRITICAL, HIGH, MEDIUM, NORMAL
- **SLA timelines**: 24h, 72h, 168h (7d), 336h (14d)
- **Distress keywords** in Telugu and English → `tier1_core/grievance_types.json`
- **14,876 labeled samples** (balanced, ~3,700 per class) → `tier2_training/sentiment/muril_sentiment_training.json`
- **10 common grievance types** with frequency data → `tier1_core/grievance_types.json`

### For Lapse Prediction (Audit Quality)
- **13 lapse categories**: 5 behavioral + 8 procedural
- **Lapse definitions** with Telugu names, severity, detection keywords → `tier1_core/lapse_definitions.json`
- **2,298 labeled Guntur audit cases** → `tier2_training/lapse_prediction/guntur_audit_training.json`
- **Top lapse**: "GRA did not speak to citizen" (42.19%)
- **Source:** Guntur District PGRS Audit (Nov 2025)

### For Response Template Selection
- **54 official Telugu templates** → `tier1_core/response_templates.json` (summary)
- **Full templates with samples** → `backend/ml/data/extracted_docs/official_telugu_templates.json`
- **7 template categories**: Status Updates, Court Cases, Land Allocation, Schemes, Capital Works, Policy, Process
- **All templates** include standard footer with Call Center (1100) and WhatsApp (9552300009)

### For Geographic/District Analysis
- **26 AP districts** with codes and mandals → `tier3_reference/district_data.json`
- **243,133 constituency pre-audit cases** → `tier4_audit/constituency_preaudit.json`
- **Improper redressal rates**: 5.31% (best) to 85.60% (worst)
- **Source:** CONSTITUENCY PRE AUDIT REPORT (April-October 2025)

### For Department Performance
- **93,892 call center feedback records** → `tier4_audit/call_center_feedback.json`
- **31 departments** covered
- **Satisfaction scores**: 0-5 scale (avg: 1.95, overall satisfied: 87.23%)
- **Top 3 by volume**: Revenue (31,627), Survey (20,836), Employment (11,989)
- **Source:** STATE CALL CENTER 1100 FEEDBACK REPORT

### For Officer Hierarchy
- **106+ HODs** across 30 departments → `tier3_reference/officer_hierarchy.json`
- **Reporting chains** for grievance assignment
- **Designations** and responsibilities
- **Source:** List of Depts with HOD.md

### For Service Catalog
- **200+ government services** → `tier3_reference/service_catalog.json`
- **96 Revenue services** alone (highest volume)
- **Department-wise service lists**
- **Source:** PGRS BOOK + Service Registration reference.md

---

## Quick Start Guides

### I Want to Classify a Grievance by Department

```json
// 1. Load departments and keywords
File: tier1_core/departments.json
Fields: keywords_english, keywords_telugu, name_english

// 2. Match keywords from grievance text
Example: "పట్టా దిద్దుబాటు" → Telugu keyword match → Revenue department

// 3. For ML approach, use training data
File: tier2_training/classification/muril_classification_training.json
Model: MuRIL or Telugu-BERT
Classes: 15 departments (15th is "Revenue" - highest volume)
```

### I Want to Detect Distress Level

```json
// 1. Load distress definitions
File: tier1_core/grievance_types.json → distress_levels array
Levels: CRITICAL (4), HIGH (3), MEDIUM (2), NORMAL (1)

// 2. Match keywords
CRITICAL: "death", "suicide", "violence", "bribe", "మరణం", "ఆత్మహత్య", "లంచం"
HIGH: "corruption", "harassment", "urgent", "అవినీతి", "వేధింపు"
MEDIUM: "delay", "quality", "problem", "ఆలస్యం", "సమస్య"
NORMAL: "information", "status", "query", "సమాచారం", "స్థితి"

// 3. For ML approach
File: tier2_training/sentiment/muril_sentiment_training.json
Model: MuRIL for Telugu sentiment
Classes: 4 (CRITICAL, HIGH, MEDIUM, NORMAL)
Distribution: Balanced (~3,700 per class)
```

### I Want to Predict Audit Lapses

```json
// 1. Load lapse definitions
File: tier1_core/lapse_definitions.json → lapses array (13 types)

// 2. Top 3 lapses to check first
ID 1: "GRA did not speak to citizen" (42.19%)
ID 2: "Not visited site" (15.83%)
ID 3: "Wrong/blank closure comments" (12.44%)

// 3. Use detection keywords
File: lapse_definitions.json → detection_keywords field
Example ID 1: "did not call", "no contact", "మాట్లాడలేదు", "కాల్ చేయలేదు"

// 4. For ML approach
File: tier2_training/lapse_prediction/guntur_audit_training.json
Type: Multi-label classification (case can have multiple lapses)
Classes: 13 lapse types
Note: Highly imbalanced (top lapse is 42%, bottom is 0.44%)
```

### I Want to Select Response Template

```json
// 1. Determine grievance status
Statuses: Registered, Viewed, Redressed, Forwarded, Court Case, etc.

// 2. Load template summary
File: tier1_core/response_templates.json → template_categories array

// 3. Map status to template
Example: status="Registered" → Template with acknowledgment
Example: status="Redressed" → Template with completion message
Example: status="Court Case" + subcase="Civil" → Specific court template

// 4. Get full template
File: backend/ml/data/extracted_docs/official_telugu_templates.json
Find: Match status + subcase
Replace: [VARIABLE] placeholders with actual values
```

### I Want to Calculate SLA

```json
// 1. Get distress level (see "Detect Distress Level" above)

// 2. Look up SLA hours
File: tier1_core/grievance_types.json → distress_levels → sla_hours
CRITICAL: 24 hours
HIGH: 72 hours
MEDIUM: 168 hours (7 days)
NORMAL: 336 hours (14 days)

// 3. For department-specific SLAs
File: tier3_reference/sla_rules.json (detailed rules)
```

---

## File Navigation Tree

```
knowledge_base/
│
├── _INDEX.json                    ← START HERE (master navigator)
├── _SCHEMA.md                      ← All JSON schemas documented
├── _QUICK_REFERENCE.md             ← This file (you are here)
│
├── tier1_core/                     ← Daily Use (4 files)
│   ├── departments.json            → 30 depts, 709 keywords, 106 subdepts
│   ├── grievance_types.json        → 4 distress levels, 10 common types
│   ├── lapse_definitions.json      → 13 lapse categories for audit
│   └── response_templates.json     → 54 Telugu templates (summary)
│
├── tier2_training/                 ← ML Training Data (4 datasets)
│   ├── classification/
│   │   └── muril_classification_training.json → 14,876 samples, 15 classes
│   ├── sentiment/
│   │   └── muril_sentiment_training.json      → 14,876 samples, 4 classes (balanced)
│   ├── lapse_prediction/
│   │   └── guntur_audit_training.json         → 2,298 cases, 13 labels (multi-label)
│   └── template_selection/
│       └── response_template_training.json    → 54 templates with context
│
├── tier3_reference/                ← Supporting Data (4 files)
│   ├── officer_hierarchy.json      → 106+ HODs, reporting chains
│   ├── district_data.json          → 26 districts, mandals, codes
│   ├── service_catalog.json        → 200+ services, department-wise
│   └── sla_rules.json              → SLA timelines, escalation rules
│
└── tier4_audit/                    ← Analytics & Audit (3 files)
    ├── guntur_audit.json           → 2,298 cases, 22.8% improper
    ├── constituency_preaudit.json  → 243,133 cases, 26 districts
    └── call_center_feedback.json   → 93,892 records, satisfaction scores
```

---

## Data Quality & Coverage

### Coverage by Department (Top 5)

| Department | Volume % | Keywords | Training Samples | Audit Cases |
|------------|----------|----------|------------------|-------------|
| Revenue | 35.0% | 98 | 219 | 2,833 redressed |
| Municipal Admin | 7.8% | 34 | 117 | 2,629 redressed |
| Police | 8.5% | 23 | 85 | 4,477 redressed |
| Panchayat Raj | 6.5% | 21 | 85 | 1,060 redressed |
| Survey & Land Records | 2nd highest | 20+ | included in Revenue | 1,168 redressed |

### Training Data Quality

**Classification (Department):**
- Samples: 14,876
- Classes: 15 departments
- Distribution: Imbalanced (Revenue has 219 samples, some depts have 32-52)
- Language: Telugu
- Format: {text, department, department_code}

**Sentiment (Distress Level):**
- Samples: 14,876
- Classes: 4 (CRITICAL, HIGH, MEDIUM, NORMAL)
- Distribution: **BALANCED** (~3,700 per class)
- Language: Telugu
- Format: {text, sentiment, distress_level}

**Lapse Prediction (Audit):**
- Samples: 2,298 (Guntur district only)
- Classes: 13 lapse types
- Distribution: **HIGHLY IMBALANCED** (42.19% vs 0.44%)
- Type: **Multi-label** (cases can have multiple lapses)
- Format: {grievance_text, officer_endorsement, lapse_categories[], department}

### Data Freshness

| Dataset | Date | Coverage | Notes |
|---------|------|----------|-------|
| Guntur Audit | Nov 2025 | 2,298 cases | Single district snapshot |
| Pre-Audit Report | Apr-Oct 2025 | 243,133 cases | State-wide, 6 months |
| Call Center Feedback | Up to Nov 2025 | 93,892 records | Cumulative |
| PGRS Keywords | 2025 | 709 keywords | From official PGRS book |
| Telugu Templates | 2025 | 54 templates | Official government messages |

---

## Common Use Cases

### Use Case 1: Auto-Route New Grievance

**Steps:**
1. Extract text from grievance (Telugu or English)
2. Load `tier1_core/departments.json`
3. Match keywords from `keywords_telugu` or `keywords_english`
4. Get department with highest keyword match score
5. Assign to HOD from `tier3_reference/officer_hierarchy.json`

**Fallback:** If no keyword match, use ML model from `tier2_training/classification/`

### Use Case 2: Priority Assignment

**Steps:**
1. Extract text from grievance
2. Load `tier1_core/grievance_types.json → distress_levels`
3. Check for CRITICAL keywords first ("death", "suicide", "bribe", "మరణం", "లంచం")
4. Then HIGH ("corruption", "harassment", "అవినీతి")
5. Then MEDIUM ("delay", "quality", "ఆలస్యం")
6. Default to NORMAL if no matches
7. Get SLA from `sla_hours` field

**ML Approach:** Use `tier2_training/sentiment/muril_sentiment_training.json` to train classifier

### Use Case 3: Audit Quality Prediction

**Steps:**
1. Extract grievance text + officer endorsement
2. Load `tier1_core/lapse_definitions.json`
3. Check detection_keywords for each lapse type
4. Flag probable lapses
5. Generate audit checklist

**ML Approach:** Train multi-label classifier on `tier2_training/lapse_prediction/guntur_audit_training.json`

### Use Case 4: Automated Response

**Steps:**
1. Determine grievance status (Registered, Viewed, Redressed, etc.)
2. Check if special case (Court, Policy, Capital Works, etc.)
3. Load `tier1_core/response_templates.json`
4. Match status + subcase to template
5. Replace [VARIABLE] placeholders (grievance_number, officer_name, etc.)
6. Send Telugu message to citizen via SMS/WhatsApp

**Note:** All templates include standard footer with Call Center 1100 and WhatsApp 9552300009

### Use Case 5: Department Performance Dashboard

**Steps:**
1. Load `tier4_audit/call_center_feedback.json`
2. Group by department
3. Calculate avg_satisfaction_5 (0-5 scale)
4. Calculate pct_satisfied (percentage)
5. Compare against improper_percentage from `tier4_audit/guntur_audit.json`
6. Identify departments needing intervention

**Key Metrics:**
- Top Satisfaction: Agriculture (2.58/5, 89.17%)
- Bottom Satisfaction: Endowment (1.09/5, 80.18%)
- Highest Volume: Revenue (31,627 records)

---

## FAQ

### Q: What's the difference between tier1, tier2, tier3, tier4?

**Tier 1 (Core):** Essential reference data used in EVERY grievance. Small files, loaded frequently.
**Tier 2 (Training):** Large datasets for training ML models. Load once during training, not in production.
**Tier 3 (Reference):** Supporting data loaded as needed (officers, districts, services, SLAs).
**Tier 4 (Audit):** Historical audit and analytics data. For dashboards and insights, not real-time processing.

### Q: Which file should I load first?

Start with `_INDEX.json` to understand what's available. Then load `tier1_core/departments.json` and `tier1_core/grievance_types.json` - these are your bread and butter.

### Q: How do I handle Telugu text in JSON?

All JSON files are UTF-8 encoded. In Python: `json.load(f, encoding='utf-8')`. In JavaScript/TypeScript: `fs.readFileSync(..., 'utf-8')`. Telugu Unicode range: U+0C00 to U+0C7F.

### Q: Can I use the training data for testing?

**No!** Split the training data into train/val/test sets. Or better yet, use the pre-audit data from `tier4_audit/constituency_preaudit.json` as a held-out test set (different districts).

### Q: The lapse prediction data is imbalanced. What do I do?

Use weighted loss functions, focal loss, or SMOTE for oversampling. Or focus on the top 5-7 lapses (covering 85%+ of cases) and group the rest as "Other".

### Q: Where's the original source data?

Check `_source` fields in each JSON file. Most source docs are in `D:\projects\dhruva\docs\`. For example:
- `docs/reference/markdown/MESSAGES_SENT_TO_PETITIONERS.json`
- `docs/data_sets/markdown/PGRS BOOK.md`
- `backend/ml/data/extracted/*.json`

### Q: How often is this data updated?

Departments/Keywords: Quarterly
Templates: As needed (when government updates)
Audit Data: Monthly (after district audits)
Training Data: One-time creation, retrain models quarterly

---

## Schema Quick Reference

### DepartmentSchema
```json
{
  "id": 1,
  "name_english": "Revenue (CCLA)",
  "name_telugu": "రెవెన్యూ",
  "code": "REV",
  "priority_rank": 1,
  "typical_volume_pct": 35.0,
  "keywords_english": ["land", "patta", "survey", ...],
  "keywords_telugu": ["భూమి", "పట్టా", "సర్వే", ...],
  "subdepartments": ["Revenue (CCLA)", "Survey Settlements", ...]
}
```

### GrievanceTypeSchema (Distress Level)
```json
{
  "level": "CRITICAL",
  "value": 4,
  "description": "Life-threatening or severe distress",
  "telugu": "క్రిటికల్",
  "keywords_english": ["death", "suicide", "violence", ...],
  "keywords_telugu": ["మరణం", "ఆత్మహత్య", "హింస", ...],
  "sla_hours": 24
}
```

### LapseDefinitionSchema
```json
{
  "id": 1,
  "name": "GRA did not speak directly with the citizen",
  "telugu": "GRA స్వయంగా స్టిజన్తో మాట్లాడలేదు",
  "type": "procedural",
  "severity": "high",
  "frequency_pct": 42.19,
  "detection_keywords": ["did not call", "మాట్లాడలేదు", ...]
}
```

### ResponseTemplateSchema
```json
{
  "status": "Registered",
  "telugu": "ప్రియమైన అర్జీదారు, మీ అర్జీ [VARIABLE](NO#) స్వీకరించబడినది...",
  "english": "Dear Petitioner, your grievance [VARIABLE](NO#) has been received...",
  "variables": ["grievance_number", "officer_name"],
  "use_case": "Initial acknowledgment"
}
```

---

## Contact & Support

**Data Owner:** DHRUVA Backend ML Team
**Last Updated:** 2025-11-25
**Location:** `D:\projects\dhruva\backend\ml\data\knowledge_base\`
**Documentation:** See `_INDEX.json` for detailed file descriptions
**Issues:** Check `_SCHEMA.md` for schema definitions

---

**Remember:** This knowledge base is your single source of truth. When in doubt, check `_INDEX.json` first!
