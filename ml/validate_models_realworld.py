#!/usr/bin/env python3
"""
Real-World Model Validation
============================
Tests our models against realistic grievance samples to assess production readiness.
"""

import pickle
import json
from pathlib import Path

BASE_DIR = Path(__file__).parent
MODELS_DIR = BASE_DIR / "models"

# Real-world test cases (NOT from training data)
# These simulate actual citizen grievances
REAL_WORLD_TESTS = [
    # Revenue cases
    {
        "text": "నా భూమి పట్టా కోసం 6 నెలలుగా ఎదురుచూస్తున్నాను",
        "expected": "Revenue",
        "description": "Land patta delay - 6 months waiting"
    },
    {
        "text": "మా ఊరిలో సర్వే చేయలేదు పరిష్కరించండి",
        "expected": "Revenue",
        "description": "Village survey not done"
    },
    {
        "text": "income certificate application pending from 2 months",
        "expected": "Revenue",
        "description": "Income certificate delay (English)"
    },
    {
        "text": "కుల ధృవీకరణ పత్రం కోసం దరఖాస్తు చేసాను ఇంకా రాలేదు",
        "expected": "Revenue",
        "description": "Caste certificate not received"
    },

    # Pension/Social Welfare cases
    {
        "text": "నా వృద్ధాప్య పెన్షన్ 3 నెలలుగా రాలేదు చాలా కష్టంగా ఉంది",
        "expected": "Social Welfare",
        "description": "Old age pension delay - distress"
    },
    {
        "text": "విధవ పెన్షన్ ఆపేసారు కారణం తెలియదు",
        "expected": "Social Welfare",
        "description": "Widow pension stopped"
    },
    {
        "text": "pension stopped without reason please help",
        "expected": "Social Welfare",
        "description": "Pension stopped (English)"
    },

    # Municipal cases
    {
        "text": "మా వీధిలో డ్రైనేజీ పని చేయడం లేదు దుర్వాసన వస్తుంది",
        "expected": "Municipal Administration",
        "description": "Drainage not working, bad smell"
    },
    {
        "text": "రోడ్డు గుంతలు చాలా ఉన్నాయి మరమ్మతు చేయండి",
        "expected": "Municipal Administration",
        "description": "Road potholes complaint"
    },
    {
        "text": "street light not working in our area for 1 month",
        "expected": "Municipal Administration",
        "description": "Streetlight issue (English)"
    },

    # Agriculture cases
    {
        "text": "పంట నష్టం పరిహారం ఇంకా రాలేదు",
        "expected": "Agriculture",
        "description": "Crop damage compensation not received"
    },
    {
        "text": "రైతు భరోసా డబ్బులు account లో పడలేదు",
        "expected": "Agriculture",
        "description": "Rythu Bharosa not credited"
    },

    # Health cases
    {
        "text": "PHC లో డాక్టర్ ఉండటం లేదు మందులు లేవు",
        "expected": "Health",
        "description": "No doctor at PHC, no medicines"
    },
    {
        "text": "ఆరోగ్యశ్రీ కార్డు ఇంకా రాలేదు",
        "expected": "Health",
        "description": "Aarogyasri card not received"
    },

    # Civil Supplies cases
    {
        "text": "రేషన్ దుకాణంలో బియ్యం ఇవ్వడం లేదు",
        "expected": "Civil Supplies",
        "description": "Ration shop not giving rice"
    },
    {
        "text": "నా రేషన్ కార్డు పేరు తప్పుగా ఉంది సరి చేయండి",
        "expected": "Civil Supplies",
        "description": "Ration card name correction"
    },

    # Energy cases
    {
        "text": "విద్యుత్ బిల్లు చాలా ఎక్కువ వచ్చింది తప్పు ఉంది",
        "expected": "Energy",
        "description": "Electricity bill too high"
    },
    {
        "text": "కొత్త కనెక్షన్ కోసం apply చేసాను 2 months అయింది",
        "expected": "Energy",
        "description": "New connection delay"
    },

    # Police cases
    {
        "text": "దొంగతనం జరిగింది FIR పెట్టలేదు",
        "expected": "Police",
        "description": "Theft occurred, FIR not filed"
    },
    {
        "text": "పొరుగువాళ్ళు వేధిస్తున్నారు సహాయం కావాలి",
        "expected": "Police",
        "description": "Neighbor harassment"
    },

    # Education cases
    {
        "text": "స్కూల్లో టీచర్ రావడం లేదు పిల్లల చదువు పాడవుతుంది",
        "expected": "Education",
        "description": "Teacher not coming to school"
    },
    {
        "text": "స్కాలర్షిప్ amount credit కాలేదు",
        "expected": "Education",
        "description": "Scholarship not credited"
    },

    # Water Resources
    {
        "text": "మా గ్రామంలో త్రాగునీరు సమస్య వారానికి ఒకసారి మాత్రమే వస్తుంది",
        "expected": "Water Resources",
        "description": "Drinking water - once a week only"
    },

    # Panchayat Raj
    {
        "text": "గ్రామంలో CC రోడ్డు పనులు ఆగిపోయాయి",
        "expected": "Panchayat Raj",
        "description": "CC road work stopped in village"
    },

    # Transport
    {
        "text": "driving license renewal ఆలస్యం అవుతుంది",
        "expected": "Transport",
        "description": "Driving license renewal delay"
    },

    # Housing
    {
        "text": "PMAY ఇంటి పట్టా కోసం apply చేసాను ఇంకా రాలేదు",
        "expected": "Housing",
        "description": "PMAY house patta pending"
    },

    # Edge cases - code-mixed
    {
        "text": "pension delay problem please solve చేయండి",
        "expected": "Social Welfare",
        "description": "Code-mixed Telugu-English"
    },
    {
        "text": "land issue MRO office వెళ్ళాను solve కాలేదు",
        "expected": "Revenue",
        "description": "Code-mixed with MRO mention"
    },

    # Ambiguous cases (harder)
    {
        "text": "నా application pending ఉంది 3 months అయింది",
        "expected": None,  # Could be many departments
        "description": "Ambiguous - just says application pending"
    },
    {
        "text": "ఏమీ జరగలేదు సహాయం చేయండి",
        "expected": None,  # Too vague
        "description": "Too vague - nothing happened help me"
    },
]


