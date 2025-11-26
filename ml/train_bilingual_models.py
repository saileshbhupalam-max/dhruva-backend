"""
Train Bilingual Models (Telugu + English)
==========================================
Adds English training data to achieve high confidence on both languages.
"""

import json
import pickle
import random
import numpy as np
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import VotingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split, cross_val_score

# Paths
BASE_DIR = Path(__file__).parent
MODELS_DIR = BASE_DIR / "models"
MURIL_DIR = BASE_DIR / "data" / "muril_training"
KNOWLEDGE_BASE = BASE_DIR / "data" / "knowledge_base"


def safe_print(text):
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode('ascii', 'replace').decode('ascii'))


# =============================================================================
# ENGLISH TRAINING DATA
# =============================================================================

ENGLISH_CLASSIFICATION_DATA = {
    "Revenue": [
        "land records not updated",
        "need pattadar passbook",
        "land survey required",
        "mutation not done",
        "ROR certificate needed",
        "land registration problem",
        "encroachment on my land",
        "land dispute with neighbor",
        "property tax issue",
        "land measurement wrong",
        "pahani not correct",
        "land owned by me taken",
        "boundary dispute",
        "land documents missing",
        "conversion of land use",
    ],
    "Social Welfare": [
        "pension not received",
        "old age pension pending",
        "widow pension stopped",
        "disability pension needed",
        "aasara pension not coming",
        "pension amount reduced",
        "pension rejected wrongly",
        "pension for 6 months not received",
        "social welfare scheme not received",
        "BC welfare benefits",
        "SC ST scholarship",
        "minority welfare",
        "pension bank account issue",
        "pension aadhaar linking problem",
        "handicapped pension",
    ],
    "Municipal Administration": [
        "road has potholes",
        "drainage not working",
        "street light not working",
        "garbage not collected",
        "sewage overflow",
        "footpath encroachment",
        "illegal construction",
        "water logging problem",
        "road repair needed",
        "drain cleaning required",
        "mosquito menace",
        "public toilet needed",
        "park maintenance poor",
        "traffic signal not working",
        "road blocked",
    ],
    "Civil Supplies": [
        "ration card needed",
        "rice not received",
        "ration dealer not giving rice",
        "new ration card required",
        "ration card correction",
        "kerosene not available",
        "fair price shop closed",
        "ration card lost",
        "add name to ration card",
        "remove name from ration card",
        "ration shop dealer cheating",
        "quality of rice poor",
        "ration card address change",
        "ration card aadhar seeding",
        "BPL card needed",
    ],
    "Agriculture": [
        "rythu bandhu not received",
        "crop loss compensation",
        "seeds not provided",
        "fertilizer shortage",
        "pesticides needed",
        "crop insurance claim",
        "farmer loan waiver",
        "agriculture subsidy",
        "bore well permission",
        "crop damage due to rain",
        "PM Kisan not received",
        "input subsidy pending",
        "tractor subsidy",
        "drip irrigation scheme",
        "agriculture land issue",
    ],
    "Health": [
        "no doctor in hospital",
        "hospital has no medicines",
        "arogyasri card needed",
        "ambulance not available",
        "PHC not functioning",
        "medical emergency help",
        "hospital staff rude",
        "medical negligence",
        "vaccination not done",
        "health card required",
        "specialist doctor needed",
        "hospital bed not available",
        "blood required urgently",
        "dialysis facility needed",
        "maternity care problem",
    ],
    "Education": [
        "no teacher in school",
        "mid day meal problem",
        "school building damaged",
        "school toilet not working",
        "admission denied",
        "scholarship not received",
        "school fee reimbursement",
        "textbooks not provided",
        "uniform not given",
        "teacher absent regularly",
        "school bus needed",
        "lack of drinking water in school",
        "school reopening issue",
        "transfer certificate delay",
        "exam center far away",
    ],
    "Energy": [
        "no electricity",
        "transformer burnt",
        "electricity bill too high",
        "new connection needed",
        "power cut daily",
        "meter reading wrong",
        "electric pole fallen",
        "wire hanging dangerously",
        "voltage fluctuation",
        "electricity theft",
        "street light pole needed",
        "solar panel subsidy",
        "agricultural power connection",
        "load extension required",
        "meter not working",
    ],
    "Police": [
        "file police complaint",
        "theft in my house",
        "harassment by someone",
        "eve teasing",
        "domestic violence",
        "cyber crime",
        "missing person",
        "accident case",
        "property dispute violence",
        "illegal activities in area",
        "noise pollution",
        "gambling in neighborhood",
        "drug selling nearby",
        "police not registering FIR",
        "need police protection",
    ],
    "Water Resources": [
        "no water supply",
        "bore well needed",
        "pipeline leakage",
        "water contaminated",
        "water tank not filled",
        "canal water not released",
        "drinking water problem",
        "water connection needed",
        "overhead tank repair",
        "hand pump not working",
        "water tanker required",
        "irrigation water not available",
        "well deepening needed",
        "water meter issue",
        "summer water scarcity",
    ],
    "Housing": [
        "house collapsed",
        "PMAY house needed",
        "house patta required",
        "housing scheme not received",
        "house damage compensation",
        "roof leaking",
        "house construction stopped",
        "housing loan subsidy",
        "house site needed",
        "double bedroom house",
        "house repair grant",
        "relocation assistance",
        "slum upgrading",
        "house number not allotted",
        "building permission",
    ],
    "Transport": [
        "bus not coming",
        "driving license needed",
        "road tax refund",
        "vehicle registration",
        "bus route change needed",
        "bus stop shelter required",
        "auto rickshaw overcharging",
        "bus conductor rude",
        "bus pass required",
        "fitness certificate",
        "permit for vehicle",
        "road accident compensation",
        "traffic jam daily",
        "bus frequency less",
        "last bus timing early",
    ],
    "Panchayat Raj": [
        "village road repair",
        "panchayat not responding",
        "gram sabha not conducted",
        "MGNREGA wages pending",
        "job card issue",
        "panchayat secretary absent",
        "village development work",
        "community hall needed",
        "village sanitation problem",
        "burial ground maintenance",
        "village tank cleaning",
        "NREGA work not given",
        "village electrification",
        "anganwadi center problem",
        "self help group loan",
    ],
    "Animal Husbandry": [
        "veterinary hospital needed",
        "cattle died no compensation",
        "sheep distribution scheme",
        "poultry farming subsidy",
        "animal vaccination",
        "milk dairy problem",
        "fodder not available",
        "livestock insurance",
        "goat farming scheme",
        "fish farming support",
        "animal disease outbreak",
        "veterinary doctor not available",
        "cattle feed subsidy",
        "artificial insemination service",
        "stray dog menace",
    ],
}

