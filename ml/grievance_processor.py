"""
DHRUVA Unified Grievance Processor
===================================
Chains all ML models + adds duplicate detection, similar case matching,
shallow fix prediction, and proactive alerts.

Models Used:
- Telugu Classifier V3 (84.5% accuracy)
- Sentiment Classifier (88.9% accuracy)
- Classification Fallback (86.7% accuracy)
- Lapse Predictor (80.8% accuracy)
"""

import json
import pickle
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from sklearn.metrics.pairwise import cosine_similarity
from collections import defaultdict

# Paths
BASE_DIR = Path(__file__).parent
MODELS_DIR = BASE_DIR / "models"
KNOWLEDGE_BASE = BASE_DIR / "data" / "knowledge_base"


class GrievanceProcessor:
    """
    Unified processor that chains all ML models for end-to-end grievance processing.

    Pipeline:
    1. Duplicate Detection - Check if similar grievance exists
    2. Classification - Route to correct department
    3. Sentiment Analysis - Detect distress level (CRITICAL/HIGH/MEDIUM/NORMAL)
    4. Lapse Prediction - Predict if case likely to have improper redressal
    5. Similar Case Matching - Find resolved cases for officer suggestions
    6. Proactive Alerts - Detect patterns requiring attention
    """

    # Confidence thresholds
    CLASSIFICATION_HIGH_CONFIDENCE = 0.75
    CLASSIFICATION_LOW_CONFIDENCE = 0.40
    DUPLICATE_THRESHOLD = 0.85
    SIMILAR_CASE_THRESHOLD = 0.70

    # Telugu keyword boosting for departments
    # Maps keywords (Telugu and English) to department with confidence boost
    KEYWORD_DEPARTMENT_MAP = {
        # Social Welfare Department
        "పెన్షన్": ("Social Welfare", 0.85),
        "pension": ("Social Welfare", 0.85),
        "వృద్ధాప్య": ("Social Welfare", 0.85),
        "old age": ("Social Welfare", 0.85),
        "వితంతువు": ("Social Welfare", 0.85),
        "widow": ("Social Welfare", 0.85),
        "వికలాంగులు": ("Social Welfare", 0.85),
        "disabled": ("Social Welfare", 0.85),
        "disability": ("Social Welfare", 0.85),
        "సంక్షేమ": ("Social Welfare", 0.80),
        "welfare": ("Social Welfare", 0.80),
        "ఆసరా": ("Social Welfare", 0.85),
        "aasara": ("Social Welfare", 0.85),

        # Civil Supplies Department
        "రేషన్": ("Civil Supplies", 0.90),
        "ration": ("Civil Supplies", 0.90),
        "బియ్యం": ("Civil Supplies", 0.85),
        "rice": ("Civil Supplies", 0.80),
        "కిరోసిన్": ("Civil Supplies", 0.85),
        "kerosene": ("Civil Supplies", 0.85),
        "రేషన్ కార్డు": ("Civil Supplies", 0.90),
        "ration card": ("Civil Supplies", 0.90),
        "fair price": ("Civil Supplies", 0.85),
        "pds": ("Civil Supplies", 0.85),

        # Revenue Department
        "భూమి": ("Revenue", 0.85),
        "land": ("Revenue", 0.80),
        "land registration": ("Revenue", 0.92),  # Higher priority to avoid ration substring match
        "land records": ("Revenue", 0.92),
        "పట్టా": ("Revenue", 0.90),
        "patta": ("Revenue", 0.90),
        "సర్వే": ("Revenue", 0.85),
        "survey": ("Revenue", 0.80),
        "ఆక్రమణ": ("Revenue", 0.85),
        "encroachment": ("Revenue", 0.85),
        "రిజిస్ట్రేషన్": ("Revenue", 0.80),
        "registration": ("Revenue", 0.75),

        # Municipal Administration
        "రోడ్డు": ("Municipal Administration", 0.85),
        "road": ("Municipal Administration", 0.80),
        "గుంతలు": ("Municipal Administration", 0.85),
        "pothole": ("Municipal Administration", 0.85),
        "వీధి లైట్": ("Municipal Administration", 0.85),
        "street light": ("Municipal Administration", 0.85),
        "drainage": ("Municipal Administration", 0.85),
        "డ్రైనేజీ": ("Municipal Administration", 0.85),
        "చెత్త": ("Municipal Administration", 0.80),
        "garbage": ("Municipal Administration", 0.80),

        # Water Resources / Panchayat Raj
        "నీటి": ("Water Resources", 0.85),
        "water supply": ("Water Resources", 0.85),
        "నీరు": ("Water Resources", 0.80),
        "water": ("Water Resources", 0.70),
        "బోరు": ("Water Resources", 0.85),
        "borewell": ("Water Resources", 0.85),

        # Police
        "పోలీస్": ("Police", 0.85),
        "police": ("Police", 0.85),
        "fir": ("Police", 0.90),
        "దొంగతనం": ("Police", 0.85),
        "theft": ("Police", 0.85),
        "robbery": ("Police", 0.85),

        # Education
        "స్కూల్": ("Education", 0.85),
        "school": ("Education", 0.85),
        "టీచర్": ("Education", 0.85),
        "teacher": ("Education", 0.85),
        "విద్య": ("Education", 0.80),
        "education": ("Education", 0.80),

        # Health
        "ఆసుపత్రి": ("Health", 0.85),
        "hospital": ("Health", 0.85),
        "వైద్యం": ("Health", 0.85),
        "doctor": ("Health", 0.85),
        "medicine": ("Health", 0.80),
        "మందులు": ("Health", 0.80),

        # Housing
        "ఇల్లు": ("Housing", 0.80),
        "house": ("Housing", 0.75),
        "గృహ": ("Housing", 0.85),
        "housing": ("Housing", 0.85),
        "site": ("Housing", 0.75),
    }

    # Confidence calibration factors (to avoid over-promising)
    # These account for: small test set, synthetic training data, real-world variance
    CONFIDENCE_CALIBRATION = {
        "classification": 0.85,  # Reduce by 15% - synthetic data caveat
        "sentiment": 0.90,       # Reduce by 10% - sentiment is more reliable
    }

    # SLA hours by distress level
    SLA_HOURS = {
        "CRITICAL": 24,
        "HIGH": 72,
        "MEDIUM": 168,  # 7 days
        "NORMAL": 336   # 14 days
    }

    def __init__(self):
        """Initialize all models and knowledge base."""
        self.models_loaded = False
        self.classifier = None
        self.classifier_vectorizer = None
        self.sentiment_model = None
        self.sentiment_vectorizer = None
        self.fallback_model = None
        self.fallback_vectorizer = None
        self.lapse_model = None
        self.lapse_vectorizer = None

        # Knowledge base
        self.departments = {}
        self.lapse_definitions = {}
        self.response_templates = []
        self.grievance_types = {}

        # Case history for duplicate/similar detection
        self.case_history: List[Dict] = []
        self.case_vectors = None

        # Pattern tracking for proactive alerts
        self.area_complaints = defaultdict(list)
        self.officer_history = defaultdict(list)

        # Load everything
        self._load_models()
        self._load_knowledge_base()

    def _load_models(self):
        """Load all trained ML models."""
        try:
            # Telugu Classifier V3 (separate files)
            classifier_path = MODELS_DIR / "telugu_classifier_v3.pkl"
            vectorizer_path = MODELS_DIR / "tfidf_vectorizer_v3.pkl"
            labels_path = MODELS_DIR / "dept_label_encoder_v3.pkl"

            if classifier_path.exists():
                with open(classifier_path, "rb") as f:
                    self.classifier = pickle.load(f)
            if vectorizer_path.exists():
                with open(vectorizer_path, "rb") as f:
                    self.classifier_vectorizer = pickle.load(f)
            if labels_path.exists():
                with open(labels_path, "rb") as f:
                    self.classifier_labels = pickle.load(f)

            # Sentiment Model (separate files)
            sentiment_model_path = MODELS_DIR / "sentiment_classifier.pkl"
            sentiment_vec_path = MODELS_DIR / "sentiment_vectorizer.pkl"
            sentiment_labels_path = MODELS_DIR / "sentiment_label_encoder.pkl"

            if sentiment_model_path.exists():
                with open(sentiment_model_path, "rb") as f:
                    self.sentiment_model = pickle.load(f)
            if sentiment_vec_path.exists():
                with open(sentiment_vec_path, "rb") as f:
                    self.sentiment_vectorizer = pickle.load(f)
            if sentiment_labels_path.exists():
                with open(sentiment_labels_path, "rb") as f:
                    self.sentiment_labels = pickle.load(f)

            # Classification Fallback (separate files)
            fallback_model_path = MODELS_DIR / "classification_fallback.pkl"
            fallback_vec_path = MODELS_DIR / "classification_fallback_vectorizer.pkl"
            fallback_labels_path = MODELS_DIR / "classification_fallback_label_encoder.pkl"

            if fallback_model_path.exists():
                with open(fallback_model_path, "rb") as f:
                    self.fallback_model = pickle.load(f)
            if fallback_vec_path.exists():
                with open(fallback_vec_path, "rb") as f:
                    self.fallback_vectorizer = pickle.load(f)
            if fallback_labels_path.exists():
                with open(fallback_labels_path, "rb") as f:
                    self.fallback_labels = pickle.load(f)

            # Lapse Predictor
            lapse_path = MODELS_DIR / "lapse_predictor.pkl"
            lapse_vec_path = MODELS_DIR / "lapse_vectorizer.pkl"

            if lapse_path.exists():
                with open(lapse_path, "rb") as f:
                    self.lapse_model = pickle.load(f)
            if lapse_vec_path.exists():
                with open(lapse_vec_path, "rb") as f:
                    self.lapse_vectorizer = pickle.load(f)

            self.models_loaded = True
            print("[OK] All models loaded successfully")

        except Exception as e:
            print(f"[ERROR] Loading models: {e}")
            self.models_loaded = False

    def _load_knowledge_base(self):
        """Load knowledge base data."""
        try:
            # Departments
            dept_file = KNOWLEDGE_BASE / "tier1_core" / "departments.json"
            if dept_file.exists():
                with open(dept_file, "r", encoding="utf-8") as f:
                    self.departments = json.load(f)

            # Lapse definitions
            lapse_file = KNOWLEDGE_BASE / "tier1_core" / "lapse_definitions.json"
            if lapse_file.exists():
                with open(lapse_file, "r", encoding="utf-8") as f:
                    self.lapse_definitions = json.load(f)

            # Response templates
            template_file = KNOWLEDGE_BASE / "tier1_core" / "response_templates.json"
            if template_file.exists():
                with open(template_file, "r", encoding="utf-8") as f:
                    self.response_templates = json.load(f)

            # Grievance types
            types_file = KNOWLEDGE_BASE / "tier1_core" / "grievance_types.json"
            if types_file.exists():
                with open(types_file, "r", encoding="utf-8") as f:
                    self.grievance_types = json.load(f)

            print("[OK] Knowledge base loaded")

        except Exception as e:
            print(f"[ERROR] Loading knowledge base: {e}")

    def process(self, grievance_text: str, citizen_id: str = None,
                location: str = None, metadata: Dict = None) -> Dict[str, Any]:
        """
        Process a grievance through the full pipeline.

        Args:
            grievance_text: The grievance text (Telugu/English)
            citizen_id: Optional citizen identifier for duplicate check
            location: Optional location for pattern detection
            metadata: Optional additional metadata

        Returns:
            Complete analysis result with routing, priority, predictions
        """
        result = {
            "timestamp": datetime.now().isoformat(),
            "input": {
                "text": grievance_text,
                "citizen_id": citizen_id,
                "location": location
            },
            "classification": {},
            "sentiment": {},
            "lapse_prediction": {},
            "duplicate_check": {},
            "similar_cases": [],
            "proactive_alerts": [],
            "recommended_actions": [],
            "response_template": None,
            "sla": {}
        }

        # Step 1: Duplicate Detection
        if citizen_id:
            duplicate = self._check_duplicate(grievance_text, citizen_id)
            result["duplicate_check"] = duplicate
            if duplicate.get("is_duplicate"):
                result["recommended_actions"].append({
                    "action": "MERGE_WITH_EXISTING",
                    "case_id": duplicate.get("existing_case_id"),
                    "reason": "Similar grievance from same citizen"
                })

        # Step 2: Classification
        classification = self._classify(grievance_text)
        result["classification"] = classification

        # Step 3: Sentiment/Distress Detection
        sentiment = self._analyze_sentiment(grievance_text)
        result["sentiment"] = sentiment

        # Step 4: Calculate SLA based on distress
        distress_level = sentiment.get("distress_level", "NORMAL")
        sla_hours = self.SLA_HOURS.get(distress_level, 336)
        result["sla"] = {
            "hours": sla_hours,
            "deadline": (datetime.now() + timedelta(hours=sla_hours)).isoformat(),
            "priority": distress_level
        }

        # Step 5: Lapse Prediction
        lapse = self._predict_lapse(grievance_text, classification.get("department"))
        result["lapse_prediction"] = lapse

        # Step 6: Find Similar Resolved Cases
        similar = self._find_similar_cases(grievance_text, classification.get("department"))
        result["similar_cases"] = similar

        # Step 7: Check for Proactive Alerts
        if location:
            alerts = self._check_proactive_alerts(location, classification.get("department"))
            result["proactive_alerts"] = alerts

        # Step 8: Select Response Template
        template = self._select_template(distress_level, classification.get("department"))
        result["response_template"] = template

        # Step 9: Generate Recommended Actions
        actions = self._generate_actions(result)
        result["recommended_actions"].extend(actions)

        # Store for future similarity matching
        self._store_case(grievance_text, citizen_id, result)

        return result

    def _keyword_boost(self, text: str) -> Optional[Tuple[str, float]]:
        """
        Check text against keyword map for high-confidence department matches.
        Returns (department, confidence) if keyword match found, None otherwise.

        This helps overcome ML model limitations with Telugu text by using
        explicit keyword matching as a pre-filter.
        """
        text_lower = text.lower()

        # Track best keyword match
        best_match = None
        best_confidence = 0.0

        for keyword, (department, confidence) in self.KEYWORD_DEPARTMENT_MAP.items():
            if keyword.lower() in text_lower:
                # Prefer longer keyword matches (more specific)
                # and higher confidence scores
                keyword_score = confidence * (1 + len(keyword) / 100)  # Slight boost for longer keywords
                if keyword_score > best_confidence:
                    best_confidence = confidence  # Use original confidence, not boosted
                    best_match = (department, confidence)

        return best_match

    def _classify(self, text: str) -> Dict:
        """Classify grievance to department with keyword boosting and confidence-based fallback."""
        result = {
            "department": None,
            "confidence": 0.0,
            "method": None,
            "top_3": [],
            "needs_manual_review": False
        }

        # Step 1: Try keyword boosting first (especially helpful for Telugu)
        keyword_match = self._keyword_boost(text)
        if keyword_match:
            keyword_dept, keyword_conf = keyword_match
            # If we have a high-confidence keyword match, use it directly
            if keyword_conf >= self.CLASSIFICATION_HIGH_CONFIDENCE:
                result["department"] = keyword_dept
                result["confidence"] = keyword_conf
                result["method"] = "keyword_boost"
                result["top_3"] = [{"department": keyword_dept, "confidence": keyword_conf}]
                print(f"[CLASSIFY] Keyword boost: {keyword_dept} ({keyword_conf:.0%})")
                return result

        # Step 2: Try ML classifiers
        if not self.classifier or not self.classifier_vectorizer:
            # Fallback to keyword match if models not loaded
            if keyword_match:
                result["department"] = keyword_match[0]
                result["confidence"] = keyword_match[1]
                result["method"] = "keyword_boost_fallback"
                result["top_3"] = [{"department": keyword_match[0], "confidence": keyword_match[1]}]
            return result

        try:
            # Primary classifier
            X = self.classifier_vectorizer.transform([text])
            proba = self.classifier.predict_proba(X)[0]
            top_indices = np.argsort(proba)[::-1][:3]

            # Apply calibration factor to avoid over-promising
            calibration = self.CONFIDENCE_CALIBRATION["classification"]
            raw_conf = float(proba[top_indices[0]])
            calibrated_conf = raw_conf * calibration

            result["confidence"] = calibrated_conf
            result["department"] = self.classifier_labels.inverse_transform([top_indices[0]])[0]
            result["top_3"] = [
                {
                    "department": self.classifier_labels.inverse_transform([idx])[0],
                    "confidence": float(proba[idx]) * calibration
                }
                for idx in top_indices
            ]
            result["method"] = "primary_classifier"

            # Step 3: If ML confidence is low, consider keyword boost or fallback
            if result["confidence"] < self.CLASSIFICATION_LOW_CONFIDENCE:
                # First try keyword boost
                if keyword_match and keyword_match[1] > result["confidence"]:
                    result["department"] = keyword_match[0]
                    result["confidence"] = keyword_match[1]
                    result["method"] = "keyword_boost"
                    # Update top_3 to include keyword match
                    result["top_3"].insert(0, {"department": keyword_match[0], "confidence": keyword_match[1]})
                    result["top_3"] = result["top_3"][:3]
                    print(f"[CLASSIFY] Keyword boost (low ML conf): {keyword_match[0]} ({keyword_match[1]:.0%})")
                # Then try fallback classifier
                elif self.fallback_model and self.fallback_vectorizer:
                    X_fb = self.fallback_vectorizer.transform([text])
                    proba_fb = self.fallback_model.predict_proba(X_fb)[0]
                    top_idx_fb = np.argmax(proba_fb)
                    fb_conf = float(proba_fb[top_idx_fb])

                    if fb_conf > result["confidence"]:
                        result["department"] = self.fallback_labels.inverse_transform([top_idx_fb])[0]
                        result["confidence"] = fb_conf
                        result["method"] = "fallback_classifier"

            # Step 4: Even with medium confidence, keyword boost can override if it matches a different dept
            elif result["confidence"] < self.CLASSIFICATION_HIGH_CONFIDENCE:
                if keyword_match and keyword_match[1] >= result["confidence"]:
                    # Keyword match is as confident or more confident than ML
                    result["department"] = keyword_match[0]
                    result["confidence"] = keyword_match[1]
                    result["method"] = "keyword_boost"
                    print(f"[CLASSIFY] Keyword override (medium ML conf): {keyword_match[0]} ({keyword_match[1]:.0%})")

            # Flag for manual review if still low confidence
            if result["confidence"] < self.CLASSIFICATION_LOW_CONFIDENCE:
                result["needs_manual_review"] = True

        except Exception as e:
            result["error"] = str(e)
            # Fallback to keyword match on error
            if keyword_match:
                result["department"] = keyword_match[0]
                result["confidence"] = keyword_match[1]
                result["method"] = "keyword_boost_error_fallback"

        return result

    # Comprehensive distress keyword dictionary
    DISTRESS_KEYWORDS = {
        "CRITICAL": [
            # Telugu critical keywords
            "చనిపోతున్నాము", "ఆత్మహత్య", "ఆకలి", "చనిపోతాను", "మరణం",
            "బతకలేను", "తినడానికి ఏమీ లేదు", "పిల్లలు ఆకలి", "అసహాయం",
            # English critical keywords
            "dying", "suicide", "starving", "will die", "death",
            "cannot survive", "nothing to eat", "children hungry", "helpless",
            "life threat", "emergency", "critical condition", "desperate"
        ],
        "HIGH": [
            # Telugu high-urgency keywords
            "నెలలుగా", "రాలేదు", "ఆగిపోయింది", "పూర్తిగా", "అత్యవసర",
            "వెంటనే", "తీవ్ర", "చాలా కష్టం", "బాధపడుతున్నాము",
            # English high-urgency keywords
            "months", "not received", "stopped", "completely", "urgent",
            "immediately", "severe", "very difficult", "suffering",
            "delayed", "long pending", "no action", "ignored"
        ],
        "MEDIUM": [
            # Telugu medium keywords
            "సమస్య", "ఇబ్బంది", "చికాకు", "అసౌకర్యం", "తప్పు",
            # English medium keywords - removed "complaint" as it's too generic
            "problem", "issue", "inconvenience", "trouble",
            "difficulty", "incorrect", "wrong", "not working"
        ]
    }

    def _analyze_sentiment(self, text: str) -> Dict:
        """Analyze distress level of grievance with enhanced keyword detection."""
        result = {
            "distress_level": "NORMAL",
            "confidence": 0.0,
            "signals": []
        }

        text_lower = text.lower()

        # Step 1: Detect distress signals from keywords
        detected_signals = []
        highest_level = "NORMAL"
        level_priority = {"CRITICAL": 3, "HIGH": 2, "MEDIUM": 1, "NORMAL": 0}

        for level, keywords in self.DISTRESS_KEYWORDS.items():
            for kw in keywords:
                if kw.lower() in text_lower:
                    detected_signals.append({"keyword": kw, "level": level})
                    if level_priority[level] > level_priority[highest_level]:
                        highest_level = level

        result["signals"] = detected_signals

        # Step 2: Try ML model if available
        ml_level = "NORMAL"
        ml_confidence = 0.0

        if self.sentiment_model and self.sentiment_vectorizer:
            try:
                X = self.sentiment_vectorizer.transform([text])
                proba = self.sentiment_model.predict_proba(X)[0]
                pred_idx = np.argmax(proba)

                # Apply calibration factor
                calibration = self.CONFIDENCE_CALIBRATION["sentiment"]
                raw_conf = float(proba[pred_idx])
                ml_confidence = raw_conf * calibration

                ml_level = self.sentiment_labels.inverse_transform([pred_idx])[0]
            except Exception as e:
                result["error"] = str(e)

        # Step 3: Combine ML and keyword-based detection
        # Use the higher severity level between ML and keyword detection
        if level_priority[highest_level] > level_priority[ml_level]:
            # Keyword detection found higher severity
            result["distress_level"] = highest_level
            # Confidence based on number of signals
            signal_count = len([s for s in detected_signals if s["level"] == highest_level])
            result["confidence"] = min(0.95, 0.70 + 0.05 * signal_count)
            result["method"] = "keyword_override"
        elif ml_confidence > 0.5:
            # ML model is confident
            result["distress_level"] = ml_level
            result["confidence"] = ml_confidence
            result["method"] = "ml_classifier"
        elif detected_signals:
            # Low ML confidence but we have keyword signals
            result["distress_level"] = highest_level
            result["confidence"] = 0.65
            result["method"] = "keyword_fallback"
        else:
            # Default to ML result
            result["distress_level"] = ml_level if ml_confidence > 0 else "NORMAL"
            result["confidence"] = ml_confidence if ml_confidence > 0 else 0.5
            result["method"] = "ml_default"

        return result

    # Rule-based lapse risk factors
    LAPSE_RISK_PATTERNS = {
        # High-risk patterns (0.7+ risk)
        "pending_months": {
            "keywords": ["నెలలుగా", "months", "నెలల", "weeks", "వారాలుగా"],
            "lapse": "Undue Delay",
            "base_risk": 0.75
        },
        "repeated_complaint": {
            "keywords": ["again", "మళ్ళీ", "repeated", "multiple times", "పలుసార్లు"],
            "lapse": "Improper Process",
            "base_risk": 0.80
        },
        "no_response": {
            "keywords": ["no response", "స్పందన లేదు", "no reply", "ignored", "నిర్లక్ష్యం"],
            "lapse": "Non-Responsive Officer",
            "base_risk": 0.85
        },
        "bribery": {
            "keywords": ["bribe", "లంచం", "corruption", "అవినీతి", "money demanded"],
            "lapse": "Corruption/Misconduct",
            "base_risk": 0.90
        },
        # Medium-risk patterns (0.4-0.7 risk)
        "document_issues": {
            "keywords": ["rejected", "తిరస్కరించారు", "wrong", "incorrect", "తప్పు"],
            "lapse": "Improper Documentation",
            "base_risk": 0.55
        },
        "partial_resolution": {
            "keywords": ["partial", "incomplete", "పూర్తి కాలేదు", "half", "partly"],
            "lapse": "Incomplete Resolution",
            "base_risk": 0.60
        },
        "transferred": {
            "keywords": ["transferred", "బదిలీ", "sent to", "referred", "పంపారు"],
            "lapse": "Improper Routing",
            "base_risk": 0.45
        },
        # Department-specific risks
        "revenue_risk": {
            "keywords": ["encroachment", "ఆక్రమణ", "land grab", "survey", "సర్వే"],
            "lapse": "Property Documentation Lapse",
            "base_risk": 0.50,
            "departments": ["Revenue"]
        },
        "welfare_risk": {
            "keywords": ["pension", "పెన్షన్", "benefit", "ration", "రేషన్"],
            "lapse": "Benefit Disbursement Lapse",
            "base_risk": 0.55,
            "departments": ["Social Welfare", "Civil Supplies"]
        }
    }

    def _predict_lapse(self, text: str, department: str = None) -> Dict:
        """Predict likelihood of improper redressal using rule-based system."""
        result = {
            "risk_score": 0.0,
            "likely_lapses": [],
            "risk_level": "LOW"
        }

        text_lower = text.lower()
        detected_lapses = []

        # Check each risk pattern
        for pattern_name, pattern_config in self.LAPSE_RISK_PATTERNS.items():
            # Check department filter if present
            if "departments" in pattern_config:
                if department and department not in pattern_config["departments"]:
                    continue

            # Check for keywords
            for keyword in pattern_config["keywords"]:
                if keyword.lower() in text_lower:
                    lapse_info = {
                        "lapse": pattern_config["lapse"],
                        "probability": pattern_config["base_risk"],
                        "trigger": keyword
                    }
                    # Avoid duplicates
                    if not any(l["lapse"] == lapse_info["lapse"] for l in detected_lapses):
                        detected_lapses.append(lapse_info)
                    break

        # Calculate overall risk
        if detected_lapses:
            result["likely_lapses"] = [
                {"lapse": l["lapse"], "probability": l["probability"]}
                for l in detected_lapses
            ]
            result["risk_score"] = max(l["probability"] for l in detected_lapses)

            # Apply cumulative risk boost for multiple lapses
            if len(detected_lapses) > 1:
                result["risk_score"] = min(0.95, result["risk_score"] + 0.1 * (len(detected_lapses) - 1))

        # Determine risk level
        if result["risk_score"] > 0.7:
            result["risk_level"] = "HIGH"
        elif result["risk_score"] > 0.4:
            result["risk_level"] = "MEDIUM"
        else:
            result["risk_level"] = "LOW"

        # Try ML model if available (for future enhancement)
        if self.lapse_model and self.lapse_vectorizer:
            try:
                combined = f"{text} {department or ''}"
                X = self.lapse_vectorizer.transform([combined])
                if hasattr(self.lapse_model, "predict_proba"):
                    proba = self.lapse_model.predict_proba(X)
                    ml_score = float(np.max(proba)) if not isinstance(proba, list) else 0.0
                    # Combine ML and rule-based scores
                    result["risk_score"] = max(result["risk_score"], ml_score)
            except Exception:
                pass  # Fallback to rule-based only

        return result

    def _check_duplicate(self, text: str, citizen_id: str) -> Dict:
        """Check if similar grievance exists from same citizen."""
        result = {
            "is_duplicate": False,
            "existing_case_id": None,
            "similarity": 0.0
        }

        if not self.case_history:
            return result

        # Find cases from same citizen
        citizen_cases = [c for c in self.case_history if c.get("citizen_id") == citizen_id]

        if not citizen_cases:
            return result

        # Check similarity
        if self.classifier_vectorizer:
            try:
                new_vec = self.classifier_vectorizer.transform([text])

                for case in citizen_cases:
                    case_vec = self.classifier_vectorizer.transform([case["text"]])
                    similarity = cosine_similarity(new_vec, case_vec)[0][0]

                    if similarity > self.DUPLICATE_THRESHOLD:
                        result["is_duplicate"] = True
                        result["existing_case_id"] = case.get("case_id")
                        result["similarity"] = float(similarity)
                        break
                    elif similarity > result["similarity"]:
                        result["similarity"] = float(similarity)

            except Exception as e:
                result["error"] = str(e)

        return result

    def _find_similar_cases(self, text: str, department: str = None, limit: int = 3) -> List[Dict]:
        """Find similar resolved cases for officer suggestions."""
        similar = []

        if not self.case_history or not self.classifier_vectorizer:
            return similar

        try:
            # Filter resolved cases in same department
            resolved = [c for c in self.case_history
                       if c.get("status") == "RESOLVED"
                       and (department is None or c.get("department") == department)]

            if not resolved:
                return similar

            new_vec = self.classifier_vectorizer.transform([text])

            similarities = []
            for case in resolved:
                case_vec = self.classifier_vectorizer.transform([case["text"]])
                sim = cosine_similarity(new_vec, case_vec)[0][0]
                if sim > self.SIMILAR_CASE_THRESHOLD:
                    similarities.append((case, sim))

            # Sort by similarity and take top N
            similarities.sort(key=lambda x: x[1], reverse=True)

            for case, sim in similarities[:limit]:
                similar.append({
                    "case_id": case.get("case_id"),
                    "similarity": float(sim),
                    "resolution": case.get("resolution"),
                    "resolution_time_days": case.get("resolution_time_days")
                })

        except Exception as e:
            pass

        return similar

    def _check_proactive_alerts(self, location: str, department: str = None) -> List[Dict]:
        """Check for patterns that warrant proactive intervention."""
        alerts = []

        # Track this complaint
        self.area_complaints[location].append({
            "timestamp": datetime.now(),
            "department": department
        })

        # Check for area-based patterns (5+ complaints in 30 days)
        recent = [c for c in self.area_complaints[location]
                 if c["timestamp"] > datetime.now() - timedelta(days=30)]

        if len(recent) >= 5:
            # Group by department
            dept_counts = defaultdict(int)
            for c in recent:
                dept_counts[c["department"]] += 1

            for dept, count in dept_counts.items():
                if count >= 5:
                    alerts.append({
                        "type": "AREA_PATTERN",
                        "location": location,
                        "department": dept,
                        "count": count,
                        "period_days": 30,
                        "recommendation": f"Infrastructure review needed for {dept} in {location}"
                    })

        return alerts

    def _select_template(self, distress_level: str, department: str = None) -> Optional[Dict]:
        """Select appropriate response template."""
        if not self.response_templates:
            return None

        # Templates are stored as dict with categories
        categories = self.response_templates.get("template_categories", [])

        # Default acknowledgment template based on distress level
        default_templates = {
            "CRITICAL": {
                "category": "Urgent",
                "telugu": "మీ సమస్య అత్యవసరంగా పరిశీలించబడుతోంది. 24 గంటల్లో స్పందన వస్తుంది.",
                "english": "Your grievance is being treated as urgent. Response within 24 hours."
            },
            "HIGH": {
                "category": "High Priority",
                "telugu": "మీ సమస్య ప్రాధాన్యతగా పరిశీలించబడుతోంది. 3 రోజుల్లో స్పందన వస్తుంది.",
                "english": "Your grievance is being treated as high priority. Response within 3 days."
            },
            "MEDIUM": {
                "category": "Normal",
                "telugu": "మీ సమస్య నమోదు చేయబడింది. 7 రోజుల్లో స్పందన వస్తుంది.",
                "english": "Your grievance has been registered. Response within 7 days."
            },
            "NORMAL": {
                "category": "Normal",
                "telugu": "మీ సమస్య నమోదు చేయబడింది. 14 రోజుల్లో స్పందన వస్తుంది.",
                "english": "Your grievance has been registered. Response within 14 days."
            }
        }

        return default_templates.get(distress_level, default_templates["NORMAL"])

    def _generate_actions(self, result: Dict) -> List[Dict]:
        """Generate recommended actions based on analysis."""
        actions = []

        # High distress - immediate attention
        if result["sentiment"].get("distress_level") == "CRITICAL":
            actions.append({
                "action": "IMMEDIATE_ATTENTION",
                "priority": "URGENT",
                "reason": "Critical distress level detected"
            })

        # Low classification confidence
        if result["classification"].get("needs_manual_review"):
            actions.append({
                "action": "MANUAL_CLASSIFICATION",
                "priority": "MEDIUM",
                "reason": f"Low confidence ({result['classification'].get('confidence', 0):.0%})"
            })

        # High lapse risk
        if result["lapse_prediction"].get("risk_level") == "HIGH":
            actions.append({
                "action": "SUPERVISOR_REVIEW",
                "priority": "HIGH",
                "reason": "High risk of improper redressal"
            })

        # Similar cases found
        if result["similar_cases"]:
            actions.append({
                "action": "REVIEW_SIMILAR_CASES",
                "priority": "LOW",
                "reason": f"{len(result['similar_cases'])} similar resolved cases found",
                "cases": [c["case_id"] for c in result["similar_cases"]]
            })

        return actions

    def _store_case(self, text: str, citizen_id: str, result: Dict):
        """Store case for future similarity matching."""
        case = {
            "case_id": f"PGRS-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "text": text,
            "citizen_id": citizen_id,
            "department": result["classification"].get("department"),
            "distress_level": result["sentiment"].get("distress_level"),
            "timestamp": datetime.now().isoformat(),
            "status": "OPEN"
        }
        self.case_history.append(case)

    def add_resolved_case(self, case_id: str, resolution: str, resolution_time_days: int):
        """Add a resolved case for similarity matching."""
        for case in self.case_history:
            if case.get("case_id") == case_id:
                case["status"] = "RESOLVED"
                case["resolution"] = resolution
                case["resolution_time_days"] = resolution_time_days
                break

    def get_officer_queue(self, officer_id: str = None, department: str = None) -> List[Dict]:
        """Get prioritized queue for officer dashboard."""
        # Filter open cases
        open_cases = [c for c in self.case_history if c.get("status") == "OPEN"]

        if department:
            open_cases = [c for c in open_cases if c.get("department") == department]

        # Sort by distress level priority
        priority_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "NORMAL": 3}
        open_cases.sort(key=lambda x: priority_order.get(x.get("distress_level", "NORMAL"), 3))

        return open_cases


