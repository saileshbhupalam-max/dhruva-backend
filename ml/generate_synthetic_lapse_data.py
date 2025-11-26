#!/usr/bin/env python3
"""
Synthetic Lapse Training Data Generator
========================================

Generates realistic synthetic lapse cases for ML model training based on:
- Guntur district audit patterns (13 lapse categories)
- AP government department and district data
- Research findings on department-lapse correlations

Author: Dhruva ML Team
Date: 2025-11-25
"""

import json
import random
import csv
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple
import sys

# Set random seed for reproducibility
random.seed(42)


# ============================================================================
# LAPSE CATEGORIES (From Guntur Audit Research)
# ============================================================================
LAPSE_CATEGORIES = [
    {
        "id": 1,
        "name": "GRA did not speak to citizen directly",
        "probability": 0.4219,
        "dept_affinity": ["REVENUE", "SOC_WELF", "MUNI", "PNCHRAJ"],
        "delay_sensitive": False,
    },
    {
        "id": 2,
        "name": "Not visited site / No field verification",
        "probability": 0.1583,
        "dept_affinity": ["REVENUE", "PNCHRAJ", "MUNI", "RNB"],
        "delay_sensitive": True,
    },
    {
        "id": 3,
        "name": "Wrong/Blank/Not related comments",
        "probability": 0.1244,
        "dept_affinity": ["ALL"],
        "delay_sensitive": False,
    },
    {
        "id": 4,
        "name": "Closed without required documents",
        "probability": 0.0583,
        "dept_affinity": ["REVENUE", "SOC_WELF", "HOUSING"],
        "delay_sensitive": False,
    },
    {
        "id": 5,
        "name": "No proper enquiry conducted",
        "probability": 0.0496,
        "dept_affinity": ["REVENUE", "HOME", "MUNI"],
        "delay_sensitive": True,
    },
    {
        "id": 6,
        "name": "Premature closure",
        "probability": 0.0405,
        "dept_affinity": ["REVENUE", "SOC_WELF", "AGRI"],
        "delay_sensitive": False,
    },
    {
        "id": 7,
        "name": "Action not taken as per rules",
        "probability": 0.0287,
        "dept_affinity": ["REVENUE", "LABOUR", "HOME"],
        "delay_sensitive": False,
    },
    {
        "id": 8,
        "name": "Inadequate action taken",
        "probability": 0.0270,
        "dept_affinity": ["MUNI", "PNCHRAJ", "WATER"],
        "delay_sensitive": False,
    },
    {
        "id": 9,
        "name": "Inordinate delay",
        "probability": 0.0261,
        "dept_affinity": ["ALL"],
        "delay_sensitive": True,
    },
    {
        "id": 10,
        "name": "Incorrect routing",
        "probability": 0.0244,
        "dept_affinity": ["ALL"],
        "delay_sensitive": False,
    },
    {
        "id": 11,
        "name": "No action letter issued",
        "probability": 0.0200,
        "dept_affinity": ["REVENUE", "SOC_WELF", "MUNI"],
        "delay_sensitive": False,
    },
    {
        "id": 12,
        "name": "Poor quality of work",
        "probability": 0.0130,
        "dept_affinity": ["PNCHRAJ", "MUNI", "RNB", "WATER"],
        "delay_sensitive": False,
    },
    {
        "id": 13,
        "name": "Beneficiary not contacted",
        "probability": 0.0078,
        "dept_affinity": ["SOC_WELF", "HOUSING", "AGRI"],
        "delay_sensitive": False,
    },
]


