#!/usr/bin/env python3
"""
Extract Training Data from ALL Docs Files
==========================================
Consolidates data from all markdown/json files in docs folder for ML training.
"""

import json
import re
from pathlib import Path
from collections import Counter
from datetime import datetime

BASE_DIR = Path(__file__).parent
DOCS_DIR = BASE_DIR.parent.parent / "docs"
OUTPUT_DIR = BASE_DIR / "data" / "extracted_docs"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def extract_petitioner_messages():
    """Extract official Telugu templates from MESSAGES_SENT_TO_PETITIONERS.json"""
    print("\n" + "="*60)
    print(" Extracting Petitioner Messages (Official Telugu Templates)")
    print("="*60)

    messages_file = DOCS_DIR / "reference" / "markdown" / "MESSAGES_SENT_TO_PETITIONERS.json"

    if not messages_file.exists():
        print(f"File not found: {messages_file}")
        return []

    with open(messages_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    templates = []

    for row in data.get("sheets", {}).get("Sheet1", {}).get("data", []):
        template = row.get("MESSAGE TO BE SENT", "")
        sample = row.get("SAMPLE MESSAGE", "")
        status = row.get("Grievance status", "")
        subcase = row.get("SUBCASE", "")

        if template and len(template) > 20:
            # Clean template
            template = template.replace("{#var#}", "[VARIABLE]")

            templates.append({
                "status": status,
                "subcase": subcase,
                "template_text": template,
                "sample_text": sample if sample else None,
                "language": "te",  # Telugu
                "type": "official_response"
            })

    print(f"Extracted {len(templates)} official Telugu templates")

    # Save
    output_file = OUTPUT_DIR / "official_telugu_templates.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "source": "MESSAGES_SENT_TO_PETITIONERS.json",
            "extracted_at": datetime.now().isoformat(),
            "count": len(templates),
            "templates": templates
        }, f, ensure_ascii=False, indent=2)

    print(f"Saved to: {output_file}")

    return templates


def extract_lapse_definitions():
    """Extract lapse definitions from Improper Redressal lapses.md"""
    print("\n" + "="*60)
    print(" Extracting Lapse Definitions")
    print("="*60)

    lapse_file = DOCS_DIR / "reference" / "markdown" / "Improper Redressal lapses.md"

    if not lapse_file.exists():
        print(f"File not found: {lapse_file}")
        return []

    with open(lapse_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract lapse types
    lapses = [
        {"id": 1, "type": "behavioral", "name": "GRA did not speak properly / scolded / used abusive language", "severity": "critical"},
        {"id": 2, "type": "behavioral", "name": "GRA threatened / pleaded / persuaded the applicant", "severity": "critical"},
        {"id": 3, "type": "behavioral", "name": "GRA took a bribe / asked for a bribe", "severity": "critical"},
        {"id": 4, "type": "behavioral", "name": "GRA did not work and involved political persons", "severity": "critical"},
        {"id": 5, "type": "behavioral", "name": "GRA intentionally avoided doing work", "severity": "critical"},
        {"id": 6, "type": "procedural", "name": "GRA did not speak directly with the citizen", "severity": "high"},
        {"id": 7, "type": "procedural", "name": "GRA did not provide the endorsement personally", "severity": "medium"},
        {"id": 8, "type": "procedural", "name": "GRA did not spend time explaining the issue", "severity": "medium"},
        {"id": 9, "type": "procedural", "name": "GRA gave WRONG/BLANK/NOT RELATED endorsement", "severity": "high"},
        {"id": 10, "type": "procedural", "name": "GRA uploaded improper enquiry photo/report", "severity": "high"},
        {"id": 11, "type": "procedural", "name": "GRA closed by forwarding to lower-level official", "severity": "high"},
        {"id": 12, "type": "procedural", "name": "GRA closed stating not under jurisdiction", "severity": "medium"},
    ]

    print(f"Extracted {len(lapses)} lapse definitions")

    # Save
    output_file = OUTPUT_DIR / "lapse_definitions.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "source": "Improper Redressal lapses.md",
            "extracted_at": datetime.now().isoformat(),
            "count": len(lapses),
            "lapses": lapses
        }, f, ensure_ascii=False, indent=2)

    print(f"Saved to: {output_file}")

    return lapses


def extract_department_list():
    """Extract department list from List of Depts with HOD.md"""
    print("\n" + "="*60)
    print(" Extracting Department List")
    print("="*60)

    dept_file = DOCS_DIR / "data_sets" / "markdown" / "List of Depts with  HOD.md"

    if not dept_file.exists():
        print(f"File not found: {dept_file}")
        return []

    with open(dept_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract department names using regex
    # Pattern: "Department Name" followed by "HOD" info
    dept_pattern = r'^\d+\.\s*([A-Za-z\s,&()]+?)(?:\s*-|\s*$)'

    departments = []
    lines = content.split('\n')

    for line in lines:
        # Simple extraction - look for numbered items
        if line.strip() and line[0].isdigit():
            # Clean up
            dept = line.strip()
            dept = re.sub(r'^\d+\.?\s*', '', dept)  # Remove number prefix
            dept = dept.split('-')[0].strip()  # Remove HOD part

            if dept and len(dept) > 3:
                departments.append(dept)

    # Deduplicate
    departments = list(set(departments))

    print(f"Extracted {len(departments)} departments")

    # Save
    output_file = OUTPUT_DIR / "department_list.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "source": "List of Depts with HOD.md",
            "extracted_at": datetime.now().isoformat(),
            "count": len(departments),
            "departments": departments
        }, f, ensure_ascii=False, indent=2)

    print(f"Saved to: {output_file}")

    return departments


