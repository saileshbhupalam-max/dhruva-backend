"""Train XGBoost model for lapse/improper redressal prediction.

Uses 13 lapse categories from Guntur audit data to train a classifier
that predicts which type of lapse is likely to occur for a given grievance.
"""

import asyncio
import json
import pickle
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.models import LapseCase


async def load_lapse_data():
    """Load lapse cases from database."""
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, expire_on_commit=False)

    async with async_session() as session:
        result = await session.execute(select(LapseCase))
        lapses = result.scalars().all()

    await engine.dispose()
    return lapses


def prepare_training_data(lapses):
    """Prepare feature matrix and labels from lapse cases."""
    print(f"\nPreparing training data from {len(lapses)} lapse cases...")

    # Convert to DataFrame
    data = []
    for lapse in lapses:
        data.append(
            {
                "lapse_category": lapse.lapse_category,
                "lapse_type": lapse.lapse_type,
                "severity": lapse.severity,
                "improper_percentage": lapse.improper_percentage or 0.0,
                "count": lapse.count,
                "total_cases_audited": lapse.total_cases_audited or 0,
                "source_audit": lapse.source_audit,
            }
        )

    df = pd.DataFrame(data)
    print(f"\nDataset shape: {df.shape}")
    print(f"\nLapse categories distribution:")
    print(df["lapse_category"].value_counts())

    # Encode categorical variables
    le_type = LabelEncoder()
    le_severity = LabelEncoder()
    le_category = LabelEncoder()

    df["lapse_type_encoded"] = le_type.fit_transform(df["lapse_type"])
    df["severity_encoded"] = le_severity.fit_transform(df["severity"])
    df["lapse_category_encoded"] = le_category.fit_transform(df["lapse_category"])

    # Features
    X = df[
        [
            "lapse_type_encoded",
            "severity_encoded",
            "improper_percentage",
            "count",
            "total_cases_audited",
        ]
    ]

    # Target
    y = df["lapse_category_encoded"]

    return X, y, le_category, df


def train_xgboost_model(X, y):
    """Train XGBoost classifier for lapse prediction."""
    print("\n" + "=" * 60)
    print("Training XGBoost Lapse Prediction Model")
    print("=" * 60)

    # Split data (80/20)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print(f"\nTraining set: {X_train.shape[0]} samples")
    print(f"Test set: {X_test.shape[0]} samples")

    # Train XGBoost model
    model = xgb.XGBClassifier(
        objective="multi:softmax",
        num_class=len(np.unique(y)),
        max_depth=4,
        learning_rate=0.1,
        n_estimators=100,
        random_state=42,
    )

    print("\nTraining model...")
    model.fit(X_train, y_train)

    # Predictions
    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test)

    # Evaluation
    accuracy = accuracy_score(y_test, y_pred)
    print(f"\nModel Accuracy: {accuracy:.4f}")

    # Classification report
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, zero_division=0))

    # Feature importance
    print("\nFeature Importance:")
    feature_names = X.columns
    for name, importance in zip(feature_names, model.feature_importances_):
        print(f"  {name:30s}: {importance:.4f}")

    return model, accuracy, y_test, y_pred


def save_model(model, label_encoder, accuracy):
    """Save trained model and label encoder."""
    model_dir = Path(__file__).parent / "models"
    model_dir.mkdir(exist_ok=True)

    # Save XGBoost model
    model_path = model_dir / "lapse_predictor.json"
    model.save_model(str(model_path))
    print(f"\nModel saved to: {model_path}")

    # Save label encoder
    encoder_path = model_dir / "lapse_label_encoder.pkl"
    with open(encoder_path, "wb") as f:
        pickle.dump(label_encoder, f)
    print(f"Label encoder saved to: {encoder_path}")

    # Save metadata
    metadata = {
        "training_date": datetime.now().isoformat(),
        "accuracy": float(accuracy),
        "model_type": "XGBoost Multi-class Classifier",
        "features": [
            "lapse_type_encoded",
            "severity_encoded",
            "improper_percentage",
            "count",
            "total_cases_audited",
        ],
        "num_classes": len(label_encoder.classes_),
        "classes": label_encoder.classes_.tolist(),
    }

    metadata_path = model_dir / "lapse_model_metadata.json"
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    print(f"Metadata saved to: {metadata_path}")


async def main():
    """Main training pipeline."""
    print("=" * 80)
    print("DHRUVA Lapse Prediction Model Training")
    print("=" * 80)

    # Load data
    lapses = await load_lapse_data()
    print(f"\nLoaded {len(lapses)} lapse cases from database")

    if len(lapses) < 5:
        print("\nERROR: Insufficient data for training (need at least 5 cases)")
        return

    # Prepare data
    X, y, label_encoder, df = prepare_training_data(lapses)

    # Train model
    model, accuracy, y_test, y_pred = train_xgboost_model(X, y)

    # Save model
    save_model(model, label_encoder, accuracy)

    print("\n" + "=" * 80)
    print("Training Complete!")
    print("=" * 80)
    print(f"\nFinal Accuracy: {accuracy:.2%}")
    print(f"Model saved in: backend/ml/models/")


if __name__ == "__main__":
    asyncio.run(main())
