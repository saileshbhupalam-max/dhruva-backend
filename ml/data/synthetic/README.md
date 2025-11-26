# Synthetic Lapse Training Data

## Overview

This directory contains synthetically generated lapse cases for training the Dhruva ML lapse prediction model. The data is based on real-world patterns observed in the Guntur district audit (2023-2024).

## Files

- **`synthetic_lapse_cases.json`** - Complete dataset with metadata (445 KB)
- **`synthetic_lapse_cases.csv`** - CSV format for easy inspection (117 KB)

## Dataset Statistics

- **Total Samples**: 1,000
- **Generation Date**: 2025-11-25
- **Confidence Level**: 0.85 (synthetic data marker)
- **Random Seed**: 42 (reproducible generation)

## Lapse Distribution

Based on Guntur audit findings:

| Rank | Lapse Type | Count | % | Research % |
|------|-----------|-------|---|-----------|
| 1 | GRA did not speak to citizen directly | 417 | 41.7% | 42.19% |
| 2 | Wrong/Blank/Not related comments | 170 | 17.0% | 12.44% |
| 3 | Not visited site / No field verification | 153 | 15.3% | 15.83% |
| 4 | Closed without required documents | 50 | 5.0% | 5.83% |
| 5 | No proper enquiry conducted | 39 | 3.9% | 4.96% |
| 6 | Premature closure | 35 | 3.5% | 4.05% |
| 7 | Inordinate delay | 32 | 3.2% | 2.61% |
| 8 | Incorrect routing | 25 | 2.5% | 2.44% |
| 9 | Inadequate action taken | 23 | 2.3% | 2.70% |
| 10 | No action letter issued | 22 | 2.2% | 2.00% |
| 11 | Action not taken as per rules | 20 | 2.0% | 2.87% |
| 12 | Poor quality of work | 10 | 1.0% | 1.30% |
| 13 | Beneficiary not contacted | 4 | 0.4% | 0.78% |

**Note**: Minor variations from research percentages are expected due to department-lapse affinity adjustments.

## Department Distribution

| Rank | Department | Count | % | Weight |
|------|-----------|-------|---|--------|
| 1 | Revenue (CCLA) | 347 | 34.7% | 0.35 |
| 2 | Social Welfare | 155 | 15.5% | 0.15 |
| 3 | Municipal Administration | 126 | 12.6% | 0.12 |
| 4 | Agriculture And Co-operation | 82 | 8.2% | 0.08 |
| 5 | Panchayat Raj And Rural Development | 71 | 7.1% | 0.08 |

## Feature Ranges

| Feature | Min | Max | Mean |
|---------|-----|-----|------|
| days_to_resolve | 1 | 108 | 19.47 |
| officer_response_count | 1 | 20 | 3.41 |

## Data Generation Methodology

### Realistic Correlations

The generator implements several research-backed correlations:

1. **Department-Lapse Affinity**
   - Revenue department → higher "Premature closure" probability
   - Municipal/Panchayat Raj → higher "Not visited site" probability
   - Social Welfare → higher "Closed without required documents"

2. **Time-Based Patterns**
   - Longer resolution times → higher "Inordinate delay" probability
   - Longer times → higher escalation levels

3. **Escalation Logic**
   - More days → higher escalation (GRA → Mandal → Tahsildar → RDO → Collector → HOD → CM)
   - High-priority departments (Revenue, Social Welfare) escalate faster
   - Higher escalation → more officer responses

4. **Noise and Variation**
   - Gaussian noise added to continuous features
   - Confidence scores vary (0.85-0.95) to avoid overfitting

### Data Fields

```json
{
  "id": 1,
  "department_code": "REVENUE",
  "department_name": "Revenue (CCLA)",
  "district_code": "GNT",
  "district_name": "Guntur",
  "grievance_category": "land_mutation",
  "days_to_resolve": 45,
  "officer_response_count": 2,
  "escalation_level": "Collector",
  "lapse_type": "Premature closure",
  "lapse_type_id": 6,
  "confidence": 0.88
}
```

### Field Descriptions

