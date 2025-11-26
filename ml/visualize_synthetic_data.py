#!/usr/bin/env python3
"""
Synthetic Data Visualization Script
====================================

Generates ASCII visualizations and statistics for the synthetic lapse data.
No external plotting libraries required (uses pure Python).

Usage:
    python visualize_synthetic_data.py
"""

import json
from pathlib import Path
from collections import Counter, defaultdict
from typing import Dict, List


def create_bar_chart(data: Dict[str, int], title: str, max_width: int = 50):
    """Create ASCII bar chart."""
    print(f"\n{title}")
    print("=" * 70)

    if not data:
        print("No data to display")
        return

    max_value = max(data.values())
    total = sum(data.values())

    for label, value in sorted(data.items(), key=lambda x: x[1], reverse=True)[:15]:
        bar_width = int((value / max_value) * max_width)
        bar = "#" * bar_width
        percentage = (value / total) * 100
        print(f"{label[:35]:35s} {bar:50s} {value:4d} ({percentage:5.1f}%)")


def create_histogram(values: List[float], title: str, bins: int = 10):
    """Create ASCII histogram."""
    print(f"\n{title}")
    print("=" * 70)

    if not values:
        print("No data to display")
        return

    min_val = min(values)
    max_val = max(values)
    bin_width = (max_val - min_val) / bins

    # Create bins
    bin_counts = [0] * bins
    for value in values:
        bin_idx = min(int((value - min_val) / bin_width), bins - 1)
        bin_counts[bin_idx] += 1

    max_count = max(bin_counts)

    # Display histogram
    for i in range(bins):
        bin_start = min_val + (i * bin_width)
        bin_end = bin_start + bin_width
        count = bin_counts[i]
        bar_width = int((count / max_count) * 40) if max_count > 0 else 0
        bar = "#" * bar_width
        print(f"{bin_start:6.1f}-{bin_end:6.1f}: {bar:40s} {count:4d}")


def analyze_correlations(samples: List[Dict]):
    """Analyze correlations between features."""
    print("\n" + "=" * 70)
    print("CORRELATION ANALYSIS")
    print("=" * 70)

    # 1. Department vs Top Lapses
    dept_lapse = defaultdict(Counter)
    for s in samples:
        dept_lapse[s['department_code']][s['lapse_type']] += 1

    print("\nTop Lapse by Department:")
    print("-" * 70)
    for dept in ['REVENUE', 'SOC_WELF', 'MUNI', 'AGRI', 'PNCHRAJ']:
        if dept in dept_lapse:
            top_lapse = dept_lapse[dept].most_common(1)[0]
            dept_total = sum(dept_lapse[dept].values())
            pct = (top_lapse[1] / dept_total) * 100
            print(f"  {dept:15s}: {top_lapse[0][:40]:40s} ({pct:.1f}%)")

    # 2. Escalation by Days
    escalation_days = defaultdict(list)
    for s in samples:
        escalation_days[s['escalation_level']].append(s['days_to_resolve'])

    print("\nAverage Days by Escalation Level:")
    print("-" * 70)
    escalation_order = ['GRA', 'Mandal', 'Tahsildar', 'RDO', 'Collector', 'HOD', 'CM']
    for level in escalation_order:
        if level in escalation_days:
            avg_days = sum(escalation_days[level]) / len(escalation_days[level])
            count = len(escalation_days[level])
            print(f"  {level:12s}: {avg_days:6.1f} days (n={count:3d})")

    # 3. Delay-sensitive lapses
    delay_lapses = ['Inordinate delay', 'Not visited site / No field verification']
    delay_avg = {}

    for lapse_type in delay_lapses:
        days = [s['days_to_resolve'] for s in samples if s['lapse_type'] == lapse_type]
        if days:
            delay_avg[lapse_type] = sum(days) / len(days)

    print("\nAverage Days for Delay-Sensitive Lapses:")
    print("-" * 70)
    for lapse, avg in sorted(delay_avg.items(), key=lambda x: x[1], reverse=True):
        print(f"  {lapse[:45]:45s}: {avg:6.1f} days")

    # Overall average
    all_days = [s['days_to_resolve'] for s in samples]
    overall_avg = sum(all_days) / len(all_days)
    print(f"\n  {'OVERALL AVERAGE':45s}: {overall_avg:6.1f} days")


