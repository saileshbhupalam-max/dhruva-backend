# Synthetic Lapse Data - Quick Start Guide

Quick reference for working with synthetic lapse training data.

## Generated Files

```
backend/ml/
├── generate_synthetic_lapse_data.py       # Generator script (587 lines)
├── validate_synthetic_data.py             # Validation script (255 lines)
├── example_train_with_synthetic.py        # Training example (233 lines)
├── visualize_synthetic_data.py            # Visualization (266 lines)
├── SYNTHETIC_DATA_GENERATION_SUMMARY.md   # Complete documentation
└── data/synthetic/
    ├── synthetic_lapse_cases.json         # 1000 samples (445 KB)
    ├── synthetic_lapse_cases.csv          # CSV format (117 KB)
    └── README.md                          # Data documentation
```

## Quick Commands

### 1. Generate Data
```bash
cd D:\projects\dhruva\backend\ml
python generate_synthetic_lapse_data.py
```

**Output**: 1,000 synthetic lapse cases in JSON and CSV formats

**Time**: ~2 seconds

### 2. Validate Data
```bash
python validate_synthetic_data.py
```

**Checks**:
- Schema compliance
- Distribution accuracy
- Feature ranges
- Internal consistency

**Expected**: VALIDATION PASSED

### 3. Visualize Data
```bash
python visualize_synthetic_data.py
```

**Shows**:
- Lapse type distribution (ASCII bar charts)
- Department/district distributions
- Days-to-resolve histogram
- Correlation analysis
- Quality indicators

### 4. Train Example Model
```bash
python example_train_with_synthetic.py
```

**Trains**: Random Forest classifier (100 trees)

**Expected Accuracy**: 20-30% (synthetic-only data)

---

## Key Statistics

### Dataset Overview
- **Total Samples**: 1,000
- **Lapse Categories**: 13
- **Departments**: 14
- **Districts**: 26 (all AP districts)

### Top 5 Lapses
1. GRA did not speak to citizen (41.7%)
2. Wrong/Blank/Not related comments (17.0%)
3. Not visited site (15.3%)
4. Closed without documents (5.0%)
5. No proper enquiry (3.9%)

### Top 5 Departments
1. Revenue (34.7%)
2. Social Welfare (15.5%)
3. Municipal Administration (12.6%)
4. Agriculture (8.2%)
5. Panchayat Raj (7.1%)

### Feature Ranges
- **Days to resolve**: 1-108 (mean: 19.5)
- **Officer responses**: 1-20 (mean: 3.4)
- **Confidence**: 0.85-0.95 (synthetic marker)

---

## Usage in Python

### Load JSON
```python
import json

with open('data/synthetic/synthetic_lapse_cases.json', 'r') as f:
    data = json.load(f)

samples = data['samples']
metadata = data['metadata']

print(f"Loaded {len(samples)} samples")
print(f"Generated: {metadata['generation_date']}")
```

### Load CSV
```python
import pandas as pd

df = pd.read_csv('data/synthetic/synthetic_lapse_cases.csv')
print(df.head())
print(df['lapse_type'].value_counts())
```

### Quick Analysis
```python
# Lapse distribution
print(df['lapse_type'].value_counts(normalize=True) * 100)

# Department stats
print(df.groupby('department_code')['days_to_resolve'].mean())

# Correlation
print(df[['days_to_resolve', 'officer_response_count', 'escalation_numeric']].corr())
```

---

## Training Pipeline

### Basic Setup
```python
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder

# Load data
df = pd.read_csv('data/synthetic/synthetic_lapse_cases.csv')

# Encode categoricals
le_dept = LabelEncoder()
df['dept_encoded'] = le_dept.fit_transform(df['department_code'])

# Prepare X, y
features = ['dept_encoded', 'days_to_resolve', 'officer_response_count']
X = df[features]
y = df['lapse_type_id']

# Split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# Train
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Evaluate
accuracy = model.score(X_test, y_test)
print(f"Accuracy: {accuracy:.3f}")
```

