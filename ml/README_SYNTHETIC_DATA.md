# Telugu Grievance Synthetic Data Generation

## Overview

This directory contains scripts for generating synthetic Telugu grievance text samples using template-based augmentation techniques without requiring external APIs.

## Files

- **`generate_synthetic_telugu_data.py`** - Main data augmentation script
- **`inspect_synthetic_samples.py`** - Inspection tool for viewing generated samples
- **`SYNTHETIC_DATA_GENERATION_REPORT.md`** - Detailed report on generated data
- **`TELUGU_GRIEVANCE_DATASET_RESEARCH.json`** - 85 authentic Telugu samples (input)
- **`data/synthetic/synthetic_telugu_grievances.json`** - 585 total samples (output)

## Quick Start

### Generate Synthetic Data

```bash
cd D:\projects\dhruva\backend\ml
python generate_synthetic_telugu_data.py
```

**Output:** `data/synthetic/synthetic_telugu_grievances.json` (585 samples)

### Inspect Generated Data

```bash
# Show statistics
python inspect_synthetic_samples.py stats

# Show random samples
python inspect_synthetic_samples.py random 10

# List all departments
python inspect_synthetic_samples.py list

# Show samples for specific department
python inspect_synthetic_samples.py Revenue
python inspect_synthetic_samples.py Agriculture
python inspect_synthetic_samples.py Health
```

## Data Generation Results

### Summary
- **Total Samples:** 585
- **Authentic:** 85 (from research)
- **Synthetic:** 500 (generated)
- **Department Coverage:** 31 departments
- **Average Confidence:** 0.816

### Department Distribution (Target: 50+ samples each)
| Department | Samples | Status |
|------------|---------|--------|
| Revenue | 57 | ✓ |
| Agriculture | 54 | ✓ |
| Health | 54 | ✓ |
| Education | 54 | ✓ |
| Municipal Administration | 54 | ✓ |
| Energy | 54 | ✓ |
| Police | 52 | ✓ |
| Social Welfare | 52 | ✓ |
| Panchayat Raj | 54 | ✓ |
| Transport | 50 | ✓ |

**All 10 target departments met their goals!**

## Augmentation Techniques

1. **Template-Based Generation** (447 samples)
   - Department-specific complaint templates
   - Authentic Telugu government vocabulary
   - Contextually appropriate entity substitution

2. **Politeness Marker Variation** (26 samples)
   - Added: దయచేసి, కృపయా, దయచేసి తెలపండి
   - Creates formality variations

3. **Urgency Marker Variation** (27 samples)
   - Added: అత్యవసరం, త్వరగా, తక్షణం, వెంటనే
   - Creates urgency variations

4. **Location Entity Replacement**
   - Village names: అన్నారం, చౌటుప్పల్, చిట్కుల్, etc.
   - Maintains geographic authenticity

5. **Sentence Pattern Recombination**
   - Combines phrases from different samples
   - Maintains grammatical correctness

## Sample Quality

### Authentic Sample (Confidence: 0.85-0.98)
```json
{
  "telugu_text": "ప్రాథమిక ఆరోగ్య కేంద్రంలో వైద్యులు హాజరుకావటం లేదు",
  "english_translation": "Doctors are not attending at Primary Health Center",
  "department": "Health",
  "confidence": 0.85
}
```

### Synthetic Sample (Confidence: 0.75-0.85)
```json
{
  "telugu_text": "కుల ధృవీకరణ పత్రం కోసం దరఖాస్తు చేసాను. గత మూడు నెలలుగా అయింది",
  "english_translation": "Applied for caste certificate. It has been three months",
  "department": "Revenue",
  "confidence": 0.84,
  "is_synthetic": true
}
```

## Usage for ML Training

### Load Dataset

```python
import json

with open('data/synthetic/synthetic_telugu_grievances.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

samples = data['samples']
print(f"Total samples: {len(samples)}")
```

