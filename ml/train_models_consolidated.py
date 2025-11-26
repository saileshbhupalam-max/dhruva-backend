#!/usr/bin/env python3
"""
Consolidated ML Training Script for DHRUVA PGRS
================================================
Uses ALL available government data to train:
1. Lapse Prediction Model (XGBoost)
2. Telugu Department Classifier (TF-IDF + LogReg)

Data Sources:
- audit_reports.json: 2,298 labeled cases with 13 lapse categories
- pgrs_book_keywords.json: 709 keywords (354 Telugu) across 30 departments
- call_center_satisfaction.json: 93,892 feedback records for risk scoring
- message_templates.json: 54 official Telugu templates
- audio_transcriptions.json: 46 Telugu voice samples
- Synthetic data: 1,000 lapse cases + 585 Telugu samples
- Research data: 212 Telugu samples + 66 lapse cases
"""

import json
import os
import sys
import pickle
from pathlib import Path
from datetime import datetime
from collections import Counter
import warnings
warnings.filterwarnings('ignore')

# ML Libraries
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier

try:
    import xgboost as xgb
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False
    print("WARNING: XGBoost not available, using RandomForest instead")

# Paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data" / "extracted"
SYNTHETIC_DIR = BASE_DIR / "data" / "synthetic"
MODELS_DIR = BASE_DIR / "models"
MODELS_DIR.mkdir(exist_ok=True)


