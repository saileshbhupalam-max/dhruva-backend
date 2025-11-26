#!/usr/bin/env python3
"""
Extract all unique district names from government data sources.

This script:
1. Reads audit_reports.json and extracts all district references
2. Reads the existing seed_districts.sql file
3. Compares what districts are in government data vs seed data
4. Creates district_analysis.json with all unique districts found
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Set

# District name variations and mappings
# Map variants to the official seed name
DISTRICT_VARIATIONS = {
    "Ananthapur": "Anantapur",  # Government docs use "Ananthapur", seed uses "Anantapur"
    "YSR Kadapa": "Kadapa",  # Government docs use "YSR Kadapa", seed uses "Kadapa"
    "Cuddapah": "Kadapa",
    "Y.S.R. Kadapa": "Kadapa",
    "NTR": "NTR District",  # Government docs sometimes use "NTR" shorthand
}

# Standard district codes
DISTRICT_CODES = {
    "Ananthapur": "ATP",
    "Chittoor": "CHT",
    "East Godavari": "EGD",
    "Guntur": "GNT",
    "YSR Kadapa": "KDP",
    "Krishna": "KRS",
    "Kurnool": "KNL",
    "Nellore": "NLR",
    "Prakasam": "PKM",
    "Srikakulam": "SKM",
    "Visakhapatnam": "VSP",
    "Vizianagaram": "VZG",
    "West Godavari": "WGD",
    "Alluri Sitharama Raju": "ASR",
    "Anakapalli": "ANA",
    "Annamaya": "ANM",
    "Bapatla": "BAP",
    "Eluru": "ELR",
    "Kakinada": "KKN",
    "Konaseema": "KNS",
    "NTR District": "NTR",
    "Palnadu": "PLN",
    "Parvathipuram Manyam": "PVM",
    "Sri Potti Sriramulu Nellore": "SPSR",
    "Sri Satya Sai": "SSS",
    "Tirupati": "TPT",
}


def extract_districts_from_audit_json(file_path: Path) -> Dict[str, List[str]]:
    """Extract all district names from audit_reports.json."""
    print(f"\n[*] Reading {file_path.name}...")

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    districts_found = {}

    # Extract from direct district field in Guntur audit
    if "guntur_audit" in data and "district" in data["guntur_audit"]:
        district = data["guntur_audit"]["district"]
        districts_found[district] = ["guntur_audit.district"]

    # Extract from district highlights in constituency audit
    if "other_audits" in data:
        for audit in data["other_audits"]:
            if audit.get("source_type") == "multi_district_report":
                if "district_highlights" in audit:
                    for district_name in audit["district_highlights"].keys():
                        if district_name not in districts_found:
                            districts_found[district_name] = []
                        districts_found[district_name].append(
                            f"{audit['name']}.district_highlights"
                        )

            if "Ananthapur" in audit.get("name", ""):
                district = "Ananthapur"
                if district not in districts_found:
                    districts_found[district] = []
                districts_found[district].append(f"{audit['name']}")

            if "West Godavari" in audit.get("name", ""):
                district = "West Godavari"
                if district not in districts_found:
                    districts_found[district] = []
                districts_found[district].append(f"{audit['name']}")

    print(f"  [+] Found {len(districts_found)} districts")
    return districts_found


def extract_districts_from_seed_sql(file_path: Path) -> Dict[str, str]:
    """Extract district names and codes from seed_districts.sql."""
    print(f"\n[*] Reading {file_path.name}...")

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Pattern: (gen_random_uuid(), 'CODE', 'District Name', NOW(), NOW())
    # Extract lines with INSERT VALUES
    pattern = r"'([A-Z]{2,10})',\s*'([^']+)',\s*NOW\(\)"
    matches = re.findall(pattern, content)

    districts = {}
    for code, name in matches:
        districts[name] = code

    print(f"  [+] Found {len(districts)} districts in seed data")
    return districts


def normalize_district_name(name: str) -> str:
    """Normalize district name for comparison."""
    # Apply known variations
    if name in DISTRICT_VARIATIONS:
        return DISTRICT_VARIATIONS[name]
    return name


def generate_district_code(district_name: str) -> str:
    """Generate a district code if not already defined."""
    if district_name in DISTRICT_CODES:
        return DISTRICT_CODES[district_name]

    # Generate code from first letters of words
    words = district_name.split()
    if len(words) == 1:
        # Single word: take first 3 letters
        return district_name[:3].upper()
    else:
        # Multiple words: take first letter of each
        code = "".join(word[0].upper() for word in words if word)
        # If too short, add more letters from first word
        if len(code) < 3:
            code += district_name.split()[0][len(code):3].upper()
        return code[:10]  # Max 10 chars


def main():
    """Main extraction logic."""
    print("\n" + "="*70)
    print("  DISTRICT EXTRACTION & ANALYSIS")
    print("="*70)

    # Define paths
    base_path = Path(__file__).parent.parent
    audit_json_path = base_path / "ml" / "data" / "extracted" / "audit_reports.json"
    seed_sql_path = base_path / "app" / "scripts" / "seed_districts.sql"
    output_path = base_path / "ml" / "district_analysis.json"

    # Extract districts from both sources
    govt_districts = extract_districts_from_audit_json(audit_json_path)
    seed_districts = extract_districts_from_seed_sql(seed_sql_path)

    # Normalize district names
    normalized_govt = {normalize_district_name(d): sources for d, sources in govt_districts.items()}

    # Compare
    print("\n" + "="*70)
    print("  COMPARISON RESULTS")
    print("="*70)

    govt_set = set(normalized_govt.keys())
    seed_set = set(seed_districts.keys())

    in_govt_only = govt_set - seed_set
    in_seed_only = seed_set - govt_set
    in_both = govt_set & seed_set

    print(f"\nSummary:")
    print(f"  - Districts in government data: {len(govt_set)}")
    print(f"  - Districts in seed data: {len(seed_set)}")
    print(f"  - Districts in both: {len(in_both)}")
    print(f"  - Districts only in govt data: {len(in_govt_only)}")
    print(f"  - Districts only in seed data: {len(in_seed_only)}")

    if in_govt_only:
        print(f"\n[!] Districts in government data but NOT in seed:")
        for district in sorted(in_govt_only):
            print(f"    - {district}")

    if in_seed_only:
        print(f"\n[+] Districts in seed data but not found in government data:")
        for district in sorted(in_seed_only):
            print(f"    - {district} ({seed_districts[district]})")

    # Create comprehensive analysis
    all_districts = {}

    # Add all districts from seed data (authoritative source)
    for district_name, district_code in seed_districts.items():
        all_districts[district_name] = {
            "district_code": district_code,
            "district_name": district_name,
            "in_seed_data": True,
            "in_govt_data": district_name in govt_set,
            "govt_data_sources": normalized_govt.get(district_name, []),
        }

    # Add any districts only in government data
    for district_name in in_govt_only:
        all_districts[district_name] = {
            "district_code": generate_district_code(district_name),
            "district_name": district_name,
            "in_seed_data": False,
            "in_govt_data": True,
            "govt_data_sources": normalized_govt[district_name],
        }

    # Create output
    output_data = {
        "extraction_date": "2025-11-25",
        "total_unique_districts": len(all_districts),
        "summary": {
            "in_seed_data": len(seed_set),
            "in_govt_data": len(govt_set),
            "in_both": len(in_both),
            "only_in_govt": len(in_govt_only),
            "only_in_seed": len(in_seed_only),
        },
        "districts": all_districts,
        "notes": [
            "Seed data is the authoritative source with 26 districts",
            "Government audit data references a subset of these districts",
            "All 26 seed districts are valid for Andhra Pradesh (2024)",
            "District codes follow standard abbreviation conventions",
        ],
    }

    # Write output
    print(f"\n[*] Writing analysis to {output_path.name}...")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"  [+] Analysis saved to: {output_path}")

    print("\n" + "="*70)
    print("  EXTRACTION COMPLETE")
    print("="*70)
    print(f"\n[+] Total unique districts: {len(all_districts)}")
    print(f"[+] Output file: {output_path}")
    print()


if __name__ == "__main__":
    main()
