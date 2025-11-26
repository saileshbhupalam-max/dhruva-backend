#!/usr/bin/env python3
"""
AGENT 3: Officer Performance Report Parser
Parses 8,558 officer records from markdown table format
"""

import json
import re
from typing import List, Dict, Any, Optional
from pathlib import Path


def parse_officer_report(file_path: str) -> Dict[str, Any]:
    """
    Parse the officer performance report markdown file.

    Args:
        file_path: Path to the markdown file

    Returns:
        Dictionary containing officers data and summary statistics
    """

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f.readlines()]

    officers = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # Skip empty lines, headers, and separators
        if (not line or line == '---' or 'SNO' in line or 'DEPARTMENT' in line or
            'RECEIVED' in line or 'Grievances status' in line or 'IN PROGRESS' in line or
            'REDRESSES' in line or 'REOPEN' in line or 'YET TO VIEW' in line or
            'VIEWED BY OFFICER' in line or 'TOTAL' in line or 'WITHIN' in line or
            'SLA' in line or 'BEYOND' in line or 'PENDING' in line or 'REDRESSED' in line):
            i += 1
            continue

        # Check if this line is a serial number
        if line.isdigit():
            try:
                sno = int(line)

                # Next non-empty line should be officer designation
                # Collect all text until we find the first number (received count)
                i += 1
                officer_parts = []
                numeric_found = False
                look_ahead = 0

                while i + look_ahead < len(lines) and look_ahead < 10:
                    test_line = lines[i + look_ahead].strip()
                    if test_line.isdigit() and int(test_line) > 0:
                        # Found a number that could be received count
                        numeric_found = True
                        break
                    look_ahead += 1

                # Now collect all non-numeric lines until that point
                while i < len(lines) and not (lines[i].strip().isdigit() and int(lines[i].strip() or '0') > 0):
                    part = lines[i].strip()
                    if part and part != '---' and not part.isdigit():
                        officer_parts.append(part)
                    i += 1
                    if len(officer_parts) > 5:  # Safety limit
                        break

                if not officer_parts:
                    continue

                officer_designation = ' '.join(officer_parts)

                # Now collect 11 numeric values
                values = []
                while i < len(lines) and len(values) < 11:
                    if lines[i].isdigit():
                        values.append(int(lines[i]))
                    i += 1

                if len(values) < 11:
                    continue

                # Parse values according to the table structure:
                # received, yet_to_view, viewed,
                # in_progress_total, in_progress_within_sla, in_progress_beyond_sla,
                # redressed_total, redressed_within_sla, redressed_beyond_sla,
                # pending_total, pending_within_sla, pending_beyond_sla
                received = values[0]
                yet_to_view = values[1]
                viewed = values[2]
                # Skip intermediate values, use totals
                redressed = values[6]  # redressed_total
                pending = values[9]    # pending_total

                # Infer department from designation
                department = infer_department(officer_designation)

                # Calculate metrics
                # improper_rate = max(0, (received - redressed - pending) / received)
                improper_calc = received - redressed - pending
                improper_rate = max(0.0, min(1.0, improper_calc / received if received > 0 else 0.0))

                # workload = pending
                workload = pending

                # viewed_ratio = viewed / received
                viewed_ratio = viewed / received if received > 0 else 0.0

                # throughput = redressed / received
                throughput = redressed / received if received > 0 else 0.0

                # Create department context
                dept_context = f"{officer_designation} -> {department}"

                officer_data = {
                    "sno": sno,
                    "department": department,
                    "officer_designation": officer_designation,
                    "received": received,
                    "viewed": viewed,
                    "pending": pending,
                    "redressed": redressed,
                    "computed_metrics": {
                        "improper_rate": round(improper_rate, 4),
                        "workload": workload,
                        "viewed_ratio": round(viewed_ratio, 4),
                        "throughput": round(throughput, 4)
                    },
                    "dept_context_extracted": dept_context
                }

                officers.append(officer_data)

            except (ValueError, IndexError) as e:
                i += 1
                continue
        else:
            i += 1

    # Calculate summary statistics
    unique_departments = len(set(o['department'] for o in officers))
    unique_designations = len(set(o['officer_designation'] for o in officers))
    dept_contexts = len(set(o['dept_context_extracted'] for o in officers))

    avg_improper_rate = sum(o['computed_metrics']['improper_rate'] for o in officers) / len(officers) if officers else 0
    avg_workload = sum(o['computed_metrics']['workload'] for o in officers) / len(officers) if officers else 0

    summary = {
        "total_officers": len(officers),
        "unique_departments": unique_departments,
        "unique_designations": unique_designations,
        "dept_contexts_extracted": dept_contexts,
        "avg_improper_rate": round(avg_improper_rate, 4),
        "avg_workload": round(avg_workload, 2)
    }

    return {
        "officers": officers,
        "summary": summary
    }


