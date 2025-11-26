#!/usr/bin/env python3
"""
Telugu Department Classifier V3 - Targeting 70%+ Accuracy
=========================================================

Key improvements:
1. Reduce to TOP 15 departments (covers 90%+ of grievances)
2. Generate SENTENCE-level samples, not just keywords
3. Better text augmentation (Telugu synonyms, variations)
4. Ensemble model (Voting: LR + RF + SVM)
5. Optimized TF-IDF parameters
"""

import json
import pickle
import random
from pathlib import Path
from collections import Counter
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, VotingClassifier, GradientBoostingClassifier
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data" / "extracted"
SYNTHETIC_DIR = BASE_DIR / "data" / "synthetic"
MODELS_DIR = BASE_DIR / "models"

# Top 15 departments by grievance volume (covers ~90% of all grievances)
TOP_DEPARTMENTS = [
    "Revenue",
    "Municipal Administration",
    "Police",
    "Agriculture",
    "Health",
    "Education",
    "Energy",
    "Panchayat Raj",
    "Social Welfare",
    "Civil Supplies",
    "Transport",
    "Housing",
    "Water Resources",
    "Women & Child Welfare",
    "Animal Husbandry"
]

# Department mapping (normalize to top 15)
DEPT_MAP = {
    # Revenue
    'revenue': 'Revenue',
    'revenue (ccla)': 'Revenue',
    'survey settlements and land records': 'Revenue',
    'registration and stamps': 'Revenue',

    # Municipal
    'municipal administration': 'Municipal Administration',
    'municipal administration and urban development': 'Municipal Administration',

    # Police
    'police': 'Police',
    'home (police)': 'Police',

    # Agriculture
    'agriculture': 'Agriculture',
    'agriculture and co-operation': 'Agriculture',

    # Health
    'health': 'Health',
    'health, medical and family welfare': 'Health',
    'medical': 'Health',
    'public health': 'Health',
    'secondary health': 'Health',

    # Education
    'education': 'Education',
    'school education': 'Education',
    'human resources (school education)': 'Education',
    'human resources (higher education)': 'Education',

    # Energy
    'energy': 'Energy',
    'electricity': 'Energy',
    'ap southern power distribution': 'Energy',
    'ap eastern power distribution': 'Energy',
    'ap central power distribution': 'Energy',

    # Panchayat Raj
    'panchayat raj': 'Panchayat Raj',
    'panchayat raj and rural development': 'Panchayat Raj',
    'panchayati raj': 'Panchayat Raj',
    'panchayati raj directorate': 'Panchayat Raj',
    'panchayati raj engineering': 'Panchayat Raj',
    'rural development': 'Panchayat Raj',

    # Social Welfare
    'social welfare': 'Social Welfare',
    'backward classes welfare': 'Social Welfare',
    'bc welfare': 'Social Welfare',
    'minorities welfare': 'Social Welfare',
    'tribal welfare': 'Social Welfare',

    # Civil Supplies
    'civil supplies': 'Civil Supplies',
    'consumer affairs, food and civil supplies': 'Civil Supplies',

    # Transport
    'transport': 'Transport',
    'transport, roads and buildings': 'Transport',
    'roads and buildings': 'Transport',

    # Housing
    'housing': 'Housing',
    'ap state housing corporation': 'Housing',

    # Water Resources
    'water resources': 'Water Resources',
    'water supply': 'Water Resources',
    'rural water supply': 'Water Resources',
    'rural water supply engineering': 'Water Resources',

    # Women & Child
    'women & child welfare': 'Women & Child Welfare',
    'women development and child welfare': 'Women & Child Welfare',
    'women, children, disabled and senior citizens': 'Women & Child Welfare',

    # Animal Husbandry
    'animal husbandry': 'Animal Husbandry',
    'animal husbandry, dairy development and fisheries': 'Animal Husbandry',
}

