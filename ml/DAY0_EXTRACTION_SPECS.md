# DAY 0: DATA EXTRACTION SPECIFICATIONS
## World-Class Quality Standards

**Date**: 2025-11-24
**Status**: Ready for parallel agent execution
**Quality Target**: Highest in the world

---

## 📋 SOURCE FILES (ALL VERIFIED ✅)

###  AGENT 1: Audio Transcription
**Source Files**:
- `docs/voice_clips/VOICE CLIPS REGARDING PGRS SENT TO PETITIONERS-OFFICERS/*.wav` (28 files)
- `docs/reference/voice_clips/*.wav` (16 files)
- `docs/bribe_cases/BRIBE CASES/*.mp3` (2 files)

**Total**: 46 audio files

### AGENT 2: PGRS BOOK Keywords
**Source File**: `docs/data_sets/markdown/PGRS BOOK.md` (181 lines)

### AGENT 3: Officer Performance Report
**Source File**: `docs/reference/markdown/PGRS DEPARTMENT-HOD WISE GRIEVANCE CUMULATIVE STATUS OFFICER WISE  REPORT AS ON DT 21-11-2025.md` (8,558 lines)

### AGENT 4: Call Center Satisfaction
**Source File**: `docs/reference/markdown/STATE CALL CENTER 1100 FEEDBACK REPORT (1).md` (93,892 records)

### AGENT 5: Telugu Message Templates
**Source File**: `docs/reference/markdown/MESSAGES_SENT_TO_PETITIONERS.json` (58 templates)

### AGENT 6: Guntur Audit + District Audits
**Source Files**:
- `docs/reference/markdown/Guntur District  PGRS review meeting notes 07.11.2025 (1).md` (1,007 lines, 2,298 cases)
- `docs/reference/markdown/Improper Redressal lapses.md` (46 lines)
- `docs/reference/markdown/CONSTITUENCY PRE AUDIT REPORT 11-11-2025 (1).md` (986 lines)
- `docs/reference/markdown/Ananthapur district department audit performance.md`
- `docs/reference/markdown/West Godavari Top 10 officers_Pre_Audit_Report_Poor_Performance.md`

---

## 🎯 AGENT 1: AUDIO TRANSCRIPTION

### **Task**: Transcribe 46 audio files to Telugu text using Whisper AI

### **Output Format**:
```json
{
  "transcriptions": [
    {
      "filename": "when grievance registered.wav",
      "source_path": "docs/voice_clips/...",
      "duration_seconds": 23.81,
      "transcription_telugu": "...",
      "transcription_english": "... (if bilingual)",
      "confidence": 0.95,
      "language_detected": "te",
      "contains_department_name": true,
      "extracted_keywords": ["register", "grievance", "petitioner"]
    }
  ],
  "total_transcribed": 46,
  "total_duration_seconds": 1068.24,
  "quality_metrics": {
    "avg_confidence": 0.92,
    "telugu_files": 46,
    "failed_transcriptions": 0
  }
}
```

### **Quality Gates**:
- ✅ ALL 46 files transcribed (no failures)
- ✅ Average confidence ≥0.80
- ✅ Telugu language detected for all files
- ✅ Transcription length ≥10 characters per file
- ✅ No encoding errors

### **Validation Rules**:
1. Check file exists before transcription
2. Verify audio format (WAV/MP3)
3. Handle Telugu Unicode properly (UTF-8)
4. Extract any department names mentioned
5. Flag files with low confidence (<0.70)

### **Output Location**: `backend/ml/data/extracted/audio_transcriptions.json`

---

## 🎯 AGENT 2: PGRS BOOK KEYWORDS

### **Task**: Extract 200+ keywords from 30 departments with Telugu + English variations

### **Output Format**:
```json
{
  "departments": [
    {
      "sno": 1,
      "name_english": "Revenue (CCLA)",
      "name_telugu": "రెవెన్యూ",
      "subjects": [
        {
          "subject_english": "Land Records",
          "subject_telugu": "భూమి రికార్డులు",
          "keywords_english": ["land", "patta", "survey", "record", "title"],
          "keywords_telugu": ["భూమి", "పట్టా", "సర్వే", "రికార్డు"],
          "sub_subjects": ["Survey Numbers", "Land Disputes", "Patta Transfer"]
        }
      ],
      "total_keywords": 25
    }
  ],
  "summary": {
    "total_departments": 30,
    "total_subjects": 100,
    "total_sub_subjects": 100,
    "total_keywords": 200,
    "telugu_keywords": 100,
    "english_keywords": 100
  }
}
```

