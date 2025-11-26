#!/usr/bin/env python3
"""
Synthetic Data Validation Script
=================================

Validates the generated synthetic lapse data for:
- Schema compliance
- Distribution accuracy
- Feature consistency
- Data quality issues

Usage:
    python validate_synthetic_data.py
"""

import json
import sys
from pathlib import Path
from collections import Counter
from typing import Dict, List, Tuple


def load_data(filepath: Path) -> Dict:
    """Load synthetic data JSON."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def validate_schema(samples: List[Dict]) -> Tuple[bool, List[str]]:
    """Validate that all samples have required fields."""
    required_fields = [
        'id', 'department_code', 'department_name', 'district_code',
        'district_name', 'grievance_category', 'days_to_resolve',
        'officer_response_count', 'escalation_level', 'lapse_type',
        'lapse_type_id', 'confidence'
    ]

    errors = []

    for i, sample in enumerate(samples):
        missing = [f for f in required_fields if f not in sample]
        if missing:
            errors.append(f"Sample {i+1} missing fields: {missing}")

    return len(errors) == 0, errors


def validate_distributions(samples: List[Dict], metadata: Dict) -> Tuple[bool, List[str]]:
    """Validate lapse distribution matches expected patterns."""
    warnings = []

    # Check lapse distribution
    lapse_counts = Counter(s['lapse_type'] for s in samples)
    metadata_dist = metadata['lapse_distribution']

    for lapse_type, stats in metadata_dist.items():
        actual_count = lapse_counts.get(lapse_type, 0)
        expected_count = stats['count']

        if actual_count != expected_count:
            warnings.append(
                f"Lapse '{lapse_type}': metadata says {expected_count}, "
                f"but actual count is {actual_count}"
            )

    # Check top lapse is "GRA did not speak to citizen directly" (~42%)
    top_lapse = lapse_counts.most_common(1)[0]
    if not top_lapse[0].startswith("GRA did not speak"):
        warnings.append(f"Expected 'GRA did not speak...' as top lapse, got '{top_lapse[0]}'")

    percentage = (top_lapse[1] / len(samples)) * 100
    if percentage < 35 or percentage > 50:
        warnings.append(
            f"Top lapse percentage {percentage:.1f}% outside expected range (35-50%)"
        )

    return len(warnings) == 0, warnings


def validate_feature_ranges(samples: List[Dict]) -> Tuple[bool, List[str]]:
    """Validate feature values are within expected ranges."""
    errors = []

    for i, sample in enumerate(samples):
        # Days to resolve: 1-120
        days = sample.get('days_to_resolve', 0)
        if not (1 <= days <= 120):
            errors.append(f"Sample {i+1}: days_to_resolve={days} out of range [1, 120]")

        # Officer response count: 1-20
        responses = sample.get('officer_response_count', 0)
        if not (1 <= responses <= 20):
            errors.append(f"Sample {i+1}: officer_response_count={responses} out of range [1, 20]")

        # Confidence: 0.85-0.95
        conf = sample.get('confidence', 0)
        if not (0.85 <= conf <= 0.95):
            errors.append(f"Sample {i+1}: confidence={conf} out of range [0.85, 0.95]")

        # Lapse type ID: 1-13
        lapse_id = sample.get('lapse_type_id', 0)
        if not (1 <= lapse_id <= 13):
            errors.append(f"Sample {i+1}: lapse_type_id={lapse_id} out of range [1, 13]")

    return len(errors) == 0, errors


def validate_consistency(samples: List[Dict]) -> Tuple[bool, List[str]]:
    """Validate internal consistency of samples."""
    warnings = []

    for i, sample in enumerate(samples):
        # High days but low escalation
        days = sample.get('days_to_resolve', 0)
        escalation = sample.get('escalation_level', '')

        if days > 60 and escalation in ['GRA', 'Mandal']:
            warnings.append(
                f"Sample {i+1}: {days} days but only escalated to {escalation}"
            )

        # Low days but high escalation
        if days < 7 and escalation in ['Collector', 'HOD', 'CM']:
            warnings.append(
                f"Sample {i+1}: Only {days} days but escalated to {escalation}"
            )

        # Many responses but few days
        responses = sample.get('officer_response_count', 0)
        if responses > days and days > 0:
            warnings.append(
                f"Sample {i+1}: {responses} responses in only {days} days (>1 per day)"
            )

    return len(warnings) == 0, warnings


def validate_unique_ids(samples: List[Dict]) -> Tuple[bool, List[str]]:
    """Validate all IDs are unique and sequential."""
    errors = []

    ids = [s.get('id') for s in samples]

    # Check for duplicates
    id_counts = Counter(ids)
    duplicates = [id_ for id_, count in id_counts.items() if count > 1]
    if duplicates:
        errors.append(f"Duplicate IDs found: {duplicates}")

    # Check sequential (should be 1 to N)
    expected_ids = set(range(1, len(samples) + 1))
    actual_ids = set(ids)
    missing = expected_ids - actual_ids
    if missing:
        errors.append(f"Missing IDs: {sorted(missing)}")

    extra = actual_ids - expected_ids
    if extra:
        errors.append(f"Unexpected IDs: {sorted(extra)}")

    return len(errors) == 0, errors


def print_validation_results(
    category: str,
    passed: bool,
    issues: List[str],
    max_display: int = 5
):
    """Print validation results for a category."""
    status = "PASS" if passed else "FAIL" if "error" in category.lower() else "WARN"
    symbol = "[OK]" if passed else "[ERROR]" if status == "FAIL" else "[WARN]"

    print(f"\n{symbol} {category}")

    if passed:
        print("  No issues found")
    else:
        print(f"  Found {len(issues)} issue(s):")
        for issue in issues[:max_display]:
            print(f"    - {issue}")
        if len(issues) > max_display:
            print(f"    ... and {len(issues) - max_display} more")


def main():
    """Main validation function."""
    data_path = Path(__file__).parent / "data" / "synthetic" / "synthetic_lapse_cases.json"

    print("=" * 70)
    print("SYNTHETIC LAPSE DATA VALIDATION")
    print("=" * 70)
    print(f"Data file: {data_path}")

    if not data_path.exists():
        print(f"\n[ERROR] Data file not found: {data_path}")
        print("Please run generate_synthetic_lapse_data.py first")
        return 1

    # Load data
    print("\nLoading data...")
    data = load_data(data_path)
    samples = data['samples']
    metadata = data['metadata']

    print(f"Loaded {len(samples)} samples")
    print(f"Generation date: {metadata['generation_date']}")

    # Run validations
    all_passed = True

    # 1. Schema validation
    passed, errors = validate_schema(samples)
    print_validation_results("Schema Validation", passed, errors)
    all_passed = all_passed and passed

    # 2. Unique IDs
    passed, errors = validate_unique_ids(samples)
    print_validation_results("Unique ID Validation", passed, errors)
    all_passed = all_passed and passed

    # 3. Feature ranges
    passed, errors = validate_feature_ranges(samples)
    print_validation_results("Feature Range Validation", passed, errors)
    all_passed = all_passed and passed

    # 4. Distribution validation
    passed, warnings = validate_distributions(samples, metadata)
    print_validation_results("Distribution Validation", passed, warnings)
    # Don't fail on distribution warnings
    if not passed:
        print("  (Distribution mismatches are warnings, not errors)")

    # 5. Consistency validation
    passed, warnings = validate_consistency(samples)
    print_validation_results("Consistency Validation", passed, warnings, max_display=10)
    # Don't fail on consistency warnings
    if not passed:
        print("  (Consistency issues are warnings, not errors)")

    # Summary
    print("\n" + "=" * 70)
    if all_passed:
        print("VALIDATION PASSED")
        print("Data is ready for ML training")
    else:
        print("VALIDATION FAILED")
        print("Please review errors above")
    print("=" * 70)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
