"""API Routers Package.

Contains all FastAPI routers for the PGRS API:
- auth: Authentication endpoints (login, logout, me)
- districts: District reference data
- departments: Department reference data
- grievances: Grievance CRUD operations
- public: Public tracking endpoints
- health: Health check endpoints
- empathy: Empathy Engine endpoints (distress detection, templates)
- resolution: Smart Resolution Engine endpoints (root cause, templates)
- empowerment: Citizen Empowerment endpoints (opt-in, rights, triggers)
- ml: ML Pipeline endpoints (classify, sentiment, analyze, batch)
"""

from app.routers import (
    public_dashboard,
    auth,
    departments,
    districts,
    empathy,
    empowerment,
    grievances,
    health,
    ml,
    public,
    resolution,
)

__all__ = [
    "auth",
    "departments",
    "districts",
    "empathy",
    "empowerment",
    "grievances",
    "health",
    "ml",
    "public",
    "public_dashboard",
    "resolution",
]
