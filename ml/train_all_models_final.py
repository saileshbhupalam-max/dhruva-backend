#!/usr/bin/env python3
"""
DHRUVA Final Model Training Pipeline
=====================================
Trains all ML models using consolidated knowledge base data.

Models to train:
1. MuRIL Sentiment (4-class: CRITICAL/HIGH/MEDIUM/NORMAL)
2. MuRIL Fallback Classifier (15 departments)

Uses data from:
- knowledge_base/tier1_core/
- knowledge_base/tier2_training/
- data/muril_training/
- data/extracted_docs/
"""

import json
import pickle
import random
import sys
from pathlib import Path
from datetime import datetime
from collections import Counter

import numpy as np
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, classification_report
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, VotingClassifier, GradientBoostingClassifier
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV

# Paths
BASE_DIR = Path(__file__).parent
KNOWLEDGE_BASE = BASE_DIR / "data" / "knowledge_base"
MURIL_DATA = BASE_DIR / "data" / "muril_training"
EXTRACTED_DOCS = BASE_DIR / "data" / "extracted_docs"
EXTRACTED_DATA = BASE_DIR / "data" / "extracted"
MODELS_DIR = BASE_DIR / "models"

# Ensure output directory
MODELS_DIR.mkdir(exist_ok=True)

# Top 15 departments
TOP_DEPARTMENTS = [
    "Revenue", "Municipal Administration", "Police", "Agriculture", "Health",
    "Education", "Energy", "Panchayat Raj", "Social Welfare", "Civil Supplies",
    "Transport", "Housing", "Water Resources", "Women & Child Welfare", "Animal Husbandry"
]

# Distress levels
DISTRESS_LEVELS = ["NORMAL", "MEDIUM", "HIGH", "CRITICAL"]


