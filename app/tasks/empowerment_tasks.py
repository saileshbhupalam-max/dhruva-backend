"""Celery background tasks for Citizen Empowerment System.

This module contains:
- check_proactive_empowerment_triggers: Hourly task to check for proactive triggers
- retry_ask_later_citizens: Daily task to re-send opt-in prompts
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict

from sqlalchemy import and_, select

from app.celery_app import celery_app
from app.config import settings
from app.database.session import get_db
from app.models.citizen_empowerment import CitizenEmpowermentPreference
from app.models.grievance import Grievance
from app.services.citizen_empowerment_service import CitizenEmpowermentService

logger = logging.getLogger(__name__)

# Configuration from settings
MAX_ASK_LATER = settings.EMPOWERMENT_MAX_ASK_LATER
ASK_LATER_DELAY_HOURS = settings.EMPOWERMENT_ASK_LATER_DELAY_HOURS


def run_async(coro: Any) -> Any:
    """Run async coroutine in sync context for Celery."""
    loop = asyncio.get_event_loop()
    if loop.is_running():
        # Create new loop if current is running
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


@celery_app.task(name="app.tasks.empowerment_tasks.check_proactive_empowerment_triggers")
def check_proactive_empowerment_triggers() -> Dict[str, Any]:
    """Hourly task to check for proactive empowerment triggers.

    Checks all active grievances for:
    - SLA at 50%
    - SLA approaching (80%)
    - No update in 7 days

    Returns:
        Dict with triggers_checked and triggers_fired counts
    """
    logger.info("Starting proactive empowerment trigger check")

    async def _check_triggers() -> Dict[str, Any]:
        async with get_db() as db:
            service = CitizenEmpowermentService(db)
            results = await service.check_proactive_triggers()

            triggers_fired = sum(1 for r in results if r.get("success", False))

            logger.info(
                f"Proactive trigger check complete: "
                f"{len(results)} checked, {triggers_fired} fired"
            )

            return {
                "triggers_checked": len(results),
                "triggers_fired": triggers_fired,
                "details": results,
            }

    return run_async(_check_triggers())


@celery_app.task(name="app.tasks.empowerment_tasks.retry_ask_later_citizens")
def retry_ask_later_citizens() -> Dict[str, Any]:
    """Daily task to re-send opt-in prompts to citizens who chose 'Ask Later'.

    Logic:
    - Only re-ask if ask_later_count < MAX_ASK_LATER (default: 2)
    - Only re-ask if last_ask_later_at was more than ASK_LATER_DELAY_HOURS ago
    - Increment ask_later_count on each retry
    - If max retries reached, stop asking

    Returns:
        Dict with citizens_retried count
    """
    logger.info("Starting ask-later citizen retry task")

    async def _retry_citizens() -> Dict[str, Any]:
        async with get_db() as db:
            # Find citizens who said "Later" and are eligible for retry
            cutoff = datetime.utcnow() - timedelta(hours=ASK_LATER_DELAY_HOURS)

            stmt = select(CitizenEmpowermentPreference).where(
                and_(
                    CitizenEmpowermentPreference.ask_later == True,
                    CitizenEmpowermentPreference.opted_out == False,
                    CitizenEmpowermentPreference.opted_in == False,
                    CitizenEmpowermentPreference.ask_later_count < MAX_ASK_LATER,
                    CitizenEmpowermentPreference.last_ask_later_at <= cutoff,
                )
            )

            result = await db.execute(stmt)
            preferences = result.scalars().all()

            service = CitizenEmpowermentService(db)
            retried = 0
            failed = 0

            for pref in preferences:
                # Find an active grievance for this citizen
                grievance_stmt = select(Grievance).where(
                    and_(
                        Grievance.citizen_phone == pref.citizen_phone,
                        Grievance.status.in_(["assigned", "in_progress"]),
                    )
                ).limit(1)

                grievance_result = await db.execute(grievance_stmt)
                grievance = grievance_result.scalar_one_or_none()

                if grievance:
                    # Get department name
                    dept_name = "Government"
                    if grievance.department:
                        dept_name = (
                            grievance.department.name
                            if hasattr(grievance.department, 'name')
                            else str(grievance.department)
                        )

                    # Re-send opt-in prompt
                    try:
                        success = await service.send_opt_in_prompt(
                            grievance_id=grievance.grievance_id,
                            citizen_phone=pref.citizen_phone,
                            department=dept_name,
                            language=pref.preferred_language,
                        )

                        if success:
                            # Update ask_later_count
                            pref.ask_later_count += 1
                            pref.last_ask_later_at = datetime.utcnow()
                            retried += 1
                        else:
                            failed += 1
                    except Exception as e:
                        logger.error(
                            f"Failed to retry opt-in for {pref.citizen_phone}: {e}"
                        )
                        failed += 1

            await db.commit()

            logger.info(
                f"Ask-later retry complete: {retried} retried, {failed} failed"
            )

            return {
                "citizens_retried": retried,
                "citizens_failed": failed,
                "total_eligible": len(preferences),
            }

    return run_async(_retry_citizens())


@celery_app.task(name="app.tasks.empowerment_tasks.send_opt_in_prompt_async")
def send_opt_in_prompt_async(
    grievance_id: str,
    citizen_phone: str,
    department: str,
    language: str = "te",
) -> Dict[str, Any]:
    """Send opt-in prompt asynchronously via Celery.

    This task can be called when a new grievance is created to
    send the opt-in prompt without blocking the main request.

    Args:
        grievance_id: The grievance ID
        citizen_phone: Citizen's phone number
        department: Department name
        language: Language code (te/en)

    Returns:
        Dict with success status
    """
    logger.info(f"Sending opt-in prompt for grievance {grievance_id}")

    async def _send_prompt() -> Dict[str, Any]:
        async with get_db() as db:
            service = CitizenEmpowermentService(db)
            success = await service.send_opt_in_prompt(
                grievance_id=grievance_id,
                citizen_phone=citizen_phone,
                department=department,
                language=language,
            )

            return {
                "success": success,
                "grievance_id": grievance_id,
                "citizen_phone": citizen_phone,
            }

    return run_async(_send_prompt())