# ============================================================================
# AP GOVERNMENT DEPARTMENTS (From actual data)
# ============================================================================
DEPARTMENTS = [
    {"code": "REVENUE", "name": "Revenue (CCLA)", "volume_weight": 0.35},
    {"code": "SOC_WELF", "name": "Social Welfare", "volume_weight": 0.15},
    {"code": "MUNI", "name": "Municipal Administration And Urban Development", "volume_weight": 0.12},
    {"code": "AGRI", "name": "Agriculture And Co-operation", "volume_weight": 0.08},
    {"code": "PNCHRAJ", "name": "Panchayat Raj And Rural Development", "volume_weight": 0.08},
    {"code": "ENERGY", "name": "Energy", "volume_weight": 0.05},
    {"code": "WATER", "name": "Water Resources", "volume_weight": 0.04},
    {"code": "HEALTH", "name": "Health, Medical And Family Welfare", "volume_weight": 0.03},
    {"code": "RNB", "name": "Transport, Roads And Buildings", "volume_weight": 0.03},
    {"code": "HOME", "name": "Home (Police)", "volume_weight": 0.02},
    {"code": "HOUSING", "name": "Housing", "volume_weight": 0.02},
    {"code": "LABOUR", "name": "Labour, Factories, Boilers And Insurance Medical Services", "volume_weight": 0.01},
    {"code": "BC_WELF", "name": "Backward Classes Welfare", "volume_weight": 0.01},
    {"code": "WOMEN", "name": "Women, Children, Disabled And Senior Citizens", "volume_weight": 0.01},
]


# ============================================================================
# AP DISTRICTS (All 26 districts)
# ============================================================================
DISTRICTS = [
    {"code": "GNT", "name": "Guntur"},
    {"code": "VSP", "name": "Visakhapatnam"},
    {"code": "ANT", "name": "Anantapur"},
    {"code": "KDP", "name": "Kadapa"},
    {"code": "WG", "name": "West Godavari"},
    {"code": "NTR", "name": "NTR District"},
    {"code": "CHT", "name": "Chittoor"},
    {"code": "EG", "name": "East Godavari"},
    {"code": "KRS", "name": "Krishna"},
    {"code": "KNL", "name": "Kurnool"},
    {"code": "NLR", "name": "Nellore"},
    {"code": "PKM", "name": "Prakasam"},
    {"code": "SKM", "name": "Srikakulam"},
    {"code": "VZG", "name": "Vizianagaram"},
    {"code": "ARL", "name": "Alluri Sitharama Raju"},
    {"code": "ANA", "name": "Anakapalli"},
    {"code": "ANM", "name": "Annamaya"},
    {"code": "BAP", "name": "Bapatla"},
    {"code": "ELR", "name": "Eluru"},
    {"code": "KKN", "name": "Kakinada"},
    {"code": "KNR", "name": "Konaseema"},
    {"code": "PLN", "name": "Palnadu"},
    {"code": "PVT", "name": "Parvathipuram Manyam"},
    {"code": "NAG", "name": "Sri Potti Sriramulu Nellore"},
    {"code": "STY", "name": "Sri Satya Sai"},
    {"code": "TPT", "name": "Tirupati"},
]


# ============================================================================
# GRIEVANCE CATEGORIES BY DEPARTMENT
# ============================================================================
GRIEVANCE_CATEGORIES = {
    "REVENUE": [
        "land_mutation", "property_dispute", "revenue_certificate",
        "land_records", "encroachment", "tax_assessment"
    ],
    "SOC_WELF": [
        "pension_not_received", "pension_delay", "disability_certificate",
        "scholarship_issue", "welfare_scheme"
    ],
    "MUNI": [
        "water_supply", "drainage_issue", "garbage_collection",
        "street_lights", "road_repair", "building_permission"
    ],
    "AGRI": [
        "crop_compensation", "subsidy_delay", "fertilizer_issue",
        "irrigation_problem", "crop_insurance"
    ],
    "PNCHRAJ": [
        "village_roads", "community_hall", "sanitation",
        "drinking_water", "village_development"
    ],
    "ENERGY": [
        "power_outage", "meter_issue", "billing_dispute",
        "new_connection", "transformer_problem"
    ],
    "WATER": [
        "irrigation_canal", "water_shortage", "bore_well",
        "tank_maintenance", "flood_control"
    ],
    "HEALTH": [
        "hospital_service", "medicine_shortage", "doctor_absence",
        "medical_reimbursement", "ambulance_service"
    ],
    "RNB": [
        "road_pothole", "bridge_repair", "highway_maintenance",
        "bus_service", "contractor_issue"
    ],
    "HOME": [
        "police_complaint", "fir_delay", "traffic_issue",
        "law_order", "police_harassment"
    ],
    "HOUSING": [
        "house_site", "housing_scheme", "construction_delay",
        "allotment_issue", "building_quality"
    ],
    "LABOUR": [
        "wage_dispute", "factory_safety", "labour_welfare",
        "esr_issue", "contractor_payment"
    ],
    "BC_WELF": [
        "caste_certificate", "hostel_admission", "scholarship",
        "welfare_benefit", "reservation_issue"
    ],
    "WOMEN": [
        "anganwadi_service", "child_welfare", "women_safety",
        "maternity_benefit", "daycare_center"
    ],
}