ENGLISH_SENTIMENT_DATA = {
    "CRITICAL": [
        # Starvation/death
        "we are dying of hunger please help",
        "will commit suicide no one helping",
        "children starving nothing to eat",
        "dying without medical treatment",
        "will die if no help comes",
        "family starving for days",
        "no food children crying",
        "medical emergency will die",
        "cannot survive anymore",
        "life in danger please help",
        "starvation death imminent",
        "suicide is only option left",
        "kids have not eaten for days",
        "dying of thirst no water",
        "will end my life today",
        "we will die without help",
        "dying dying please save us",
        "death is near help us",
        "starving to death",
        "children will die of hunger",
        "no food no water dying",
        "life threatening situation",
        "will not survive",
        "about to die please help",
        "family dying of starvation",
    ],
    "HIGH": [
        # Months pending
        "pension not received for 6 months",
        "salary pending for 3 months",
        "no electricity for weeks",
        "ration not received for 4 months",
        "urgent help needed",
        "immediate assistance required",
        "very difficult situation",
        "cannot wait any longer",
        "months without any response",
        "desperate for help",
        "unbearable condition",
        "suffering for long time",
        "no response for months",
        "waiting since many months",
        "critical situation please help fast",
        "5 months no pension",
        "waiting for 6 months",
        "pending since 4 months",
        "3 months salary not paid",
        "months of suffering",
        "long time no resolution",
        "weeks without electricity",
        "many months passed no action",
        "urgent urgent please help",
        "immediate action needed",
    ],
    "MEDIUM": [
        # Infrastructure/service issues
        "road needs repair",
        "drainage problem in area",
        "street light not working",
        "garbage collection issue",
        "maintenance needed",
        "service not proper",
        "please look into this",
        "problem needs attention",
        "issue persisting",
        "complaint regarding service",
        "not satisfactory service",
        "needs improvement",
        "please fix this issue",
        "problem in my area",
        "service quality poor",
        "road has potholes fix it",
        "drainage blocked",
        "light not working",
        "garbage not collected",
        "water supply irregular",
        "poor maintenance",
        "infrastructure problem",
        "civic issue",
        "local problem",
        "area has issues",
    ],
    "NORMAL": [
        # Routine requests/queries
        "need certificate please help",
        "want new connection",
        "information required",
        "application status please",
        "where to get form",
        "how to apply",
        "general enquiry",
        "need guidance",
        "please provide details",
        "request for information",
        "want to know process",
        "need help with application",
        "seeking assistance",
        "please guide me",
        "query about scheme",
        "certificate required",
        "new application",
        "enquiry about service",
        "status update please",
        "how to get certificate",
        "application form needed",
        "procedure query",
        "information about scheme",
        "help with form",
        "guidance needed",
    ],
}


