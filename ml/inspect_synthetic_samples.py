"""
Quick inspection script to view synthetic Telugu samples by department.
Usage: python inspect_synthetic_samples.py [department_name]
"""

import json
import sys
import random
from pathlib import Path
from collections import defaultdict

# Fix Windows console encoding for Telugu text
if sys.platform == 'win32':
    import codecs
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')


def load_samples(filepath):
    """Load synthetic samples from JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data


def print_sample(sample, index=None):
    """Pretty print a single sample."""
    if index is not None:
        print(f"\n{'='*70}")
        print(f"Sample #{index + 1}")
        print('='*70)

    print(f"\nID: {sample['id']}")
    print(f"Department: {sample['department']}")
    print(f"Department (Telugu): {sample.get('department_telugu', 'N/A')}")
    print(f"Category: {sample.get('category', 'N/A')}")
    print(f"Source Type: {sample['source_type']}")
    print(f"Confidence: {sample['confidence']}")

    if sample.get('is_synthetic'):
        print(f"Synthetic: YES")
        if 'variation_type' in sample:
            print(f"Variation Type: {sample['variation_type']}")

    print(f"\nTelugu Text:")
    print(f"  {sample['telugu_text']}")

    print(f"\nEnglish Translation:")
    print(f"  {sample['english_translation']}")


def show_department_samples(data, department_name, limit=5):
    """Show sample grievances for a specific department."""
    samples = data['samples']
    dept_samples = [s for s in samples if s['department'] == department_name]

    if not dept_samples:
        print(f"No samples found for department: {department_name}")
        print(f"\nAvailable departments:")
        for dept in sorted(set(s['department'] for s in samples)):
            count = len([s for s in samples if s['department'] == dept])
            print(f"  - {dept} ({count} samples)")
        return

    print(f"\n{'='*70}")
    print(f"Department: {department_name}")
    print(f"Total Samples: {len(dept_samples)}")
    print('='*70)

    # Show authentic samples first
    authentic = [s for s in dept_samples if not s.get('is_synthetic')]
    synthetic = [s for s in dept_samples if s.get('is_synthetic')]

    print(f"\nAuthentic: {len(authentic)}, Synthetic: {len(synthetic)}")

    # Show mix of authentic and synthetic
    to_show = []
    if authentic:
        to_show.extend(random.sample(authentic, min(2, len(authentic))))
    if synthetic:
        to_show.extend(random.sample(synthetic, min(limit - len(to_show), len(synthetic))))

    for i, sample in enumerate(to_show[:limit]):
        print_sample(sample, i)


def show_statistics(data):
    """Show overall statistics."""
    metadata = data['metadata']
    stats = data['statistics']
    dept_dist = data['department_distribution']

    print("\n" + "="*70)
    print("SYNTHETIC TELUGU GRIEVANCE DATASET STATISTICS")
    print("="*70)

    print(f"\nGeneration Date: {metadata['generation_date']}")
    print(f"Total Samples: {metadata['total_samples']}")
    print(f"  - Authentic: {metadata['authentic_samples']}")
    print(f"  - Synthetic: {metadata['synthetic_samples']}")
    print(f"\nAverage Confidence: {stats['average_confidence']}")
    print(f"Categories Covered: {stats['categories_covered']}")
    print(f"Department Targets Met: {metadata['department_targets_met']}/10")

    print(f"\n\nSamples by Source Type:")
    for source_type, count in sorted(stats['samples_per_source_type'].items()):
        print(f"  {source_type}: {count}")

    print(f"\n\nTop 15 Departments by Sample Count:")
    sorted_depts = sorted(dept_dist.items(), key=lambda x: x[1], reverse=True)
    for dept, count in sorted_depts[:15]:
        print(f"  {dept}: {count}")

    print(f"\n\nAugmentation Methods Used:")
    for method in metadata['augmentation_methods']:
        print(f"  - {method}")


def show_random_samples(data, count=10):
    """Show random samples from the dataset."""
    samples = data['samples']
    random_samples = random.sample(samples, min(count, len(samples)))

    print(f"\n{'='*70}")
    print(f"RANDOM SAMPLE INSPECTION ({count} samples)")
    print('='*70)

    for i, sample in enumerate(random_samples):
        print_sample(sample, i)


def main():
    """Main entry point."""
    # File path
    base_dir = Path(__file__).parent
    data_file = base_dir / "data" / "synthetic" / "synthetic_telugu_grievances.json"

    if not data_file.exists():
        print(f"ERROR: Data file not found: {data_file}")
        print("Run generate_synthetic_telugu_data.py first!")
        return 1

    # Load data
    data = load_samples(data_file)

    # Parse arguments
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == "stats":
            show_statistics(data)

        elif command == "random":
            count = int(sys.argv[2]) if len(sys.argv) > 2 else 10
            show_random_samples(data, count)

        elif command == "list":
            # List all departments
            samples = data['samples']
            dept_dist = data['department_distribution']
            print("\nAvailable Departments:")
            for dept in sorted(dept_dist.keys()):
                count = dept_dist[dept]
                print(f"  {dept}: {count} samples")

        else:
            # Treat as department name
            department = command.title()
            # Try exact match first
            if department in data['department_distribution']:
                show_department_samples(data, department)
            else:
                # Try partial match
                matches = [d for d in data['department_distribution'].keys()
                          if command.lower() in d.lower()]
                if matches:
                    print(f"Did you mean one of these?")
                    for match in matches:
                        print(f"  - {match}")
                    print(f"\nShowing samples for: {matches[0]}")
                    show_department_samples(data, matches[0])
                else:
                    print(f"Department not found: {department}")
                    print("\nUse 'python inspect_synthetic_samples.py list' to see all departments")
    else:
        # Default: show statistics
        show_statistics(data)
        print("\n\nUSAGE:")
        print("  python inspect_synthetic_samples.py stats        - Show statistics")
        print("  python inspect_synthetic_samples.py random [N]   - Show N random samples")
        print("  python inspect_synthetic_samples.py list         - List all departments")
        print("  python inspect_synthetic_samples.py <dept_name>  - Show samples for department")
        print("\nEXAMPLES:")
        print("  python inspect_synthetic_samples.py Revenue")
        print("  python inspect_synthetic_samples.py Agriculture")
        print("  python inspect_synthetic_samples.py random 5")

    return 0


if __name__ == "__main__":
    exit(main())
