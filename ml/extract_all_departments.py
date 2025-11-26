#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extract ALL unique department names from government data sources.

This script:
1. Reads all JSON data files
2. Extracts unique department names from multiple sources
3. Creates department analysis with frequencies and sources
4. Generates department mapping (govt name -> normalized name)
5. Creates comprehensive seed script for ALL departments
"""

import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set, Tuple

# Set UTF-8 encoding for stdout on Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')


# Paths
SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR / "data" / "extracted"
PGRS_BOOK_FILE = DATA_DIR / "pgrs_book_keywords.json"
OFFICER_FILE = DATA_DIR / "officer_performance.json"
CALL_CENTER_FILE = DATA_DIR / "call_center_satisfaction.json"
AUDIT_FILE = DATA_DIR / "audit_reports.json"

OUTPUT_ANALYSIS_FILE = SCRIPT_DIR / "department_analysis.json"
OUTPUT_MAPPING_FILE = SCRIPT_DIR / "department_mapping.json"
OUTPUT_SEED_FILE = SCRIPT_DIR.parent / "scripts" / "seed_all_departments.py"


def normalize_department_name(name: str) -> str:
    """Normalize department name for comparison."""
    # Remove parentheses content, extra spaces, punctuation
    normalized = re.sub(r'\([^)]*\)', '', name)
    normalized = re.sub(r'[,\-\.]', ' ', normalized)
    normalized = ' '.join(normalized.split())
    return normalized.strip().lower()


def create_dept_code(name: str) -> str:
    """Create abbreviated department code from name."""
    # Handle special cases first
    special_cases = {
        'revenue': 'REVENUE',
        'police': 'POLICE',
        'ccla': 'CCLA',
        'survey settlements and land records': 'SSLR',
        'survey settlements': 'SSLR',
        'endowment': 'ENDOW',
        'municipal administration': 'MUNI',
        'panchayat raj': 'PNCHRAJ',
        'panchayati raj': 'PNCHRAJ',
        'civil supplies': 'CIVIL_SUP',
        'school education': 'SCH_EDU',
        'higher education': 'HIGH_EDU',
        'health': 'HEALTH',
        'public health': 'PUB_HLTH',
        'agriculture': 'AGRI',
        'animal husbandry': 'ANI_HUSB',
        'roads and buildings': 'RNB',
        'water resources': 'WATER',
        'energy': 'ENERGY',
        'transport': 'TRANS',
        'labour': 'LABOUR',
        'tribal welfare': 'TRIBAL',
        'social welfare': 'SOC_WELF',
        'backward classes': 'BC_WELF',
        'minorities': 'MINOR',
        'women': 'WOMEN',
        'child welfare': 'CHILD',
        'disabled': 'DISABLED',
        'disaster': 'DISASTER',
        'environment': 'ENVIRON',
        'forest': 'FOREST',
        'finance': 'FINANCE',
        'industries': 'INDUST',
        'commerce': 'COMM',
        'housing': 'HOUSING',
        'skills': 'SKILLS',
        'training': 'TRAIN',
        'employment': 'EMPLOY',
        'registration': 'REG',
        'stamps': 'STAMPS',
        'law': 'LAW',
    }

    name_lower = normalize_department_name(name)

    # Check special cases
    for key, code in special_cases.items():
        if key in name_lower:
            return code

    # Generate from words
    words = name_lower.split()
    if len(words) == 1:
        return words[0][:8].upper()
    elif len(words) == 2:
        return (words[0][:4] + words[1][:4]).upper()
    else:
        # Take first letter of each word, max 8 chars
        code = ''.join(w[0] for w in words if w)[:8].upper()
        return code if code else name[:8].upper()


def load_pgrs_book_departments() -> List[Dict]:
    """Extract departments from PGRS book keywords."""
    print(f"Loading PGRS Book from: {PGRS_BOOK_FILE}")
    with open(PGRS_BOOK_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    departments = []
    for dept in data.get('departments', []):
        departments.append({
            'source': 'pgrs_book_keywords',
            'name_english': dept.get('name_english'),
            'name_telugu': dept.get('name_telugu'),
            'count': 1,
            'has_telugu': True
        })

    print(f"  -> Found {len(departments)} departments")
    return departments


def load_officer_performance_departments() -> List[Dict]:
    """Extract departments from officer performance data."""
    print(f"Loading Officer Performance from: {OFFICER_FILE}")
    with open(OFFICER_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    dept_counts = defaultdict(int)
    for officer in data.get('officers', []):
        dept_name = officer.get('department')
        if dept_name:
            dept_counts[dept_name] += 1

    departments = [
        {
            'source': 'officer_performance',
            'name_english': dept,
            'name_telugu': None,
            'count': count,
            'has_telugu': False
        }
        for dept, count in dept_counts.items()
    ]

    print(f"  -> Found {len(departments)} unique departments ({sum(dept_counts.values())} officers)")
    return departments


def load_call_center_departments() -> List[Dict]:
    """Extract departments from call center satisfaction data."""
    print(f"Loading Call Center Satisfaction from: {CALL_CENTER_FILE}")
    with open(CALL_CENTER_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    departments = []
    for dept in data.get('departments', []):
        dept_name = dept.get('department')
        if dept_name:
            departments.append({
                'source': 'call_center_satisfaction',
                'name_english': dept_name,
                'name_telugu': None,
                'count': dept.get('total_feedback', 1),
                'has_telugu': False
            })

    print(f"  -> Found {len(departments)} departments")
    return departments


def load_audit_departments() -> List[Dict]:
    """Extract departments from audit reports."""
    print(f"Loading Audit Reports from: {AUDIT_FILE}")
    with open(AUDIT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    dept_set = set()

    # Extract from Guntur audit department_breakdown
    guntur = data.get('guntur_audit', {})
    dept_breakdown = guntur.get('department_breakdown', {})
    for dept_name in dept_breakdown.keys():
        dept_set.add(dept_name)

    # Extract from other audits
    for audit in data.get('other_audits', []):
        if audit.get('source_type') == 'district_department_analysis':
            dept_perf = audit.get('department_performance', {})
            for dept_key in dept_perf.keys():
                # Convert underscore names back to spaces
                dept_name = dept_key.replace('_', ' ').title()
                dept_set.add(dept_name)

    departments = [
        {
            'source': 'audit_reports',
            'name_english': dept,
            'name_telugu': None,
            'count': 1,
            'has_telugu': False
        }
        for dept in dept_set
    ]

    print(f"  -> Found {len(departments)} departments")
    return departments


def merge_departments(all_depts: List[Dict]) -> Dict:
    """Merge departments from all sources, handling name variations."""
    print("\nMerging departments from all sources...")

    # Group by normalized name
    normalized_map = defaultdict(lambda: {
        'names': [],
        'telugu_names': set(),
        'sources': set(),
        'total_count': 0,
        'original_names': []
    })

    for dept in all_depts:
        name_eng = dept['name_english']
        if not name_eng:
            continue

        normalized = normalize_department_name(name_eng)

        normalized_map[normalized]['names'].append(name_eng)
        normalized_map[normalized]['original_names'].append(name_eng)
        normalized_map[normalized]['sources'].add(dept['source'])
        normalized_map[normalized]['total_count'] += dept['count']

        if dept.get('name_telugu'):
            normalized_map[normalized]['telugu_names'].add(dept['name_telugu'])

    # Choose best name for each normalized group
    merged = {}
    for norm_name, data in normalized_map.items():
        # Pick the most common full name (or first if tie)
        from collections import Counter
        name_counter = Counter(data['names'])
        best_name = name_counter.most_common(1)[0][0]

        # Pick telugu name if available
        telugu_name = list(data['telugu_names'])[0] if data['telugu_names'] else None

        merged[norm_name] = {
            'name_english': best_name,
            'name_telugu': telugu_name,
            'sources': list(data['sources']),
            'total_count': data['total_count'],
            'name_variations': list(set(data['original_names'])),
            'dept_code': create_dept_code(best_name)
        }

    print(f"  -> Merged into {len(merged)} unique departments")
    return merged


def create_department_mapping(merged_depts: Dict) -> Dict:
    """Create mapping from all name variations to normalized names."""
    print("\nCreating department name mapping...")

    mapping = {}
    for norm_name, data in merged_depts.items():
        canonical = data['name_english']

        # Map all variations to canonical name
        for variation in data['name_variations']:
            mapping[variation] = {
                'canonical_name': canonical,
                'dept_code': data['dept_code'],
                'name_telugu': data['name_telugu']
            }

    print(f"  -> Created {len(mapping)} name mappings")
    return mapping


def generate_seed_script(merged_depts: Dict) -> str:
    """Generate Python seed script for all departments."""
    print("\nGenerating seed script...")

    # Sort departments alphabetically
    sorted_depts = sorted(merged_depts.values(), key=lambda d: d['name_english'])

    script = '''#!/usr/bin/env python3
"""
Seed ALL departments from government data sources.