### **Quality Gates**:
- ✅ Exactly 30 departments extracted
- ✅ ≥100 subjects mapped to departments
- ✅ ≥100 sub-subjects identified
- ✅ ≥200 total keywords (Telugu + English)
- ✅ Each department has ≥5 keywords
- ✅ No duplicate keywords within same department
- ✅ Telugu Unicode properly encoded

### **Validation Rules**:
1. Match department names to MEEKOSAM 26-dept standard
2. Extract both page 1 dept list AND detailed subjects
3. Include Telugu variations for each keyword
4. Remove duplicates (case-insensitive)
5. Validate Telugu characters (no mojibake)

### **Output Location**: `backend/ml/data/extracted/pgrs_book_keywords.json`

---

## 🎯 AGENT 3: OFFICER PERFORMANCE REPORT

### **Task**: Parse 8,558 officer records and extract performance metrics + department mappings

### **Output Format**:
```json
{
  "officers": [
    {
      "sno": 1,
      "department": "Revenue",
      "officer_designation": "Manager Of Dsh",
      "received": 3103,
      "viewed": 123,
      "pending": 342,
      "redressed": 2651,
      "computed_metrics": {
        "improper_rate": 0.12,
        "workload": 342,
        "viewed_ratio": 0.04,
        "throughput": 0.85
      },
      "dept_context_extracted": "Manager Of Dsh → DSH → Social Welfare"
    }
  ],
  "summary": {
    "total_officers": 8558,
    "unique_departments": 30,
    "unique_designations": 1000,
    "dept_contexts_extracted": 1000,
    "avg_improper_rate": 0.12,
    "avg_workload": 156
  }
}
```

### **Quality Gates**:
- ✅ ≥8,000 officers parsed (target: 8,558)
- ✅ All numeric fields valid (no NaN)
- ✅ Improper rate between 0-1
- ✅ ≥1,000 unique officer designations extracted
- ✅ ≥1,000 department context pairs
- ✅ No parsing errors

### **Validation Rules**:
1. Parse table rows (skip headers)
2. Handle merged cells gracefully
3. Compute metrics: improper_rate = (received - redressed - pending) / received
4. Clip improper_rate to [0, 1] range
5. Extract designation → department mapping
6. Handle missing values (use null, not 0)

### **Output Location**: `backend/ml/data/extracted/officer_performance.json`

---

## 🎯 AGENT 4: CALL CENTER SATISFACTION

### **Task**: Extract 93,892 satisfaction records with department-level statistics

### **Output Format**:
```json
{
  "departments": [
    {
      "sno": 1,
      "department": "Revenue (CCLA)",
      "total_feedback": 31627,
      "avg_satisfaction_5": 2.04,
      "pct_satisfied": 88.64,
      "computed_metrics": {
        "dept_risk_score": 0.74,
        "rank": 1,
        "relative_weight": 0.337
      }
    }
  ],
  "summary": {
    "total_records": 93892,
    "total_departments": 27,
    "avg_satisfaction": 1.95,
    "overall_satisfied_pct": 87.23
  }
}
```

### **Quality Gates**:
- ✅ ≥27 departments extracted
- ✅ Total feedback sum ≈93,892
- ✅ Satisfaction scores between 1-5
- ✅ Percentages between 0-100
- ✅ Risk scores between 0-1
- ✅ No missing departments

### **Validation Rules**:
1. Parse markdown table
2. Compute risk_score = (5 - avg_satisfaction) / 4
3. Normalize department names (match PGRS BOOK)
4. Validate totals sum to 93,892
5. Calculate relative weights for class balancing

### **Output Location**: `backend/ml/data/extracted/call_center_satisfaction.json`

---

## 🎯 AGENT 5: TELUGU MESSAGE TEMPLATES

### **Task**: Extract 58 official Telugu message templates