def load_existing_data():
    """Load existing Telugu training data."""
    classification_samples = []
    sentiment_samples = []

    # Load classification data
    class_file = MURIL_DIR / "muril_classification_training.json"
    if class_file.exists():
        with open(class_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict) and "samples" in data:
                classification_samples = data["samples"]
            elif isinstance(data, list):
                classification_samples = data
        print(f"Loaded {len(classification_samples)} Telugu classification samples")

    # Load sentiment data
    sent_file = MURIL_DIR / "muril_sentiment_training.json"
    if sent_file.exists():
        with open(sent_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict) and "samples" in data:
                sentiment_samples = data["samples"]
            elif isinstance(data, list):
                sentiment_samples = data
        print(f"Loaded {len(sentiment_samples)} Telugu sentiment samples")

    return classification_samples, sentiment_samples


def create_english_classification_samples():
    """Create English classification training samples."""
    samples = []

    for dept, texts in ENGLISH_CLASSIFICATION_DATA.items():
        for text in texts:
            samples.append({"text": text, "label": dept})
            # Add variations
            samples.append({"text": text + " please help", "label": dept})
            samples.append({"text": "my " + text, "label": dept})
            samples.append({"text": text + " urgent", "label": dept})
            samples.append({"text": "complaint about " + text, "label": dept})

    print(f"Created {len(samples)} English classification samples")
    return samples


def create_english_sentiment_samples():
    """Create English sentiment training samples."""
    samples = []

    for level, texts in ENGLISH_SENTIMENT_DATA.items():
        for text in texts:
            samples.append({"text": text, "label": level})
            # Add variations
            samples.append({"text": text + " please", "label": level})
            samples.append({"text": "sir " + text, "label": level})

    print(f"Created {len(samples)} English sentiment samples")
    return samples


def balance_samples(samples, target_per_class=None):
    """Balance samples across classes."""
    by_label = {}
    for s in samples:
        label = s["label"]
        if label not in by_label:
            by_label[label] = []
        by_label[label].append(s)

    if target_per_class is None:
        # Use max class size
        target_per_class = max(len(items) for items in by_label.values())

    balanced = []
    for label, items in by_label.items():
        if len(items) >= target_per_class:
            balanced.extend(random.sample(items, target_per_class))
        else:
            # Oversample
            balanced.extend(items)
            while len([s for s in balanced if s["label"] == label]) < target_per_class:
                balanced.append(random.choice(items))

    random.shuffle(balanced)
    return balanced


