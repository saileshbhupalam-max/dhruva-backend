"""Celery application configuration for background tasks.

This module configures Celery for:
- Proactive empowerment triggers (hourly)
- Ask-later citizen retries (daily)
"""

from celery import Celery

from app.config import settings

celery_app = Celery(
    "dhruva",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.empowerment_tasks"],
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True,
    # Beat schedule for proactive empowerment triggers
    beat_schedule={
        "check-proactive-triggers-hourly": {
            "task": "app.tasks.empowerment_tasks.check_proactive_empowerment_triggers",
            "schedule": 3600.0,  # Every hour
        },
        "retry-ask-later-citizens-daily": {
            "task": "app.tasks.empowerment_tasks.retry_ask_later_citizens",
            "schedule": 86400.0,  # Every 24 hours
        },
    },
)
