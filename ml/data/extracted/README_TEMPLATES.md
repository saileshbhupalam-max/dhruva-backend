# Telugu Message Templates - Extracted Data

## Overview

This directory contains **54 official Telugu message templates** extracted from the PGRS (Praja Samasya Parikaara Vedika) system documentation.

## Files

### Main Output
- **`message_templates.json`** (155 KB)
  - 54 Telugu message templates with full metadata
  - Department and officer mappings
  - Keyword categorization
  - Variable information

### Scripts
- **`extract_templates.py`** (20 KB)
  - Extraction script with quality gates
  - Department and officer detection logic
  - Telugu encoding validation

- **`validate_templates.py`** (3.3 KB)
  - Validation script for data integrity
  - 8 validation checks
  - Quick statistics report

### Documentation
- **`AGENT_5_COMPLETION_REPORT.md`** (9.7 KB)
  - Full extraction methodology
  - Quality gate results
  - Usage instructions
  - Integration guidelines

- **`README_TEMPLATES.md`** (this file)
  - Quick reference guide

## Quick Stats

- **Total Templates:** 54
- **Telugu Templates:** 54 (100%)
- **Average Length:** 451 characters
- **Categories:** 5 (Registration, Viewed, Forwarding, Closure, Feedback)
- **Departments:** 6 (Agriculture, Education, Forest, Health, MAUD, PRRD)
- **Officers:** 5 (Collector, Executive Engineer, MRO, Mandal Officer, Officer)
- **Encoding:** UTF-8 ✅
- **Quality:** All validation checks passed ✅

## Data Structure

```json
{
  "templates": [
    {
      "template_id": 1,
      "category": "Registration",
      "grievance_status": "Registered",
      "subcase": null,
      "text_telugu": "ప్రజా సమస్యల పరిష్కార వేదిక...",
      "text_english": null,
      "sample_message": "ప్రజా సమస్యల పరిష్కార వేదిక\n...",
      "contains_department": false,
      "extracted_departments": [],
      "extracted_keywords": ["registration", "feedback"],
      "officer_designations": ["Mandal Officer"],
      "character_count": 423,
      "variable_count": 2,
      "variables": {
        "var_1": "GRIEVANCE NUMBER",
        "var_2": "OFFICER",
        "var_3": null
      }
    }
  ],
  "summary": {
    "total_templates": 54,
    "telugu_templates": 54,
    "avg_length": 451.39,
    "unique_departments_mentioned": 6,
    "unique_officer_designations": 5,
    "departments": [...],
    "officer_designations": [...],
    "encoding_issues": []
  }
}
```

## Usage

### Python
```python
import json

# Load templates
with open('message_templates.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

templates = data['templates']
summary = data['summary']

# Get a specific template
registration_template = templates[0]
print(registration_template['text_telugu'])

# Filter by category
closure_templates = [t for t in templates if t['category'] == 'Closure']

# Fill variables
message = registration_template['text_telugu']
message = message.replace('{#var#}', 'GNT190620250001', 1)  # Grievance number
message = message.replace('{#var#}', 'MPDO', 1)  # Officer name
```

### Validation
```bash
# Run validation checks
python validate_templates.py

# Should output:
# RESULT: 8/8 checks passed
# STATUS: VALID - All checks passed!
```

## Categories

1. **Registration** - Grievance registration confirmation
2. **Viewed** - Officer viewed the grievance
3. **Forwarding** - Grievance forwarded to another department
4. **Closure** - Grievance resolved/closed
5. **Feedback** - Request for feedback

## Keywords

- `registration` - Grievance registration
- `escalation` - Forwarding/escalating
- `closure` - Resolution/completion
- `feedback` - User feedback request
- `viewed` - Officer viewing
- `action` - Action taken
- `reminder` - Status reminders
- `status` - Status updates

## Departments Found

1. Agriculture - వ్యవసాయం
2. Education - విద్య
3. Forest - అటవీ
4. Health - ఆరోగ్యం
5. MAUD - పురపాలక
6. PRRD - పంచాయతీ రాజ్

## Officer Designations

1. Collector - కలెక్టర్
2. Executive Engineer - ఎగ్జిక్యూటివ్ ఇంజనీర్
3. MRO - Mandal Revenue Officer
4. Mandal Officer - MPDO
5. Officer (Generic) - ఆఫీసర్/అధికారి

## Quality Assurance

✅ **All Quality Gates Passed:**
- 54 templates extracted ✅
- All have Telugu text ✅
- No encoding issues ✅
- 6 departments detected ✅
- 5 officer designations ✅
- Average length 451 chars ✅

✅ **All Validation Checks Passed:**
- Telugu text present ✅
- Text length >50 chars ✅
- Telugu Unicode chars present ✅
- No mojibake ✅
- Categories assigned ✅
- Keywords extracted ✅
- Statistics accurate ✅
- Character counts correct ✅

## Source

**Original File:** `docs/reference/markdown/MESSAGES_SENT_TO_PETITIONERS.json`
- Converted from Excel file
- 58 rows total (54 templates + 4 headers)
- Official PGRS system messages

## Integration

This data supports:
- **Template Service** - Dynamic message generation
- **ML Models** - Text classification and NER training
- **Analytics** - Usage patterns and statistics
- **API Endpoints** - Template retrieval and filtering

## Next Steps

1. Integrate with `backend/app/services/template_service.py`
2. Create API endpoints for template access
3. Add template search/filter functionality
4. Generate English translations (manual or NMT)
5. Expand department and officer coverage

## Contact

**Agent:** AGENT 5 - Telugu Message Templates Extraction
**Date:** 2025-11-25
**Status:** ✅ COMPLETE

For questions or issues, refer to `AGENT_5_COMPLETION_REPORT.md`.