# ============================================================================
# ESCALATION LEVELS
# ============================================================================
ESCALATION_LEVELS = ["GRA", "Mandal", "Tahsildar", "RDO", "Collector", "HOD", "CM"]


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def select_weighted_random(items: List[Dict], weight_key: str) -> Dict:
    """Select item based on weighted probability."""
    total = sum(item[weight_key] for item in items)
    rand = random.uniform(0, total)
    cumulative = 0
    for item in items:
        cumulative += item[weight_key]
        if rand <= cumulative:
            return item
    return items[-1]


def select_lapse_category(department_code: str) -> Dict:
    """
    Select lapse category based on department affinity and probability distribution.
    Uses adjusted probabilities when department matches affinity.
    """
    # Calculate adjusted probabilities based on department affinity
    adjusted_lapses = []
    for lapse in LAPSE_CATEGORIES:
        base_prob = lapse["probability"]

        # Boost probability if department has affinity for this lapse
        if "ALL" in lapse["dept_affinity"] or department_code in lapse["dept_affinity"]:
            adjusted_prob = base_prob * 1.5  # 50% boost for matching departments
        else:
            adjusted_prob = base_prob * 0.5  # 50% reduction for non-matching

        adjusted_lapses.append({
            **lapse,
            "adjusted_probability": adjusted_prob
        })

    # Normalize probabilities
    total_prob = sum(l["adjusted_probability"] for l in adjusted_lapses)
    for lapse in adjusted_lapses:
        lapse["adjusted_probability"] /= total_prob

    # Select based on adjusted probabilities
    return select_weighted_random(adjusted_lapses, "adjusted_probability")


def generate_days_to_resolve(lapse_category: Dict, base_sla: int = 7) -> int:
    """
    Generate realistic days_to_resolve based on lapse type.
    Delay-sensitive lapses tend to have longer resolution times.
    """
    if lapse_category.get("delay_sensitive"):
        # Inordinate delay cases: 15-90 days
        mean = 45
        std_dev = 20
    else:
        # Normal cases: 3-30 days
        mean = 12
        std_dev = 8

    days = int(random.gauss(mean, std_dev))
    return max(1, min(days, 120))  # Clamp between 1 and 120 days