### Advanced Features
```python
import numpy as np

# Add engineered features
df['is_delayed'] = (df['days_to_resolve'] > 15).astype(int)
df['log_days'] = np.log1p(df['days_to_resolve'])
df['responses_per_day'] = df['officer_response_count'] / (df['days_to_resolve'] + 1)

# Escalation mapping
escalation_map = {'GRA': 1, 'Mandal': 2, 'Tahsildar': 3, 'RDO': 4, 'Collector': 5, 'HOD': 6, 'CM': 7}
df['escalation_numeric'] = df['escalation_level'].map(escalation_map)
```

---

## Customization

### Change Sample Count
Edit `generate_synthetic_lapse_data.py`:
```python
NUM_SAMPLES = 5000  # Change from 1000
```

### Adjust Lapse Probabilities
Edit `LAPSE_CATEGORIES` in generator:
```python
{
    "id": 1,
    "name": "GRA did not speak to citizen directly",
    "probability": 0.5,  # Increase from 0.4219
    ...
}
```

### Add New Departments
Edit `DEPARTMENTS`:
```python
{"code": "NEWDEPT", "name": "New Department", "volume_weight": 0.05}
```

### Change Random Seed
For different variations:
```python
random.seed(123)  # Change from 42
```

---

## Common Issues

### Issue: Unicode errors on Windows
**Fix**: All scripts now use ASCII-safe characters (#, OK, FAIL instead of █, ✓, ✗)

### Issue: Low model accuracy (20-30%)
**Expected**: This is synthetic data. Combine with real audit data for better accuracy.
**Target**: 80% real + 20% synthetic → 60-70% accuracy

### Issue: Class imbalance warnings
**Expected**: Top lapse (41.7%) vs bottom (0.5%) is intentional.
**Fix**: Use `class_weight='balanced'` in sklearn models

### Issue: Inconsistent escalation patterns (warnings in validation)
**Expected**: 3-5 warnings are acceptable. Real data also has exceptions.
**Fix**: Only regenerate if >10% of samples have issues

---

## Performance Benchmarks

| Operation | Time | Output Size |
|-----------|------|-------------|
| Generate 1,000 samples | ~2s | 445 KB JSON |
| Generate 10,000 samples | ~15s | 4.4 MB JSON |
| Validate data | <1s | Console output |
| Visualize data | ~1s | Console output |
| Train Random Forest (100 trees) | ~3s | Model object |
| Train with 10,000 samples | ~20s | Model object |

---

## Next Steps

### Phase 1: Validation (Week 1)
- [x] Generate synthetic data
- [x] Validate data quality
- [x] Create visualizations
- [ ] Share with team for review

### Phase 2: Real Data Integration (Week 2-3)
- [ ] Collect 50-100 real labeled cases from Guntur audit
- [ ] Merge with synthetic (80% real, 20% synthetic)
- [ ] Retrain model and compare accuracy
- [ ] Document performance improvements

### Phase 3: Expansion (Week 4-6)
- [ ] Expand to 5,000 synthetic samples
- [ ] Add more departments (30+ total)
- [ ] Collect data from 3+ districts
- [ ] Implement cross-validation

### Phase 4: Production (Month 2-3)
- [ ] Deploy model as API endpoint
- [ ] Add real-time prediction
- [ ] Monitor model drift
- [ ] Implement continuous learning

---

## Resources

### Documentation
- **Complete Guide**: `SYNTHETIC_DATA_GENERATION_SUMMARY.md`
- **Data Docs**: `data/synthetic/README.md`
- **ML Handoff**: `ML_TRAINING_HANDOFF_DOCUMENT.md`

### Scripts
- **Generator**: `generate_synthetic_lapse_data.py` (587 lines)
- **Validator**: `validate_synthetic_data.py` (255 lines)
- **Training**: `example_train_with_synthetic.py` (233 lines)
- **Viz**: `visualize_synthetic_data.py` (266 lines)

### Data Files
- **JSON**: `data/synthetic/synthetic_lapse_cases.json` (445 KB)
- **CSV**: `data/synthetic/synthetic_lapse_cases.csv` (117 KB)

---

## Support

For questions or issues:

1. Check this guide first
2. Review `SYNTHETIC_DATA_GENERATION_SUMMARY.md` for details
3. Run validation script to check data quality
4. Review example training script for usage patterns

---

**Last Updated**: 2025-11-25
**Status**: Production Ready
**Version**: 1.0
