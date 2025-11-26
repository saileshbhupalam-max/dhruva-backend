#!/usr/bin/env python3
"""
Validate Telugu message templates JSON
Quick integrity checks for message_templates.json
"""

import json
from pathlib import Path


def validate_templates():
    """Validate extracted templates"""
    file_path = Path(__file__).parent / "message_templates.json"

    print("=" * 80)
    print("VALIDATING TELUGU MESSAGE TEMPLATES")
    print("=" * 80)
    print()

    # Load data
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    templates = data['templates']
    summary = data['summary']

    print(f"Loaded {len(templates)} templates")
    print()

    # Validation checks
    checks = []

    # Check 1: All templates have Telugu text
    empty_text = [t['template_id'] for t in templates if not t['text_telugu']]
    checks.append(("All templates have Telugu text", len(empty_text) == 0, f"Empty: {empty_text if empty_text else 'None'}"))

    # Check 2: All Telugu text is non-trivial (>50 chars)
    short_text = [t['template_id'] for t in templates if len(t['text_telugu']) < 50]
    checks.append(("All templates >50 characters", len(short_text) == 0, f"Short: {short_text if short_text else 'None'}"))

    # Check 3: Telugu encoding (check for Telugu chars)
    def has_telugu(text):
        return any('\u0C00' <= c <= '\u0C7F' for c in text)

    no_telugu = [t['template_id'] for t in templates if not has_telugu(t['text_telugu'])]
    checks.append(("All templates have Telugu characters", len(no_telugu) == 0, f"No Telugu: {no_telugu if no_telugu else 'None'}"))

    # Check 4: No mojibake
    def has_mojibake(text):
        return any(c in text for c in ['�', '\ufffd'])

    mojibake = [t['template_id'] for t in templates if has_mojibake(t['text_telugu'])]
    checks.append(("No mojibake detected", len(mojibake) == 0, f"Mojibake: {mojibake if mojibake else 'None'}"))

    # Check 5: All templates have category
    no_category = [t['template_id'] for t in templates if not t['category']]
    checks.append(("All templates have category", len(no_category) == 0, f"No category: {no_category if no_category else 'None'}"))

    # Check 6: All templates have keywords
    no_keywords = [t['template_id'] for t in templates if not t['extracted_keywords']]
    checks.append(("All templates have keywords", len(no_keywords) == 0, f"No keywords: {len(no_keywords)} templates"))

    # Check 7: Summary matches data
    summary_check = (
        summary['total_templates'] == len(templates) and
        summary['telugu_templates'] == len(templates)
    )
    checks.append(("Summary statistics match", summary_check, f"Total: {len(templates)}, Summary: {summary['total_templates']}"))

    # Check 8: Character counts are accurate
    wrong_counts = [
        t['template_id'] for t in templates
        if t['character_count'] != len(t['text_telugu'])
    ]
    checks.append(("Character counts accurate", len(wrong_counts) == 0, f"Wrong counts: {wrong_counts if wrong_counts else 'None'}"))

    # Print results
    print("VALIDATION RESULTS:")
    print("-" * 80)
    passed = 0
    for check_name, passed_check, details in checks:
        status = "[PASS]" if passed_check else "[FAIL]"
        print(f"{status} {check_name}")
        if not passed_check:
            print(f"      Details: {details}")
        if passed_check:
            passed += 1

    print()
    print("=" * 80)
    print(f"RESULT: {passed}/{len(checks)} checks passed")

    if passed == len(checks):
        print("STATUS: VALID - All checks passed!")
    else:
        print(f"STATUS: ISSUES FOUND - {len(checks) - passed} checks failed")
    print("=" * 80)

    # Additional statistics
    print()
    print("STATISTICS:")
    print(f"  Templates: {len(templates)}")
    print(f"  Departments: {summary['unique_departments_mentioned']}")
    print(f"  Officers: {summary['unique_officer_designations']}")
    print(f"  Avg length: {summary['avg_length']:.2f} chars")
    print(f"  Categories: {len(set(t['category'] for t in templates))}")
    print()

    return passed == len(checks)


if __name__ == "__main__":
    success = validate_templates()
    exit(0 if success else 1)