def generate_officer_response_count(days: int, escalation_level: str) -> int:
    """
    Generate officer response count based on resolution time and escalation.
    More days and higher escalation → more responses.
    """
    # Base on days
    base_count = max(1, days // 7)

    # Adjust for escalation level
    escalation_multiplier = {
        "GRA": 1.0,
        "Mandal": 1.2,
        "Tahsildar": 1.3,
        "RDO": 1.5,
        "Collector": 1.8,
        "HOD": 2.0,
        "CM": 2.5,
    }

    count = int(base_count * escalation_multiplier.get(escalation_level, 1.0))

    # Add Gaussian noise
    count = int(random.gauss(count, count * 0.3))

    return max(1, min(count, 20))  # Clamp between 1 and 20


def select_escalation_level(days: int, department_code: str) -> str:
    """
    Select escalation level based on days and department importance.
    Longer delays → higher escalation probability.
    """
    if days < 7:
        levels = ["GRA"] * 70 + ["Mandal"] * 20 + ["Tahsildar"] * 10
    elif days < 15:
        levels = ["GRA"] * 40 + ["Mandal"] * 30 + ["Tahsildar"] * 20 + ["RDO"] * 10
    elif days < 30:
        levels = ["Mandal"] * 30 + ["Tahsildar"] * 30 + ["RDO"] * 20 + ["Collector"] * 20
    elif days < 60:
        levels = ["Tahsildar"] * 20 + ["RDO"] * 30 + ["Collector"] * 40 + ["HOD"] * 10
    else:  # 60+ days
        levels = ["RDO"] * 10 + ["Collector"] * 40 + ["HOD"] * 30 + ["CM"] * 20

    # High-priority departments (Revenue, Social Welfare) escalate faster
    if department_code in ["REVENUE", "SOC_WELF"] and random.random() < 0.3:
        # Boost escalation by 1-2 levels
        current_level = random.choice(levels)
        current_idx = ESCALATION_LEVELS.index(current_level)
        boosted_idx = min(current_idx + random.randint(1, 2), len(ESCALATION_LEVELS) - 1)
        return ESCALATION_LEVELS[boosted_idx]

    return random.choice(levels)


def generate_confidence_score() -> float:
    """
    Generate synthetic confidence score (0.85-0.95).
    Indicates this is synthetic data, not ground truth.
    """
    return round(random.uniform(0.85, 0.95), 2)


def generate_sample(sample_id: int) -> Dict:
    """Generate a single synthetic lapse case sample."""

    # 1. Select department (weighted by volume)
    department = select_weighted_random(DEPARTMENTS, "volume_weight")
    dept_code = department["code"]
    dept_name = department["name"]

    # 2. Select district (uniform distribution)
    district = random.choice(DISTRICTS)

    # 3. Select grievance category for this department
    categories = GRIEVANCE_CATEGORIES.get(dept_code, ["general_grievance"])
    grievance_category = random.choice(categories)

    # 4. Select lapse type (department-aware)
    lapse = select_lapse_category(dept_code)

    # 5. Generate days_to_resolve (lapse-aware)
    days_to_resolve = generate_days_to_resolve(lapse)

    # 6. Select escalation level (days-aware)
    escalation_level = select_escalation_level(days_to_resolve, dept_code)

    # 7. Generate officer response count (days and escalation aware)
    officer_response_count = generate_officer_response_count(days_to_resolve, escalation_level)

    # 8. Generate confidence score
    confidence = generate_confidence_score()

    return {
        "id": sample_id,
        "department_code": dept_code,
        "department_name": dept_name,
        "district_code": district["code"],
        "district_name": district["name"],
        "grievance_category": grievance_category,
        "days_to_resolve": days_to_resolve,
        "officer_response_count": officer_response_count,
        "escalation_level": escalation_level,
        "lapse_type": lapse["name"],
        "lapse_type_id": lapse["id"],
        "confidence": confidence,
    }


# ============================================================================
# MAIN GENERATION LOGIC
# ============================================================================

def generate_synthetic_dataset(num_samples: int = 1000) -> Dict:
    """Generate complete synthetic dataset with metadata."""

    print(f"Generating {num_samples} synthetic lapse cases...")
    print(f"Based on Guntur audit patterns with {len(LAPSE_CATEGORIES)} lapse categories")
    print(f"Across {len(DEPARTMENTS)} departments and {len(DISTRICTS)} districts")
    print()

    samples = []
    for i in range(1, num_samples + 1):
        sample = generate_sample(i)
        samples.append(sample)

        if i % 100 == 0:
            print(f"Generated {i}/{num_samples} samples...")

    print(f"\nCompleted: {num_samples} samples generated")

    # Calculate statistics
    lapse_distribution = {}
    dept_distribution = {}

    for sample in samples:
        lapse_type = sample["lapse_type"]
        dept_code = sample["department_code"]

        lapse_distribution[lapse_type] = lapse_distribution.get(lapse_type, 0) + 1
        dept_distribution[dept_code] = dept_distribution.get(dept_code, 0) + 1

    # Create metadata
    metadata = {
        "generation_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_samples": num_samples,
        "source": "synthetic_based_on_guntur_audit_patterns",
        "confidence_level": 0.85,
        "random_seed": 42,
        "lapse_categories": len(LAPSE_CATEGORIES),
        "departments": len(DEPARTMENTS),
        "districts": len(DISTRICTS),
        "lapse_distribution": {
            k: {"count": v, "percentage": round(v / num_samples * 100, 2)}
            for k, v in sorted(lapse_distribution.items(), key=lambda x: x[1], reverse=True)
        },
        "department_distribution": {
            k: {"count": v, "percentage": round(v / num_samples * 100, 2)}
            for k, v in sorted(dept_distribution.items(), key=lambda x: x[1], reverse=True)
        },
        "feature_ranges": {
            "days_to_resolve": {
                "min": min(s["days_to_resolve"] for s in samples),
                "max": max(s["days_to_resolve"] for s in samples),
                "mean": round(sum(s["days_to_resolve"] for s in samples) / len(samples), 2),
            },
            "officer_response_count": {
                "min": min(s["officer_response_count"] for s in samples),
                "max": max(s["officer_response_count"] for s in samples),
                "mean": round(sum(s["officer_response_count"] for s in samples) / len(samples), 2),
            },
        },
    }

    return {
        "metadata": metadata,
        "samples": samples,
    }


def save_json(data: Dict, output_path: Path):
    """Save dataset as JSON."""
    print(f"\nSaving JSON to: {output_path}")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"JSON saved: {output_path.stat().st_size / 1024:.2f} KB")