def train_classification_model(telugu_samples, english_samples):
    """Train bilingual classification model."""
    print("\n" + "=" * 60)
    print(" TRAINING BILINGUAL CLASSIFICATION MODEL")
    print("=" * 60)

    # Combine samples - give more weight to Telugu (3x)
    all_samples = telugu_samples * 3 + english_samples
    print(f"Total samples: {len(all_samples)}")

    # Balance to reasonable size
    balanced = balance_samples(all_samples, target_per_class=500)
    print(f"Balanced samples: {len(balanced)}")

    # Count distribution
    dist = {}
    for s in balanced:
        label = s["label"]
        dist[label] = dist.get(label, 0) + 1
    print(f"Classes: {len(dist)}")

    # Prepare data
    texts = [s["text"] for s in balanced]
    labels = [s["label"] for s in balanced]

    # Encode labels
    label_encoder = LabelEncoder()
    y = label_encoder.fit_transform(labels)

    # Create TF-IDF features (char n-grams work for both languages)
    vectorizer = TfidfVectorizer(
        analyzer='char_wb',
        ngram_range=(2, 6),
        max_features=15000,
        min_df=2,
        sublinear_tf=True,
    )
    X = vectorizer.fit_transform(texts)
    print(f"Feature matrix: {X.shape}")

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Train ensemble
    print("\nTraining ensemble...")
    lr = LogisticRegression(max_iter=1000, C=1.0, class_weight='balanced')
    rf = RandomForestClassifier(n_estimators=100, class_weight='balanced', random_state=42)
    svm = SVC(probability=True, kernel='linear', C=1.0, class_weight='balanced')

    ensemble = VotingClassifier(
        estimators=[('lr', lr), ('rf', rf), ('svm', svm)],
        voting='soft'
    )
    ensemble.fit(X_train, y_train)

    # Evaluate
    train_acc = ensemble.score(X_train, y_train)
    test_acc = ensemble.score(X_test, y_test)
    print(f"Train accuracy: {train_acc:.1%}")
    print(f"Test accuracy: {test_acc:.1%}")

    # Cross-validation
    cv_scores = cross_val_score(ensemble, X, y, cv=5)
    print(f"CV: {cv_scores.mean():.1%} (+/- {cv_scores.std()*2:.1%})")

    return ensemble, vectorizer, label_encoder


def train_sentiment_model(telugu_samples, english_samples):
    """Train bilingual sentiment model."""
    print("\n" + "=" * 60)
    print(" TRAINING BILINGUAL SENTIMENT MODEL")
    print("=" * 60)

    # Combine samples - give more weight to Telugu (2x)
    all_samples = telugu_samples * 2 + english_samples
    print(f"Total samples: {len(all_samples)}")

    # Balance
    balanced = balance_samples(all_samples, target_per_class=2000)
    print(f"Balanced samples: {len(balanced)}")

    # Prepare data
    texts = [s["text"] for s in balanced]
    labels = [s["label"] for s in balanced]

    # Encode labels
    label_encoder = LabelEncoder()
    y = label_encoder.fit_transform(labels)
    print(f"Classes: {list(label_encoder.classes_)}")

    # Create TF-IDF features
    vectorizer = TfidfVectorizer(
        analyzer='char_wb',
        ngram_range=(2, 6),
        max_features=8000,
        min_df=2,
        sublinear_tf=True,
    )
    X = vectorizer.fit_transform(texts)
    print(f"Feature matrix: {X.shape}")

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Train ensemble
    print("\nTraining ensemble...")
    lr = LogisticRegression(max_iter=1000, C=1.0, class_weight='balanced')
    rf = RandomForestClassifier(n_estimators=100, class_weight='balanced', random_state=42)
    svm = SVC(probability=True, kernel='linear', C=1.0, class_weight='balanced')

    ensemble = VotingClassifier(
        estimators=[('lr', lr), ('rf', rf), ('svm', svm)],
        voting='soft'
    )
    ensemble.fit(X_train, y_train)

    # Evaluate
    train_acc = ensemble.score(X_train, y_train)
    test_acc = ensemble.score(X_test, y_test)
    print(f"Train accuracy: {train_acc:.1%}")
    print(f"Test accuracy: {test_acc:.1%}")

    return ensemble, vectorizer, label_encoder