This script seeds ALL unique departments found across:
- PGRS Book Keywords (30 departments)
- Officer Performance data (40+ departments)
- Call Center Satisfaction (31 departments)
- Audit Reports (25+ departments)

Auto-generated from: backend/ml/extract_all_departments.py
"""

import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.models import Department
from app.core.config import settings


async def seed_all_departments():
    """Seed all departments found in government data."""

    # Create async engine
    engine = create_async_engine(
        settings.ASYNC_DATABASE_URL,
        echo=False,
    )

    # Create async session
    async_session = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    departments = [
'''

    # Add all departments
    for dept in sorted_depts:
        telugu = dept['name_telugu']
        telugu_str = f'"{telugu}"' if telugu else 'None'

        script += f'''        {{
            "dept_code": "{dept['dept_code']}",
            "dept_name": "{dept['name_english']}",
            "name_telugu": {telugu_str},
            "sla_days": 7,
        }},
'''

    script += '''    ]

    async with async_session() as session:
        print(f"Seeding {len(departments)} departments...")

        for dept_data in departments:
            # Check if exists
            from sqlalchemy import select
            stmt = select(Department).where(
                Department.dept_code == dept_data["dept_code"]
            )
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                print(f"  OK {dept_data['dept_code']} already exists")
            else:
                dept = Department(**dept_data)
                session.add(dept)
                print(f"  + Created {dept_data['dept_code']}: {dept_data['dept_name']}")

        await session.commit()
        print(f"\\nOK Seeded {len(departments)} departments successfully!")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_all_departments())
'''

    print(f"  -> Generated seed script for {len(sorted_depts)} departments")
    return script


def main():
    """Main execution."""
    print("=" * 80)
    print("EXTRACTING ALL UNIQUE DEPARTMENTS FROM GOVERNMENT DATA")
    print("=" * 80)

    # Load from all sources
    print("\n[1/6] Loading data from all sources...")
    all_depts = []
    all_depts.extend(load_pgrs_book_departments())
    all_depts.extend(load_officer_performance_departments())
    all_depts.extend(load_call_center_departments())
    all_depts.extend(load_audit_departments())

    print(f"\n  TOTAL: {len(all_depts)} department entries loaded")

    # Merge and deduplicate
    print("\n[2/6] Merging and deduplicating...")
    merged_depts = merge_departments(all_depts)

    # Create mapping
    print("\n[3/6] Creating department name mapping...")
    dept_mapping = create_department_mapping(merged_depts)

    # Generate seed script
    print("\n[4/6] Generating seed script...")
    seed_script = generate_seed_script(merged_depts)

    # Save analysis
    print("\n[5/6] Saving analysis...")
    OUTPUT_ANALYSIS_FILE.parent.mkdir(parents=True, exist_ok=True)

    analysis = {
        'metadata': {
            'total_unique_departments': len(merged_depts),
            'total_name_variations': len(dept_mapping),
            'sources': ['pgrs_book_keywords', 'officer_performance', 'call_center_satisfaction', 'audit_reports'],
            'extraction_date': '2025-11-25'
        },
        'departments': {
            norm: {
                **data,
                'sources': list(data['sources']),
            }
            for norm, data in merged_depts.items()
        }
    }

    with open(OUTPUT_ANALYSIS_FILE, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)
    print(f"  -> Saved: {OUTPUT_ANALYSIS_FILE}")

    # Save mapping
    with open(OUTPUT_MAPPING_FILE, 'w', encoding='utf-8') as f:
        json.dump(dept_mapping, f, indent=2, ensure_ascii=False)
    print(f"  -> Saved: {OUTPUT_MAPPING_FILE}")

    # Save seed script
    print("\n[6/6] Saving seed script...")
    OUTPUT_SEED_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_SEED_FILE, 'w', encoding='utf-8') as f:
        f.write(seed_script)
    print(f"  -> Saved: {OUTPUT_SEED_FILE}")

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"OK Found {len(merged_depts)} unique departments")
    print(f"OK Mapped {len(dept_mapping)} name variations")
    print(f"OK Generated seed script for {len(merged_depts)} departments")
    print(f"\nTop 10 departments by frequency:")

    sorted_by_count = sorted(merged_depts.values(), key=lambda d: d['total_count'], reverse=True)[:10]
    for i, dept in enumerate(sorted_by_count, 1):
        telugu = f" ({dept['name_telugu'][:20]}...)" if dept['name_telugu'] else ""
        print(f"  {i:2d}. {dept['dept_code']:12s} - {dept['name_english']}{telugu} (count: {dept['total_count']})")

    print(f"\nDepartments with Telugu names: {sum(1 for d in merged_depts.values() if d['name_telugu'])}")
    print(f"Departments without Telugu: {sum(1 for d in merged_depts.values() if not d['name_telugu'])}")

    print("\n" + "=" * 80)
    print("FILES CREATED:")
    print("=" * 80)
    print(f"1. {OUTPUT_ANALYSIS_FILE}")
    print(f"2. {OUTPUT_MAPPING_FILE}")
    print(f"3. {OUTPUT_SEED_FILE}")
    print("\nTo seed the database, run:")
    print(f"  python {OUTPUT_SEED_FILE}")
    print("=" * 80)


if __name__ == "__main__":
    main()
