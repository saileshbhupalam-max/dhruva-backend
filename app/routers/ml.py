"""ML Router - Unified ML Pipeline API Endpoints.

Provides endpoints for:
- POST /ml/analyze - Full grievance analysis pipeline
- POST /ml/classify - Department classification only
- POST /ml/sentiment - Distress/sentiment analysis only
- POST /ml/predict-lapse - Lapse prediction only
- GET /ml/health - ML models health check
- GET /ml/queue - Officer prioritized queue
"""

import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

# Add ML directory to path (backend/ml)
ML_DIR = Path(__file__).parent.parent.parent / "ml"
sys.path.insert(0, str(ML_DIR))

from app.dependencies.auth import get_current_active_user, require_role
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ml", tags=["ML Pipeline"])

# Lazy load processor to avoid startup delay
_processor = None


def get_processor():
    """Get or create GrievanceProcessor instance."""
    global _processor
    if _processor is None:
        try:
            from grievance_processor import GrievanceProcessor
            _processor = GrievanceProcessor()
            logger.info("GrievanceProcessor initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize GrievanceProcessor: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"ML models not available: {str(e)}"
            )
    return _processor


# Request/Response Models
class AnalyzeRequest(BaseModel):
    """Full analysis request."""
    text: str = Field(..., min_length=10, max_length=5000, description="Grievance text (Telugu/English)")
    citizen_id: Optional[str] = Field(None, description="Citizen identifier for duplicate detection")
    location: Optional[str] = Field(None, description="Location for pattern detection")

    class Config:
        json_schema_extra = {
            "example": {
                "text": "నా పెన్షన్ 6 నెలలుగా రాలేదు పిల్లలకు తినడానికి ఏమీ లేదు",
                "citizen_id": "C001",
                "location": "Guntur"
            }
        }


class ClassifyRequest(BaseModel):
    """Classification-only request."""
    text: str = Field(..., min_length=10, max_length=5000, description="Grievance text")

    class Config:
        json_schema_extra = {
            "example": {
                "text": "రోడ్డు మీద గుంతలు ఉన్నాయి రిపేర్ చేయండి"
            }
        }


class SentimentRequest(BaseModel):
    """Sentiment analysis request."""
    text: str = Field(..., min_length=10, max_length=5000, description="Grievance text")

    class Config:
        json_schema_extra = {
            "example": {
                "text": "ఆకలితో చనిపోతున్నాము సహాయం చేయండి"
            }
        }


class LapsePredictRequest(BaseModel):
    """Lapse prediction request."""
    text: str = Field(..., min_length=10, max_length=5000, description="Grievance text")
    department: Optional[str] = Field(None, description="Department name for context")

    class Config:
        json_schema_extra = {
            "example": {
                "text": "నా భూమి సర్వే సరిగ్గా చేయలేదు",
                "department": "Revenue"
            }
        }


class ClassificationResult(BaseModel):
    """Classification result."""
    department: Optional[str] = None
    confidence: float = 0.0
    method: Optional[str] = None
    top_3: List[Dict[str, Any]] = []
    needs_manual_review: bool = False


class SentimentResult(BaseModel):
    """Sentiment/distress result."""
    distress_level: str = "NORMAL"
    confidence: float = 0.0
    signals: List[Dict[str, str]] = []


class LapsePredictionResult(BaseModel):
    """Lapse prediction result."""
    risk_score: float = 0.0
    risk_level: str = "LOW"
    likely_lapses: List[Dict[str, Any]] = []


class SLAResult(BaseModel):
    """SLA calculation result."""
    hours: int
    deadline: str
    priority: str


class AnalyzeResponse(BaseModel):
    """Full analysis response."""
    timestamp: str
    classification: ClassificationResult
    sentiment: SentimentResult
    lapse_prediction: LapsePredictionResult
    sla: SLAResult
    duplicate_check: Dict[str, Any] = {}
    similar_cases: List[Dict[str, Any]] = []
    proactive_alerts: List[Dict[str, Any]] = []
    recommended_actions: List[Dict[str, Any]] = []
    response_template: Optional[Dict[str, str]] = None


class HealthResponse(BaseModel):
    """ML health check response."""
    status: str
    models_loaded: bool
    models: Dict[str, bool]
    knowledge_base_loaded: bool