def print_summary_stats(samples: List[Dict]):
    """Print summary statistics."""
    print("\n" + "=" * 70)
    print("SUMMARY STATISTICS")
    print("=" * 70)

    # Days to resolve
    days = [s['days_to_resolve'] for s in samples]
    days.sort()

    print("\nDays to Resolve:")
    print(f"  Min:          {min(days):6.1f}")
    print(f"  25th %ile:    {days[len(days)//4]:6.1f}")
    print(f"  Median:       {days[len(days)//2]:6.1f}")
    print(f"  75th %ile:    {days[3*len(days)//4]:6.1f}")
    print(f"  95th %ile:    {days[int(len(days)*0.95)]:6.1f}")
    print(f"  Max:          {max(days):6.1f}")
    print(f"  Mean:         {sum(days)/len(days):6.1f}")

    # Officer responses
    responses = [s['officer_response_count'] for s in samples]
    responses.sort()

    print("\nOfficer Response Count:")
    print(f"  Min:          {min(responses):6.1f}")
    print(f"  Median:       {responses[len(responses)//2]:6.1f}")
    print(f"  Max:          {max(responses):6.1f}")
    print(f"  Mean:         {sum(responses)/len(responses):6.1f}")

    # Confidence
    confidence = [s['confidence'] for s in samples]
    print("\nConfidence Scores:")
    print(f"  Min:          {min(confidence):6.2f}")
    print(f"  Median:       {confidence[len(confidence)//2]:6.2f}")
    print(f"  Max:          {max(confidence):6.2f}")
    print(f"  Mean:         {sum(confidence)/len(confidence):6.2f}")


def main():
    """Main visualization function."""
    data_path = Path(__file__).parent / "data" / "synthetic" / "synthetic_lapse_cases.json"

    print("=" * 70)
    print("SYNTHETIC LAPSE DATA - VISUALIZATIONS")
    print("=" * 70)
    print(f"Data: {data_path}")

    if not data_path.exists():
        print(f"\nERROR: Data file not found: {data_path}")
        return 1

    # Load data
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    samples = data['samples']
    metadata = data['metadata']

    print(f"\nLoaded: {len(samples)} samples")
    print(f"Generated: {metadata['generation_date']}")

    # 1. Lapse distribution
    lapse_counts = Counter(s['lapse_type'] for s in samples)
    create_bar_chart(dict(lapse_counts), "LAPSE TYPE DISTRIBUTION")

    # 2. Department distribution
    dept_counts = Counter(s['department_code'] for s in samples)
    create_bar_chart(dict(dept_counts), "DEPARTMENT DISTRIBUTION")

    # 3. District distribution
    district_counts = Counter(s['district_name'] for s in samples)
    create_bar_chart(dict(district_counts), "DISTRICT DISTRIBUTION (Top 15)")

    # 4. Escalation level distribution
    escalation_counts = Counter(s['escalation_level'] for s in samples)
    create_bar_chart(dict(escalation_counts), "ESCALATION LEVEL DISTRIBUTION")

    # 5. Days histogram
    days = [s['days_to_resolve'] for s in samples]
    create_histogram(days, "DAYS TO RESOLVE - DISTRIBUTION", bins=12)

    # 6. Summary statistics
    print_summary_stats(samples)

    # 7. Correlation analysis
    analyze_correlations(samples)

    # 8. Data quality indicators
    print("\n" + "=" * 70)
    print("DATA QUALITY INDICATORS")
    print("=" * 70)

    # Check for expected patterns
    checks = []

    # Top lapse should be "GRA did not speak"
    top_lapse = lapse_counts.most_common(1)[0]
    if "GRA did not speak" in top_lapse[0]:
        checks.append(("OK", "Top lapse is 'GRA did not speak to citizen' (expected)"))
    else:
        checks.append(("FAIL", f"Top lapse is '{top_lapse[0]}' (unexpected)"))

    # Revenue should be top department
    top_dept = dept_counts.most_common(1)[0]
    if top_dept[0] == 'REVENUE':
        checks.append(("OK", "Top department is Revenue (expected)"))
    else:
        checks.append(("FAIL", f"Top department is {top_dept[0]} (unexpected)"))

    # Mean days should be 15-25
    mean_days = sum(days) / len(days)
    if 15 <= mean_days <= 25:
        checks.append(("OK", f"Mean days = {mean_days:.1f} (expected range: 15-25)"))
    else:
        checks.append(("WARN", f"Mean days = {mean_days:.1f} (outside expected 15-25)"))

    # All samples should have confidence 0.85-0.95
    confidence = [s['confidence'] for s in samples]
    if all(0.85 <= c <= 0.95 for c in confidence):
        checks.append(("OK", "All confidence scores in range [0.85, 0.95]"))
    else:
        checks.append(("FAIL", "Some confidence scores out of range"))

    # No missing values
    required_fields = ['id', 'department_code', 'lapse_type', 'days_to_resolve']
    all_complete = all(all(f in s for f in required_fields) for s in samples)
    if all_complete:
        checks.append(("OK", "All samples have required fields"))
    else:
        checks.append(("FAIL", "Some samples missing required fields"))

    for symbol, message in checks:
        print(f"  [{symbol}] {message}")

    print("\n" + "=" * 70)
    print("Visualization complete!")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
