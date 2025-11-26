#!/usr/bin/env python3
"""
Telugu Department Classifier V2 - With Department Consolidation
===============================================================
Improves accuracy by:
1. Consolidating duplicate department names
2. Using word-level TF-IDF for better Telugu handling
3. Adding proper department normalization
"""

import json
import pickle
from pathlib import Path
from collections import Counter
import warnings
warnings.filterwarnings('ignore')

import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, accuracy_score
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data" / "extracted"
SYNTHETIC_DIR = BASE_DIR / "data" / "synthetic"
MODELS_DIR = BASE_DIR / "models"


# Department Consolidation Map - Maps variations to canonical names
DEPT_CONSOLIDATION = {
    # Agriculture variations
    'agriculture': 'Agriculture',
    'agriculture and co-operation': 'Agriculture',
    'agriculture and cooperation': 'Agriculture',

    # Animal Husbandry variations
    'animal husbandry': 'Animal Husbandry',
    'animal husbandry, dairy development and fisheries': 'Animal Husbandry',

    # Consumer Affairs variations
    'civil supplies': 'Civil Supplies',
    'consumer affairs, food and civil supplies': 'Civil Supplies',

    # Education variations
    'education': 'Education',
    'school education': 'Education',
    'human resources (school education)': 'Education',
    'human resources (higher education)': 'Higher Education',

    # Energy variations
    'energy': 'Energy',
    'electricity': 'Energy',

    # Environment variations
    'environment, forest, science and technology': 'Environment & Forest',
    'forest': 'Environment & Forest',

    # Finance variations
    'finance': 'Finance',

    # Health variations
    'health': 'Health',
    'health, medical and family welfare': 'Health',
    'medical': 'Health',

    # Home/Police variations
    'police': 'Police',
    'home (police)': 'Police',

    # Housing variations
    'housing': 'Housing',

    # Municipal variations
    'municipal administration': 'Municipal Administration',
    'municipal administration and urban development': 'Municipal Administration',

    # Panchayat variations
    'panchayat raj': 'Panchayat Raj',
    'panchayat raj and rural development': 'Panchayat Raj',
    'panchayati raj': 'Panchayat Raj',

    # Revenue variations
    'revenue': 'Revenue',
    'revenue (ccla)': 'Revenue',

    # Social Welfare variations
    'social welfare': 'Social Welfare',

    # Transport variations
    'transport': 'Transport',
    'transport, roads and buildings': 'Transport',

    # Water variations
    'water resources': 'Water Resources',
    'water supply': 'Water Resources',

    # Women & Child variations
    'women development and child welfare': 'Women & Child Welfare',
    'women, children, disabled and senior citizens': 'Women & Child Welfare',

    # Other departments
    'backward classes welfare': 'BC Welfare',
    'minorities welfare': 'Minorities Welfare',
    'tribal welfare': 'Tribal Welfare',
    'disaster management': 'Disaster Management',
    'industries and commerce': 'Industries',
    'labour, factories, boilers and insurance medical services': 'Labour',
    'labour': 'Labour',
    'law': 'Law',
    'planning': 'Planning',
    'department of skills development and training': 'Skills & Training',
    'grama volunteers/ward volunteers and village secretariats/ward secretariats': 'Village Secretariat',
    'general administration': 'General Administration',
    'youth advancement, tourism and culture': 'Tourism & Culture',
}


def normalize_department(dept_name):
    """Normalize department name to canonical form."""
    if not dept_name:
        return 'Other'

    lower = dept_name.lower().strip()

    # Direct match
    if lower in DEPT_CONSOLIDATION:
        return DEPT_CONSOLIDATION[lower]

    # Partial match
    for key, value in DEPT_CONSOLIDATION.items():
        if key in lower or lower in key:
            return value

    # Return as-is if no match (capitalize first letter)
    return dept_name.strip().title()