def load_models():
    """Load trained models."""
    print("Loading models...")

    with open(MODELS_DIR / "telugu_classifier_v3.pkl", 'rb') as f:
        classifier = pickle.load(f)

    with open(MODELS_DIR / "tfidf_vectorizer_v3.pkl", 'rb') as f:
        vectorizer = pickle.load(f)

    with open(MODELS_DIR / "dept_label_encoder_v3.pkl", 'rb') as f:
        label_encoder = pickle.load(f)

    with open(MODELS_DIR / "telugu_classifier_v3_metadata.json", 'r') as f:
        metadata = json.load(f)

    print(f"Loaded V3 classifier (reported accuracy: {metadata['accuracy']:.2%})")
    print(f"Classes: {metadata['num_classes']}")

    return classifier, vectorizer, label_encoder, metadata


def predict(text, classifier, vectorizer, label_encoder):
    """Make prediction with confidence."""
    X = vectorizer.transform([text])

    # Get prediction
    pred_idx = classifier.predict(X)[0]
    pred_dept = label_encoder.inverse_transform([pred_idx])[0]

    # Get probabilities
    proba = classifier.predict_proba(X)[0]
    confidence = proba[pred_idx]

    # Get top 3
    top3_idx = proba.argsort()[-3:][::-1]
    top3 = [(label_encoder.inverse_transform([i])[0], proba[i]) for i in top3_idx]

    return pred_dept, confidence, top3


def safe_print(text):
    """Print with fallback for encoding issues."""
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode('ascii', 'replace').decode('ascii'))