class QueueItem(BaseModel):
    """Queue item for officer dashboard."""
    case_id: str
    text_preview: str
    department: Optional[str]
    distress_level: str
    timestamp: str
    status: str


class QueueResponse(BaseModel):
    """Officer queue response."""
    total: int
    items: List[QueueItem]


# Endpoints
@router.post(
    "/analyze",
    response_model=AnalyzeResponse,
    summary="Full grievance analysis",
    description="Process grievance through complete ML pipeline: classification, sentiment, lapse prediction, duplicate detection, similar case matching.",
)
async def analyze_grievance(
    request: AnalyzeRequest,
) -> AnalyzeResponse:
    """Full grievance analysis pipeline.

    This endpoint chains all ML models:
    1. Duplicate Detection - Check if similar grievance exists
    2. Classification - Route to correct department (84.5% accuracy)
    3. Sentiment Analysis - Detect distress level (88.9% accuracy)
    4. Lapse Prediction - Predict improper redressal risk
    5. Similar Case Matching - Find resolved cases for suggestions
    6. Proactive Alerts - Detect area-based patterns

    Args:
        request: Grievance text with optional citizen_id and location

    Returns:
        Complete analysis with routing, priority, and recommendations
    """
    processor = get_processor()

    try:
        result = processor.process(
            grievance_text=request.text,
            citizen_id=request.citizen_id,
            location=request.location
        )

        return AnalyzeResponse(
            timestamp=result["timestamp"],
            classification=ClassificationResult(**result["classification"]),
            sentiment=SentimentResult(**result["sentiment"]),
            lapse_prediction=LapsePredictionResult(**result["lapse_prediction"]),
            sla=SLAResult(**result["sla"]),
            duplicate_check=result.get("duplicate_check", {}),
            similar_cases=result.get("similar_cases", []),
            proactive_alerts=result.get("proactive_alerts", []),
            recommended_actions=result.get("recommended_actions", []),
            response_template=result.get("response_template"),
        )

    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )


@router.post(
    "/classify",
    response_model=ClassificationResult,
    summary="Department classification only",
    description="Classify grievance to appropriate department using Telugu Classifier V3 (84.5% accuracy).",
)
async def classify_only(
    request: ClassifyRequest,
) -> ClassificationResult:
    """Department classification only.

    Uses Telugu Classifier V3 with fallback model for low-confidence cases.

    Args:
        request: Grievance text

    Returns:
        Classification result with department and confidence
    """
    processor = get_processor()

    try:
        result = processor._classify(request.text)
        return ClassificationResult(**result)

    except Exception as e:
        logger.error(f"Classification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Classification failed: {str(e)}"
        )


@router.post(
    "/sentiment",
    response_model=SentimentResult,
    summary="Distress/sentiment analysis only",
    description="Analyze grievance for distress level (CRITICAL/HIGH/MEDIUM/NORMAL) using Sentiment Classifier (88.9% accuracy).",
)
async def sentiment_only(
    request: SentimentRequest,
) -> SentimentResult:
    """Distress/sentiment analysis only.

    Detects distress level which determines SLA:
    - CRITICAL: 24 hours (life-threatening situations)
    - HIGH: 72 hours (urgent needs)
    - MEDIUM: 7 days (standard issues)
    - NORMAL: 14 days (routine queries)

    Args:
        request: Grievance text

    Returns:
        Sentiment result with distress level and confidence
    """
    processor = get_processor()

    try:
        result = processor._analyze_sentiment(request.text)
        return SentimentResult(**result)

    except Exception as e:
        logger.error(f"Sentiment analysis failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sentiment analysis failed: {str(e)}"
        )