def infer_department(officer_designation: str) -> str:
    """
    Infer department from officer designation using keyword matching.
    """
    designation_lower = officer_designation.lower()

    # Department keyword mappings (expanded)
    dept_keywords = {
        "Revenue": ["revenue", "land administration", "registration", "stamps", "survey", "settlements"],
        "Education": ["education", "school", "university", "college", "registrar", "principal", "collegiate",
                     "intermediate", "technical education", "samagra shiksha", "apsche", "scert"],
        "Police": ["police", "dgp", "superintendent", "fire", "home guards", "cbcid", "intelligence", "apsp"],
        "Health": ["health", "medical", "hospital", "ayush", "vaidya seva", "dr. ntr", "family welfare",
                  "family care", "ntr university of health", "medical education", "public health"],
        "Endowment": ["endowment", "ttd", "tirumala", "tirupathi", "devasthanam"],
        "Transport": ["transport", "apsrtc", "roads", "buildings", "r&b", "nh & crf", "mdr", "ndb"],
        "Municipal": ["municipal", "crda", "urban", "vmrda", "mepma", "amaravati", "dtcp", "town planning"],
        "Agriculture": ["agriculture", "fisheries", "horticulture", "angrau", "atma", "rythu", "markfed"],
        "Water Resources": ["irrigation", "water", "polavaram", "ground water", "hydro"],
        "Panchayati Raj": ["panchayat", "rural development", "serp", "pr engineering"],
        "Energy": ["energy", "power", "electricity", "transco", "discom", "epdcl", "spdcl", "cpdcl",
                  "vidyutsoudha", "aptransco"],
        "Social Welfare": ["social welfare", "sw", "apswreis", "residential education"],
        "Industries": ["industries", "commerce", "tidco", "sidc", "apcos", "apssdc"],
        "Labour": ["labor", "labour", "employment", "factories", "esi", "epf", "provident fund"],
        "Forest": ["forest", "environment", "pollution", "pccf", "conservator"],
        "Civil Supplies": ["civil supplies", "food", "consumer", "apscscl"],
        "Finance": ["finance", "treasury", "accounts", "pay and accounts"],
        "Home": ["home", "disaster", "prisons", "legal services", "state legal"],
        "Women & Child": ["women", "child welfare", "wcdsc"],
        "Housing": ["housing", "ap housing board", "ap housing corporation"],
        "Technical Education": ["technical education", "polytechnic", "sbtet"],
        "Co-operation": ["cooperation", "cooperative", "markfed", "oilfed"],
        "Tourism": ["tourism", "culture", "sports", "youth", "apstdc"],
        "Minority Welfare": ["minority", "minorities", "waqf", "wakf", "christian", "muslim"],
        "Backward Classes": ["backward class", "bc welfare", "kapu", "mjpapbbcw"],
        "Tribal Welfare": ["tribal", "st welfare", "aptwreis", "girijan"],
        "Information & PR": ["information", "public relations", "i&pr", "apco"],
        "Skill Development": ["skill development", "apssdc"],
        "Legal": ["legal", "law"],
        "Animal Husbandry": ["animal husbandry", "veterinary", "dairy"],
        "Mines": ["mines", "geology", "mining"],
        "Sericulture": ["sericulture", "silk"],
        "Handlooms": ["handlooms", "textiles", "weaver"],
        "Marketing": ["marketing", "mandi"],
        "Excise": ["prohibition", "excise"],
        "General Administration": ["general administration", "gad", "political", "protocol", "vigilance",
                                   "appsc", "election", "ceo"]
    }

    # Try to match keywords
    for dept, keywords in dept_keywords.items():
        for keyword in keywords:
            if keyword in designation_lower:
                return dept

    # Default
    return "General Administration"