def load_json(filepath):
    """Load JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_telugu_data():
    """Load all Telugu training data with department consolidation."""
    print("="*60)
    print(" Loading Telugu Training Data (V2 - Consolidated)")
    print("="*60)

    all_texts = []
    all_labels = []

    # 1. PGRS Keywords
    keywords_file = DATA_DIR / "pgrs_book_keywords.json"
    if keywords_file.exists():
        print(f"\nLoading: {keywords_file}")
        data = load_json(keywords_file)

        for dept in data.get('departments', []):
            dept_name = normalize_department(dept.get('name_english', ''))

            for subject in dept.get('subjects', []):
                # Telugu keywords (primary)
                for kw in subject.get('keywords_telugu', []):
                    all_texts.append(kw)
                    all_labels.append(dept_name)

                # English keywords
                for kw in subject.get('keywords_english', []):
                    all_texts.append(kw)
                    all_labels.append(dept_name)

        print(f"  Loaded {len(all_texts)} samples")

    # 2. Research samples
    research_file = BASE_DIR / "TELUGU_GRIEVANCE_DATASET_RESEARCH.json"
    if research_file.exists():
        print(f"\nLoading: {research_file}")
        data = load_json(research_file)

        count = 0
        for sample in data.get('samples', []):
            text = sample.get('telugu_text', '')
            dept = normalize_department(sample.get('department', ''))
            if text and dept:
                all_texts.append(text)
                all_labels.append(dept)
                count += 1

        print(f"  Added {count} samples")

    # 3. Synthetic samples
    synthetic_file = SYNTHETIC_DIR / "synthetic_telugu_grievances.json"
    if synthetic_file.exists():
        print(f"\nLoading: {synthetic_file}")
        data = load_json(synthetic_file)

        count = 0
        for sample in data.get('samples', []):
            text = sample.get('telugu_text', '')
            dept = normalize_department(sample.get('department', ''))
            if text and dept:
                all_texts.append(text)
                all_labels.append(dept)
                count += 1

        print(f"  Added {count} samples")

    # Summary
    print(f"\n{'='*60}")
    print(f" Total samples: {len(all_texts)}")
    print(f" Unique departments (after consolidation): {len(set(all_labels))}")
    print(f"{'='*60}")

    # Class distribution
    dist = Counter(all_labels)
    print("\nTop 15 departments by sample count:")
    for dept, count in dist.most_common(15):
        print(f"  {dept}: {count}")

    return all_texts, all_labels


def train_classifier(texts, labels):
    """Train the Telugu classifier."""
    print(f"\n{'='*60}")
    print(" Training Telugu Department Classifier V2")
    print("="*60)

    # Encode labels
    label_encoder = LabelEncoder()
    y = label_encoder.fit_transform(labels)

    print(f"\nNumber of classes: {len(label_encoder.classes_)}")

    # TF-IDF with character n-grams (better for Telugu)
    print("\nCreating TF-IDF vectors...")
    vectorizer = TfidfVectorizer(
        analyzer='char_wb',
        ngram_range=(2, 5),  # Wider n-gram range
        max_features=8000,   # More features
        min_df=2,            # Minimum document frequency
        lowercase=False      # Preserve Telugu characters
    )

    X = vectorizer.fit_transform(texts)
    print(f"Feature matrix: {X.shape}")

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print(f"\nTraining samples: {X_train.shape[0]}")
    print(f"Test samples: {X_test.shape[0]}")

    # Train Logistic Regression
    print("\nTraining Logistic Regression...")
    model = LogisticRegression(
        max_iter=2000,
        multi_class='multinomial',
        solver='lbfgs',
        random_state=42,
        class_weight='balanced',
        C=1.0
    )

    model.fit(X_train, y_train)

    # Evaluate
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)

    print(f"\n{'='*60}")
    print(f" RESULTS")
    print("="*60)
    print(f"\nTest Accuracy: {accuracy:.2%}")

    # Top-3 accuracy
    y_proba = model.predict_proba(X_test)
    top3_correct = sum(1 for i, proba in enumerate(y_proba)
                       if y_test[i] in np.argsort(proba)[-3:])
    top3_acc = top3_correct / len(y_test)
    print(f"Top-3 Accuracy: {top3_acc:.2%}")

    # Top-5 accuracy
    top5_correct = sum(1 for i, proba in enumerate(y_proba)
                       if y_test[i] in np.argsort(proba)[-5:])
    top5_acc = top5_correct / len(y_test)
    print(f"Top-5 Accuracy: {top5_acc:.2%}")

    # Cross-validation
    print("\nRunning 5-fold cross-validation...")
    cv_scores = cross_val_score(model, X, y, cv=5)
    print(f"CV Scores: {cv_scores}")
    print(f"Mean CV: {cv_scores.mean():.2%} (+/- {cv_scores.std()*2:.2%})")

    return model, vectorizer, label_encoder, accuracy


def save_models(model, vectorizer, label_encoder, accuracy):
    """Save all model artifacts."""
    print(f"\n{'='*60}")
    print(" Saving Models")
    print("="*60)

    # Model
    with open(MODELS_DIR / "telugu_classifier_v2.pkl", 'wb') as f:
        pickle.dump(model, f)
    print("Saved: telugu_classifier_v2.pkl")

    # Vectorizer
    with open(MODELS_DIR / "tfidf_vectorizer_v2.pkl", 'wb') as f:
        pickle.dump(vectorizer, f)
    print("Saved: tfidf_vectorizer_v2.pkl")

    # Label encoder
    with open(MODELS_DIR / "dept_label_encoder_v2.pkl", 'wb') as f:
        pickle.dump(label_encoder, f)
    print("Saved: dept_label_encoder_v2.pkl")

    # Metadata
    metadata = {
        "version": "2.0",
        "accuracy": accuracy,
        "num_classes": len(label_encoder.classes_),
        "classes": list(label_encoder.classes_),
        "vectorizer": "TF-IDF char_wb ngram(2-5) 8000 features",
        "model": "LogisticRegression multinomial balanced"
    }

    with open(MODELS_DIR / "telugu_classifier_v2_metadata.json", 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    print("Saved: telugu_classifier_v2_metadata.json")


def test_predictions(model, vectorizer, label_encoder):
    """Test the model with sample inputs."""
    print(f"\n{'='*60}")
    print(" Sample Predictions")
    print("="*60)

    test_samples = [
        "భూమి పట్టా సమస్య",  # Land patta issue -> Revenue
        "పంట నష్టం పరిహారం",  # Crop damage compensation -> Agriculture
        "విద్యుత్ బిల్లు సమస్య",  # Electricity bill issue -> Energy
        "ఆసుపత్రి వైద్యుడు లేరు",  # No doctor in hospital -> Health
        "రేషన్ కార్డు రాలేదు",  # Ration card not received -> Civil Supplies
        "రోడ్డు గుంతలు మరమ్మతు",  # Road pothole repair -> Municipal
        "పెన్షన్ రాలేదు",  # Pension not received -> Social Welfare
        "పోలీస్ ఫిర్యాదు",  # Police complaint -> Police
        "water supply problem",  # Water issue -> Water Resources
        "pension delay",  # Pension delay -> Social Welfare
    ]

    for text in test_samples:
        X = vectorizer.transform([text])
        pred_idx = model.predict(X)[0]
        pred_dept = label_encoder.inverse_transform([pred_idx])[0]

        # Get confidence
        proba = model.predict_proba(X)[0]
        confidence = proba[pred_idx] * 100

        # Get top 3
        top3_idx = np.argsort(proba)[-3:][::-1]
        top3 = [(label_encoder.inverse_transform([i])[0], proba[i]*100) for i in top3_idx]

        print(f"\nInput: {text}")
        print(f"  → Prediction: {pred_dept} ({confidence:.1f}%)")
        print(f"  → Top 3: {[(d, f'{c:.1f}%') for d, c in top3]}")


def main():
    """Main training pipeline."""
    # Load data
    texts, labels = load_telugu_data()

    # Train
    model, vectorizer, label_encoder, accuracy = train_classifier(texts, labels)

    # Save
    save_models(model, vectorizer, label_encoder, accuracy)

    # Test
    test_predictions(model, vectorizer, label_encoder)

    print(f"\n{'='*60}")
    print(" TRAINING COMPLETE")
    print("="*60)
    print(f"Final Accuracy: {accuracy:.2%}")
    print(f"Number of Classes: {len(label_encoder.classes_)}")


if __name__ == "__main__":
    main()