def validate_bilingual(class_model, class_vec, class_enc, sent_model, sent_vec, sent_enc):
    """Validate on both Telugu and English test cases."""
    print("\n" + "=" * 60)
    print(" BILINGUAL VALIDATION")
    print("=" * 60)

    # Classification test cases
    class_tests = [
        # Telugu
        ("నా పెన్షన్ రాలేదు", "Social Welfare", "Telugu: Pension"),
        ("రోడ్డు మీద గుంతలు", "Municipal Administration", "Telugu: Road"),
        ("రేషన్ కార్డు కావాలి", "Civil Supplies", "Telugu: Ration"),
        ("భూమి సర్వే చేయండి", "Revenue", "Telugu: Land"),
        ("కరెంట్ రావడం లేదు", "Energy", "Telugu: Electricity"),
        # English
        ("pension not received for months", "Social Welfare", "English: Pension"),
        ("road has many potholes please repair", "Municipal Administration", "English: Road"),
        ("need new ration card", "Civil Supplies", "English: Ration"),
        ("land survey required urgently", "Revenue", "English: Land"),
        ("no electricity in our area", "Energy", "English: Electricity"),
        # Code-mixed
        ("pension naku raaledu please help", "Social Welfare", "Mixed: Pension"),
        ("road repair cheyandi", "Municipal Administration", "Mixed: Road"),
    ]

    print("\n--- Classification Tests ---")
    class_correct = 0
    for text, expected, desc in class_tests:
        X = class_vec.transform([text])
        pred_idx = class_model.predict(X)[0]
        pred = class_enc.inverse_transform([pred_idx])[0]
        proba = class_model.predict_proba(X)[0]
        conf = proba[pred_idx]

        status = "[OK]" if pred == expected else "[FAIL]"
        if pred == expected:
            class_correct += 1

        safe_print(f"  {status} {desc}: {pred} ({conf:.0%})")

    class_acc = class_correct / len(class_tests)
    print(f"\n  Classification accuracy: {class_acc:.1%}")

    # Sentiment test cases
    sent_tests = [
        # Telugu CRITICAL
        ("ఆకలితో చనిపోతున్నాము", "CRITICAL", "Telugu: Dying hunger"),
        ("చనిపోతున్నాము సహాయం చేయండి", "CRITICAL", "Telugu: Dying help"),
        # Telugu HIGH
        ("6 నెలలుగా పెన్షన్ రాలేదు", "HIGH", "Telugu: 6 months pending"),
        ("నెలల తరబడి జీతం రాలేదు", "HIGH", "Telugu: Months salary"),
        # Telugu MEDIUM
        ("సమస్య ఉంది చూడండి", "MEDIUM", "Telugu: Problem"),
        ("డ్రైనేజీ సమస్య", "MEDIUM", "Telugu: Drainage"),
        # Telugu NORMAL
        ("సర్టిఫికేట్ కావాలి", "NORMAL", "Telugu: Certificate"),
        ("సమాచారం కావాలి", "NORMAL", "Telugu: Information"),
        # English CRITICAL
        ("we are dying of hunger please help", "CRITICAL", "English: Dying hunger"),
        ("children starving will die", "CRITICAL", "English: Starving die"),
        # English HIGH
        ("pension not received for 6 months", "HIGH", "English: 6 months pension"),
        ("salary pending for 3 months urgent", "HIGH", "English: 3 months salary"),
        # English MEDIUM
        ("road has potholes fix it", "MEDIUM", "English: Road potholes"),
        ("drainage problem in area", "MEDIUM", "English: Drainage"),
        # English NORMAL
        ("need certificate please", "NORMAL", "English: Certificate"),
        ("information required about scheme", "NORMAL", "English: Information"),
    ]

    print("\n--- Sentiment Tests ---")
    sent_correct = 0
    for text, expected, desc in sent_tests:
        X = sent_vec.transform([text])
        pred_idx = sent_model.predict(X)[0]
        pred = sent_enc.inverse_transform([pred_idx])[0]
        proba = sent_model.predict_proba(X)[0]
        conf = proba[pred_idx]

        status = "[OK]" if pred == expected else "[FAIL]"
        if pred == expected:
            sent_correct += 1

        safe_print(f"  {status} {desc}: {pred} ({conf:.0%})")

    sent_acc = sent_correct / len(sent_tests)
    print(f"\n  Sentiment accuracy: {sent_acc:.1%}")

    return class_acc, sent_acc