- **id**: Unique sample identifier (1-1000)
- **department_code**: Standard AP government department code
- **department_name**: Full department name
- **district_code**: AP district code (26 districts)
- **district_name**: Full district name
- **grievance_category**: Specific type of grievance (department-specific)
- **days_to_resolve**: Number of days from filing to closure (1-120)
- **officer_response_count**: Number of officer interactions (1-20)
- **escalation_level**: Highest level the case reached
- **lapse_type**: Procedural lapse category (1 of 13 types)
- **lapse_type_id**: Numeric lapse category ID (1-13)
- **confidence**: Synthetic data confidence score (0.85-0.95)

## Departments Covered (14)

1. Revenue (CCLA) - Land, property, certificates
2. Social Welfare - Pensions, scholarships, welfare schemes
3. Municipal Administration - Water, sanitation, urban services
4. Agriculture And Co-operation - Crop compensation, subsidies
5. Panchayat Raj And Rural Development - Village infrastructure
6. Energy - Power supply, electricity issues
7. Water Resources - Irrigation, water management
8. Health, Medical And Family Welfare - Healthcare services
9. Transport, Roads And Buildings - Infrastructure
10. Home (Police) - Law enforcement, security
11. Housing - Housing schemes, construction
12. Labour - Worker welfare, factory safety
13. Backward Classes Welfare - BC community services
14. Women, Children, Disabled And Senior Citizens - Vulnerable groups

## Districts Covered (26)

All 26 Andhra Pradesh districts with uniform distribution:
- Guntur, Visakhapatnam, Anantapur, Kadapa, West Godavari, NTR District
- Chittoor, East Godavari, Krishna, Kurnool, Nellore, Prakasam
- Srikakulam, Vizianagaram, and 12 newer districts

## Usage for ML Training

### Loading Data (Python)

```python
import json
import pandas as pd

# Load JSON
with open('synthetic_lapse_cases.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

metadata = data['metadata']
samples = data['samples']

# Or load CSV directly
df = pd.read_csv('synthetic_lapse_cases.csv')
```

### Feature Engineering

Recommended feature transformations:

```python
# Categorical encoding
df['dept_encoded'] = df['department_code'].astype('category').cat.codes
df['district_encoded'] = df['district_code'].astype('category').cat.codes
df['escalation_encoded'] = df['escalation_level'].astype('category').cat.codes

# Temporal features
df['is_delayed'] = (df['days_to_resolve'] > 15).astype(int)
df['log_days'] = np.log1p(df['days_to_resolve'])

# Response rate
df['responses_per_day'] = df['officer_response_count'] / df['days_to_resolve']
```

### Train/Test Split

```python
from sklearn.model_selection import train_test_split

# Stratified split to maintain lapse distribution
X = df.drop(['id', 'lapse_type', 'lapse_type_id', 'confidence'], axis=1)
y = df['lapse_type_id']

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
```

## Limitations

1. **Synthetic Nature**: This is generated data, not real audit findings
2. **Simplified Correlations**: Real-world patterns are more complex
3. **Confidence Scores**: All samples marked 0.85-0.95 to indicate synthetic origin
4. **Limited Scope**: Only covers 14 of 70+ departments
5. **No Temporal Trends**: No seasonal or time-of-year patterns

## Next Steps

1. **Combine with Real Data**: Merge with actual audit data when available
2. **Validate Model**: Test on held-out real-world cases
3. **Feature Expansion**: Add officer IDs, constituency data, complaint text
4. **Temporal Features**: Add month, quarter, year patterns
5. **Citizen Demographics**: Add optional citizen-level features (age, gender, location)

## Regeneration

To regenerate with different parameters:

```bash
cd D:\projects\dhruva\backend\ml
python generate_synthetic_lapse_data.py
```

Modify constants in the script:
- `NUM_SAMPLES` - Number of samples to generate
- `random.seed()` - Change seed for different random variations
- Department weights in `DEPARTMENTS`
- Lapse probabilities in `LAPSE_CATEGORIES`

## References

- Guntur District Audit Report (2023-2024)
- AP Government Departments List (2024)
- AP District Reorganization (2024)

## Contact

For questions about the synthetic data generation:
- Review `generate_synthetic_lapse_data.py` for implementation details
- Check `ML_TRAINING_HANDOFF_DOCUMENT.md` for broader ML pipeline documentation

---

**Generated**: 2025-11-25
**Version**: 1.0
**Status**: Ready for ML training
