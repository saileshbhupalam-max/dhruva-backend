# Quick Start: Telugu Grievance Data Augmentation

## One-Line Summary
Generate 500+ synthetic Telugu grievance samples from 85 authentic samples using template-based augmentation **without any external APIs**.

---

## Quick Commands

### Generate Dataset (First Time)
```bash
cd D:\projects\dhruva\backend\ml
python generate_synthetic_telugu_data.py
```
**Output:** `data/synthetic/synthetic_telugu_grievances.json` (585 samples)

### View Statistics
```bash
python inspect_synthetic_samples.py stats
```

### View Samples by Department
```bash
python inspect_synthetic_samples.py Revenue
python inspect_synthetic_samples.py Agriculture
python inspect_synthetic_samples.py Health
```

### View Random Samples
```bash
python inspect_synthetic_samples.py random 10
```

---

## What You Get

| Metric | Value |
|--------|-------|
| Total Samples | 585 |
| Authentic | 85 |
| Synthetic | 500 |
| Departments | 31 |
| Major Depts (50+ samples) | 10 |
| Categories | 96 |
| Avg Confidence | 0.816 |

---

## Target Departments (All Met 50+ Samples)

✓ Revenue (57)
✓ Agriculture (54)
✓ Health (54)
✓ Education (54)
✓ Municipal Administration (54)
✓ Energy (54)
✓ Police (52)
✓ Social Welfare (52)
✓ Panchayat Raj (54)
✓ Transport (50)

---

## Load in Python

```python
import json

# Load dataset
with open('data/synthetic/synthetic_telugu_grievances.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Get samples
samples = data['samples']  # 585 samples
texts = [s['telugu_text'] for s in samples]
labels = [s['department'] for s in samples]

# Filter high-quality
high_quality = [s for s in samples if s['confidence'] >= 0.80]  # 585 samples

# Get authentic only
authentic = [s for s in samples if not s.get('is_synthetic')]  # 85 samples

# Get by department
revenue = [s for s in samples if s['department'] == 'Revenue']  # 57 samples
```

---

## Sample Output

### Authentic Sample
```json
{
  "telugu_text": "పంచాయతీ కార్యాలయంలో పనులు ఆలస్యం అవుతున్నాయి",
  "english_translation": "Work is being delayed in Panchayat office",
  "department": "Panchayat Raj",
  "confidence": 0.85
}
```

### Synthetic Sample
```json
{
  "telugu_text": "కుల ధృవీకరణ పత్రం కోసం దరఖాస్తు చేసాను. గత మూడు నెలలుగా అయింది",
  "english_translation": "Applied for caste certificate. It has been three months",
  "department": "Revenue",
  "confidence": 0.84,
  "is_synthetic": true
}
```

---

## Configuration

### Change Target Counts
Edit `generate_synthetic_telugu_data.py`:
```python
self.department_targets = {
    "Revenue": 100,  # Change from 50
    "Agriculture": 75,  # Change from 50
}
```

### Add New Templates
Edit `generate_synthetic_telugu_data.py`:
```python
self.dept_patterns = {
    "Revenue": [
        "మీ టెంప్లేట్ {placeholder}",
    ]
}
```

---

## Files

- **generate_synthetic_telugu_data.py** - Main script
- **inspect_synthetic_samples.py** - View samples
- **data/synthetic/synthetic_telugu_grievances.json** - Output (585 samples)
- **TELUGU_AUGMENTATION_COMPLETE.md** - Full documentation
- **SYNTHETIC_DATA_GENERATION_REPORT.md** - Detailed report

---

## Augmentation Techniques

1. **Template-Based** (447 samples) - Fill department-specific templates
2. **Politeness Variation** (26 samples) - Add దయచేసి, కృపయా
3. **Urgency Variation** (27 samples) - Add అత్యవసరం, త్వరగా
4. **Location Replacement** - Swap village names
5. **Pattern Recombination** - Mix phrases from different samples

---

## Requirements

- Python 3.7+
- **No pip installs required**
- **No external APIs needed**
- Works completely offline

---

## Train/Test Split

```python
from sklearn.model_selection import train_test_split

X_train, X_test, y_train, y_test = train_test_split(
    texts, labels,
    test_size=0.2,
    stratify=labels,
    random_state=42
)

print(f"Train: {len(X_train)}, Test: {len(X_test)}")
# Output: Train: 468, Test: 117
```

---

## Troubleshooting

### Issue: File not found
**Solution:** Run `generate_synthetic_telugu_data.py` first

### Issue: Unicode errors on Windows
**Solution:** Script handles this automatically with UTF-8 encoding

### Issue: Want more samples
**Solution:** Modify `department_targets` in script and re-run

---

## Next Steps

1. ✓ Generate dataset (done)
2. Load samples in Python
3. Train department classifier
4. Evaluate on test set
5. Deploy to production
6. Collect real grievances
7. Retrain with real data

---

**Ready for ML Training:** YES ✓

---

*Quick Reference - 2025-11-25*
