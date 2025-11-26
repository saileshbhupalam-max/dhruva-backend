"""SQLAlchemy Models for DHRUVA-PGRS."""

from app.models.base import Base
from app.models.district import District
from app.models.department import Department
from app.models.user import User
from app.models.grievance import Grievance
from app.models.attachment import Attachment
from app.models.audit_log import AuditLog
from app.models.verification import Verification
# ML Training Models
from app.models.audio_clip import AudioClip
from app.models.department_keyword import DepartmentKeyword
from app.models.officer import Officer
from app.models.satisfaction_metric import SatisfactionMetric
from app.models.message_template import MessageTemplate
from app.models.lapse_case import LapseCase
# Empathy Engine Models
from app.models.empathy import DistressKeyword, EmpathyTemplate, GrievanceSentiment
# Smart Resolution Engine Models
from app.models.resolution import (
    ClarificationResponse,
    InterventionQuestion,
    ResolutionTemplate,
    RootCauseAnalysis,
    TemplateApplication,
)
# Citizen Empowerment Models
from app.models.citizen_empowerment import (
    CitizenEmpowermentPreference,
    EmpowermentInteraction,
    ProactiveTriggerConfig,
    RightsKnowledgeBase,
)
# Verifier Portal Models
from app.models.verifier_profile import VerifierProfile
from app.models.verifier_activity import VerifierActivity

__all__ = [
    "Base",
    "District",
    "Department",
    "User",
    "Grievance",
    "Attachment",
    "AuditLog",
    "Verification",
    # ML Models
    "AudioClip",
    "DepartmentKeyword",
    "Officer",
    "SatisfactionMetric",
    "MessageTemplate",
    "LapseCase",
    # Empathy Engine Models
    "DistressKeyword",
    "EmpathyTemplate",
    "GrievanceSentiment",
    # Smart Resolution Engine Models
    "RootCauseAnalysis",
    "ResolutionTemplate",
    "InterventionQuestion",
    "ClarificationResponse",
    "TemplateApplication",
    # Citizen Empowerment Models
    "RightsKnowledgeBase",
    "CitizenEmpowermentPreference",
    "EmpowermentInteraction",
    "ProactiveTriggerConfig",
    # Verifier Portal Models
    "VerifierProfile",
    "VerifierActivity",
]