# Telugu sentence templates for each department
TELUGU_TEMPLATES = {
    'Revenue': [
        "{keyword} సమస్య పరిష్కరించండి",
        "{keyword} కోసం దరఖాస్తు చేసాను",
        "నా {keyword} ఇంకా రాలేదు",
        "{keyword} విషయంలో సహాయం కావాలి",
        "{keyword} సంబంధిత ఫిర్యాదు",
        "మా గ్రామంలో {keyword} సమస్య ఉంది",
        "{keyword} పరిష్కారం చేయలేదు",
        "నేను {keyword} దరఖాస్తు చేసి 3 నెలలు అయింది",
    ],
    'Municipal Administration': [
        "{keyword} సమస్య పరిష్కరించండి",
        "మా వార్డులో {keyword} సమస్య",
        "{keyword} మరమ్మతు చేయండి",
        "{keyword} శుభ్రం చేయండి",
        "మా ప్రాంతంలో {keyword} లేదు",
        "{keyword} సరిగా పని చేయడం లేదు",
    ],
    'Police': [
        "{keyword} ఫిర్యాదు నమోదు చేయండి",
        "{keyword} కేసు విచారణ చేయండి",
        "{keyword} సమస్యపై చర్య తీసుకోండి",
        "నా {keyword} ఫిర్యాదు పరిష్కరించలేదు",
        "{keyword} విషయంలో న్యాయం కావాలి",
    ],
    'Agriculture': [
        "{keyword} సహాయం అందించండి",
        "నా {keyword} ఇంకా రాలేదు",
        "{keyword} పథకం ప్రయోజనం అందలేదు",
        "రైతుగా {keyword} సమస్య ఎదుర్కొంటున్నాను",
        "{keyword} పరిహారం ఇవ్వండి",
    ],
    'Health': [
        "{keyword} సేవలు అందించండి",
        "ఆసుపత్రిలో {keyword} లేదు",
        "{keyword} చికిత్స అందలేదు",
        "{keyword} సమస్యపై సహాయం కావాలి",
        "ప్రాథమిక ఆరోగ్య కేంద్రంలో {keyword} లేదు",
    ],
    'Education': [
        "పాఠశాలలో {keyword} సమస్య",
        "{keyword} సౌకర్యం లేదు",
        "విద్యార్థులకు {keyword} అందలేదు",
        "{keyword} కోసం దరఖాస్తు చేసాను",
        "టీచర్ {keyword} సమస్య",
    ],
    'Energy': [
        "{keyword} సమస్య పరిష్కరించండి",
        "మా ఇంట్లో {keyword} సమస్య",
        "{keyword} బిల్లు సరిగా లేదు",
        "{keyword} కనెక్షన్ ఇవ్వండి",
        "విద్యుత్ {keyword} సమస్య",
    ],
    'Panchayat Raj': [
        "గ్రామంలో {keyword} సమస్య",
        "{keyword} పనులు చేయలేదు",
        "పంచాయతీలో {keyword} సేవ అందలేదు",
        "{keyword} మరమ్మతు అవసరం",
        "గ్రామ సచివాలయంలో {keyword} సమస్య",
    ],
    'Social Welfare': [
        "నా {keyword} ఇంకా రాలేదు",
        "{keyword} పథకం ప్రయోజనం అందలేదు",
        "{keyword} కోసం దరఖాస్తు చేసాను",
        "{keyword} నిలిపివేశారు",
        "వృద్ధాప్య {keyword} సహాయం కావాలి",
    ],
    'Civil Supplies': [
        "{keyword} సమస్య పరిష్కరించండి",
        "రేషన్ దుకాణంలో {keyword} లేదు",
        "నా {keyword} కార్డు రాలేదు",
        "{keyword} సరిగా అందలేదు",
        "{keyword} నాణ్యత సరిగా లేదు",
    ],
    'Transport': [
        "{keyword} సమస్య పరిష్కరించండి",
        "నా {keyword} ఇంకా రాలేదు",
        "{keyword} కోసం దరఖాస్తు చేసాను",
        "RTO లో {keyword} సమస్య",
        "{keyword} మరమ్మతు అవసరం",
    ],
    'Housing': [
        "{keyword} సమస్య పరిష్కరించండి",
        "నా {keyword} ఇంకా రాలేదు",
        "{keyword} పథకం ప్రయోజనం అందలేదు",
        "ఇంటి {keyword} కోసం దరఖాస్తు",
        "{keyword} స్థలం కేటాయింపు కావాలి",
    ],
    'Water Resources': [
        "{keyword} సమస్య పరిష్కరించండి",
        "మా గ్రామంలో {keyword} లేదు",
        "{keyword} సరఫరా నిలిచిపోయింది",
        "{keyword} కనెక్షన్ ఇవ్వండి",
        "త్రాగు {keyword} సమస్య",
    ],
    'Women & Child Welfare': [
        "{keyword} సహాయం అందించండి",
        "అంగన్‌వాడీలో {keyword} లేదు",
        "{keyword} పథకం ప్రయోజనం అందలేదు",
        "మహిళా {keyword} సమస్య",
        "{keyword} కోసం దరఖాస్తు చేసాను",
    ],
    'Animal Husbandry': [
        "{keyword} సేవలు అందించండి",
        "పశువైద్య {keyword} లేదు",
        "{keyword} సమస్యపై సహాయం కావాలి",
        "నా పశువులకు {keyword} అవసరం",
        "{keyword} సబ్సిడీ అందలేదు",
    ],
}