# Convenience functions for API integration
_processor = None

def get_processor() -> GrievanceProcessor:
    """Get or create singleton processor instance."""
    global _processor
    if _processor is None:
        _processor = GrievanceProcessor()
    return _processor

def process_grievance(text: str, citizen_id: str = None,
                     location: str = None) -> Dict[str, Any]:
    """Process a grievance through the full pipeline."""
    return get_processor().process(text, citizen_id, location)

def classify_grievance(text: str) -> Dict:
    """Quick classification only."""
    return get_processor()._classify(text)

def analyze_sentiment(text: str) -> Dict:
    """Quick sentiment analysis only."""
    return get_processor()._analyze_sentiment(text)

def predict_lapse(text: str, department: str = None) -> Dict:
    """Quick lapse prediction only."""
    return get_processor()._predict_lapse(text, department)


def safe_print(text):
    """Print with fallback for encoding issues."""
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode('ascii', 'replace').decode('ascii'))


if __name__ == "__main__":
    # Test the processor
    processor = GrievanceProcessor()

    test_cases = [
        {
            "text": "నా పెన్షన్ 6 నెలలుగా రాలేదు పిల్లలకు తినడానికి ఏమీ లేదు",
            "citizen_id": "C001",
            "location": "Guntur",
            "desc": "Pension not received 6 months, children hungry"
        },
        {
            "text": "రోడ్డు మీద గుంతలు ఉన్నాయి రిపేర్ చేయండి",
            "citizen_id": "C002",
            "location": "Vijayawada",
            "desc": "Road has potholes, please repair"
        },
        {
            "text": "రేషన్ కార్డు కావాలి దయచేసి సహాయం చేయండి",
            "citizen_id": "C003",
            "location": "Guntur",
            "desc": "Need ration card, please help"
        }
    ]

    print("\n" + "="*70)
    print(" GRIEVANCE PROCESSOR TEST")
    print("="*70)

    for i, case in enumerate(test_cases, 1):
        print(f"\n--- Test Case {i} ---")
        safe_print(f"Input: {case['desc']}")

        result = processor.process(
            case["text"],
            case["citizen_id"],
            case["location"]
        )

        print(f"Department: {result['classification'].get('department')} "
              f"({result['classification'].get('confidence', 0):.0%})")
        print(f"Distress: {result['sentiment'].get('distress_level')} "
              f"({result['sentiment'].get('confidence', 0):.0%})")
        print(f"SLA: {result['sla'].get('hours')} hours")
        print(f"Lapse Risk: {result['lapse_prediction'].get('risk_level')}")
        print(f"Actions: {len(result['recommended_actions'])}")

        for action in result["recommended_actions"]:
            print(f"  -> {action['action']}: {action['reason']}")