def run_validation():
    """Run real-world validation."""
    safe_print("\n" + "="*70)
    safe_print(" REAL-WORLD MODEL VALIDATION")
    safe_print("="*70)

    classifier, vectorizer, label_encoder, metadata = load_models()

    # Results tracking
    correct = 0
    incorrect = 0
    ambiguous_correct = 0
    low_confidence_cases = []
    wrong_predictions = []

    safe_print("\n" + "-"*70)
    safe_print(" TEST RESULTS")
    safe_print("-"*70)

    for i, test in enumerate(REAL_WORLD_TESTS):
        text = test["text"]
        expected = test["expected"]
        desc = test["description"]

        pred, conf, top3 = predict(text, classifier, vectorizer, label_encoder)

        # Determine correctness
        if expected is None:
            # Ambiguous case - just report
            status = "AMBIGUOUS"
            ambiguous_correct += 1
        elif pred == expected:
            status = "CORRECT"
            correct += 1
        else:
            # Check if expected is in top 3
            top3_depts = [d for d, _ in top3]
            if expected in top3_depts:
                status = "TOP-3"
                incorrect += 1  # Still count as incorrect for strict accuracy
            else:
                status = "WRONG"
                incorrect += 1
                wrong_predictions.append({
                    "text": text,
                    "expected": expected,
                    "predicted": pred,
                    "confidence": conf,
                    "description": desc
                })

        # Track low confidence
        if conf < 0.70:
            low_confidence_cases.append({
                "text": text[:50] + "...",
                "confidence": conf,
                "prediction": pred
            })

        # Print result
        conf_str = f"{conf:.0%}"
        safe_print(f"\n{i+1}. {desc}")
        safe_print(f"   Expected: {expected or 'N/A'} | Predicted: {pred} ({conf_str}) | {status}")
        if status in ["WRONG", "TOP-3"]:
            safe_print(f"   Top-3: {[(d, f'{c:.0%}') for d, c in top3]}")

    # Summary
    total_testable = len([t for t in REAL_WORLD_TESTS if t["expected"] is not None])
    accuracy = correct / total_testable if total_testable > 0 else 0

    safe_print("\n" + "="*70)
    safe_print(" VALIDATION SUMMARY")
    safe_print("="*70)
    safe_print(f"\nTotal Tests: {len(REAL_WORLD_TESTS)}")
    safe_print(f"Testable (with expected answer): {total_testable}")
    safe_print(f"Correct: {correct}")
    safe_print(f"Incorrect: {incorrect}")
    safe_print(f"Ambiguous (skipped): {ambiguous_correct}")
    safe_print(f"\n>>> REAL-WORLD ACCURACY: {accuracy:.1%} <<<")

    # Comparison with reported
    reported = metadata['accuracy']
    gap = reported - accuracy
    safe_print(f"\nReported Test Accuracy: {reported:.1%}")
    safe_print(f"Real-World Accuracy: {accuracy:.1%}")
    safe_print(f"Gap: {gap:.1%}")

    if gap > 0.10:
        safe_print("\nWARNING: Significant gap between test and real-world accuracy!")
        safe_print("   This suggests overfitting to training data patterns.")
    elif gap > 0.05:
        safe_print("\nCAUTION: Moderate gap - model may struggle with edge cases.")
    else:
        safe_print("\nGOOD: Real-world accuracy close to reported accuracy!")

    # Low confidence analysis
    safe_print(f"\n" + "-"*70)
    safe_print(f" LOW CONFIDENCE CASES (< 70%): {len(low_confidence_cases)}")
    safe_print("-"*70)
    for case in low_confidence_cases[:5]:
        safe_print(f"  {case['confidence']:.0%} - {case['prediction']}")

    # Wrong predictions analysis
    if wrong_predictions:
        safe_print(f"\n" + "-"*70)
        safe_print(f" WRONG PREDICTIONS: {len(wrong_predictions)}")
        safe_print("-"*70)
        for wp in wrong_predictions:
            safe_print(f"\n  Expected: {wp['expected']}")
            safe_print(f"  Got: {wp['predicted']} ({wp['confidence']:.0%})")
            safe_print(f"  Desc: {wp['description']}")

    # Final assessment
    safe_print("\n" + "="*70)
    safe_print(" PRODUCTION READINESS ASSESSMENT")
    safe_print("="*70)

    if accuracy >= 0.80:
        safe_print("\n[PRODUCTION READY]")
        safe_print("   Model performs well on real-world data.")
        safe_print("   Recommended: Deploy with confidence-based fallbacks.")
    elif accuracy >= 0.70:
        safe_print("\n[CONDITIONALLY READY]")
        safe_print("   Model is usable but needs guardrails.")
        safe_print("   Recommended: Use LLM fallback for confidence < 70%.")
    elif accuracy >= 0.60:
        safe_print("\n[NEEDS IMPROVEMENT]")
        safe_print("   Model struggles with real-world variations.")
        safe_print("   Recommended: Add more training data, especially edge cases.")
    else:
        safe_print("\n[NOT READY]")
        safe_print("   Model fails on real-world data.")
        safe_print("   Recommended: Retrain with real grievance samples.")

    return accuracy, len(low_confidence_cases), len(wrong_predictions)


if __name__ == "__main__":
    run_validation()