# Department-specific keywords for sentence generation
DEPT_KEYWORDS = {
    'Revenue': [
        'పట్టా', 'భూమి', 'సర్వే', 'రికార్డు', 'మ్యూటేషన్', 'ఆదాయ సర్టిఫికేట్',
        'కుల ధృవీకరణ', 'నివాస ధృవీకరణ', 'భూ వివాదం', 'సరిహద్దు', 'పునర్సర్వే',
        'land', 'patta', 'survey', 'mutation', 'certificate', 'income', 'caste',
    ],
    'Municipal Administration': [
        'డ్రైనేజీ', 'రోడ్డు', 'గుంత', 'వీధి లైట్', 'చెత్త', 'నీటి సరఫరా',
        'అనుమతి', 'బిల్డింగ్', 'పన్ను', 'మురుగు నీరు', 'పారిశుధ్యం',
        'road', 'drainage', 'streetlight', 'garbage', 'water', 'sanitation',
    ],
    'Police': [
        'FIR', 'కేసు', 'దొంగతనం', 'దాడి', 'వేధింపు', 'మోసం', 'భూమి కబ్జా',
        'నేరం', 'పోలీస్ స్టేషన్', 'దర్యాప్తు', 'రక్షణ',
        'crime', 'theft', 'complaint', 'harassment', 'fraud', 'investigation',
    ],
    'Agriculture': [
        'పంట', 'బీమా', 'నష్టం', 'పరిహారం', 'ఎరువులు', 'విత్తనాలు', 'రుణం',
        'రైతు భరోసా', 'సబ్సిడీ', 'వ్యవసాయం', 'రైతు',
        'crop', 'insurance', 'fertilizer', 'subsidy', 'farmer', 'loan',
    ],
    'Health': [
        'డాక్టర్', 'మందులు', 'ఆసుపత్రి', 'చికిత్స', 'అంబులెన్స్', 'ఆరోగ్యశ్రీ',
        'వైద్యం', 'నర్సు', 'PHC', 'టీకా', 'ఆరోగ్యం',
        'doctor', 'medicine', 'hospital', 'treatment', 'ambulance', 'health',
    ],
    'Education': [
        'పాఠశాల', 'టీచర్', 'విద్యార్థి', 'స్కాలర్‌షిప్', 'ఫీజు', 'పుస్తకాలు',
        'యూనిఫారం', 'మధ్యాహ్న భోజనం', 'అడ్మిషన్', 'సర్టిఫికేట్', 'కళాశాల',
        'school', 'teacher', 'student', 'scholarship', 'fee', 'admission',
    ],
    'Energy': [
        'విద్యుత్', 'బిల్లు', 'మీటర్', 'కనెక్షన్', 'ట్రాన్స్‌ఫార్మర్', 'పవర్ కట్',
        'వోల్టేజ్', 'వైర్', 'పోల్', 'సరఫరా',
        'electricity', 'bill', 'meter', 'connection', 'power', 'voltage',
    ],
    'Panchayat Raj': [
        'గ్రామం', 'రోడ్డు', 'CC రోడ్డు', 'డ్రైనేజీ', 'వీధి లైట్', 'చెరువు',
        'సమావేశం', 'సర్పంచ్', 'NREGS', 'పని', 'గ్రామ సచివాలయం',
        'village', 'road', 'drainage', 'tank', 'panchayat', 'nregs',
    ],
    'Social Welfare': [
        'పెన్షన్', 'వృద్ధాప్య', 'విధవ', 'వికలాంగ', 'స్కాలర్‌షిప్', 'హాస్టల్',
        'సంక్షేమం', 'BC', 'SC', 'ST', 'మైనారిటీ',
        'pension', 'welfare', 'scholarship', 'hostel', 'disabled',
    ],
    'Civil Supplies': [
        'రేషన్', 'కార్డు', 'బియ్యం', 'గోధుమలు', 'కిరోసిన్', 'దుకాణం',
        'PDS', 'ఆధార్', 'కోటా', 'సరఫరా',
        'ration', 'card', 'rice', 'kerosene', 'pds', 'fair price shop',
    ],
    'Transport': [
        'లైసెన్స్', 'RC', 'వాహనం', 'రోడ్డు', 'బస్సు', 'RTO',
        'పర్మిట్', 'పన్ను', 'బ్రిడ్జి', 'హైవే',
        'license', 'registration', 'vehicle', 'road', 'bus', 'permit',
    ],
    'Housing': [
        'ఇల్లు', 'స్థలం', 'పట్టా', 'నిర్మాణం', 'సబ్సిడీ', 'PMAY',
        'గృహం', 'ప్లాట్', 'కేటాయింపు',
        'house', 'site', 'plot', 'construction', 'pmay', 'housing scheme',
    ],
    'Water Resources': [
        'నీరు', 'త్రాగునీరు', 'బోర్', 'చెరువు', 'కాలువ', 'పైపు',
        'సరఫరా', 'కనెక్షన్', 'ట్యాంక్',
        'water', 'drinking water', 'bore', 'tank', 'canal', 'pipeline',
    ],
    'Women & Child Welfare': [
        'అంగన్‌వాడీ', 'పోషణ', 'గర్భిణి', 'శిశు', 'SHG', 'మహిళ',
        'బాలల', 'పథకం', 'సహాయం',
        'anganwadi', 'nutrition', 'pregnant', 'child', 'women', 'shg',
    ],
    'Animal Husbandry': [
        'పశువు', 'వైద్యం', 'టీకా', 'పాలు', 'డైరీ', 'చేప',
        'సబ్సిడీ', 'మేత', 'గొర్రె', 'కోళ్ళు',
        'veterinary', 'cattle', 'vaccination', 'dairy', 'fish', 'poultry',
    ],
}


