#!/usr/bin/env python3
"""
Example: Training Lapse Classifier with Synthetic Data
=======================================================

Demonstrates how to use the synthetic lapse data for ML model training.

This is a reference implementation showing:
- Data loading and preprocessing
- Feature engineering
- Train/test splitting
- Model training with multiple algorithms
- Evaluation and metrics

Usage:
    python example_train_with_synthetic.py
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score


def load_synthetic_data(filepath: Path) -> pd.DataFrame:
    """Load synthetic data from JSON into pandas DataFrame."""
    print(f"Loading data from: {filepath}")

    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    df = pd.DataFrame(data['samples'])
    print(f"Loaded {len(df)} samples")
    print(f"Generation date: {data['metadata']['generation_date']}")

    return df


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create additional features from raw data."""
    df = df.copy()

    # Categorical encoding
    label_encoders = {}
    categorical_cols = ['department_code', 'district_code', 'escalation_level', 'grievance_category']

    for col in categorical_cols:
        le = LabelEncoder()
        df[f'{col}_encoded'] = le.fit_transform(df[col])
        label_encoders[col] = le

    # Temporal features
    df['is_delayed'] = (df['days_to_resolve'] > 15).astype(int)
    df['is_highly_delayed'] = (df['days_to_resolve'] > 30).astype(int)
    df['log_days'] = np.log1p(df['days_to_resolve'])

    # Response rate
    df['responses_per_day'] = df['officer_response_count'] / (df['days_to_resolve'] + 1)  # +1 to avoid div by zero

    # Escalation level numeric (ordinal)
    escalation_order = {
        'GRA': 1, 'Mandal': 2, 'Tahsildar': 3,
        'RDO': 4, 'Collector': 5, 'HOD': 6, 'CM': 7
    }
    df['escalation_numeric'] = df['escalation_level'].map(escalation_order)

    # High-priority departments
    high_priority_depts = ['REVENUE', 'SOC_WELF', 'MUNI']
    df['is_high_priority_dept'] = df['department_code'].isin(high_priority_depts).astype(int)

    return df, label_encoders


def prepare_training_data(df: pd.DataFrame):
    """Prepare X and y for training."""

    # Features to use
    feature_cols = [
        'department_code_encoded',
        'district_code_encoded',
        'escalation_level_encoded',
        'grievance_category_encoded',
        'days_to_resolve',
        'officer_response_count',
        'is_delayed',
        'is_highly_delayed',
        'log_days',
        'responses_per_day',
        'escalation_numeric',
        'is_high_priority_dept',
    ]

    X = df[feature_cols]
    y = df['lapse_type_id']  # Target: lapse category ID (1-13)

    # Also keep lapse type names for evaluation
    lapse_names = df['lapse_type']

    return X, y, lapse_names


def train_model(X_train, y_train):
    """Train a Random Forest classifier."""
    print("\nTraining Random Forest classifier...")

    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        min_samples_split=10,
        random_state=42,
        class_weight='balanced',  # Handle class imbalance
        n_jobs=-1
    )

    model.fit(X_train, y_train)

    print("Training complete!")

    return model


def evaluate_model(model, X_test, y_test, lapse_names_test):
    """Evaluate model and print metrics."""
    print("\nEvaluating model...")

    y_pred = model.predict(X_test)

    # Overall accuracy
    accuracy = accuracy_score(y_test, y_pred)
    print(f"\nOverall Accuracy: {accuracy:.3f}")

    # Classification report
    print("\nClassification Report:")
    print("=" * 70)

    # Get unique lapse types for labels
    lapse_type_mapping = dict(zip(y_test, lapse_names_test))
    unique_lapses = sorted(set(lapse_type_mapping.items()), key=lambda x: x[0])
    target_names = [name for _, name in unique_lapses]

    report = classification_report(
        y_test, y_pred,
        target_names=target_names,
        labels=[lid for lid, _ in unique_lapses],
        zero_division=0
    )
    print(report)

    # Feature importance
    print("\nTop 10 Feature Importances:")
    print("=" * 70)
    feature_importance = pd.DataFrame({
        'feature': X_test.columns,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)

    for i, row in feature_importance.head(10).iterrows():
        print(f"  {row['feature']:30s}: {row['importance']:.4f}")

    return accuracy, y_pred


def main():
    """Main training pipeline."""
    print("=" * 70)
    print("LAPSE CLASSIFIER TRAINING - SYNTHETIC DATA")
    print("=" * 70)

    # 1. Load data
    data_path = Path(__file__).parent / "data" / "synthetic" / "synthetic_lapse_cases.json"
    df = load_synthetic_data(data_path)

    print("\nData shape:", df.shape)
    print("\nLapse distribution:")
    print(df['lapse_type'].value_counts().head(5))

    # 2. Feature engineering
    print("\nEngineering features...")
    df, label_encoders = engineer_features(df)
    print(f"Total features after engineering: {len(df.columns)}")

    # 3. Prepare training data
    X, y, lapse_names = prepare_training_data(df)
    print(f"\nFeature matrix shape: {X.shape}")
    print(f"Target distribution: {len(y.unique())} unique lapse types")

    # 4. Train/test split (stratified to maintain distribution)
    X_train, X_test, y_train, y_test, lapse_train, lapse_test = train_test_split(
        X, y, lapse_names,
        test_size=0.2,
        random_state=42,
        stratify=y
    )

    print(f"\nTrain samples: {len(X_train)}")
    print(f"Test samples: {len(X_test)}")

    # 5. Train model
    model = train_model(X_train, y_train)

    # 6. Evaluate
    accuracy, y_pred = evaluate_model(model, X_test, y_test, lapse_test)

    # 7. Summary
    print("\n" + "=" * 70)
    print("TRAINING SUMMARY")
    print("=" * 70)
    print(f"Model: Random Forest (100 trees)")
    print(f"Train samples: {len(X_train)}")
    print(f"Test samples: {len(X_test)}")
    print(f"Test accuracy: {accuracy:.3f}")
    print(f"Number of lapse types: {len(y.unique())}")
    print("=" * 70)

    print("\nNOTE: This is trained on SYNTHETIC data.")
    print("For production use, combine with real audit data.")
    print("\nNext steps:")
    print("  1. Collect real labeled lapse data from audits")
    print("  2. Merge with synthetic data (80% real, 20% synthetic)")
    print("  3. Use cross-validation for robust evaluation")
    print("  4. Fine-tune hyperparameters")
    print("  5. Deploy and monitor in production")

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