### Filter by Confidence

```python
# High-quality samples only
high_quality = [s for s in samples if s['confidence'] >= 0.80]

# Authentic samples only
authentic = [s for s in samples if not s.get('is_synthetic')]

# Department-specific
revenue_samples = [s for s in samples if s['department'] == 'Revenue']
```

### Prepare for Training

```python
# Extract features
texts = [s['telugu_text'] for s in samples]
labels = [s['department'] for s in samples]

# Train/test split
from sklearn.model_selection import train_test_split

X_train, X_test, y_train, y_test = train_test_split(
    texts, labels,
    test_size=0.2,
    stratify=labels,
    random_state=42
)
```

## Configuration

### Modify Department Targets

Edit `generate_synthetic_telugu_data.py`:

```python
self.department_targets = {
    "Revenue": 100,      # Increase to 100
    "Agriculture": 75,   # Increase to 75
    # ...
}
```

### Add New Templates

Edit `generate_synthetic_telugu_data.py`:

```python
self.dept_patterns = {
    "Revenue": [
        "{certificate_type} కోసం దరఖాస్తు చేసాను. {period} అయింది",
        "Your new template here {placeholder}",
        # ...
    ]
}
```

### Add New Entities

Edit `generate_synthetic_telugu_data.py`:

```python
self.entities = {
    "certificate_type": [
        "కుల ధృవీకరణ పత్రం",
        "Your new certificate type",
        # ...
    ]
}
```

## Validation

The script performs basic validation:
- ✓ All samples have valid department mappings
- ✓ All Telugu text is non-empty
- ✓ Confidence scores are within valid range (0.75-0.98)
- ✓ Department distribution meets targets

## Quality Assurance

### Telugu Language Quality
- Proper Telugu grammar maintained
- Authentic government vocabulary used
- Formal complaint register maintained
- Correct use of compound words

### Department Accuracy
- All departments match official AP Government nomenclature
- Telugu department names correctly paired
- Categories span all major grievance types

## Limitations

1. **English Translations:** Rule-based and approximate
2. **Synthetic Confidence:** Lower than authentic samples (0.75-0.85)
3. **Template Dependency:** Synthetic samples follow template patterns
4. **Under-represented Departments:** Some departments have <10 samples

## Next Steps

### Phase 1: Initial Training
1. Train department classifier with 585 samples
2. Evaluate accuracy on test set
3. Identify weak departments

### Phase 2: Real Data Collection
1. Deploy model to production
2. Collect real grievances
3. Add to training set
4. Retrain with real data

### Phase 3: Continuous Improvement
1. Monitor classification accuracy
2. Add new templates from real patterns
3. Generate more synthetic samples for weak categories

## Technical Details

### Dependencies
- Python 3.7+
- Standard library only (no external dependencies)
- Works standalone without APIs

### Output Format
```json
{
  "metadata": {
    "generation_date": "ISO-8601",
    "total_samples": 585,
    "authentic_samples": 85,
    "synthetic_samples": 500,
    "augmentation_methods": [...]
  },
  "samples": [...],
  "department_distribution": {...},
  "statistics": {...}
}
```

### Sample Schema
```json
{
  "id": 1000,
  "source_type": "synthetic_template",
  "confidence": 0.84,
  "telugu_text": "...",
  "english_translation": "...",
  "department": "Revenue",
  "department_telugu": "రెవెన్యూ",
  "category": "certificate_delay",
  "generation_date": "2025-11-25T19:47:36",
  "is_synthetic": true
}
```

## Support

For issues or questions:
1. Check `SYNTHETIC_DATA_GENERATION_REPORT.md` for detailed analysis
2. Run `python inspect_synthetic_samples.py` to explore samples
3. Verify input file exists: `TELUGU_GRIEVANCE_DATASET_RESEARCH.json`

## License

This data generation script is part of the Dhruva project.

---

*Generated: 2025-11-25*
*Version: 1.0*