def normalize_dept(name):
    """Normalize department name to top 15."""
    if not name:
        return None

    lower = name.lower().strip()

    # Direct match
    if lower in DEPT_MAP:
        return DEPT_MAP[lower]

    # Partial match
    for key, val in DEPT_MAP.items():
        if key in lower or lower in key:
            return val

    # Check if already in top departments
    for dept in TOP_DEPARTMENTS:
        if dept.lower() in lower or lower in dept.lower():
            return dept

    return None  # Exclude if not in top 15


def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def generate_sentence_samples():
    """Generate sentence-level training samples."""
    print("="*60)
    print(" Generating Sentence-Level Training Samples")
    print("="*60)

    samples = []

    for dept, templates in TELUGU_TEMPLATES.items():
        keywords = DEPT_KEYWORDS.get(dept, [])

        for keyword in keywords:
            for template in templates:
                try:
                    sentence = template.format(keyword=keyword)
                    samples.append((sentence, dept))
                except:
                    pass

        # Also add raw keywords
        for keyword in keywords:
            samples.append((keyword, dept))

    print(f"Generated {len(samples)} sentence samples")
    return samples


def load_existing_data():
    """Load existing training data."""
    print("\n" + "="*60)
    print(" Loading Existing Training Data")
    print("="*60)

    texts = []
    labels = []

    # 1. PGRS Keywords
    keywords_file = DATA_DIR / "pgrs_book_keywords.json"
    if keywords_file.exists():
        data = load_json(keywords_file)
        count = 0
        for dept in data.get('departments', []):
            dept_name = normalize_dept(dept.get('name_english', ''))
            if dept_name:
                for subj in dept.get('subjects', []):
                    for kw in subj.get('keywords_telugu', []) + subj.get('keywords_english', []):
                        texts.append(kw)
                        labels.append(dept_name)
                        count += 1
        print(f"PGRS Keywords: {count} samples")

    # 2. Research samples
    research_file = BASE_DIR / "TELUGU_GRIEVANCE_DATASET_RESEARCH.json"
    if research_file.exists():
        data = load_json(research_file)
        count = 0
        for sample in data.get('samples', []):
            dept = normalize_dept(sample.get('department', ''))
            text = sample.get('telugu_text', '')
            if dept and text:
                texts.append(text)
                labels.append(dept)
                count += 1
        print(f"Research samples: {count}")

    # 3. Synthetic samples
    synthetic_file = SYNTHETIC_DIR / "synthetic_telugu_grievances.json"
    if synthetic_file.exists():
        data = load_json(synthetic_file)
        count = 0
        for sample in data.get('samples', []):
            dept = normalize_dept(sample.get('department', ''))
            text = sample.get('telugu_text', '')
            if dept and text:
                texts.append(text)
                labels.append(dept)
                count += 1
        print(f"Synthetic samples: {count}")

    return texts, labels


