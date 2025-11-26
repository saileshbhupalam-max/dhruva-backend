#!/usr/bin/env python3
"""
Prepare Training Data for MuRIL Models
=======================================
Consolidates all available data for:
1. MuRIL Sentiment/Distress Detection (4-class)
2. MuRIL Fallback Classifier (15-class)

Data Sources:
- Call Center 1100 Feedback (93,892 records) → Sentiment
- PGRS Keywords (709) → Classification
- Message Templates (54) → Response templates
- Existing training data → Classification augmentation
"""

import json
import re
import csv
from pathlib import Path
from collections import Counter
from datetime import datetime

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data" / "extracted"
DOCS_DIR = BASE_DIR.parent.parent / "docs" / "reference" / "markdown"
OUTPUT_DIR = BASE_DIR / "data" / "muril_training"

# Ensure output directory exists
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Department mapping (same as classifier v3)
TOP_DEPARTMENTS = [
    "Revenue", "Municipal Administration", "Police", "Agriculture", "Health",
    "Education", "Energy", "Panchayat Raj", "Social Welfare", "Civil Supplies",
    "Transport", "Housing", "Water Resources", "Women & Child Welfare", "Animal Husbandry"
]

# Distress level mapping based on satisfaction scores
# Score 1.0-1.5 = CRITICAL, 1.5-2.0 = HIGH, 2.0-2.5 = MEDIUM, 2.5+ = NORMAL
def satisfaction_to_distress(score):
    """Convert satisfaction score to distress level."""
    if score <= 1.5:
        return "CRITICAL"
    elif score <= 2.0:
        return "HIGH"
    elif score <= 2.5:
        return "MEDIUM"
    else:
        return "NORMAL"


