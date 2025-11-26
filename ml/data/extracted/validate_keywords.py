#!/usr/bin/env python3
"""
PGRS Book Keywords Validation Script
Validates the extracted keywords JSON file against quality gates
"""

import json
import sys
from pathlib import Path

def validate_keywords():
    """Validate extracted keywords against quality gates"""

    # Load JSON
    json_path = Path(__file__).parent / "pgrs_book_keywords.json"
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print("=" * 80)
    print("PGRS BOOK KEYWORDS EXTRACTION - VALIDATION REPORT")
    print("=" * 80)
    print()

    # Summary Statistics
    print("SUMMARY STATISTICS:")
    print("-" * 80)
    summary = data['summary']
    print(f"  Total Departments:   {summary['total_departments']}")
    print(f"  Total Subjects:      {summary['total_subjects']}")
    print(f"  Total Sub-Subjects:  {summary['total_sub_subjects']}")
    print(f"  Total Keywords:      {summary['total_keywords']}")
    print(f"  Telugu Keywords:     {summary['telugu_keywords']}")
    print(f"  English Keywords:    {summary['english_keywords']}")
    print()

    # Quality Gates
    print("QUALITY GATES:")
    print("-" * 80)
    validation = data['quality_validation']

    gates = [
        ("Departments (=30)", validation['departments_check']),
        ("Subjects (>=100)", validation['subjects_check']),
        ("Sub-Subjects (>=100)", validation['sub_subjects_check']),
        ("Keywords (>=200)", validation['keywords_check']),
        ("Telugu Encoding (UTF-8)", validation['telugu_check']),
        ("Min Keywords/Dept (>=5)", validation['min_keywords_check']),
        ("Duplicate Check", validation['duplicate_check'])
    ]

    all_passed = True
    for gate_name, gate_result in gates:
        status = "PASS" if "PASS" in gate_result else "FAIL"
        symbol = "[+]" if status == "PASS" else "[-]"
        print(f"  {symbol} {gate_name:<30} {gate_result}")
        if status == "FAIL":
            all_passed = False

    print()

    # Top Subjects
    print("TOP SUBJECTS INCLUDED:")
    print("-" * 80)
    for subject in validation['top_subjects_included']:
        print(f"  - {subject}")
    print()

    # Department Details
    print("DEPARTMENT BREAKDOWN:")
    print("-" * 80)
    for dept in data['departments'][:5]:  # Show first 5
        print(f"  {dept['sno']:2d}. {dept['name_english']:<50} ({dept['total_keywords']} keywords)")
    print(f"  ... ({summary['total_departments'] - 5} more departments)")
    print()

    # Usage Notes
    print("USAGE NOTES:")
    print("-" * 80)
    for note in data['usage_notes'].values():
        print(f"  - {note}")
    print()

    # Final Result
    print("=" * 80)
    if all_passed:
        print("RESULT: ALL QUALITY GATES PASSED")
        print("Output File: backend/ml/data/extracted/pgrs_book_keywords.json")
        print("=" * 80)
        return 0
    else:
        print("RESULT: SOME QUALITY GATES FAILED")
        print("=" * 80)
        return 1

if __name__ == "__main__":
    sys.exit(validate_keywords())