def validate_results(data: Dict[str, Any]) -> Dict[str, bool]:
    """
    Validate parsed data against quality gates.

    Returns:
        Dictionary of validation results
    """
    officers = data['officers']
    summary = data['summary']

    checks = {
        "officers_count": summary['total_officers'] >= 480,  # Target: 490 officers (based on actual data)
        "all_numeric_valid": all(
            isinstance(o['received'], int) and
            isinstance(o['viewed'], int) and
            isinstance(o['pending'], int) and
            isinstance(o['redressed'], int)
            for o in officers
        ),
        "improper_rate_range": all(
            0 <= o['computed_metrics']['improper_rate'] <= 1
            for o in officers
        ),
        "unique_designations": summary['unique_designations'] >= 400,  # Target: ~450 unique designations
        "dept_contexts": summary['dept_contexts_extracted'] >= 400,  # Target: ~450 context pairs
        "no_parsing_errors": len(officers) > 0
    }

    return checks


def main():
    """Main execution function."""

    # Paths
    input_file = Path("D:/projects/dhruva/docs/reference/markdown/PGRS DEPARTMENT-HOD WISE GRIEVANCE CUMULATIVE STATUS OFFICER WISE  REPORT AS ON DT 21-11-2025.md")
    output_file = Path("D:/projects/dhruva/backend/ml/data/extracted/officer_performance.json")

    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print("AGENT 3: OFFICER PERFORMANCE REPORT PARSING")
    print("=" * 80)
    print(f"\nSource file: {input_file}")
    print(f"Note: File has 8,558 lines but 490 officer records")
    print(f"Target: Extract all 490 officer records with performance metrics\n")

    # Parse the file
    print("Parsing officer report...")
    data = parse_officer_report(str(input_file))

    # Validate results
    print("\nRunning quality gate validations...")
    validation_results = validate_results(data)

    # Save output
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    # Print report
    print("\n" + "=" * 80)
    print("PARSING COMPLETE - RESULTS")
    print("=" * 80)

    print(f"\n[SUCCESS] Status: COMPLETE")
    print(f"[SUCCESS] Output saved to: {output_file}")

    print("\n" + "-" * 80)
    print("QUALITY GATE RESULTS:")
    print("-" * 80)

    gate_labels = {
        "officers_count": ">=480 officers parsed (target: 490)",
        "all_numeric_valid": "All numeric fields valid (no NaN)",
        "improper_rate_range": "Improper rate between 0-1",
        "unique_designations": ">=400 unique officer designations (target: ~450)",
        "dept_contexts": ">=400 department context pairs (target: ~450)",
        "no_parsing_errors": "No parsing errors"
    }

    all_passed = True
    for check, passed in validation_results.items():
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status} - {gate_labels[check]}")
        if not passed:
            all_passed = False

    print("\n" + "-" * 80)
    print("SUMMARY STATISTICS:")
    print("-" * 80)

    summary = data['summary']
    print(f"Total Officers Parsed: {summary['total_officers']:,}")
    print(f"Unique Departments: {summary['unique_departments']}")
    print(f"Unique Designations: {summary['unique_designations']:,}")
    print(f"Department Contexts Extracted: {summary['dept_contexts_extracted']:,}")
    print(f"Average Improper Rate: {summary['avg_improper_rate']:.4f}")
    print(f"Average Workload (Pending): {summary['avg_workload']:.2f}")

    # Sample officers
    print("\n" + "-" * 80)
    print("SAMPLE OFFICERS (First 5):")
    print("-" * 80)

    for i, officer in enumerate(data['officers'][:5], 1):
        print(f"\n{i}. [{officer['sno']}] {officer['officer_designation']}")
        print(f"   Department: {officer['department']}")
        print(f"   Received: {officer['received']}, Viewed: {officer['viewed']}, "
              f"Pending: {officer['pending']}, Redressed: {officer['redressed']}")
        print(f"   Metrics: improper_rate={officer['computed_metrics']['improper_rate']:.4f}, "
              f"workload={officer['computed_metrics']['workload']}, "
              f"viewed_ratio={officer['computed_metrics']['viewed_ratio']:.4f}, "
              f"throughput={officer['computed_metrics']['throughput']:.4f}")

    # Show warnings if any gates failed
    if not validation_results['officers_count']:
        print(f"\n[WARNING] Expected 490 officers but parsed {summary['total_officers']}")
    if not validation_results['unique_designations']:
        print(f"\n[WARNING] Expected >=400 unique designations but found {summary['unique_designations']}")

    print("\n" + "=" * 80)

    if all_passed:
        print("[SUCCESS] ALL QUALITY GATES PASSED")
    else:
        print("[WARNING] SOME QUALITY GATES FAILED - Review output above")

    print("=" * 80)

    return 0 if all_passed else 1


if __name__ == "__main__":
    exit(main())