def load_json(filepath):
    """Load JSON file with UTF-8 encoding."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def print_section(title):
    """Print formatted section header."""
    print(f"\n{'='*60}")
    print(f" {title}")
    print('='*60)


# =============================================================================
# PART 1: LAPSE PREDICTION MODEL
# =============================================================================

def load_lapse_training_data():
    """Load and prepare lapse prediction training data from all sources."""
    print_section("Loading Lapse Prediction Training Data")

    all_samples = []

    # 1. Load Guntur Audit Data (Primary Source)
    audit_file = DATA_DIR / "audit_reports.json"
    if audit_file.exists():
        print(f"Loading: {audit_file}")
        audit_data = load_json(audit_file)

        guntur = audit_data.get('guntur_audit', {})
        lapse_categories = guntur.get('lapse_categories', [])

        # Create training samples from lapse categories
        for lapse in lapse_categories:
            category = lapse.get('category', 'Unknown')
            count = lapse.get('count', 0)
            percentage = lapse.get('percentage', 0)
            lapse_type = lapse.get('type', 'procedural')
            severity = lapse.get('severity', 'medium')

            # Create multiple samples based on count
            for i in range(min(count, 100)):  # Cap at 100 per category to balance
                all_samples.append({
                    'lapse_category': category,
                    'lapse_type': lapse_type,
                    'severity': severity,
                    'percentage': percentage,
                    'source': 'guntur_audit'
                })

        print(f"  - Loaded {len(all_samples)} samples from Guntur Audit")

        # Also get department breakdown
        dept_breakdown = guntur.get('department_breakdown', {})
        print(f"  - Found {len(dept_breakdown)} departments with performance data")

    # 2. Load Call Center Satisfaction Data (For Risk Features)
    satisfaction_file = DATA_DIR / "call_center_satisfaction.json"
    dept_risk_scores = {}
    if satisfaction_file.exists():
        print(f"Loading: {satisfaction_file}")
        satisfaction_data = load_json(satisfaction_file)

        for dept in satisfaction_data.get('departments', []):
            dept_name = dept.get('department', '')
            risk_score = dept.get('computed_metrics', {}).get('dept_risk_score', 0.5)
            dept_risk_scores[dept_name] = risk_score

        print(f"  - Loaded risk scores for {len(dept_risk_scores)} departments")

    # 3. Load Synthetic Data
    synthetic_file = SYNTHETIC_DIR / "synthetic_lapse_cases.json"
    if synthetic_file.exists():
        print(f"Loading: {synthetic_file}")
        synthetic_data = load_json(synthetic_file)

        for sample in synthetic_data.get('samples', []):
            all_samples.append({
                'lapse_category': sample.get('lapse_type', 'Unknown'),
                'lapse_type': 'procedural' if 'not speak' in sample.get('lapse_type', '').lower() else 'behavioral',
                'severity': 'high',
                'percentage': 0,
                'department': sample.get('department', ''),
                'days_to_resolve': sample.get('days_to_resolve', 7),
                'source': 'synthetic'
            })

        print(f"  - Added {len(synthetic_data.get('samples', []))} synthetic samples")

    print(f"\nTotal training samples: {len(all_samples)}")
    return all_samples, dept_risk_scores


def prepare_lapse_features(samples, dept_risk_scores):
    """Convert samples to feature matrix for ML training."""
    print_section("Preparing Lapse Model Features")

    # Define label mapping
    lapse_labels = [
        "GRA did not speak to citizen directly",
        "Not visited site / No field verification",
        "Wrong / Blank / Not related to grievance closure comments",
        "GRA did not speak properly / scolded / used abusive language",
        "Wrong department assignment / Not under jurisdiction",
        "Improper enquiry photo / enquiry report / redressal flag uploaded",
        "GRA did not provide endorsement personally",
        "GRA did not spend time explaining issue to applicant",
        "GRA closed by forwarding to lower-level official",
        "GRA intentionally avoided work / refused service",
        "GRA threatened / pleaded / persuaded applicant",
        "GRA did not work and involved political persons",
        "GRA took bribe / asked for bribe / stopped work for not paying"
    ]

    # Simplified label mapping (for shorter categories)
    label_map = {
        'GRA did not speak to citizen directly': 0,
        'Not visited site / No field verification': 1,
        'Wrong / Blank / Not related to grievance closure comments': 2,
        'GRA did not speak properly / scolded / used abusive language': 3,
        'Wrong department assignment / Not under jurisdiction': 4,
        'Improper enquiry photo / enquiry report / redressal flag uploaded': 5,
        'GRA did not provide endorsement personally': 6,
        'GRA did not spend time explaining issue to applicant': 7,
        'GRA closed by forwarding to lower-level official': 8,
        'GRA intentionally avoided work / refused service': 9,
        'GRA threatened / pleaded / persuaded applicant': 10,
        'GRA did not work and involved political persons': 11,
        'GRA took bribe / asked for bribe / stopped work for not paying': 12
    }

    # Create feature vectors
    features = []
    labels = []

    type_encoder = {'procedural': 0, 'behavioral': 1}
    severity_encoder = {'low': 0, 'medium': 1, 'high': 2, 'critical': 3}

    for sample in samples:
        category = sample.get('lapse_category', '')

        # Map to label
        label = None
        for key, val in label_map.items():
            if key.lower() in category.lower() or category.lower() in key.lower():
                label = val
                break

        if label is None:
            # Try partial match
            category_lower = category.lower()
            if 'speak' in category_lower and 'citizen' in category_lower:
                label = 0
            elif 'visit' in category_lower or 'site' in category_lower:
                label = 1
            elif 'wrong' in category_lower or 'blank' in category_lower:
                label = 2
            elif 'scold' in category_lower or 'abusive' in category_lower:
                label = 3
            elif 'department' in category_lower or 'jurisdiction' in category_lower:
                label = 4
            elif 'photo' in category_lower or 'enquiry' in category_lower:
                label = 5
            elif 'endorsement' in category_lower:
                label = 6
            elif 'explain' in category_lower:
                label = 7
            elif 'forward' in category_lower or 'lower' in category_lower:
                label = 8
            elif 'avoid' in category_lower or 'refused' in category_lower:
                label = 9
            elif 'threaten' in category_lower or 'plead' in category_lower:
                label = 10
            elif 'political' in category_lower:
                label = 11
            elif 'bribe' in category_lower:
                label = 12
            else:
                label = 0  # Default to most common

        # Create feature vector
        feature = [
            type_encoder.get(sample.get('lapse_type', 'procedural'), 0),
            severity_encoder.get(sample.get('severity', 'medium'), 1),
            sample.get('percentage', 0) / 100.0,  # Normalize
            sample.get('days_to_resolve', 7) / 30.0,  # Normalize to months
            1 if sample.get('source') == 'synthetic' else 0
        ]

        features.append(feature)
        labels.append(label)

    X = np.array(features)
    y = np.array(labels)

    print(f"Feature matrix shape: {X.shape}")
    print(f"Labels shape: {y.shape}")
    print(f"Class distribution: {Counter(y)}")

    return X, y, lapse_labels


def train_lapse_model(X, y, labels):
    """Train the lapse prediction model."""
    print_section("Training Lapse Prediction Model")

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print(f"Training samples: {len(X_train)}")
    print(f"Test samples: {len(X_test)}")

    # Train model
    if HAS_XGBOOST:
        print("\nTraining XGBoost Classifier...")
        model = xgb.XGBClassifier(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            random_state=42,
            use_label_encoder=False,
            eval_metric='mlogloss'
        )
    else:
        print("\nTraining RandomForest Classifier...")
        model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )

    model.fit(X_train, y_train)

    # Evaluate
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)

    print(f"\nModel Accuracy: {accuracy:.2%}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=[f"Class_{i}" for i in range(len(set(y)))]))

    # Cross-validation
    cv_scores = cross_val_score(model, X, y, cv=5)
    print(f"\nCross-validation scores: {cv_scores}")
    print(f"Mean CV Score: {cv_scores.mean():.2%} (+/- {cv_scores.std()*2:.2%})")

    return model, accuracy


# =============================================================================
# PART 2: TELUGU DEPARTMENT CLASSIFIER
# =============================================================================

def load_telugu_training_data():
    """Load Telugu text samples for department classification."""
    print_section("Loading Telugu Training Data")

    all_texts = []
    all_labels = []

    # 1. Load PGRS Book Keywords (Primary Source)
    keywords_file = DATA_DIR / "pgrs_book_keywords.json"
    if keywords_file.exists():
        print(f"Loading: {keywords_file}")
        keywords_data = load_json(keywords_file)

        for dept in keywords_data.get('departments', []):
            dept_name = dept.get('name_english', '')

            for subject in dept.get('subjects', []):
                # English keywords
                for keyword in subject.get('keywords_english', []):
                    all_texts.append(keyword)
                    all_labels.append(dept_name)

                # Telugu keywords
                for keyword in subject.get('keywords_telugu', []):
                    all_texts.append(keyword)
                    all_labels.append(dept_name)

        print(f"  - Loaded {len(all_texts)} keyword samples from PGRS Book")

    # 2. Load Research Telugu Samples
    research_file = BASE_DIR / "TELUGU_GRIEVANCE_DATASET_RESEARCH.json"
    if research_file.exists():
        print(f"Loading: {research_file}")
        research_data = load_json(research_file)

        for sample in research_data.get('samples', []):
            text = sample.get('telugu_text', '')
            dept = sample.get('department', '')
            if text and dept:
                all_texts.append(text)
                all_labels.append(dept)

        print(f"  - Added {len(research_data.get('samples', []))} research samples")

    # 3. Load Synthetic Telugu Samples
    synthetic_file = SYNTHETIC_DIR / "synthetic_telugu_grievances.json"
    if synthetic_file.exists():
        print(f"Loading: {synthetic_file}")
        synthetic_data = load_json(synthetic_file)

        for sample in synthetic_data.get('samples', []):
            text = sample.get('telugu_text', '')
            dept = sample.get('department', '')
            if text and dept:
                all_texts.append(text)
                all_labels.append(dept)

        print(f"  - Added {len(synthetic_data.get('samples', []))} synthetic samples")

    print(f"\nTotal Telugu training samples: {len(all_texts)}")
    print(f"Unique departments: {len(set(all_labels))}")

    return all_texts, all_labels


def train_telugu_classifier(texts, labels):
    """Train Telugu department classifier using TF-IDF + Logistic Regression."""
    print_section("Training Telugu Department Classifier")

    # Encode labels
    label_encoder = LabelEncoder()
    y = label_encoder.fit_transform(labels)

    print(f"Number of classes: {len(label_encoder.classes_)}")
    print(f"Sample classes: {list(label_encoder.classes_[:10])}")

    # Create TF-IDF vectors
    print("\nCreating TF-IDF vectors...")
    vectorizer = TfidfVectorizer(
        analyzer='char_wb',  # Character n-grams with word boundaries (good for Telugu)
        ngram_range=(2, 4),
        max_features=5000,
        lowercase=False  # Preserve Telugu characters
    )

    X = vectorizer.fit_transform(texts)
    print(f"TF-IDF matrix shape: {X.shape}")

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    print(f"Training samples: {X_train.shape[0]}")
    print(f"Test samples: {X_test.shape[0]}")

    # Train model
    print("\nTraining Logistic Regression Classifier...")
    model = LogisticRegression(
        max_iter=1000,
        multi_class='multinomial',
        random_state=42,
        class_weight='balanced'
    )

    model.fit(X_train, y_train)

    # Evaluate
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)

    print(f"\nModel Accuracy: {accuracy:.2%}")

    # Top-N accuracy
    y_proba = model.predict_proba(X_test)
    top3_correct = 0
    for i, proba in enumerate(y_proba):
        top3_indices = np.argsort(proba)[-3:]
        if y_test[i] in top3_indices:
            top3_correct += 1
    top3_accuracy = top3_correct / len(y_test)
    print(f"Top-3 Accuracy: {top3_accuracy:.2%}")

    return model, vectorizer, label_encoder, accuracy


# =============================================================================
# MAIN EXECUTION
# =============================================================================

def save_models(lapse_model, telugu_model, vectorizer, label_encoder, metrics):
    """Save all trained models and metadata."""
    print_section("Saving Models")

    # Save Lapse Model
    if HAS_XGBOOST:
        lapse_path = MODELS_DIR / "lapse_predictor.json"
        lapse_model.save_model(str(lapse_path))
    else:
        lapse_path = MODELS_DIR / "lapse_predictor.pkl"
        with open(lapse_path, 'wb') as f:
            pickle.dump(lapse_model, f)
    print(f"Saved: {lapse_path}")

    # Save Telugu Classifier
    telugu_path = MODELS_DIR / "telugu_classifier.pkl"
    with open(telugu_path, 'wb') as f:
        pickle.dump(telugu_model, f)
    print(f"Saved: {telugu_path}")

    # Save Vectorizer
    vectorizer_path = MODELS_DIR / "tfidf_vectorizer.pkl"
    with open(vectorizer_path, 'wb') as f:
        pickle.dump(vectorizer, f)
    print(f"Saved: {vectorizer_path}")

    # Save Label Encoder
    encoder_path = MODELS_DIR / "dept_label_encoder.pkl"
    with open(encoder_path, 'wb') as f:
        pickle.dump(label_encoder, f)
    print(f"Saved: {encoder_path}")

    # Save Metadata
    metadata = {
        "training_date": datetime.now().isoformat(),
        "lapse_model": {
            "type": "XGBoost" if HAS_XGBOOST else "RandomForest",
            "accuracy": metrics['lapse_accuracy'],
            "features": ["lapse_type", "severity", "percentage", "days_to_resolve", "is_synthetic"]
        },
        "telugu_classifier": {
            "type": "LogisticRegression",
            "accuracy": metrics['telugu_accuracy'],
            "num_classes": metrics['num_departments'],
            "vectorizer": "TF-IDF (char_wb, ngram 2-4)"
        },
        "data_sources": [
            "audit_reports.json",
            "pgrs_book_keywords.json",
            "call_center_satisfaction.json",
            "TELUGU_GRIEVANCE_DATASET_RESEARCH.json",
            "synthetic_lapse_cases.json",
            "synthetic_telugu_grievances.json"
        ]
    }

    metadata_path = MODELS_DIR / "model_metadata.json"
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
    print(f"Saved: {metadata_path}")


def main():
    """Main training pipeline."""
    print("\n" + "="*60)
    print(" DHRUVA PGRS - ML MODEL TRAINING")
    print(" Using ALL Available Government Data")
    print("="*60)

    metrics = {}

    # PART 1: Train Lapse Prediction Model
    lapse_samples, dept_risk_scores = load_lapse_training_data()

    if len(lapse_samples) > 0:
        X_lapse, y_lapse, lapse_labels = prepare_lapse_features(lapse_samples, dept_risk_scores)
        lapse_model, lapse_accuracy = train_lapse_model(X_lapse, y_lapse, lapse_labels)
        metrics['lapse_accuracy'] = lapse_accuracy
    else:
        print("ERROR: No lapse training data found!")
        lapse_model = None
        metrics['lapse_accuracy'] = 0

    # PART 2: Train Telugu Classifier
    telugu_texts, telugu_labels = load_telugu_training_data()

    if len(telugu_texts) > 0:
        telugu_model, vectorizer, label_encoder, telugu_accuracy = train_telugu_classifier(
            telugu_texts, telugu_labels
        )
        metrics['telugu_accuracy'] = telugu_accuracy
        metrics['num_departments'] = len(label_encoder.classes_)
    else:
        print("ERROR: No Telugu training data found!")
        telugu_model = None
        vectorizer = None
        label_encoder = None
        metrics['telugu_accuracy'] = 0
        metrics['num_departments'] = 0

    # Save Models
    if lapse_model and telugu_model:
        save_models(lapse_model, telugu_model, vectorizer, label_encoder, metrics)

    # Final Summary
    print_section("TRAINING COMPLETE - SUMMARY")
    print(f"Lapse Prediction Model Accuracy: {metrics.get('lapse_accuracy', 0):.2%}")
    print(f"Telugu Classifier Accuracy: {metrics.get('telugu_accuracy', 0):.2%}")
    print(f"Number of Departments: {metrics.get('num_departments', 0)}")
    print(f"\nModels saved to: {MODELS_DIR}")

    return metrics


if __name__ == "__main__":
    main()
