#!/usr/bin/env python3
"""
MuRIL Model Fine-tuning for DHRUVA
===================================
Fine-tunes Google's MuRIL (Multilingual Representations for Indian Languages) for:
1. Sentiment/Distress Detection (4-class)
2. Department Classification (15-class fallback)

Requirements:
    pip install transformers torch datasets scikit-learn

Usage:
    python train_muril_models.py --task sentiment
    python train_muril_models.py --task classification
    python train_muril_models.py --task both
"""

import argparse
import json
import os
from pathlib import Path
from datetime import datetime

import torch
from torch.utils.data import DataLoader
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    TrainingArguments,
    Trainer,
    EarlyStoppingCallback
)
from datasets import Dataset, DatasetDict
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import numpy as np

# Paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data" / "muril_training"
MODELS_DIR = BASE_DIR / "models"

# Model configuration
MODEL_NAME = "google/muril-base-cased"
MAX_LENGTH = 128  # Telugu text is usually short

# Labels
SENTIMENT_LABELS = ["NORMAL", "MEDIUM", "HIGH", "CRITICAL"]
DEPARTMENT_LABELS = [
    "Revenue", "Municipal Administration", "Police", "Agriculture", "Health",
    "Education", "Energy", "Panchayat Raj", "Social Welfare", "Civil Supplies",
    "Transport", "Housing", "Water Resources", "Women & Child Welfare", "Animal Husbandry"
]


def load_training_data(task: str):
    """Load training data for the specified task."""
    print(f"\nLoading {task} training data...")

    if task == "sentiment":
        data_file = DATA_DIR / "muril_sentiment_training.json"
        labels = SENTIMENT_LABELS
    else:
        data_file = DATA_DIR / "muril_classification_training.json"
        labels = DEPARTMENT_LABELS

    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    samples = data["samples"]
    print(f"Loaded {len(samples)} samples")

    # Convert to lists
    texts = [s["text"] for s in samples]
    label_names = [s["label"] for s in samples]

    # Convert labels to indices
    label2id = {label: i for i, label in enumerate(labels)}
    label_ids = [label2id.get(l, 0) for l in label_names]

    return texts, label_ids, labels, label2id


def create_dataset(texts, labels, tokenizer, test_size=0.2):
    """Create HuggingFace datasets."""
    # Split data
    train_texts, val_texts, train_labels, val_labels = train_test_split(
        texts, labels, test_size=test_size, random_state=42, stratify=labels
    )

    print(f"Train samples: {len(train_texts)}")
    print(f"Validation samples: {len(val_texts)}")

    def tokenize_function(examples):
        return tokenizer(
            examples["text"],
            padding="max_length",
            truncation=True,
            max_length=MAX_LENGTH
        )

    # Create datasets
    train_dataset = Dataset.from_dict({"text": train_texts, "label": train_labels})
    val_dataset = Dataset.from_dict({"text": val_texts, "label": val_labels})

    # Tokenize
    train_dataset = train_dataset.map(tokenize_function, batched=True)
    val_dataset = val_dataset.map(tokenize_function, batched=True)

    # Set format
    train_dataset.set_format(type="torch", columns=["input_ids", "attention_mask", "label"])
    val_dataset.set_format(type="torch", columns=["input_ids", "attention_mask", "label"])

    return train_dataset, val_dataset


def compute_metrics(eval_pred):
    """Compute metrics for evaluation."""
    logits, labels = eval_pred
    predictions = np.argmax(logits, axis=-1)
    acc = accuracy_score(labels, predictions)
    return {"accuracy": acc}