def save_csv(samples: List[Dict], output_path: Path):
    """Save samples as CSV for easy inspection."""
    print(f"\nSaving CSV to: {output_path}")

    if not samples:
        print("No samples to save!")
        return

    fieldnames = list(samples[0].keys())

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(samples)

    print(f"CSV saved: {output_path.stat().st_size / 1024:.2f} KB")


def print_summary(metadata: Dict):
    """Print generation summary."""
    print("\n" + "=" * 70)
    print("SYNTHETIC LAPSE DATA GENERATION SUMMARY")
    print("=" * 70)
    print(f"Generation Date: {metadata['generation_date']}")
    print(f"Total Samples: {metadata['total_samples']}")
    print(f"Confidence Level: {metadata['confidence_level']}")
    print(f"Random Seed: {metadata['random_seed']}")
    print()

    print("TOP 5 LAPSE TYPES:")
    for i, (lapse, stats) in enumerate(list(metadata["lapse_distribution"].items())[:5], 1):
        print(f"  {i}. {lapse}: {stats['count']} ({stats['percentage']}%)")
    print()

    print("TOP 5 DEPARTMENTS:")
    for i, (dept, stats) in enumerate(list(metadata["department_distribution"].items())[:5], 1):
        dept_name = next((d["name"] for d in DEPARTMENTS if d["code"] == dept), dept)
        print(f"  {i}. {dept_name}: {stats['count']} ({stats['percentage']}%)")
    print()

    print("FEATURE RANGES:")
    print(f"  Days to Resolve: {metadata['feature_ranges']['days_to_resolve']['min']}-"
          f"{metadata['feature_ranges']['days_to_resolve']['max']} "
          f"(mean: {metadata['feature_ranges']['days_to_resolve']['mean']})")
    print(f"  Officer Responses: {metadata['feature_ranges']['officer_response_count']['min']}-"
          f"{metadata['feature_ranges']['officer_response_count']['max']} "
          f"(mean: {metadata['feature_ranges']['officer_response_count']['mean']})")
    print("=" * 70)


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Main execution function."""
    # Configuration
    NUM_SAMPLES = 1000
    OUTPUT_DIR = Path(__file__).parent / "data" / "synthetic"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    JSON_OUTPUT = OUTPUT_DIR / "synthetic_lapse_cases.json"
    CSV_OUTPUT = OUTPUT_DIR / "synthetic_lapse_cases.csv"

    print("=" * 70)
    print("DHRUVA ML - SYNTHETIC LAPSE DATA GENERATOR")
    print("=" * 70)
    print(f"Output directory: {OUTPUT_DIR}")
    print()

    # Generate dataset
    dataset = generate_synthetic_dataset(NUM_SAMPLES)

    # Save outputs
    save_json(dataset, JSON_OUTPUT)
    save_csv(dataset["samples"], CSV_OUTPUT)

    # Print summary
    print_summary(dataset["metadata"])

    print("\n[SUCCESS] Synthetic data generation complete!")
    print(f"[SUCCESS] JSON: {JSON_OUTPUT}")
    print(f"[SUCCESS] CSV:  {CSV_OUTPUT}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