def augment_data(texts, labels, target_per_class=150):
    """Augment data to balance classes."""
    print("\n" + "="*60)
    print(" Augmenting Data for Class Balance")
    print("="*60)

    # Group by class
    class_samples = {}
    for text, label in zip(texts, labels):
        if label not in class_samples:
            class_samples[label] = []
        class_samples[label].append(text)

    augmented_texts = []
    augmented_labels = []

    for dept in TOP_DEPARTMENTS:
        samples = class_samples.get(dept, [])
        current_count = len(samples)

        # Add all existing samples
        augmented_texts.extend(samples)
        augmented_labels.extend([dept] * len(samples))

        # Augment if needed
        if current_count < target_per_class and current_count > 0:
            needed = target_per_class - current_count

            # Simple augmentation: repeat with minor variations
            for _ in range(needed):
                base = random.choice(samples)
                # Add variation markers
                variations = [
                    base,
                    base + " సమస్య",
                    base + " పరిష్కరించండి",
                    "దయచేసి " + base,
                    base + " కావాలి",
                ]
                augmented_texts.append(random.choice(variations))
                augmented_labels.append(dept)

        final_count = augmented_labels.count(dept)
        print(f"  {dept}: {current_count} -> {final_count}")

    print(f"\nTotal after augmentation: {len(augmented_texts)}")
    return augmented_texts, augmented_labels


def train_ensemble(X_train, y_train, X_test, y_test):
    """Train ensemble classifier."""
    print("\n" + "="*60)
    print(" Training Ensemble Classifier")
    print("="*60)

    # Individual models
    lr = LogisticRegression(max_iter=2000, class_weight='balanced', C=1.0, random_state=42)
    rf = RandomForestClassifier(n_estimators=200, max_depth=20, class_weight='balanced', random_state=42)
    svm = CalibratedClassifierCV(LinearSVC(max_iter=5000, class_weight='balanced', random_state=42))

    # Train and evaluate individual models
    print("\nTraining Logistic Regression...")
    lr.fit(X_train, y_train)
    lr_acc = accuracy_score(y_test, lr.predict(X_test))
    print(f"  LR Accuracy: {lr_acc:.2%}")

    print("\nTraining Random Forest...")
    rf.fit(X_train, y_train)
    rf_acc = accuracy_score(y_test, rf.predict(X_test))
    print(f"  RF Accuracy: {rf_acc:.2%}")

    print("\nTraining SVM...")
    svm.fit(X_train, y_train)
    svm_acc = accuracy_score(y_test, svm.predict(X_test))
    print(f"  SVM Accuracy: {svm_acc:.2%}")

    # Ensemble (soft voting)
    print("\nCreating Voting Ensemble...")
    ensemble = VotingClassifier(
        estimators=[('lr', lr), ('rf', rf), ('svm', svm)],
        voting='soft'
    )
    ensemble.fit(X_train, y_train)

    y_pred = ensemble.predict(X_test)
    ensemble_acc = accuracy_score(y_test, y_pred)
    print(f"\n  ENSEMBLE Accuracy: {ensemble_acc:.2%}")

    # Top-N accuracy
    y_proba = ensemble.predict_proba(X_test)
    top3 = sum(1 for i, p in enumerate(y_proba) if y_test[i] in np.argsort(p)[-3:]) / len(y_test)
    top5 = sum(1 for i, p in enumerate(y_proba) if y_test[i] in np.argsort(p)[-5:]) / len(y_test)
    print(f"  Top-3 Accuracy: {top3:.2%}")
    print(f"  Top-5 Accuracy: {top5:.2%}")

    return ensemble, {'lr': lr_acc, 'rf': rf_acc, 'svm': svm_acc, 'ensemble': ensemble_acc, 'top3': top3, 'top5': top5}


