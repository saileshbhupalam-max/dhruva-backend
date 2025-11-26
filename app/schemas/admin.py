"""Admin analytics schemas for dashboard endpoints."""

from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field


# ===== Fraud Detection Schemas =====

class ScatterDataPoint(BaseModel):
    """Single data point for fraud detection scatter plot."""
    grievance_id: str
    photo_similarity: float = Field(..., ge=0.0, le=1.0)
    resolution_time_days: float
    officer_id: str
    officer_name: str
    is_flagged: bool


class BoxPlotData(BaseModel):
    """Box plot statistics for an officer."""
    officer_id: str
    officer_name: str
    min: float
    q1: float  # First quartile
    median: float
    q3: float  # Third quartile
    max: float
    outliers: List[float]


class BenfordDigitData(BaseModel):
    """Benford's Law analysis for a digit."""
    digit: int = Field(..., ge=1, le=9)
    expected: float = Field(..., description="Expected frequency by Benford's Law")
    actual: float = Field(..., description="Actual frequency in data")
    deviation: float = Field(..., description="Absolute deviation")


class FlaggedCase(BaseModel):
    """Flagged case for manual review."""
    grievance_id: str
    officer_id: str
    officer_name: str
    flag_reasons: List[str]
    photo_similarity: float
    resolution_time_days: float
    flagged_at: datetime
    review_status: str = Field(default="pending", description="pending, reviewed, confirmed_fraud, false_positive")


class FraudSummary(BaseModel):
    """Summary statistics for fraud detection."""
    total_analyzed: int
    flagged_count: int
    reviewed_count: int
    confirmed_fraud: int


class FraudMetricsResponse(BaseModel):
    """Response for fraud detection metrics endpoint."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "scatter_data": [
                    {
                        "grievance_id": "PGRS-2024-01-00001",
                        "photo_similarity": 0.95,
                        "resolution_time_days": 1.2,
                        "officer_id": "550e8400-e29b-41d4-a716-446655440001",
                        "officer_name": "Officer Kumar",
                        "is_flagged": True
                    }
                ],
                "box_plot_data": [
                    {
                        "officer_id": "550e8400-e29b-41d4-a716-446655440001",
                        "officer_name": "Officer Kumar",
                        "min": 0.5,
                        "q1": 3.0,
                        "median": 5.0,
                        "q3": 7.0,
                        "max": 15.0,
                        "outliers": [0.5, 0.8]
                    }
                ],
                "benford_data": [
                    {
                        "digit": 1,
                        "expected": 0.301,
                        "actual": 0.35,
                        "deviation": 0.049
                    }
                ],
                "flagged_cases": [],
                "summary": {
                    "total_analyzed": 1250,
                    "flagged_count": 15,
                    "reviewed_count": 10,
                    "confirmed_fraud": 3
                }
            }
        }
    )

    scatter_data: List[ScatterDataPoint]
    box_plot_data: List[BoxPlotData]
    benford_data: List[BenfordDigitData]
    flagged_cases: List[FlaggedCase]
    summary: FraudSummary


# ===== NLP Performance Schemas =====

class AccuracyTrendPoint(BaseModel):
    """Single point in accuracy trend over time."""
    date: str  # YYYY-MM-DD format
    accuracy: float = Field(..., ge=0.0, le=1.0)
    sample_count: int


class ConfusionMatrixData(BaseModel):
    """Confusion matrix for classification performance."""
    labels: List[str]
    matrix: List[List[int]]  # 2D matrix


class MisclassificationCase(BaseModel):
    """Top misclassification example."""
    true_category: str
    predicted_category: str
    count: int
    example_text: str


class LanguageDistribution(BaseModel):
    """Distribution of grievances by language."""
    language: str
    count: int
    percentage: float


class ModelInfo(BaseModel):
    """Information about the NLP model."""
    model_version: str
    training_samples: int
    categories: List[str]
    last_trained: datetime


class NLPMetricsResponse(BaseModel):
    """Response for NLP performance metrics endpoint."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "overall_accuracy": 0.87,
                "accuracy_trend": [
                    {
                        "date": "2024-01-01",
                        "accuracy": 0.85,
                        "sample_count": 120
                    }
                ],
                "confusion_matrix": {
                    "labels": ["Health", "Revenue", "Roads", "Water"],
                    "matrix": [[45, 3, 1, 0], [2, 38, 1, 0], [1, 0, 42, 2], [0, 1, 1, 40]]
                },
                "top_misclassifications": [
                    {
                        "true_category": "Health",
                        "predicted_category": "Revenue",
                        "count": 5,
                        "example_text": "Medical bill payment issue..."
                    }
                ],
                "language_distribution": [
                    {"language": "te", "count": 850, "percentage": 68.0},
                    {"language": "en", "count": 320, "percentage": 25.6}
                ],
                "model_info": {
                    "model_version": "v3.2",
                    "training_samples": 5000,
                    "categories": ["Health", "Revenue", "Roads", "Water"],
                    "last_trained": "2024-01-15T10:30:00Z"
                }
            }
        }
    )

    overall_accuracy: float
    accuracy_trend: List[AccuracyTrendPoint]
    confusion_matrix: ConfusionMatrixData
    top_misclassifications: List[MisclassificationCase]
    language_distribution: List[LanguageDistribution]
    model_info: ModelInfo