def save_models(class_model, class_vec, class_enc, sent_model, sent_vec, sent_enc):
    """Save all models."""
    print("\n" + "=" * 60)
    print(" SAVING MODELS")
    print("=" * 60)

    # Save classification model (as V4 - bilingual)
    with open(MODELS_DIR / "telugu_classifier_v3.pkl", "wb") as f:
        pickle.dump(class_model, f)
    with open(MODELS_DIR / "tfidf_vectorizer_v3.pkl", "wb") as f:
        pickle.dump(class_vec, f)
    with open(MODELS_DIR / "dept_label_encoder_v3.pkl", "wb") as f:
        pickle.dump(class_enc, f)
    print("  Saved classification model (v3 bilingual)")

    # Save sentiment model
    with open(MODELS_DIR / "sentiment_classifier.pkl", "wb") as f:
        pickle.dump(sent_model, f)
    with open(MODELS_DIR / "sentiment_vectorizer.pkl", "wb") as f:
        pickle.dump(sent_vec, f)
    with open(MODELS_DIR / "sentiment_label_encoder.pkl", "wb") as f:
        pickle.dump(sent_enc, f)
    print("  Saved sentiment model (bilingual)")

    # Save fallback model (same as main for now)
    with open(MODELS_DIR / "classification_fallback.pkl", "wb") as f:
        pickle.dump(class_model, f)
    with open(MODELS_DIR / "classification_fallback_vectorizer.pkl", "wb") as f:
        pickle.dump(class_vec, f)
    with open(MODELS_DIR / "classification_fallback_label_encoder.pkl", "wb") as f:
        pickle.dump(class_enc, f)
    print("  Saved fallback model (bilingual)")


def main():
    """Main training pipeline."""
    print("=" * 60)
    print(" DHRUVA BILINGUAL MODEL TRAINING")
    print(" Telugu + English Support")
    print("=" * 60)

    # Load existing Telugu data
    telugu_class, telugu_sent = load_existing_data()

    # Create English data
    english_class = create_english_classification_samples()
    english_sent = create_english_sentiment_samples()

    # Train classification model
    class_model, class_vec, class_enc = train_classification_model(
        telugu_class, english_class
    )

    # Train sentiment model
    sent_model, sent_vec, sent_enc = train_sentiment_model(
        telugu_sent, english_sent
    )

    # Validate
    class_acc, sent_acc = validate_bilingual(
        class_model, class_vec, class_enc,
        sent_model, sent_vec, sent_enc
    )

    # Save if good enough
    if class_acc >= 0.80 and sent_acc >= 0.80:
        save_models(
            class_model, class_vec, class_enc,
            sent_model, sent_vec, sent_enc
        )
        print("\n" + "=" * 60)
        print(" SUCCESS! Bilingual models saved.")
        print(f" Classification: {class_acc:.1%}")
        print(f" Sentiment: {sent_acc:.1%}")
        print("=" * 60)
    else:
        print("\n[WARN] Accuracy below threshold, models not saved")
        print(f"  Classification: {class_acc:.1%} (need 80%)")
        print(f"  Sentiment: {sent_acc:.1%} (need 80%)")


if __name__ == "__main__":
    main()