def main():
    print("\n" + "="*60)
    print(" TELUGU CLASSIFIER V3 - TARGET 70%+")
    print("="*60)

    # 1. Generate sentence samples
    sentence_samples = generate_sentence_samples()

    # 2. Load existing data
    existing_texts, existing_labels = load_existing_data()

    # 3. Combine
    all_texts = [s[0] for s in sentence_samples] + existing_texts
    all_labels = [s[1] for s in sentence_samples] + existing_labels

    # Filter to top 15 departments only
    filtered = [(t, l) for t, l in zip(all_texts, all_labels) if l in TOP_DEPARTMENTS]
    all_texts = [t for t, _ in filtered]
    all_labels = [l for _, l in filtered]

    print(f"\nFiltered to top 15 departments: {len(all_texts)} samples")
    print(f"Class distribution: {Counter(all_labels)}")

    # 4. Augment
    all_texts, all_labels = augment_data(all_texts, all_labels, target_per_class=200)

    # 5. Encode labels
    label_encoder = LabelEncoder()
    y = label_encoder.fit_transform(all_labels)

    print(f"\nFinal classes: {len(label_encoder.classes_)}")

    # 6. TF-IDF
    print("\n" + "="*60)
    print(" Creating TF-IDF Features")
    print("="*60)

    vectorizer = TfidfVectorizer(
        analyzer='char_wb',
        ngram_range=(2, 6),
        max_features=10000,
        min_df=2,
        sublinear_tf=True,
        lowercase=False
    )

    X = vectorizer.fit_transform(all_texts)
    print(f"Feature matrix: {X.shape}")

    # 7. Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print(f"Train: {X_train.shape[0]}, Test: {X_test.shape[0]}")

    # 8. Train ensemble
    model, metrics = train_ensemble(X_train, y_train, X_test, y_test)

    # 9. Cross-validation
    print("\n" + "="*60)
    print(" Cross-Validation")
    print("="*60)

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    # Use LR for CV (faster)
    lr_model = LogisticRegression(max_iter=2000, class_weight='balanced', random_state=42)
    cv_scores = cross_val_score(lr_model, X, y, cv=cv, scoring='accuracy')
    print(f"CV Scores: {cv_scores}")
    print(f"Mean CV: {cv_scores.mean():.2%} (+/- {cv_scores.std()*2:.2%})")

    # 10. Save
    print("\n" + "="*60)
    print(" Saving Models")
    print("="*60)

    with open(MODELS_DIR / "telugu_classifier_v3.pkl", 'wb') as f:
        pickle.dump(model, f)
    print("Saved: telugu_classifier_v3.pkl")

    with open(MODELS_DIR / "tfidf_vectorizer_v3.pkl", 'wb') as f:
        pickle.dump(vectorizer, f)
    print("Saved: tfidf_vectorizer_v3.pkl")

    with open(MODELS_DIR / "dept_label_encoder_v3.pkl", 'wb') as f:
        pickle.dump(label_encoder, f)
    print("Saved: dept_label_encoder_v3.pkl")

    metadata = {
        "version": "3.0",
        "timestamp": datetime.now().isoformat(),
        "accuracy": metrics['ensemble'],
        "top3_accuracy": metrics['top3'],
        "top5_accuracy": metrics['top5'],
        "cv_mean": float(cv_scores.mean()),
        "num_classes": len(label_encoder.classes_),
        "classes": list(label_encoder.classes_),
        "individual_models": {
            "lr": metrics['lr'],
            "rf": metrics['rf'],
            "svm": metrics['svm']
        }
    }

    with open(MODELS_DIR / "telugu_classifier_v3_metadata.json", 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    print("Saved: telugu_classifier_v3_metadata.json")

    # Final summary
    print("\n" + "="*60)
    print(" FINAL RESULTS")
    print("="*60)
    print(f"Ensemble Accuracy: {metrics['ensemble']:.2%}")
    print(f"Top-3 Accuracy: {metrics['top3']:.2%}")
    print(f"Top-5 Accuracy: {metrics['top5']:.2%}")
    print(f"CV Mean: {cv_scores.mean():.2%}")
    print(f"Classes: {len(label_encoder.classes_)}")

    if metrics['ensemble'] >= 0.70:
        print("\n✅ TARGET ACHIEVED: 70%+ accuracy!")
    else:
        gap = 0.70 - metrics['ensemble']
        print(f"\n⚠️ Gap to 70%: {gap:.2%}")


if __name__ == "__main__":
    main()