def load_json(path):
    """Load JSON file."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def parse_call_center_data():
    """
    Parse Call Center 1100 data from markdown file.
    Creates sentiment training data from satisfaction scores.
    """
    print("="*60)
    print(" Parsing Call Center 1100 Data for Sentiment Training")
    print("="*60)

    call_center_file = DOCS_DIR / "STATE CALL CENTER 1100 FEEDBACK REPORT (1).md"

    if not call_center_file.exists():
        print(f"WARNING: {call_center_file} not found")
        return []

    with open(call_center_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract department-wise satisfaction data
    # Format: | Department | Total | Score |
    dept_pattern = r'\|\s*([A-Za-z\s&,()]+)\s*\|\s*(\d+)\s*\|\s*([\d.]+)\s*\|'
    matches = re.findall(dept_pattern, content)

    sentiment_data = []

    for dept, total, score in matches:
        dept = dept.strip()
        try:
            total = int(total)
            score = float(score)
        except:
            continue

        if total < 10:  # Skip very small samples
            continue

        distress = satisfaction_to_distress(score)

        # Generate synthetic grievance texts based on department
        # We'll use this to create training samples
        sentiment_data.append({
            "department": dept,
            "total_cases": total,
            "satisfaction_score": score,
            "distress_level": distress
        })

    print(f"Extracted {len(sentiment_data)} department satisfaction records")

    # Distribution
    dist = Counter([d["distress_level"] for d in sentiment_data])
    print(f"Distress distribution: {dict(dist)}")

    return sentiment_data


def create_sentiment_training_samples(dept_satisfaction_data):
    """
    Create sentiment training samples using:
    1. Department satisfaction data (provides labels)
    2. PGRS keywords (provides text)
    3. Templates (provides sentence structure)
    """
    print("\n" + "="*60)
    print(" Creating Sentiment Training Samples")
    print("="*60)

    # Load keywords
    keywords_file = DATA_DIR / "pgrs_book_keywords.json"
    keywords_data = load_json(keywords_file) if keywords_file.exists() else {"departments": []}

    # Distress keyword augmentation
    DISTRESS_KEYWORDS = {
        "CRITICAL": [
            "చనిపోతున్నాము", "ఆకలి", "అత్యవసర", "ప్రాణాలు", "మరణం",
            "dying", "starving", "emergency", "desperate", "critical"
        ],
        "HIGH": [
            "నెలలుగా", "ఆపేసారు", "తిరస్కరించారు", "ఎక్కడికి వెళ్ళాలి", "నిరాశ",
            "months", "stopped", "rejected", "helpless", "nowhere"
        ],
        "MEDIUM": [
            "ఆలస్యం", "సమస్య", "కష్టం", "రాలేదు",
            "delay", "problem", "difficult", "waiting"
        ],
        "NORMAL": [
            "కావాలి", "దరఖాస్తు", "సమాచారం", "అభ్యర్థన",
            "need", "request", "information", "apply"
        ]
    }

    # Templates for each distress level
    DISTRESS_TEMPLATES = {
        "CRITICAL": [
            "{keyword} లేక చనిపోతున్నాము",
            "{keyword} 6 నెలలుగా రాలేదు ఆకలితో ఉన్నాము",
            "అత్యవసర {keyword} సహాయం కావాలి లేకపోతే ప్రాణాలు పోతాయి",
            "emergency {keyword} needed urgently please help",
        ],
        "HIGH": [
            "{keyword} 3 నెలలుగా రాలేదు",
            "{keyword} ఆపేసారు కారణం తెలియదు",
            "నా {keyword} తిరస్కరించారు ఎక్కడికి వెళ్ళాలి తెలియదు",
            "{keyword} stopped for months please help",
        ],
        "MEDIUM": [
            "{keyword} ఆలస్యం అవుతుంది",
            "{keyword} సమస్య పరిష్కరించండి",
            "నా {keyword} ఇంకా రాలేదు",
            "{keyword} delay problem please solve",
        ],
        "NORMAL": [
            "{keyword} కోసం దరఖాస్తు చేసాను",
            "{keyword} సమాచారం కావాలి",
            "నా {keyword} status తెలియజేయండి",
            "requesting {keyword} information",
        ]
    }

    samples = []

    # Generate samples from keywords + distress templates
    for dept_data in keywords_data.get("departments", []):
        for subject in dept_data.get("subjects", []):
            keywords = subject.get("keywords_telugu", []) + subject.get("keywords_english", [])

            for keyword in keywords:
                for distress_level, templates in DISTRESS_TEMPLATES.items():
                    for template in templates:
                        try:
                            text = template.format(keyword=keyword)
                            samples.append({
                                "text": text,
                                "label": distress_level
                            })
                        except:
                            pass

    # Add pure distress keyword samples
    for level, keywords in DISTRESS_KEYWORDS.items():
        for kw in keywords:
            samples.append({"text": kw, "label": level})
            samples.append({"text": f"{kw} సమస్య", "label": level})
            samples.append({"text": f"{kw} problem", "label": level})

    print(f"Generated {len(samples)} sentiment samples")

    # Balance classes
    label_counts = Counter([s["label"] for s in samples])
    print(f"Label distribution: {dict(label_counts)}")

    return samples


def create_classification_training_data():
    """
    Create classification training data for MuRIL fallback.
    Uses existing data + augmentation.
    """
    print("\n" + "="*60)
    print(" Creating Classification Training Data")
    print("="*60)

    samples = []

    # 1. Load existing training data from classifier v3
    keywords_file = DATA_DIR / "pgrs_book_keywords.json"
    if keywords_file.exists():
        data = load_json(keywords_file)

        DEPT_MAP = {
            'revenue': 'Revenue', 'revenue (ccla)': 'Revenue',
            'municipal administration': 'Municipal Administration',
            'police': 'Police', 'home (police)': 'Police',
            'agriculture': 'Agriculture',
            'health': 'Health', 'health, medical and family welfare': 'Health',
            'education': 'Education', 'school education': 'Education',
            'energy': 'Energy', 'electricity': 'Energy',
            'panchayat raj': 'Panchayat Raj',
            'social welfare': 'Social Welfare',
            'civil supplies': 'Civil Supplies',
            'transport': 'Transport',
            'housing': 'Housing',
            'water resources': 'Water Resources',
            'women & child welfare': 'Women & Child Welfare',
            'animal husbandry': 'Animal Husbandry',
        }

        for dept in data.get("departments", []):
            dept_name = dept.get("name_english", "").lower()
            mapped_dept = None

            for key, val in DEPT_MAP.items():
                if key in dept_name or dept_name in key:
                    mapped_dept = val
                    break

            if not mapped_dept or mapped_dept not in TOP_DEPARTMENTS:
                continue

            for subject in dept.get("subjects", []):
                for kw in subject.get("keywords_telugu", []) + subject.get("keywords_english", []):
                    samples.append({"text": kw, "label": mapped_dept})

    # 2. Load research samples
    research_file = BASE_DIR / "TELUGU_GRIEVANCE_DATASET_RESEARCH.json"
    if research_file.exists():
        data = load_json(research_file)
        for sample in data.get("samples", []):
            dept = sample.get("department", "")
            text = sample.get("telugu_text", "")

            # Normalize department
            for top_dept in TOP_DEPARTMENTS:
                if top_dept.lower() in dept.lower() or dept.lower() in top_dept.lower():
                    samples.append({"text": text, "label": top_dept})
                    break

    # 3. Load synthetic samples
    synthetic_file = BASE_DIR / "data" / "synthetic" / "synthetic_telugu_grievances.json"
    if synthetic_file.exists():
        data = load_json(synthetic_file)
        for sample in data.get("samples", []):
            dept = sample.get("department", "")
            text = sample.get("telugu_text", "")

            for top_dept in TOP_DEPARTMENTS:
                if top_dept.lower() in dept.lower() or dept.lower() in top_dept.lower():
                    samples.append({"text": text, "label": top_dept})
                    break

    # Filter to only top departments
    samples = [s for s in samples if s["label"] in TOP_DEPARTMENTS]

    print(f"Total classification samples: {len(samples)}")

    label_counts = Counter([s["label"] for s in samples])
    print(f"Label distribution:")
    for dept in TOP_DEPARTMENTS:
        print(f"  {dept}: {label_counts.get(dept, 0)}")

    return samples


def save_training_data(sentiment_samples, classification_samples):
    """Save training data in formats suitable for MuRIL fine-tuning."""
    print("\n" + "="*60)
    print(" Saving Training Data")
    print("="*60)

    # 1. Sentiment data - JSON
    sentiment_file = OUTPUT_DIR / "muril_sentiment_training.json"
    with open(sentiment_file, 'w', encoding='utf-8') as f:
        json.dump({
            "version": "1.0",
            "created": datetime.now().isoformat(),
            "task": "sentiment_classification",
            "labels": ["NORMAL", "MEDIUM", "HIGH", "CRITICAL"],
            "samples": sentiment_samples
        }, f, ensure_ascii=False, indent=2)
    print(f"Saved: {sentiment_file} ({len(sentiment_samples)} samples)")

    # 2. Sentiment data - CSV (for HuggingFace)
    sentiment_csv = OUTPUT_DIR / "muril_sentiment_training.csv"
    with open(sentiment_csv, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["text", "label"])
        for sample in sentiment_samples:
            writer.writerow([sample["text"], sample["label"]])
    print(f"Saved: {sentiment_csv}")

    # 3. Classification data - JSON
    classification_file = OUTPUT_DIR / "muril_classification_training.json"
    with open(classification_file, 'w', encoding='utf-8') as f:
        json.dump({
            "version": "1.0",
            "created": datetime.now().isoformat(),
            "task": "department_classification",
            "labels": TOP_DEPARTMENTS,
            "samples": classification_samples
        }, f, ensure_ascii=False, indent=2)
    print(f"Saved: {classification_file} ({len(classification_samples)} samples)")

    # 4. Classification data - CSV
    classification_csv = OUTPUT_DIR / "muril_classification_training.csv"
    with open(classification_csv, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["text", "label"])
        for sample in classification_samples:
            writer.writerow([sample["text"], sample["label"]])
    print(f"Saved: {classification_csv}")

    # 5. Summary
    summary = {
        "created": datetime.now().isoformat(),
        "sentiment": {
            "total_samples": len(sentiment_samples),
            "labels": ["NORMAL", "MEDIUM", "HIGH", "CRITICAL"],
            "distribution": dict(Counter([s["label"] for s in sentiment_samples]))
        },
        "classification": {
            "total_samples": len(classification_samples),
            "labels": TOP_DEPARTMENTS,
            "distribution": dict(Counter([s["label"] for s in classification_samples]))
        }
    }

    summary_file = OUTPUT_DIR / "training_data_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"Saved: {summary_file}")


def main():
    print("\n" + "="*60)
    print(" MURIL TRAINING DATA PREPARATION")
    print("="*60)

    # 1. Parse call center data
    dept_satisfaction = parse_call_center_data()

    # 2. Create sentiment training samples
    sentiment_samples = create_sentiment_training_samples(dept_satisfaction)

    # 3. Create classification training samples
    classification_samples = create_classification_training_data()

    # 4. Save all data
    save_training_data(sentiment_samples, classification_samples)

    print("\n" + "="*60)
    print(" COMPLETE")
    print("="*60)
    print(f"\nSentiment samples: {len(sentiment_samples)}")
    print(f"Classification samples: {len(classification_samples)}")
    print(f"\nOutput directory: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