@router.post(
    "/predict-lapse",
    response_model=LapsePredictionResult,
    summary="Lapse prediction only",
    description="Predict likelihood of improper redressal using Lapse Predictor (80.8% accuracy).",
)
async def predict_lapse_only(
    request: LapsePredictRequest,
) -> LapsePredictionResult:
    """Lapse prediction only.

    Predicts risk of improper redressal based on:
    - Grievance content
    - Department patterns
    - Historical lapse data (13 lapse categories)

    Args:
        request: Grievance text and optional department

    Returns:
        Lapse prediction with risk level and likely lapse types
    """
    processor = get_processor()

    try:
        result = processor._predict_lapse(request.text, request.department)
        return LapsePredictionResult(**result)

    except Exception as e:
        logger.error(f"Lapse prediction failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lapse prediction failed: {str(e)}"
        )


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="ML models health check",
    description="Check status of all ML models and knowledge base.",
)
async def ml_health() -> HealthResponse:
    """ML models health check.

    Returns status of:
    - Telugu Classifier V3
    - Sentiment Classifier
    - Classification Fallback
    - Lapse Predictor
    - Knowledge Base

    Returns:
        Health status of all ML components
    """
    try:
        processor = get_processor()

        models_status = {
            "telugu_classifier_v3": processor.classifier is not None,
            "sentiment_classifier": processor.sentiment_model is not None,
            "classification_fallback": processor.fallback_model is not None,
            "lapse_predictor": processor.lapse_model is not None,
        }

        all_loaded = all(models_status.values())

        return HealthResponse(
            status="healthy" if all_loaded else "degraded",
            models_loaded=all_loaded,
            models=models_status,
            knowledge_base_loaded=bool(processor.departments),
        )

    except Exception as e:
        return HealthResponse(
            status="unhealthy",
            models_loaded=False,
            models={},
            knowledge_base_loaded=False,
        )


@router.get(
    "/queue",
    response_model=QueueResponse,
    summary="Get officer prioritized queue",
    description="Get prioritized queue of grievances sorted by distress level and SLA.",
)
async def get_queue(
    department: Optional[str] = Query(None, description="Filter by department"),
    limit: int = Query(20, ge=1, le=100, description="Max items to return"),
    current_user: User = Depends(require_role(["officer", "supervisor", "admin"])),
) -> QueueResponse:
    """Get prioritized queue for officer dashboard.

    Returns grievances sorted by:
    1. Distress level (CRITICAL first)
    2. SLA deadline (earliest first)

    Args:
        department: Optional department filter
        limit: Maximum items to return
        current_user: Authenticated officer

    Returns:
        Prioritized queue of grievances
    """
    processor = get_processor()

    try:
        # Get queue from processor (in-memory for now)
        queue = processor.get_officer_queue(
            officer_id=str(current_user.id) if current_user else None,
            department=department
        )[:limit]

        items = [
            QueueItem(
                case_id=item.get("case_id", ""),
                text_preview=item.get("text", "")[:100] + "..." if len(item.get("text", "")) > 100 else item.get("text", ""),
                department=item.get("department"),
                distress_level=item.get("distress_level", "NORMAL"),
                timestamp=item.get("timestamp", ""),
                status=item.get("status", "OPEN"),
            )
            for item in queue
        ]

        return QueueResponse(
            total=len(items),
            items=items,
        )

    except Exception as e:
        logger.error(f"Queue fetch failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Queue fetch failed: {str(e)}"
        )


# Batch processing endpoint
class BatchAnalyzeRequest(BaseModel):
    """Batch analysis request."""
    grievances: List[AnalyzeRequest] = Field(..., max_length=50, description="List of grievances to analyze")


class BatchAnalyzeResponse(BaseModel):
    """Batch analysis response."""
    total: int
    successful: int
    failed: int
    results: List[Dict[str, Any]]


@router.post(
    "/analyze/batch",
    response_model=BatchAnalyzeResponse,
    summary="Batch grievance analysis",
    description="Process multiple grievances in a single request (max 50).",
)
async def analyze_batch(
    request: BatchAnalyzeRequest,
    current_user: User = Depends(require_role(["supervisor", "admin"])),
) -> BatchAnalyzeResponse:
    """Batch grievance analysis.

    Process up to 50 grievances in a single request.
    Useful for bulk imports or backlog processing.

    Args:
        request: List of grievances to analyze
        current_user: Authenticated supervisor/admin

    Returns:
        Batch results with success/failure counts
    """
    processor = get_processor()
    results = []
    successful = 0
    failed = 0

    for grievance in request.grievances:
        try:
            result = processor.process(
                grievance_text=grievance.text,
                citizen_id=grievance.citizen_id,
                location=grievance.location
            )
            results.append({
                "status": "success",
                "classification": result["classification"],
                "sentiment": result["sentiment"],
            })
            successful += 1
        except Exception as e:
            results.append({
                "status": "failed",
                "error": str(e),
            })
            failed += 1

    return BatchAnalyzeResponse(
        total=len(request.grievances),
        successful=successful,
        failed=failed,
        results=results,
    )