# ===== Department Analytics Schemas =====

class SLAHeatmapData(BaseModel):
    """SLA compliance heatmap for a department."""
    department: str
    within_sla: int
    near_breach: int  # Within 20% of deadline
    breached: int


class SatisfactionTrend(BaseModel):
    """Satisfaction trend over time."""
    department: str
    date: str
    avg_satisfaction: float
    feedback_count: int


class DepartmentPerformance(BaseModel):
    """Department performance ranking."""
    department: str
    avg_resolution_days: float
    sla_compliance_rate: float
    satisfaction_score: float
    total_grievances: int
    rank: int


class DepartmentAnalyticsResponse(BaseModel):
    """Response for department analytics endpoint."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "sla_heatmap": [
                    {
                        "department": "Health",
                        "within_sla": 120,
                        "near_breach": 15,
                        "breached": 5
                    }
                ],
                "satisfaction_trends": [
                    {
                        "department": "Health",
                        "date": "2024-01",
                        "avg_satisfaction": 4.2,
                        "feedback_count": 145
                    }
                ],
                "performance_ranking": [
                    {
                        "department": "Health",
                        "avg_resolution_days": 4.5,
                        "sla_compliance_rate": 0.92,
                        "satisfaction_score": 4.2,
                        "total_grievances": 140,
                        "rank": 1
                    }
                ]
            }
        }
    )

    sla_heatmap: List[SLAHeatmapData]
    satisfaction_trends: List[SatisfactionTrend]
    performance_ranking: List[DepartmentPerformance]


# ===== System Metrics Schemas =====

class GrievanceStats(BaseModel):
    """Overall grievance statistics."""
    total: int
    today: int
    this_week: int
    this_month: int
    growth_rate: float = Field(..., description="Month-over-month growth rate")


class UserStats(BaseModel):
    """User statistics."""
    total_officers: int
    active_officers: int  # Logged in within last 30 days
    total_citizens: int


class ResolutionStats(BaseModel):
    """Resolution performance statistics."""
    avg_time_days: float
    trend: str = Field(..., description="up, down, or stable")
    fastest_dept: str
    slowest_dept: str


class EmpathyStats(BaseModel):
    """Empathy engine statistics."""
    critical_cases: int
    high_cases: int
    avg_distress_score: float
    sla_compliance: float = Field(..., description="SLA compliance rate for high-distress cases")


class VerificationStats(BaseModel):
    """Verification statistics."""
    pending: int
    verified_rate: float
    disputed_rate: float


class GrowthChartPoint(BaseModel):
    """Growth chart data point."""
    date: str
    grievances: int
    resolved: int
    pending: int


class SystemMetricsResponse(BaseModel):
    """Response for system metrics overview endpoint."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "grievances": {
                    "total": 5420,
                    "today": 12,
                    "this_week": 87,
                    "this_month": 340,
                    "growth_rate": 0.08
                },
                "users": {
                    "total_officers": 45,
                    "active_officers": 38,
                    "total_citizens": 4200
                },
                "resolution": {
                    "avg_time_days": 5.2,
                    "trend": "down",
                    "fastest_dept": "Health",
                    "slowest_dept": "Revenue"
                },
                "empathy": {
                    "critical_cases": 8,
                    "high_cases": 42,
                    "avg_distress_score": 3.2,
                    "sla_compliance": 0.95
                },
                "verification": {
                    "pending": 15,
                    "verified_rate": 0.89,
                    "disputed_rate": 0.03
                },
                "growth_chart": [
                    {
                        "date": "2024-01-01",
                        "grievances": 120,
                        "resolved": 95,
                        "pending": 25
                    }
                ]
            }
        }
    )

    grievances: GrievanceStats
    users: UserStats
    resolution: ResolutionStats
    empathy: EmpathyStats
    verification: VerificationStats
    growth_chart: List[GrowthChartPoint]