def train_model(task: str, epochs: int = 3, batch_size: int = 16):
    """Train MuRIL model for the specified task."""
    print("\n" + "="*60)
    print(f" Training MuRIL for {task.upper()}")
    print("="*60)

    # Check for GPU
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")

    # Load data
    texts, labels, label_names, label2id = load_training_data(task)
    id2label = {i: l for l, i in label2id.items()}
    num_labels = len(label_names)

    # Load tokenizer
    print(f"\nLoading tokenizer from {MODEL_NAME}...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

    # Create datasets
    train_dataset, val_dataset = create_dataset(texts, labels, tokenizer)

    # Load model
    print(f"Loading model from {MODEL_NAME}...")
    model = AutoModelForSequenceClassification.from_pretrained(
        MODEL_NAME,
        num_labels=num_labels,
        id2label=id2label,
        label2id=label2id
    )

    # Output directory
    output_dir = MODELS_DIR / f"muril_{task}"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Training arguments
    training_args = TrainingArguments(
        output_dir=str(output_dir),
        num_train_epochs=epochs,
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=batch_size,
        warmup_steps=100,
        weight_decay=0.01,
        logging_dir=str(output_dir / "logs"),
        logging_steps=50,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="accuracy",
        greater_is_better=True,
        report_to="none",  # Disable wandb etc.
    )

    # Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        compute_metrics=compute_metrics,
        callbacks=[EarlyStoppingCallback(early_stopping_patience=2)]
    )

    # Train
    print("\nStarting training...")
    trainer.train()

    # Evaluate
    print("\nEvaluating...")
    eval_results = trainer.evaluate()
    print(f"Validation Accuracy: {eval_results['eval_accuracy']:.2%}")

    # Save model
    print(f"\nSaving model to {output_dir}...")
    trainer.save_model(str(output_dir / "final"))
    tokenizer.save_pretrained(str(output_dir / "final"))

    # Save metadata
    metadata = {
        "task": task,
        "model_base": MODEL_NAME,
        "num_labels": num_labels,
        "labels": label_names,
        "label2id": label2id,
        "accuracy": eval_results['eval_accuracy'],
        "epochs": epochs,
        "batch_size": batch_size,
        "max_length": MAX_LENGTH,
        "train_samples": len(train_dataset),
        "val_samples": len(val_dataset),
        "trained_at": datetime.now().isoformat()
    }

    with open(output_dir / "metadata.json", 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f"\nTraining complete!")
    print(f"Model saved to: {output_dir / 'final'}")

    return eval_results['eval_accuracy']


def test_model(task: str):
    """Test a trained model with sample inputs."""
    print("\n" + "="*60)
    print(f" Testing MuRIL {task.upper()} Model")
    print("="*60)

    model_dir = MODELS_DIR / f"muril_{task}" / "final"

    if not model_dir.exists():
        print(f"Model not found at {model_dir}")
        print("Please train the model first.")
        return

    # Load model and tokenizer
    print("Loading model...")
    tokenizer = AutoTokenizer.from_pretrained(model_dir)
    model = AutoModelForSequenceClassification.from_pretrained(model_dir)

    # Load metadata
    with open(model_dir.parent / "metadata.json", 'r') as f:
        metadata = json.load(f)

    id2label = {int(k): v for k, v in model.config.id2label.items()}

    # Test samples
    if task == "sentiment":
        test_samples = [
            "నా పెన్షన్ 3 నెలలుగా రాలేదు ఆకలితో చనిపోతున్నాము",  # CRITICAL
            "pension not coming for 3 months starving",  # CRITICAL
            "రేషన్ కార్డు రాలేదు కష్టంగా ఉంది",  # HIGH
            "certificate delay problem",  # MEDIUM
            "information about scheme",  # NORMAL
        ]
    else:
        test_samples = [
            "భూమి పట్టా సమస్య",  # Revenue
            "రోడ్డు గుంతలు మరమ్మతు చేయండి",  # Municipal
            "పెన్షన్ రాలేదు",  # Social Welfare
            "electricity bill issue",  # Energy
            "ration card problem",  # Civil Supplies
        ]

    print("\nTest Predictions:")
    print("-" * 50)

    for text in test_samples:
        inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=MAX_LENGTH)

        with torch.no_grad():
            outputs = model(**inputs)
            probs = torch.softmax(outputs.logits, dim=1)
            pred_idx = torch.argmax(probs).item()
            confidence = probs[0][pred_idx].item()

        pred_label = id2label[pred_idx]

        # Safe print for Windows
        try:
            print(f"\nText: {text[:50]}...")
        except:
            print(f"\nText: [Telugu text]")
        print(f"Prediction: {pred_label} ({confidence:.0%})")


def main():
    parser = argparse.ArgumentParser(description="Train MuRIL models for DHRUVA")
    parser.add_argument(
        "--task",
        choices=["sentiment", "classification", "both", "test-sentiment", "test-classification"],
        default="both",
        help="Task to train or test"
    )
    parser.add_argument("--epochs", type=int, default=3, help="Number of epochs")
    parser.add_argument("--batch-size", type=int, default=16, help="Batch size")

    args = parser.parse_args()

    if args.task == "sentiment":
        train_model("sentiment", args.epochs, args.batch_size)
    elif args.task == "classification":
        train_model("classification", args.epochs, args.batch_size)
    elif args.task == "both":
        print("\n" + "="*60)
        print(" TRAINING BOTH MODELS")
        print("="*60)

        sent_acc = train_model("sentiment", args.epochs, args.batch_size)
        class_acc = train_model("classification", args.epochs, args.batch_size)

        print("\n" + "="*60)
        print(" TRAINING COMPLETE")
        print("="*60)
        print(f"Sentiment Model Accuracy: {sent_acc:.2%}")
        print(f"Classification Model Accuracy: {class_acc:.2%}")
    elif args.task == "test-sentiment":
        test_model("sentiment")
    elif args.task == "test-classification":
        test_model("classification")


if __name__ == "__main__":
    main()
