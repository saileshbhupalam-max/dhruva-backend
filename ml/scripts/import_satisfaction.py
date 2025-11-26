"""Import call center satisfaction metrics into database."""

import asyncio
import json
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.models import Department, SatisfactionMetric


async def import_satisfaction_metrics():
    """Import satisfaction metrics from JSON file."""
    # Create async engine
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Load JSON data
    json_path = Path(__file__).parent.parent / "data" / "extracted" / "call_center_satisfaction.json"
    print(f"Loading satisfaction metrics from: {json_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    departments_data = data.get("departments", [])
    print(f"Found {len(departments_data)} department satisfaction records to import")

    # Import data
    async with async_session() as session:
        async with session.begin():
            # Load existing departments for mapping
            result = await session.execute(select(Department))
            db_departments = {dept.dept_name: dept for dept in result.scalars().all()}
            print(f"Found {len(db_departments)} departments in database")

            imported = 0
            skipped = 0

            for dept_data in departments_data:
                try:
                    dept_name = dept_data.get("department")
                    department = db_departments.get(dept_name)

                    if not department:
                        print(f"WARNING: Department not found: {dept_name}")
                        skipped += 1
                        continue

                    # Extract computed metrics
                    metrics = dept_data.get("computed_metrics", {})

                    # Create SatisfactionMetric instance
                    satisfaction = SatisfactionMetric(
                        department_id=department.id,
                        total_feedback=dept_data.get("total_feedback", 0),
                        avg_satisfaction_5=float(dept_data.get("avg_satisfaction_5", 0.0)),
                        pct_satisfied=float(dept_data.get("pct_satisfied", 0.0)),
                        dept_risk_score=float(metrics.get("dept_risk_score", 0.0)),
                        rank=metrics.get("rank", 0),
                        relative_weight=float(metrics.get("relative_weight", 0.0)),
                        source="call_center_1100",
                    )

                    session.add(satisfaction)
                    imported += 1

                except Exception as e:
                    print(f"ERROR importing satisfaction for {dept_data.get('department')}: {e}")
                    skipped += 1
                    continue

            # Commit transaction
            await session.commit()

            print(f"\nImport Summary:")
            print(f"  - Imported: {imported}")
            print(f"  - Skipped: {skipped}")
            print(f"  - Total: {len(departments_data)}")

    await engine.dispose()


if __name__ == "__main__":
    print("=" * 60)
    print("Call Center Satisfaction Import")
    print("=" * 60)
    asyncio.run(import_satisfaction_metrics())
    print("\nSatisfaction metrics import complete!")