def load_json(path):
    """Load JSON file safely."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def safe_print(msg):
    """Print with encoding fallback."""
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode('ascii', 'replace').decode('ascii'))


# =============================================================================
# DATA LOADING FROM KNOWLEDGE BASE
# =============================================================================

def load_departments_data():
    """Load department keywords from knowledge base."""
    safe_print("\n" + "="*60)
    safe_print(" Loading Department Data from Knowledge Base")
    safe_print("="*60)

    dept_file = KNOWLEDGE_BASE / "tier1_core" / "departments.json"
    if not dept_file.exists():
        safe_print(f"WARNING: {dept_file} not found, using fallback")
        dept_file = EXTRACTED_DATA / "pgrs_book_keywords.json"

    data = load_json(dept_file)

    samples = []

    # Extract from knowledge base format
    if "departments" in data:
        for dept in data["departments"]:
            dept_name = dept.get("name_english", "")

            # Map to top 15
            mapped_dept = None
            for top_dept in TOP_DEPARTMENTS:
                if top_dept.lower() in dept_name.lower() or dept_name.lower() in top_dept.lower():
                    mapped_dept = top_dept
                    break

            if not mapped_dept:
                continue

            # Get keywords
            keywords_en = dept.get("keywords_english", [])
            keywords_te = dept.get("keywords_telugu", [])

            for kw in keywords_en + keywords_te:
                if kw and len(kw) > 1:
                    samples.append({"text": kw, "label": mapped_dept})

            # Get common subjects
            for subj in dept.get("common_subjects", []):
                if subj:
                    samples.append({"text": subj, "label": mapped_dept})

    safe_print(f"Loaded {len(samples)} department keyword samples")
    return samples


def load_grievance_types():
    """Load grievance types and distress keywords."""
    safe_print("\n" + "="*60)
    safe_print(" Loading Grievance Types from Knowledge Base")
    safe_print("="*60)

    types_file = KNOWLEDGE_BASE / "tier1_core" / "grievance_types.json"
    if not types_file.exists():
        safe_print(f"WARNING: {types_file} not found")
        return []

    data = load_json(types_file)
    samples = []

    # Extract distress keywords
    for level_data in data.get("distress_levels", []):
        level = level_data.get("level", "NORMAL")
        keywords_en = level_data.get("keywords_english", [])
        keywords_te = level_data.get("keywords_telugu", [])

        for kw in keywords_en + keywords_te:
            if kw:
                samples.append({"text": kw, "label": level})

    safe_print(f"Loaded {len(samples)} distress keyword samples")
    return samples


def load_response_templates():
    """Load official Telugu response templates."""
    safe_print("\n" + "="*60)
    safe_print(" Loading Response Templates")
    safe_print("="*60)

    templates_file = EXTRACTED_DOCS / "official_telugu_templates.json"
    if not templates_file.exists():
        safe_print(f"WARNING: {templates_file} not found")
        return []

    data = load_json(templates_file)
    templates = data.get("templates", [])

    safe_print(f"Loaded {len(templates)} response templates")
    return templates


def load_existing_training_data():
    """Load existing MuRIL training data."""
    safe_print("\n" + "="*60)
    safe_print(" Loading Existing Training Data")
    safe_print("="*60)

    sentiment_samples = []
    classification_samples = []

    # Sentiment
    sentiment_file = MURIL_DATA / "muril_sentiment_training.json"
    if sentiment_file.exists():
        data = load_json(sentiment_file)
        sentiment_samples = data.get("samples", [])
        safe_print(f"Loaded {len(sentiment_samples)} sentiment samples")

    # Classification
    class_file = MURIL_DATA / "muril_classification_training.json"
    if class_file.exists():
        data = load_json(class_file)
        classification_samples = data.get("samples", [])
        safe_print(f"Loaded {len(classification_samples)} classification samples")

    return sentiment_samples, classification_samples


def load_lapse_definitions():
    """Load lapse definitions for training features."""
    safe_print("\n" + "="*60)
    safe_print(" Loading Lapse Definitions")
    safe_print("="*60)

    lapse_file = KNOWLEDGE_BASE / "tier1_core" / "lapse_definitions.json"
    if not lapse_file.exists():
        lapse_file = EXTRACTED_DOCS / "lapse_definitions.json"

    if not lapse_file.exists():
        safe_print("WARNING: Lapse definitions not found")
        return []

    data = load_json(lapse_file)
    lapses = data.get("lapses", [])

    safe_print(f"Loaded {len(lapses)} lapse definitions")
    return lapses


# =============================================================================
# DATA AUGMENTATION
# =============================================================================

def augment_sentiment_data(samples, target_per_class=4000):
    """Augment sentiment data with templates."""
    safe_print("\n" + "="*60)
    safe_print(" Augmenting Sentiment Data")
    safe_print("="*60)

    # Distress templates
    DISTRESS_TEMPLATES = {
        "CRITICAL": [
            "{kw} వల్ల చనిపోతున్నాము",
            "{kw} లేక ప్రాణాలు పోతున్నాయి",
            "అత్యవసర {kw} సహాయం కావాలి",
            "{kw} emergency please help urgently",
            "{kw} causing death situation critical",
        ],
        "HIGH": [
            "{kw} 3 నెలలుగా రాలేదు",
            "{kw} ఆపేసారు సహాయం చేయండి",
            "{kw} denied need help desperately",
            "waiting for {kw} for months",
        ],
        "MEDIUM": [
            "{kw} ఆలస్యం అవుతుంది పరిష్కరించండి",
            "{kw} సమస్య ఉంది",
            "{kw} delay problem",
            "facing issue with {kw}",
        ],
        "NORMAL": [
            "{kw} సమాచారం కావాలి",
            "{kw} status తెలియజేయండి",
            "need information about {kw}",
            "query regarding {kw}",
        ]
    }

    # Distress keywords for augmentation
    DISTRESS_KEYWORDS = {
        "CRITICAL": ["pension", "పెన్షన్", "food", "ఆహారం", "medicine", "మందు", "hospital", "ఆసుపత్రి", "death", "మరణం"],
        "HIGH": ["ration", "రేషన్", "salary", "జీతం", "payment", "చెల్లింపు", "job", "ఉద్యోగం", "certificate", "సర్టిఫికేట్"],
        "MEDIUM": ["application", "దరఖాస్తు", "request", "అభ్యర్థన", "service", "సేవ", "bill", "బిల్లు", "repair", "మరమ్మత్తు"],
        "NORMAL": ["status", "స్థితి", "information", "సమాచారం", "query", "ప్రశ్న", "update", "నవీకరణ", "details", "వివరాలు"]
    }

    augmented = list(samples)

    for level, templates in DISTRESS_TEMPLATES.items():
        keywords = DISTRESS_KEYWORDS.get(level, [])
        current_count = len([s for s in augmented if s["label"] == level])
        needed = max(0, target_per_class - current_count)

        for _ in range(needed):
            kw = random.choice(keywords)
            template = random.choice(templates)
            text = template.replace("{kw}", kw)
            augmented.append({"text": text, "label": level})

    # Balance check
    dist = Counter([s["label"] for s in augmented])
    safe_print(f"Augmented distribution: {dict(dist)}")
    safe_print(f"Total samples: {len(augmented)}")

    return augmented


def augment_classification_data(samples, dept_data, target_per_class=200):
    """Augment classification data with department keywords."""
    safe_print("\n" + "="*60)
    safe_print(" Augmenting Classification Data")
    safe_print("="*60)

    # Telugu sentence templates by department type
    DEPT_TEMPLATES = {
        "default": [
            "{kw} సమస్య పరిష్కరించండి",
            "{kw} కోసం దరఖాస్తు చేసాను",
            "నా {kw} ఇంకా రాలేదు",
            "{kw} problem please solve",
            "need help with {kw}",
        ],
        "Revenue": [
            "{kw} పట్టా సమస్య",
            "నా భూమి {kw} కావాలి",
            "{kw} సర్వే చేయండి",
            "land {kw} issue",
        ],
        "Health": [
            "ఆసుపత్రిలో {kw} లేదు",
            "{kw} చికిత్స అందలేదు",
            "hospital {kw} problem",
        ],
        "Social Welfare": [
            "నా {kw} పెన్షన్ రాలేదు",
            "{kw} సంక్షేమ పథకం",
            "{kw} welfare scheme not received",
        ],
    }

    augmented = list(samples)

    # Add from department keywords
    for dept_sample in dept_data:
        if dept_sample["label"] in TOP_DEPARTMENTS:
            augmented.append(dept_sample)

    # Augment underrepresented classes
    for dept in TOP_DEPARTMENTS:
        current = [s for s in augmented if s["label"] == dept]
        current_count = len(current)

        if current_count < target_per_class and current_count > 0:
            needed = target_per_class - current_count
            templates = DEPT_TEMPLATES.get(dept, DEPT_TEMPLATES["default"])

            for _ in range(needed):
                base = random.choice(current)
                template = random.choice(templates)

                # Use existing text as keyword
                kw = base["text"][:30]  # Truncate long texts
                text = template.replace("{kw}", kw)
                augmented.append({"text": text, "label": dept})

    # Filter to top departments only
    augmented = [s for s in augmented if s["label"] in TOP_DEPARTMENTS]

    dist = Counter([s["label"] for s in augmented])
    safe_print(f"Classification distribution:")
    for dept in TOP_DEPARTMENTS:
        safe_print(f"  {dept}: {dist.get(dept, 0)}")
    safe_print(f"Total samples: {len(augmented)}")

    return augmented


# =============================================================================
# MODEL TRAINING
# =============================================================================

def train_sentiment_model(samples):
    """Train sentiment/distress detection model."""
    safe_print("\n" + "="*70)
    safe_print(" TRAINING SENTIMENT/DISTRESS MODEL")
    safe_print("="*70)

    # Prepare data
    texts = [s["text"] for s in samples]
    labels = [s["label"] for s in samples]

    # Encode labels
    label_encoder = LabelEncoder()
    label_encoder.classes_ = np.array(DISTRESS_LEVELS)
    y = label_encoder.transform(labels)

    safe_print(f"\nSamples: {len(texts)}")
    safe_print(f"Classes: {len(DISTRESS_LEVELS)}")

    # TF-IDF
    safe_print("\nCreating TF-IDF features...")
    vectorizer = TfidfVectorizer(
        analyzer='char_wb',
        ngram_range=(2, 5),
        max_features=8000,
        min_df=2,
        sublinear_tf=True,
        lowercase=False
    )
    X = vectorizer.fit_transform(texts)
    safe_print(f"Feature matrix: {X.shape}")

    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Train ensemble
    safe_print("\nTraining ensemble model...")

    lr = LogisticRegression(max_iter=2000, class_weight='balanced', C=1.0, random_state=42)
    rf = RandomForestClassifier(n_estimators=150, max_depth=15, class_weight='balanced', random_state=42)
    svm = CalibratedClassifierCV(LinearSVC(max_iter=3000, class_weight='balanced', random_state=42))

    # Train individual models
    lr.fit(X_train, y_train)
    lr_acc = accuracy_score(y_test, lr.predict(X_test))
    safe_print(f"  Logistic Regression: {lr_acc:.2%}")

    rf.fit(X_train, y_train)
    rf_acc = accuracy_score(y_test, rf.predict(X_test))
    safe_print(f"  Random Forest: {rf_acc:.2%}")

    svm.fit(X_train, y_train)
    svm_acc = accuracy_score(y_test, svm.predict(X_test))
    safe_print(f"  SVM: {svm_acc:.2%}")

    # Ensemble
    ensemble = VotingClassifier(
        estimators=[('lr', lr), ('rf', rf), ('svm', svm)],
        voting='soft'
    )
    ensemble.fit(X_train, y_train)

    y_pred = ensemble.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)

    # Top-N accuracy
    y_proba = ensemble.predict_proba(X_test)
    top2_correct = sum(1 for i, p in enumerate(y_proba) if y_test[i] in np.argsort(p)[-2:])
    top2_acc = top2_correct / len(y_test)

    safe_print(f"\n  ENSEMBLE Accuracy: {accuracy:.2%}")
    safe_print(f"  Top-2 Accuracy: {top2_acc:.2%}")

    # Cross-validation
    safe_print("\nCross-validation...")
    cv_scores = cross_val_score(lr, X, y, cv=5, scoring='accuracy')
    safe_print(f"CV Mean: {cv_scores.mean():.2%} (+/- {cv_scores.std()*2:.2%})")

    # Save
    safe_print("\nSaving sentiment model...")

    with open(MODELS_DIR / "sentiment_classifier.pkl", 'wb') as f:
        pickle.dump(ensemble, f)

    with open(MODELS_DIR / "sentiment_vectorizer.pkl", 'wb') as f:
        pickle.dump(vectorizer, f)

    with open(MODELS_DIR / "sentiment_label_encoder.pkl", 'wb') as f:
        pickle.dump(label_encoder, f)

    metadata = {
        "model": "sentiment_classifier",
        "version": "1.0",
        "created": datetime.now().isoformat(),
        "accuracy": accuracy,
        "top2_accuracy": top2_acc,
        "cv_mean": float(cv_scores.mean()),
        "classes": DISTRESS_LEVELS,
        "num_classes": 4,
        "train_samples": len(X_train.toarray()),
        "test_samples": len(X_test.toarray()),
        "individual_models": {"lr": lr_acc, "rf": rf_acc, "svm": svm_acc}
    }

    with open(MODELS_DIR / "sentiment_classifier_metadata.json", 'w') as f:
        json.dump(metadata, f, indent=2)

    safe_print(f"Saved to: {MODELS_DIR / 'sentiment_classifier.pkl'}")

    return accuracy, ensemble, vectorizer, label_encoder


def train_classification_model(samples):
    """Train department classification fallback model."""
    safe_print("\n" + "="*70)
    safe_print(" TRAINING DEPARTMENT CLASSIFICATION (FALLBACK) MODEL")
    safe_print("="*70)

    # Filter valid samples
    samples = [s for s in samples if s["label"] in TOP_DEPARTMENTS]

    texts = [s["text"] for s in samples]
    labels = [s["label"] for s in samples]

    # Encode labels
    label_encoder = LabelEncoder()
    label_encoder.classes_ = np.array(TOP_DEPARTMENTS)
    y = label_encoder.transform(labels)

    safe_print(f"\nSamples: {len(texts)}")
    safe_print(f"Classes: {len(TOP_DEPARTMENTS)}")

    # TF-IDF
    safe_print("\nCreating TF-IDF features...")
    vectorizer = TfidfVectorizer(
        analyzer='char_wb',
        ngram_range=(2, 6),
        max_features=10000,
        min_df=2,
        sublinear_tf=True,
        lowercase=False
    )
    X = vectorizer.fit_transform(texts)
    safe_print(f"Feature matrix: {X.shape}")

    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Train ensemble
    safe_print("\nTraining ensemble model...")

    lr = LogisticRegression(max_iter=2000, class_weight='balanced', C=1.0, random_state=42)
    rf = RandomForestClassifier(n_estimators=200, max_depth=20, class_weight='balanced', random_state=42)
    svm = CalibratedClassifierCV(LinearSVC(max_iter=5000, class_weight='balanced', random_state=42))

    lr.fit(X_train, y_train)
    lr_acc = accuracy_score(y_test, lr.predict(X_test))
    safe_print(f"  Logistic Regression: {lr_acc:.2%}")

    rf.fit(X_train, y_train)
    rf_acc = accuracy_score(y_test, rf.predict(X_test))
    safe_print(f"  Random Forest: {rf_acc:.2%}")

    svm.fit(X_train, y_train)
    svm_acc = accuracy_score(y_test, svm.predict(X_test))
    safe_print(f"  SVM: {svm_acc:.2%}")

    # Ensemble
    ensemble = VotingClassifier(
        estimators=[('lr', lr), ('rf', rf), ('svm', svm)],
        voting='soft'
    )
    ensemble.fit(X_train, y_train)

    y_pred = ensemble.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)

    # Top-N accuracy
    y_proba = ensemble.predict_proba(X_test)
    top3_correct = sum(1 for i, p in enumerate(y_proba) if y_test[i] in np.argsort(p)[-3:])
    top3_acc = top3_correct / len(y_test)
    top5_correct = sum(1 for i, p in enumerate(y_proba) if y_test[i] in np.argsort(p)[-5:])
    top5_acc = top5_correct / len(y_test)

    safe_print(f"\n  ENSEMBLE Accuracy: {accuracy:.2%}")
    safe_print(f"  Top-3 Accuracy: {top3_acc:.2%}")
    safe_print(f"  Top-5 Accuracy: {top5_acc:.2%}")

    # Cross-validation
    safe_print("\nCross-validation...")
    cv_scores = cross_val_score(lr, X, y, cv=5, scoring='accuracy')
    safe_print(f"CV Mean: {cv_scores.mean():.2%} (+/- {cv_scores.std()*2:.2%})")

    # Save
    safe_print("\nSaving classification fallback model...")

    with open(MODELS_DIR / "classification_fallback.pkl", 'wb') as f:
        pickle.dump(ensemble, f)

    with open(MODELS_DIR / "classification_fallback_vectorizer.pkl", 'wb') as f:
        pickle.dump(vectorizer, f)

    with open(MODELS_DIR / "classification_fallback_label_encoder.pkl", 'wb') as f:
        pickle.dump(label_encoder, f)

    metadata = {
        "model": "classification_fallback",
        "version": "1.0",
        "created": datetime.now().isoformat(),
        "accuracy": accuracy,
        "top3_accuracy": top3_acc,
        "top5_accuracy": top5_acc,
        "cv_mean": float(cv_scores.mean()),
        "classes": TOP_DEPARTMENTS,
        "num_classes": 15,
        "train_samples": len(X_train.toarray()),
        "test_samples": len(X_test.toarray()),
        "individual_models": {"lr": lr_acc, "rf": rf_acc, "svm": svm_acc}
    }

    with open(MODELS_DIR / "classification_fallback_metadata.json", 'w') as f:
        json.dump(metadata, f, indent=2)

    safe_print(f"Saved to: {MODELS_DIR / 'classification_fallback.pkl'}")

    return accuracy, ensemble, vectorizer, label_encoder


# =============================================================================
# REAL-WORLD VALIDATION
# =============================================================================

def validate_sentiment_model(model, vectorizer, label_encoder):
    """Validate sentiment model with real-world tests."""
    safe_print("\n" + "="*70)
    safe_print(" REAL-WORLD VALIDATION: SENTIMENT MODEL")
    safe_print("="*70)

    test_cases = [
        ("నా పెన్షన్ 6 నెలలుగా రాలేదు ఆకలితో చనిపోతున్నాము", "CRITICAL"),
        ("pension not coming for months we are starving", "CRITICAL"),
        ("మందులు లేవు చాలా emergency", "CRITICAL"),
        ("నా రేషన్ కార్డు 3 నెలలుగా రాలేదు", "HIGH"),
        ("ration card stopped need help", "HIGH"),
        ("certificate ఇంకా రాలేదు", "MEDIUM"),
        ("road repair delay problem", "MEDIUM"),
        ("application status తెలియజేయండి", "NORMAL"),
        ("need information about scheme", "NORMAL"),
    ]

    correct = 0
    for text, expected in test_cases:
        X = vectorizer.transform([text])
        pred_idx = model.predict(X)[0]
        pred = label_encoder.inverse_transform([pred_idx])[0]

        proba = model.predict_proba(X)[0]
        conf = proba[pred_idx]

        status = "OK" if pred == expected else "WRONG"
        if pred != expected:
            # Check if in top 2
            top2 = np.argsort(proba)[-2:]
            exp_idx = label_encoder.transform([expected])[0]
            if exp_idx in top2:
                status = "TOP-2"
        else:
            correct += 1

        safe_print(f"  [{status}] {expected} -> {pred} ({conf:.0%})")

    accuracy = correct / len(test_cases)
    safe_print(f"\nReal-world accuracy: {accuracy:.1%}")
    return accuracy


def validate_classification_model(model, vectorizer, label_encoder):
    """Validate classification model with real-world tests."""
    safe_print("\n" + "="*70)
    safe_print(" REAL-WORLD VALIDATION: CLASSIFICATION MODEL")
    safe_print("="*70)

    test_cases = [
        ("భూమి పట్టా సమస్య పరిష్కరించండి", "Revenue"),
        ("land survey not done", "Revenue"),
        ("పెన్షన్ రాలేదు సహాయం చేయండి", "Social Welfare"),
        ("pension delay problem", "Social Welfare"),
        ("రోడ్డు గుంతలు మరమ్మతు చేయండి", "Municipal Administration"),
        ("drainage problem in our area", "Municipal Administration"),
        ("పంట నష్టం పరిహారం కావాలి", "Agriculture"),
        ("crop insurance claim", "Agriculture"),
        ("ఆసుపత్రిలో డాక్టర్ లేరు", "Health"),
        ("PHC medicine not available", "Health"),
        ("electricity bill too high", "Energy"),
        ("విద్యుత్ కనెక్షన్ ఇవ్వండి", "Energy"),
        ("రేషన్ దుకాణంలో బియ్యం ఇవ్వడం లేదు", "Civil Supplies"),
        ("ration card not received", "Civil Supplies"),
        ("FIR నమోదు చేయండి", "Police"),
    ]

    correct = 0
    for text, expected in test_cases:
        X = vectorizer.transform([text])
        pred_idx = model.predict(X)[0]
        pred = label_encoder.inverse_transform([pred_idx])[0]

        proba = model.predict_proba(X)[0]
        conf = proba[pred_idx]

        status = "OK" if pred == expected else "WRONG"
        if pred != expected:
            top3 = np.argsort(proba)[-3:]
            exp_idx = label_encoder.transform([expected])[0]
            if exp_idx in top3:
                status = "TOP-3"
        else:
            correct += 1

        safe_print(f"  [{status}] {expected} -> {pred} ({conf:.0%})")

    accuracy = correct / len(test_cases)
    safe_print(f"\nReal-world accuracy: {accuracy:.1%}")
    return accuracy


# =============================================================================
# MAIN
# =============================================================================

def main():
    safe_print("\n" + "="*70)
    safe_print(" DHRUVA FINAL MODEL TRAINING")
    safe_print(" Using Knowledge Base + All Available Data")
    safe_print("="*70)

    # 1. Load all data from knowledge base
    dept_data = load_departments_data()
    grievance_data = load_grievance_types()
    templates = load_response_templates()
    sentiment_samples, classification_samples = load_existing_training_data()
    lapses = load_lapse_definitions()

    # 2. Augment data
    sentiment_augmented = augment_sentiment_data(sentiment_samples, target_per_class=4000)
    classification_augmented = augment_classification_data(
        classification_samples, dept_data, target_per_class=250
    )

    # 3. Train Sentiment Model
    sent_acc, sent_model, sent_vec, sent_enc = train_sentiment_model(sentiment_augmented)

    # 4. Train Classification Fallback Model
    class_acc, class_model, class_vec, class_enc = train_classification_model(classification_augmented)

    # 5. Real-world validation
    sent_real = validate_sentiment_model(sent_model, sent_vec, sent_enc)
    class_real = validate_classification_model(class_model, class_vec, class_enc)

    # 6. Final Summary
    safe_print("\n" + "="*70)
    safe_print(" TRAINING COMPLETE - FINAL SUMMARY")
    safe_print("="*70)

    safe_print("\n| Model                    | Test Acc | Real-World | Status |")
    safe_print("|--------------------------|----------|------------|--------|")
    safe_print(f"| Telugu Classifier V3     | 84.5%    | 82.1%      | DONE   |")
    safe_print(f"| Lapse Predictor          | 80.8%    | TBD        | DONE   |")
    safe_print(f"| Sentiment Classifier     | {sent_acc:.1%}    | {sent_real:.1%}      | NEW    |")
    safe_print(f"| Classification Fallback  | {class_acc:.1%}    | {class_real:.1%}      | NEW    |")

    safe_print("\nModels saved to:")
    safe_print(f"  - {MODELS_DIR / 'sentiment_classifier.pkl'}")
    safe_print(f"  - {MODELS_DIR / 'classification_fallback.pkl'}")

    # Save final summary
    summary = {
        "training_completed": datetime.now().isoformat(),
        "models": {
            "telugu_classifier_v3": {"test_accuracy": 0.845, "real_world": 0.821, "status": "production_ready"},
            "lapse_predictor": {"test_accuracy": 0.808, "real_world": "TBD", "status": "ready"},
            "sentiment_classifier": {"test_accuracy": sent_acc, "real_world": sent_real, "status": "new"},
            "classification_fallback": {"test_accuracy": class_acc, "real_world": class_real, "status": "new"}
        },
        "data_sources": [
            "knowledge_base/tier1_core/departments.json",
            "knowledge_base/tier1_core/grievance_types.json",
            "muril_training/muril_sentiment_training.json",
            "muril_training/muril_classification_training.json"
        ]
    }

    with open(MODELS_DIR / "training_summary.json", 'w') as f:
        json.dump(summary, f, indent=2)

    safe_print(f"\nSummary saved to: {MODELS_DIR / 'training_summary.json'}")


if __name__ == "__main__":
    main()