def extract_grievance_statuses():
    """Extract all grievance status types from templates"""
    print("\n" + "="*60)
    print(" Extracting Grievance Statuses")
    print("="*60)

    messages_file = DOCS_DIR / "reference" / "markdown" / "MESSAGES_SENT_TO_PETITIONERS.json"

    if not messages_file.exists():
        return []

    with open(messages_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    statuses = set()
    subcases = set()

    for row in data.get("sheets", {}).get("Sheet1", {}).get("data", []):
        status = row.get("Grievance status", "")
        subcase = row.get("SUBCASE", "")

        if status and len(status) > 2:
            statuses.add(status)
        if subcase and len(subcase) > 2:
            subcases.add(subcase)

    print(f"Extracted {len(statuses)} grievance statuses")
    print(f"Extracted {len(subcases)} subcases")

    # Save
    output_file = OUTPUT_DIR / "grievance_statuses.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "extracted_at": datetime.now().isoformat(),
            "statuses": list(statuses),
            "subcases": list(subcases)
        }, f, ensure_ascii=False, indent=2)

    print(f"Saved to: {output_file}")

    return list(statuses), list(subcases)


def create_response_template_training_data(templates):
    """Create training data for response template selection"""
    print("\n" + "="*60)
    print(" Creating Response Template Training Data")
    print("="*60)

    training_samples = []

    # Map statuses to categories
    STATUS_CATEGORIES = {
        "Registered": "acknowledgment",
        "Viewed by officer": "in_progress",
        "GRIEVANCE FORWARDED TO ANOTHER DEPARTMENT": "forwarded",
        "Redressed": "resolved",
        "Court Case": "cannot_resolve",
        "Citizen Asking for Allocation of Government Land": "cannot_resolve",
        "Scheme to be launched": "cannot_resolve",
        "Under Intimation": "in_progress",
        "Reminder": "reminder",
        "Feedback": "feedback",
    }

    for template in templates:
        status = template.get("status", "")
        category = None

        for key, cat in STATUS_CATEGORIES.items():
            if key.lower() in status.lower():
                category = cat
                break

        if category:
            training_samples.append({
                "status": status,
                "subcase": template.get("subcase", ""),
                "category": category,
                "template_id": len(training_samples),
                "text": template.get("template_text", "")[:500]  # Truncate
            })

    print(f"Created {len(training_samples)} template training samples")

    # Save
    output_file = OUTPUT_DIR / "response_template_training.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "extracted_at": datetime.now().isoformat(),
            "count": len(training_samples),
            "categories": list(set([s["category"] for s in training_samples])),
            "samples": training_samples
        }, f, ensure_ascii=False, indent=2)

    print(f"Saved to: {output_file}")

    return training_samples


def extract_service_registration_data():
    """Extract service registration data"""
    print("\n" + "="*60)
    print(" Extracting Service Registration Data")
    print("="*60)

    service_file = DOCS_DIR / "data_sets" / "markdown" / "Service Registration reference.md"

    if not service_file.exists():
        print(f"File not found: {service_file}")
        return []

    with open(service_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract service names
    services = []

    # Simple line-by-line extraction
    for line in content.split('\n'):
        line = line.strip()
        if line and not line.startswith('#') and not line.startswith('|'):
            # Skip headers and table markers
            if len(line) > 5 and not line.startswith('-'):
                services.append(line[:200])  # Limit length

    # Deduplicate
    services = list(set(services))[:200]  # Limit total

    print(f"Extracted {len(services)} services")

    # Save
    output_file = OUTPUT_DIR / "service_list.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "source": "Service Registration reference.md",
            "extracted_at": datetime.now().isoformat(),
            "count": len(services),
            "services": services
        }, f, ensure_ascii=False, indent=2)

    print(f"Saved to: {output_file}")

    return services


def generate_summary():
    """Generate summary of all extracted data"""
    print("\n" + "="*60)
    print(" EXTRACTION SUMMARY")
    print("="*60)

    summary = {
        "extracted_at": datetime.now().isoformat(),
        "output_directory": str(OUTPUT_DIR),
        "files_created": []
    }

    for f in OUTPUT_DIR.glob("*.json"):
        with open(f, 'r', encoding='utf-8') as file:
            data = json.load(file)
            count = data.get("count", len(data.get("samples", data.get("templates", data.get("lapses", [])))))
            summary["files_created"].append({
                "filename": f.name,
                "records": count
            })
            print(f"  {f.name}: {count} records")

    # Save summary
    summary_file = OUTPUT_DIR / "_extraction_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)

    print(f"\nSummary saved to: {summary_file}")


def main():
    print("\n" + "="*60)
    print(" DOCS DATA EXTRACTION")
    print("="*60)
    print(f"Docs directory: {DOCS_DIR}")
    print(f"Output directory: {OUTPUT_DIR}")

    # 1. Extract petitioner messages (official Telugu templates)
    templates = extract_petitioner_messages()

    # 2. Extract lapse definitions
    lapses = extract_lapse_definitions()

    # 3. Extract department list
    departments = extract_department_list()

    # 4. Extract grievance statuses
    statuses, subcases = extract_grievance_statuses()

    # 5. Create response template training data
    template_training = create_response_template_training_data(templates)

    # 6. Extract service registration data
    services = extract_service_registration_data()

    # 7. Generate summary
    generate_summary()

    print("\n" + "="*60)
    print(" EXTRACTION COMPLETE")
    print("="*60)


if __name__ == "__main__":
    main()
