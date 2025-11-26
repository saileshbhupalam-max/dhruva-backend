"""
Comprehensive Test Suite for DHRUVA Grievance Processor
========================================================
Tests all ML models and the unified processor pipeline.

Run with: python test_grievance_processor.py
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

# Test configuration
CLASSIFICATION_MIN_ACCURACY = 0.80  # 80%
SENTIMENT_MIN_ACCURACY = 0.85  # 85%
TOP3_MIN_ACCURACY = 0.90  # 90%


def safe_print(text: str):
    """Print with encoding fallback."""
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode('ascii', 'replace').decode('ascii'))


class TestSuite:
    """Comprehensive test suite for GrievanceProcessor."""

    def __init__(self):
        self.processor = None
        self.results = {
            "classification": {"passed": 0, "failed": 0, "cases": []},
            "sentiment": {"passed": 0, "failed": 0, "cases": []},
            "integration": {"passed": 0, "failed": 0, "cases": []},
            "edge_cases": {"passed": 0, "failed": 0, "cases": []},
        }

    def setup(self) -> bool:
        """Initialize processor."""
        try:
            from grievance_processor import GrievanceProcessor
            self.processor = GrievanceProcessor()
            return self.processor.models_loaded
        except Exception as e:
            safe_print(f"[FAIL] Setup failed: {e}")
            return False

    def run_all(self):
        """Run all test suites."""
        print("\n" + "=" * 70)
        print(" DHRUVA GRIEVANCE PROCESSOR - COMPREHENSIVE TEST SUITE")
        print("=" * 70)

        if not self.setup():
            safe_print("[FAIL] Could not initialize processor. Aborting tests.")
            return

        print("\n[OK] Processor initialized successfully")
        print(f"    - Classifier: {'OK' if self.processor.classifier else 'MISSING'}")
        print(f"    - Sentiment: {'OK' if self.processor.sentiment_model else 'MISSING'}")
        print(f"    - Fallback: {'OK' if self.processor.fallback_model else 'MISSING'}")
        print(f"    - Lapse: {'OK' if self.processor.lapse_model else 'MISSING'}")

        # Run test suites
        self.test_classification()
        self.test_sentiment()
        self.test_integration()
        self.test_edge_cases()
        self.test_duplicate_detection()
        self.test_proactive_alerts()

        # Print summary
        self.print_summary()

    def test_classification(self):
        """Test department classification accuracy."""
        print("\n" + "-" * 70)
        print(" TEST SUITE: Department Classification")
        print("-" * 70)

        # Comprehensive test cases - Telugu grievances
        test_cases = [
            # Revenue Department
            ("పట్టాదారు పాస్ పుస్తకం కావాలి", "Revenue", "Pattadar passbook request"),
            ("భూమి రికార్డులు సరిగ్గా లేవు", "Revenue", "Land records issue"),
            ("ఆర్ఓఆర్ సర్టిఫికేట్ కావాలి", "Revenue", "ROR certificate request"),
            ("మ్యుటేషన్ చేయించుకోవాలి", "Revenue", "Mutation request"),
            ("భూమి సర్వే చేయించండి", "Revenue", "Land survey request"),

            # Pensions / Social Welfare
            ("వృద్ధాప్య పెన్షన్ రాలేదు", "Social Welfare", "Old age pension"),
            ("వితంతు పెన్షన్ 3 నెలలుగా రాలేదు", "Social Welfare", "Widow pension"),
            ("వికలాంగ పెన్షన్ కావాలి", "Social Welfare", "Disability pension"),
            ("ఆసరా పెన్షన్ ఆగిపోయింది", "Social Welfare", "Aasara pension stopped"),

            # Municipal Administration
            ("రోడ్డు మీద గుంతలు ఉన్నాయి", "Municipal Administration", "Road potholes"),
            ("డ్రైనేజీ పని చేయడం లేదు", "Municipal Administration", "Drainage not working"),
            ("స్ట్రీట్ లైట్ వేయండి", "Municipal Administration", "Street light request"),
            ("చెత్త ఎత్తుకోవడం లేదు", "Municipal Administration", "Garbage not collected"),

            # Civil Supplies
            ("రేషన్ కార్డు కావాలి", "Civil Supplies", "Ration card request"),
            ("బియ్యం రాలేదు", "Civil Supplies", "Rice not received"),
            ("రేషన్ డీలర్ బియ్యం ఇవ్వడం లేదు", "Civil Supplies", "Dealer not giving rice"),
            ("కొత్త రేషన్ కార్డు కావాలి", "Civil Supplies", "New ration card"),

            # Agriculture
            ("రైతు బంధు డబ్బులు రాలేదు", "Agriculture", "Rythu Bandhu not received"),
            ("పంట నష్టపోయింది పరిహారం కావాలి", "Agriculture", "Crop loss compensation"),
            ("విత్తనాలు సరిగ్గా రాలేదు", "Agriculture", "Seeds not received properly"),
            ("పురుగు మందులు కావాలి", "Agriculture", "Pesticides needed"),

            # Health
            ("ఆసుపత్రిలో డాక్టర్ లేరు", "Health", "No doctor in hospital"),
            ("PHC లో మందులు లేవు", "Health", "No medicines in PHC"),
            ("ఆరోగ్య శ్రీ కార్డు కావాలి", "Health", "Arogyasri card needed"),
            ("అంబులెన్స్ రాలేదు", "Health", "Ambulance didn't come"),

            # Education
            ("స్కూల్లో టీచర్ లేరు", "Education", "No teacher in school"),
            ("మధ్యాహ్న భోజనం సరిగ్గా రావడం లేదు", "Education", "Mid-day meal issue"),
            ("స్కూల్ బిల్డింగ్ పాడైపోయింది", "Education", "School building damaged"),

            # Energy / Electricity
            ("కరెంట్ రావడం లేదు", "Energy", "No electricity"),
            ("ట్రాన్స్ఫార్మర్ కాలిపోయింది", "Energy", "Transformer burnt"),
            ("కరెంట్ బిల్లు ఎక్కువ వచ్చింది", "Energy", "High electricity bill"),
            ("కొత్త కనెక్షన్ కావాలి", "Energy", "New connection needed"),

            # Police
            ("పోలీస్ కేసు పెట్టండి", "Police", "File police case"),
            ("దొంగతనం జరిగింది", "Police", "Theft occurred"),
            ("వేధింపులు జరుగుతున్నాయి", "Police", "Harassment happening"),

            # Water Resources
            ("నీళ్ళు రావడం లేదు", "Water Resources", "No water supply"),
            ("బోర్ వేయించండి", "Water Resources", "Bore well needed"),
            ("పైపులైన్ లీకేజీ", "Water Resources", "Pipeline leakage"),

            # Housing
            ("ఇల్లు పడిపోయింది", "Housing", "House collapsed"),
            ("పీఎంఏవై ఇల్లు కావాలి", "Housing", "PMAY house needed"),
            ("ఇంటి పట్టా కావాలి", "Housing", "House patta needed"),

            # Transport
            ("బస్సు రావడం లేదు", "Transport", "Bus not coming"),
            ("డ్రైవింగ్ లైసెన్స్ కావాలి", "Transport", "Driving license needed"),
            ("రోడ్ టాక్స్ రిఫండ్ కావాలి", "Transport", "Road tax refund"),
        ]

        correct = 0
        top3_correct = 0

        for text, expected_dept, desc in test_cases:
            result = self.processor._classify(text)
            predicted = result.get("department")
            confidence = result.get("confidence", 0)
            top3 = [r["department"] for r in result.get("top_3", [])]

            is_correct = predicted == expected_dept
            is_top3 = expected_dept in top3

            if is_correct:
                correct += 1
                status = "[OK]"
            elif is_top3:
                top3_correct += 1
                status = "[TOP3]"
            else:
                status = "[FAIL]"

            self.results["classification"]["cases"].append({
                "desc": desc,
                "expected": expected_dept,
                "predicted": predicted,
                "confidence": confidence,
                "correct": is_correct,
                "top3": is_top3,
            })

            safe_print(f"  {status} {desc}: {predicted} ({confidence:.0%}) [expected: {expected_dept}]")

        total = len(test_cases)
        accuracy = correct / total
        top3_accuracy = (correct + top3_correct) / total

        self.results["classification"]["passed"] = correct
        self.results["classification"]["failed"] = total - correct
        self.results["classification"]["accuracy"] = accuracy
        self.results["classification"]["top3_accuracy"] = top3_accuracy

        print(f"\n  Accuracy: {accuracy:.1%} ({correct}/{total})")
        print(f"  Top-3 Accuracy: {top3_accuracy:.1%}")

        if accuracy >= CLASSIFICATION_MIN_ACCURACY:
            print(f"  [PASS] Classification accuracy >= {CLASSIFICATION_MIN_ACCURACY:.0%}")
        else:
            print(f"  [FAIL] Classification accuracy < {CLASSIFICATION_MIN_ACCURACY:.0%}")

    def test_sentiment(self):
        """Test sentiment/distress detection accuracy."""
        print("\n" + "-" * 70)
        print(" TEST SUITE: Sentiment/Distress Detection")
        print("-" * 70)

        test_cases = [
            # CRITICAL - Life threatening
            ("ఆకలితో చనిపోతున్నాము సహాయం చేయండి", "CRITICAL", "Dying of hunger"),
            ("ఆత్మహత్య చేసుకుంటాను ఎవరూ సహాయం చేయడం లేదు", "CRITICAL", "Suicide threat"),
            ("పిల్లలు ఆకలితో అలమటిస్తున్నారు", "CRITICAL", "Children starving"),
            ("తినడానికి ఏమీ లేదు చావడం తప్ప", "CRITICAL", "Nothing to eat, will die"),
            ("వైద్య సహాయం లేక చనిపోతున్నారు", "CRITICAL", "Dying without medical help"),

            # HIGH - Urgent needs
            ("పెన్షన్ 6 నెలలుగా రాలేదు", "HIGH", "Pension 6 months pending"),
            ("3 నెలలుగా జీతం రాలేదు", "HIGH", "Salary 3 months pending"),
            ("వారాలుగా కరెంట్ లేదు", "HIGH", "No electricity for weeks"),
            ("రేషన్ 4 నెలలుగా రాలేదు", "HIGH", "Ration 4 months not received"),
            ("అత్యవసర చికిత్స కావాలి", "HIGH", "Need emergency treatment"),

            # MEDIUM - Standard issues
            ("రోడ్డు రిపేర్ చేయండి", "MEDIUM", "Road repair needed"),
            ("డ్రైనేజీ సమస్య ఉంది", "MEDIUM", "Drainage problem"),
            ("స్ట్రీట్ లైట్ పని చేయడం లేదు", "MEDIUM", "Street light not working"),
            ("చెత్త సేకరణ సరిగ్గా జరగడం లేదు", "MEDIUM", "Garbage collection issue"),
            ("పార్కు నిర్వహణ బాగా లేదు", "MEDIUM", "Park maintenance poor"),

            # NORMAL - Routine queries
            ("సర్టిఫికేట్ కావాలి", "NORMAL", "Certificate needed"),
            ("కొత్త కనెక్షన్ కావాలి", "NORMAL", "New connection needed"),
            ("సమాచారం కావాలి", "NORMAL", "Information needed"),
            ("అప్లికేషన్ స్టేటస్ తెలియజేయండి", "NORMAL", "Application status query"),
            ("ఫారం ఎక్కడ దొరుకుతుంది", "NORMAL", "Where to get form"),
        ]

        correct = 0

        for text, expected_level, desc in test_cases:
            result = self.processor._analyze_sentiment(text)
            predicted = result.get("distress_level")
            confidence = result.get("confidence", 0)

            is_correct = predicted == expected_level

            if is_correct:
                correct += 1
                status = "[OK]"
            else:
                status = "[FAIL]"

            self.results["sentiment"]["cases"].append({
                "desc": desc,
                "expected": expected_level,
                "predicted": predicted,
                "confidence": confidence,
                "correct": is_correct,
            })

            safe_print(f"  {status} {desc}: {predicted} ({confidence:.0%}) [expected: {expected_level}]")

        total = len(test_cases)
        accuracy = correct / total

        self.results["sentiment"]["passed"] = correct
        self.results["sentiment"]["failed"] = total - correct
        self.results["sentiment"]["accuracy"] = accuracy

        print(f"\n  Accuracy: {accuracy:.1%} ({correct}/{total})")

        if accuracy >= SENTIMENT_MIN_ACCURACY:
            print(f"  [PASS] Sentiment accuracy >= {SENTIMENT_MIN_ACCURACY:.0%}")
        else:
            print(f"  [FAIL] Sentiment accuracy < {SENTIMENT_MIN_ACCURACY:.0%}")

    def test_integration(self):
        """Test full pipeline integration."""
        print("\n" + "-" * 70)
        print(" TEST SUITE: Full Pipeline Integration")
        print("-" * 70)

        test_cases = [
            {
                "text": "నా పెన్షన్ 6 నెలలుగా రాలేదు పిల్లలకు తినడానికి ఏమీ లేదు",
                "citizen_id": "C001",
                "location": "Guntur",
                "expected_dept": "Social Welfare",
                "expected_distress": "CRITICAL",
                "desc": "Pension + children hungry"
            },
            {
                "text": "రోడ్డు మీద పెద్ద గుంతలు ఉన్నాయి వాహనాలు ప్రమాదంలో పడుతున్నాయి",
                "citizen_id": "C002",
                "location": "Vijayawada",
                "expected_dept": "Municipal Administration",
                "expected_distress": "HIGH",
                "desc": "Road potholes + accidents"
            },
            {
                "text": "కొత్త రేషన్ కార్డు కావాలి దయచేసి సహాయం చేయండి",
                "citizen_id": "C003",
                "location": "Guntur",
                "expected_dept": "Civil Supplies",
                "expected_distress": "NORMAL",
                "desc": "New ration card request"
            },
        ]

        passed = 0

        for case in test_cases:
            result = self.processor.process(
                case["text"],
                case["citizen_id"],
                case["location"]
            )

            dept_correct = result["classification"].get("department") == case["expected_dept"]
            distress_correct = result["sentiment"].get("distress_level") == case["expected_distress"]
            has_sla = result["sla"].get("hours") is not None
            has_timestamp = result.get("timestamp") is not None

            all_correct = dept_correct and distress_correct and has_sla and has_timestamp

            if all_correct:
                passed += 1
                status = "[OK]"
            else:
                status = "[FAIL]"

            self.results["integration"]["cases"].append({
                "desc": case["desc"],
                "dept_correct": dept_correct,
                "distress_correct": distress_correct,
                "has_sla": has_sla,
            })

            safe_print(f"  {status} {case['desc']}")
            print(f"      Dept: {result['classification'].get('department')} [expected: {case['expected_dept']}]")
            print(f"      Distress: {result['sentiment'].get('distress_level')} [expected: {case['expected_distress']}]")
            print(f"      SLA: {result['sla'].get('hours')} hours")

        self.results["integration"]["passed"] = passed
        self.results["integration"]["failed"] = len(test_cases) - passed

        print(f"\n  Passed: {passed}/{len(test_cases)}")

    def test_edge_cases(self):
        """Test edge cases and boundary conditions."""
        print("\n" + "-" * 70)
        print(" TEST SUITE: Edge Cases")
        print("-" * 70)

        test_cases = [
            # Mixed language (code-mixing)
            ("pension amount credit avvaledhu please help", "Code-mixing English"),
            ("naa ration card missing ayindi", "Code-mixing Telugu-English"),

            # Short text
            ("pension kavali", "Very short request"),

            # Long text
            ("నా పెన్షన్ చాలా నెలలుగా రాలేదు అధికారులను కలిసాను ఏమీ చేయడం లేదు ఎన్నిసార్లు వెళ్ళినా సమాధానం లేదు పిల్లలు ఆకలితో అలమటిస్తున్నారు దయచేసి సహాయం చేయండి లేకపోతే ఆత్మహత్య చేసుకుంటాను", "Very long grievance"),

            # Multiple issues
            ("రోడ్డు బాగా లేదు మరియు కరెంట్ కూడా రావడం లేదు", "Multiple issues"),

            # Numbers and dates
            ("15 రోజులుగా నీళ్ళు రావడం లేదు 01-01-2025 నుండి", "With dates"),

            # Special characters
            ("pension ₹1000 కావాలి @urgent #help", "Special characters"),
        ]

        passed = 0

        for text, desc in test_cases:
            try:
                result = self.processor.process(text)
                has_classification = result["classification"].get("department") is not None
                has_sentiment = result["sentiment"].get("distress_level") is not None

                if has_classification or has_sentiment:
                    passed += 1
                    status = "[OK]"
                else:
                    status = "[WARN]"

                self.results["edge_cases"]["cases"].append({
                    "desc": desc,
                    "success": True,
                    "has_classification": has_classification,
                    "has_sentiment": has_sentiment,
                })

                safe_print(f"  {status} {desc}: processed successfully")

            except Exception as e:
                self.results["edge_cases"]["cases"].append({
                    "desc": desc,
                    "success": False,
                    "error": str(e),
                })
                safe_print(f"  [FAIL] {desc}: {e}")

        self.results["edge_cases"]["passed"] = passed
        self.results["edge_cases"]["failed"] = len(test_cases) - passed

        print(f"\n  Handled: {passed}/{len(test_cases)}")

    def test_duplicate_detection(self):
        """Test duplicate detection functionality."""
        print("\n" + "-" * 70)
        print(" TEST SUITE: Duplicate Detection")
        print("-" * 70)

        # Submit first grievance
        text1 = "నా పెన్షన్ రాలేదు సహాయం చేయండి"
        result1 = self.processor.process(text1, "C100", "Guntur")

        # Submit similar grievance from same citizen
        text2 = "నా పెన్షన్ రాలేదు దయచేసి సహాయం చేయండి"
        result2 = self.processor.process(text2, "C100", "Guntur")

        # Submit different grievance from same citizen
        text3 = "రోడ్డు మీద గుంతలు ఉన్నాయి"
        result3 = self.processor.process(text3, "C100", "Guntur")

        print(f"  First grievance: stored")
        print(f"  Similar grievance (same citizen): duplicate_check = {result2.get('duplicate_check', {})}")
        print(f"  Different grievance (same citizen): duplicate_check = {result3.get('duplicate_check', {})}")

    def test_proactive_alerts(self):
        """Test proactive alert generation."""
        print("\n" + "-" * 70)
        print(" TEST SUITE: Proactive Alerts")
        print("-" * 70)

        # Simulate multiple complaints from same area
        location = "Ward7_Test"
        for i in range(6):
            result = self.processor.process(
                f"నీళ్ళు రావడం లేదు సమస్య {i}",
                f"C{200+i}",
                location
            )

        # Check if alert was generated
        final_result = self.processor.process(
            "నీళ్ళు సమస్య మళ్ళీ",
            "C210",
            location
        )

        alerts = final_result.get("proactive_alerts", [])
        print(f"  Submitted 7 complaints from {location}")
        print(f"  Alerts generated: {len(alerts)}")

        if alerts:
            for alert in alerts:
                print(f"    - {alert.get('type')}: {alert.get('recommendation')}")

    def print_summary(self):
        """Print test summary."""
        print("\n" + "=" * 70)
        print(" TEST SUMMARY")
        print("=" * 70)

        total_passed = 0
        total_failed = 0

        for suite_name, suite_results in self.results.items():
            passed = suite_results.get("passed", 0)
            failed = suite_results.get("failed", 0)
            accuracy = suite_results.get("accuracy", None)

            total_passed += passed
            total_failed += failed

            status = "[PASS]" if failed == 0 or (accuracy and accuracy >= 0.80) else "[FAIL]"

            if accuracy:
                print(f"  {status} {suite_name}: {passed}/{passed+failed} ({accuracy:.1%})")
            else:
                print(f"  {status} {suite_name}: {passed}/{passed+failed}")

        print(f"\n  TOTAL: {total_passed}/{total_passed+total_failed} tests passed")

        # Final verdict
        classification_ok = self.results["classification"].get("accuracy", 0) >= CLASSIFICATION_MIN_ACCURACY
        sentiment_ok = self.results["sentiment"].get("accuracy", 0) >= SENTIMENT_MIN_ACCURACY

        print("\n  FINAL VERDICT:")
        if classification_ok and sentiment_ok:
            print("  [PASS] All accuracy thresholds met!")
            print(f"    - Classification: {self.results['classification'].get('accuracy', 0):.1%} >= {CLASSIFICATION_MIN_ACCURACY:.0%}")
            print(f"    - Sentiment: {self.results['sentiment'].get('accuracy', 0):.1%} >= {SENTIMENT_MIN_ACCURACY:.0%}")
        else:
            print("  [FAIL] Some accuracy thresholds not met")
            if not classification_ok:
                print(f"    - Classification: {self.results['classification'].get('accuracy', 0):.1%} < {CLASSIFICATION_MIN_ACCURACY:.0%}")
            if not sentiment_ok:
                print(f"    - Sentiment: {self.results['sentiment'].get('accuracy', 0):.1%} < {SENTIMENT_MIN_ACCURACY:.0%}")

        # Save results to file
        self.save_results()

    def save_results(self):
        """Save test results to JSON file."""
        output_file = Path(__file__).parent / "test_results.json"

        output = {
            "timestamp": datetime.now().isoformat(),
            "thresholds": {
                "classification_min": CLASSIFICATION_MIN_ACCURACY,
                "sentiment_min": SENTIMENT_MIN_ACCURACY,
                "top3_min": TOP3_MIN_ACCURACY,
            },
            "results": self.results,
        }

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

        print(f"\n  Results saved to: {output_file}")


if __name__ == "__main__":
    suite = TestSuite()
    suite.run_all()