### **Output Format**:
```json
{
  "templates": [
    {
      "template_id": 1,
      "category": "Grievance Registration",
      "text_telugu": "మీ ఫిర్యాదు నమోదు చేయబడింది...",
      "text_english": "Your grievance has been registered...",
      "contains_department": true,
      "extracted_departments": ["Revenue", "Survey"],
      "extracted_keywords": ["register", "grievance", "number"],
      "officer_designations": ["GRA", "Mandal Officer"],
      "character_count": 250
    }
  ],
  "summary": {
    "total_templates": 58,
    "telugu_templates": 58,
    "avg_length": 180,
    "unique_departments_mentioned": 15,
    "unique_officer_designations": 20
  }
}
```

### **Quality Gates**:
- ✅ Exactly 58 templates extracted
- ✅ All templates have Telugu text
- ✅ No mojibake (proper UTF-8)
- ✅ ≥10 departments mentioned across templates
- ✅ ≥15 officer designations extracted
- ✅ Average length ≥100 characters

### **Validation Rules**:
1. Parse JSON file (handle nested structure)
2. Extract Telugu text (check for "text" or "message" fields)
3. Detect department names (match against PGRS BOOK)
4. Extract officer titles (GRA, Collector, etc.)
5. Remove HTML tags if present
6. Validate Telugu encoding

### **Output Location**: `backend/ml/data/extracted/message_templates.json`

---

## 🎯 AGENT 6: AUDIT REPORTS (GUNTUR + DISTRICTS)

### **Task**: Extract lapse patterns and audit findings from 5 district reports

### **Output Format**:
```json
{
  "guntur_audit": {
    "source_file": "Guntur District  PGRS review meeting notes 07.11.2025 (1).md",
    "total_cases_audited": 2298,
    "lapse_categories": [
      {
        "category": "GRA didn't speak to citizen",
        "count": 970,
        "percentage": 42.19,
        "examples": ["Case ID 123: Revenue dept, officer didn't call citizen"]
      },
      {
        "category": "Not visited site",
        "count": 364,
        "percentage": 15.83
      }
    ],
    "department_breakdown": {
      "Revenue": 850,
      "Survey": 420,
      "Police": 300
    }
  },
  "other_audits": [
    {
      "name": "Constituency Pre-Audit",
      "file": "CONSTITUENCY PRE AUDIT REPORT 11-11-2025 (1).md",
      "findings": ["..."],
      "edge_cases": 50
    }
  ],
  "summary": {
    "total_audits": 5,
    "total_cases": 2500,
    "unique_lapse_types": 12,
    "edge_cases_extracted": 50
  }
}
```

### **Quality Gates**:
- ✅ ≥2,000 Guntur cases identified
- ✅ ≥10 lapse categories extracted
- ✅ ≥5 district audits processed
- ✅ ≥50 edge case examples
- ✅ Department breakdown available
- ✅ Percentages sum to ≈100%

### **Validation Rules**:
1. Parse Guntur meeting notes table
2. Extract lapse category breakdown
3. Count cases per department
4. Extract specific failure examples
5. Process other 4 audit files
6. Deduplicate examples

### **Output Location**: `backend/ml/data/extracted/audit_reports.json`

---

## ✅ CONSOLIDATED VALIDATION (After All Agents Complete)

### **Cross-Validation Checks**:
1. Department names consistent across all 6 outputs
2. Total keywords ≥200 (PGRS BOOK)
3. Total audio transcriptions = 46
4. Officer count = 8,558
5. Call center records ≈93,892
6. Templates = 58
7. Guntur cases ≥2,000

### **Quality Scorecard**:
```
PASS Criteria (ALL must be true):
- [ ] All 6 agents completed successfully
- [ ] All JSON files valid (parseable)
- [ ] All UTF-8 encoding correct (no mojibake)
- [ ] All counts match expectations (±5%)
- [ ] No null/NaN values in required fields
- [ ] All quality gates passed
```

### **Final Output**:
`backend/ml/data/extracted/DAY0_CONSOLIDATED_DATASET.json` containing all 6 outputs + validation report

---

**Execution Strategy**: Launch all 6 agents in parallel using a single message with 6 Task tool calls
**Expected Duration**: 2-3 hours wall-clock time
**Fallback**: If any agent fails, re-run individually with debugging
