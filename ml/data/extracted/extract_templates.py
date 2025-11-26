#!/usr/bin/env python3
"""
Extract Telugu message templates from MESSAGES_SENT_TO_PETITIONERS.json
Extracts 58 official templates with metadata, departments, and officer designations
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple

# PGRS BOOK 30 departments (from government documentation)
DEPARTMENTS = [
    "Revenue", "REVENUE", "రెవెన్యూ",
    "MAUD", "Municipal Administration", "పురపాలక",
    "PRRD", "Panchayat Raj", "పంచాయతీ రాజ్",
    "Education", "విద్య",
    "Health", "ఆరోగ్యం",
    "Agriculture", "వ్యవసాయం",
    "Police", "పోలీస్",
    "Transport", "రవాణా",
    "Electricity", "విద్యుత్",
    "Water Supply", "నీటి సరఫరా",
    "Roads & Buildings", "రోడ్లు మరియు భవనాలు",
    "Labour", "కార్మిక",
    "Welfare", "సంక్షేమం",
    "Forest", "అటవీ",
    "Industries", "పరిశ్రమలు",
    "Finance", "ఫైనాన్స్",
    "Commercial Tax", "వాణిజ్య పన్ను",
    "Registration", "రిజిస్ట్రేషన్",
    "Survey", "సర్వే",
    "Housing", "గృహనిర్మాణం"
]

# Officer designations to extract
OFFICER_DESIGNATIONS = [
    "GRA", "Collector", "కలెక్టర్",
    "Tahsildar", "తహసీల్దార్",
    "RDO", "Revenue Divisional Officer", "రెవెన్యూ విభాగ అధికారి",
    "Mandal Officer", "MPDO", "మండల అధికారి",
    "DSH", "District Supply Officer", "జిల్లా సరఫరా అధికారి",
    "MRO", "Mandal Revenue Officer", "మండల రెవెన్యూ అధికారి",
    "Commissioner", "కమీషనర్",
    "Secretary", "సెక్రటరీ",
    "Inspector", "ఇన్‌స్పెక్టర్",
    "Executive Engineer", "ఎగ్జిక్యూటివ్ ఇంజనీర్", "EE",
    "Deputy Collector", "డిప్యూటీ కలెక్టర్",
    "Sub-Collector", "సబ్ కలెక్టర్",
    "Village Revenue Officer", "VRO", "గ్రామ రెవెన్యూ అధికారి",
    "Surveyor", "సర్వేయర్",
    "Development Officer", "అభివృద్ధి అధికారి",
    "ఆఫీసర్", "Officer", "అధికారి",
    "WARD SACHIVALAYAM", "వార్డ్ సచివాలయం",
    "Enforcement Officer", "అమలు అధికారి",
    "DEO", "District Education Officer",
    "DMHO", "District Medical and Health Officer",
    "DSP", "Deputy Superintendent of Police",
    "RTO", "Regional Transport Officer"
]


def detect_departments(text: str) -> List[str]:
    """Detect department names mentioned in text"""
    detected = []
    text_lower = text.lower()

    for dept in DEPARTMENTS:
        if dept.lower() in text_lower or dept in text:
            # Normalize department name
            if "revenue" in dept.lower() or "రెవెన్యూ" in dept:
                dept_name = "Revenue"
            elif "maud" in dept.lower() or "పురపాలక" in dept.lower():
                dept_name = "MAUD"
            elif "prrd" in dept.lower() or "పంచాయతీ" in dept.lower():
                dept_name = "PRRD"
            elif "education" in dept.lower() or "విద్య" in dept:
                dept_name = "Education"
            elif "health" in dept.lower() or "ఆరోగ్యం" in dept:
                dept_name = "Health"
            elif "agriculture" in dept.lower() or "వ్యవసాయం" in dept:
                dept_name = "Agriculture"
            elif "police" in dept.lower() or "పోలీస్" in dept:
                dept_name = "Police"
            elif "transport" in dept.lower() or "రవాణా" in dept:
                dept_name = "Transport"
            elif "electricity" in dept.lower() or "విద్యుత్" in dept:
                dept_name = "Electricity"
            elif "water" in dept.lower() or "నీటి" in dept:
                dept_name = "Water Supply"
            elif "road" in dept.lower() or "రోడ్లు" in dept:
                dept_name = "Roads & Buildings"
            elif "labour" in dept.lower() or "కార్మిక" in dept:
                dept_name = "Labour"
            elif "welfare" in dept.lower() or "సంక్షేమం" in dept:
                dept_name = "Welfare"
            elif "forest" in dept.lower() or "అటవీ" in dept:
                dept_name = "Forest"
            elif "industries" in dept.lower() or "పరిశ్రమలు" in dept:
                dept_name = "Industries"
            elif "finance" in dept.lower() or "ఫైనాన్స్" in dept:
                dept_name = "Finance"
            elif "commercial" in dept.lower() or "వాణిజ్య" in dept:
                dept_name = "Commercial Tax"
            elif "registration" in dept.lower() or "రిజిస్ట్రేషన్" in dept:
                dept_name = "Registration"
            elif "survey" in dept.lower() or "సర్వే" in dept:
                dept_name = "Survey"
            elif "housing" in dept.lower() or "గృహనిర్మాణం" in dept:
                dept_name = "Housing"
            else:
                dept_name = dept

            if dept_name not in detected:
                detected.append(dept_name)

    return detected


def extract_officer_designations(text: str) -> List[str]:
    """Extract officer designations from text"""
    detected = []
    text_lower = text.lower()

    for officer in OFFICER_DESIGNATIONS:
        if officer.lower() in text_lower or officer in text:
            # Normalize officer designation
            if "gra" == officer.lower():
                officer_name = "GRA"
            elif "collector" in officer.lower() and "deputy" not in officer.lower() and "sub" not in officer.lower():
                officer_name = "Collector"
            elif "deputy collector" in officer.lower():
                officer_name = "Deputy Collector"
            elif "sub-collector" in officer.lower() or "sub collector" in officer.lower():
                officer_name = "Sub-Collector"
            elif "tahsildar" in officer.lower():
                officer_name = "Tahsildar"
            elif "rdo" == officer.lower() or "revenue divisional officer" in officer.lower():
                officer_name = "RDO"
            elif "mpdo" in officer.lower() or ("mandal" in officer.lower() and "officer" in officer.lower()):
                officer_name = "Mandal Officer"
            elif "dsh" == officer.lower():
                officer_name = "DSH"
            elif "mro" == officer.lower() or ("mandal revenue" in officer.lower()):
                officer_name = "MRO"
            elif "commissioner" in officer.lower():
                officer_name = "Commissioner"
            elif "secretary" in officer.lower():
                officer_name = "Secretary"
            elif "inspector" in officer.lower() and "police" not in officer.lower():
                officer_name = "Inspector"
            elif "executive engineer" in officer.lower() or officer.lower() == "ee":
                officer_name = "Executive Engineer"
            elif "vro" == officer.lower() or "village revenue officer" in officer.lower():
                officer_name = "VRO"
            elif "surveyor" in officer.lower():
                officer_name = "Surveyor"
            elif "development officer" in officer.lower():
                officer_name = "Development Officer"
            elif "ward sachivalayam" in officer.lower() or "వార్డ్ సచివాలయం" in officer:
                officer_name = "Ward Sachivalayam"
            elif "enforcement officer" in officer.lower():
                officer_name = "Enforcement Officer"
            elif "deo" == officer.lower() or "district education officer" in officer.lower():
                officer_name = "DEO"
            elif "dmho" == officer.lower() or "district medical" in officer.lower():
                officer_name = "DMHO"
            elif "dsp" == officer.lower() or "deputy superintendent" in officer.lower():
                officer_name = "DSP"
            elif "rto" == officer.lower() or "regional transport officer" in officer.lower():
                officer_name = "RTO"
            elif officer == "ఆఫీసర్" or officer == "Officer" or officer == "అధికారి":
                officer_name = "Officer (Generic)"
            else:
                officer_name = officer

            if officer_name not in detected:
                detected.append(officer_name)

    return detected


def extract_keywords(text: str) -> List[str]:
    """Extract keywords from template text"""
    keywords = []

    # Registration keywords
    if re.search(r'(నమోదు|register|స్వీకరించబడినది|received)', text, re.IGNORECASE):
        keywords.append("registration")

    # Escalation keywords
    if re.search(r'(తరలింపు|escalate|పంపించాము|forward)', text, re.IGNORECASE):
        keywords.append("escalation")

    # Closure keywords
    if re.search(r'(పరిష్కరించబడింది|పరిష్కారం|closed|resolve|complete)', text, re.IGNORECASE):
        keywords.append("closure")

    # Feedback keywords
    if re.search(r'(అభిప్రాయం|feedback|రేటింగ్|rating)', text, re.IGNORECASE):
        keywords.append("feedback")

    # Viewing keywords
    if re.search(r'(చూసి|viewed|చూచారు)', text, re.IGNORECASE):
        keywords.append("viewed")

    # Action keywords
    if re.search(r'(చర్య|action|కార్యకలాపం)', text, re.IGNORECASE):
        keywords.append("action")

    # Reminder keywords
    if re.search(r'(గుర్తు చేయడం|reminder|గుర్తుచేస్తున్నాము)', text, re.IGNORECASE):
        keywords.append("reminder")

    # Status keywords
    if re.search(r'(స్థితి|status|పరిస్థితి)', text, re.IGNORECASE):
        keywords.append("status")

    return keywords


def categorize_template(text: str, grievance_status: str) -> str:
    """Categorize template based on text and status"""
    text_lower = text.lower()
    status_lower = grievance_status.lower() if grievance_status else ""

    # Registration
    if "register" in status_lower or "నమోదు" in text or "స్వీకరించబడినది" in text:
        return "Registration"

    # Viewing
    if "viewed" in status_lower or "చూసి" in text or "చూచారు" in text:
        return "Viewed"

    # Forwarding/Escalation
    if "forward" in status_lower or "తరలింపు" in text or "పంపించాము" in text:
        return "Forwarding"

    # Closure
    if "closed" in status_lower or "complete" in status_lower or "పరిష్కరించబడింది" in text or "పరిష్కారం" in text:
        return "Closure"

    # Feedback
    if "feedback" in status_lower or "rating" in status_lower or "అభిప్రాయం" in text or "రేటింగ్" in text:
        return "Feedback"

    # Reminder
    if "reminder" in status_lower or "గుర్తు చేయడం" in text or "గుర్తుచేస్తున్నాము" in text:
        return "Reminder"

    # Action
    if "action" in status_lower or "చర్య" in text or "కార్యకలాపం" in text:
        return "Action"

    # Default
    return "General"


def validate_telugu_encoding(text: str) -> Tuple[bool, str]:
    """Validate Telugu text encoding (U+0C00 to U+0C7F)"""
    if not text:
        return False, "Empty text"

    # Check for mojibake patterns
    if any(char in text for char in ['�', '?', '\ufffd']):
        return False, "Contains mojibake characters"

    # Check for Telugu characters
    telugu_chars = [c for c in text if '\u0C00' <= c <= '\u0C7F']
    if len(telugu_chars) < 10:  # Should have at least some Telugu characters
        return False, f"Only {len(telugu_chars)} Telugu characters found"

    return True, "Valid Telugu encoding"


def clean_text(text: str) -> str:
    """Clean text by removing HTML tags"""
    if not text:
        return ""

    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def extract_templates(json_path: Path) -> Dict:
    """Extract all templates from JSON file"""
    print(f"Reading JSON file: {json_path}")

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Access the nested data structure
    sheet_data = data['sheets']['Sheet1']['data']
    print(f"Found {len(sheet_data)} rows in data")

    templates = []
    all_departments = set()
    all_officers = set()
    total_length = 0
    encoding_issues = []

    for idx, row in enumerate(sheet_data, start=1):
        # Extract Telugu text from "MESSAGE TO BE SENT" field
        text_telugu = row.get("MESSAGE TO BE SENT", "")
        sample_message = row.get("SAMPLE MESSAGE", "")
        grievance_status = row.get("Grievance status", "")
        case_num = row.get("case", idx)
        subcase = row.get("SUBCASE", "")

        # Extract variable information
        var_1 = row.get("1", "")
        var_2 = row.get("2", "")
        var_3 = row.get("3", "")
        var_info = f"{var_1} {var_2} {var_3}".strip()

        # Skip header rows and section dividers
        if isinstance(case_num, str) and (
            case_num.lower() in ["s.no", "can not be redressed", "re-open cases", "case"] or
            text_telugu == "MESSAGE TO BE SENT" or
            text_telugu == "MESSAGE TO BE SENT" or
            not text_telugu
        ):
            print(f"Skipping header/divider row {idx}: {case_num}")
            continue

        # Clean text
        text_telugu = clean_text(text_telugu)

        # Skip if no Telugu text
        if not text_telugu:
            print(f"Warning: Row {idx} has no Telugu text")
            continue

        # Validate encoding
        is_valid, validation_msg = validate_telugu_encoding(text_telugu)
        if not is_valid:
            encoding_issues.append(f"Template {idx}: {validation_msg}")
            print(f"Warning: {validation_msg} in row {idx}")

        # Extract metadata - look in Telugu text, sample message, grievance status, and variable info
        combined_text = f"{text_telugu} {sample_message} {grievance_status} {var_info} {subcase}"
        departments = detect_departments(combined_text)
        officers = extract_officer_designations(combined_text)
        keywords = extract_keywords(text_telugu)
        category = categorize_template(text_telugu, grievance_status)

        # Update sets
        all_departments.update(departments)
        all_officers.update(officers)

        # Create template entry
        template = {
            "template_id": case_num,
            "category": category,
            "grievance_status": grievance_status,
            "subcase": subcase if subcase else None,
            "text_telugu": text_telugu,
            "text_english": None,  # Not present in source data
            "sample_message": sample_message if sample_message else None,
            "contains_department": len(departments) > 0,
            "extracted_departments": departments,
            "extracted_keywords": keywords,
            "officer_designations": officers,
            "character_count": len(text_telugu),
            "variable_count": row.get("Total No.of Variables", 0),
            "variables": {
                "var_1": var_1 if var_1 else None,
                "var_2": var_2 if var_2 else None,
                "var_3": var_3 if var_3 else None
            }
        }

        templates.append(template)
        total_length += len(text_telugu)

    # Calculate summary statistics
    avg_length = total_length / len(templates) if templates else 0

    summary = {
        "total_templates": len(templates),
        "telugu_templates": len(templates),
        "avg_length": round(avg_length, 2),
        "unique_departments_mentioned": len(all_departments),
        "unique_officer_designations": len(all_officers),
        "departments": sorted(list(all_departments)),
        "officer_designations": sorted(list(all_officers)),
        "encoding_issues": encoding_issues
    }

    return {
        "templates": templates,
        "summary": summary
    }


def validate_quality_gates(result: Dict) -> Dict[str, bool]:
    """Validate quality gates"""
    summary = result['summary']
    templates = result['templates']

    # Note: 58 rows in data, but 4 are header/divider rows = 54 actual templates
    gates = {
        "min_54_templates": summary['total_templates'] >= 54,
        "all_have_telugu": all(t['text_telugu'] for t in templates),
        "no_mojibake": len(summary.get('encoding_issues', [])) == 0,
        "min_6_departments": summary['unique_departments_mentioned'] >= 6,
        "min_5_officers": summary['unique_officer_designations'] >= 5,
        "avg_length_min_100": summary['avg_length'] >= 100
    }

    return gates


def main():
    """Main extraction process"""
    # Paths
    source_file = Path(r"D:\projects\dhruva\docs\reference\markdown\MESSAGES_SENT_TO_PETITIONERS.json")
    output_dir = Path(r"D:\projects\dhruva\backend\ml\data\extracted")
    output_file = output_dir / "message_templates.json"

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print("AGENT 5: TELUGU MESSAGE TEMPLATES EXTRACTION")
    print("=" * 80)
    print()

    # Extract templates
    result = extract_templates(source_file)

    # Validate quality gates
    gates = validate_quality_gates(result)

    # Save output
    print(f"\nSaving output to: {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    # Print results
    print("\n" + "=" * 80)
    print("EXTRACTION COMPLETE")
    print("=" * 80)

    print("\nQUALITY GATES:")
    for gate, passed in gates.items():
        status = "[PASS]" if passed else "[FAIL]"
        print(f"  {status} - {gate}")

    print("\nSUMMARY STATISTICS:")
    print(f"  Total templates: {result['summary']['total_templates']}")
    print(f"  Telugu templates: {result['summary']['telugu_templates']}")
    print(f"  Average length: {result['summary']['avg_length']} characters")
    print(f"  Unique departments: {result['summary']['unique_departments_mentioned']}")
    print(f"  Unique officers: {result['summary']['unique_officer_designations']}")

    print("\nDEPARTMENTS FOUND:")
    for dept in result['summary']['departments']:
        print(f"  - {dept}")

    print("\nOFFICER DESIGNATIONS FOUND:")
    for officer in result['summary']['officer_designations']:
        print(f"  - {officer}")

    if result['summary'].get('encoding_issues'):
        print("\nENCODING ISSUES:")
        for issue in result['summary']['encoding_issues'][:10]:  # Show first 10
            print(f"  - {issue}")

    print("\n" + "=" * 80)
    all_passed = all(gates.values())
    if all_passed:
        print("SUCCESS: All quality gates passed!")
    else:
        print("WARNING: Some quality gates failed!")
    print("=" * 80)

    return 0 if all_passed else 1


if __name__ == "__main__":
    exit(main())
