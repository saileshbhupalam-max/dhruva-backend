"""Import officer performance metrics into database."""

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
from app.models import Department, Officer


async def import_officer_performance():
    """Import officer performance metrics from JSON file."""
    # Create async engine
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Load JSON data
    json_path = Path(__file__).parent.parent / "data" / "extracted" / "officer_performance.json"
    print(f"Loading officer performance from: {json_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    officers_data = data.get("officers", [])
    print(f"Found {len(officers_data)} officers to import")

    # Import data
    async with async_session() as session:
        async with session.begin():
            # Load existing departments for mapping
            result = await session.execute(select(Department))
            db_departments = {dept.dept_name: dept for dept in result.scalars().all()}
            print(f"Found {len(db_departments)} departments in database")

            imported = 0
            skipped = 0

            for officer_data in officers_data:
                try:
                    dept_name = officer_data.get("department")
                    department = db_departments.get(dept_name)

                    if not department:
                        print(f"WARNING: Department not found: {dept_name}")
                        skipped += 1
                        continue

                    # Extract computed metrics
                    metrics = officer_data.get("computed_metrics", {})

                    # Create Officer instance
                    officer = Officer(
                        department_id=department.id,
                        designation=officer_data.get("officer_designation"),
                        received=officer_data.get("received", 0),
                        viewed=officer_data.get("viewed", 0),
                        pending=officer_data.get("pending", 0),
                        redressed=officer_data.get("redressed", 0),
                        improper_rate=metrics.get("improper_rate", 0.0),
                        workload=metrics.get("workload", 0),
                        viewed_ratio=metrics.get("viewed_ratio", 0.0),
                        throughput=metrics.get("throughput", 0.0),
                        dept_context=officer_data.get("dept_context_extracted"),
                    )

                    session.add(officer)
                    imported += 1

                except Exception as e:
                    print(f"ERROR importing officer {officer_data.get('officer_designation')}: {e}")
                    skipped += 1
                    continue

            # Commit transaction
            await session.commit()

            print(f"\nImport Summary:")
            print(f"  - Imported: {imported}")
            print(f"  - Skipped: {skipped}")
            print(f"  - Total: {len(officers_data)}")

    await engine.dispose()


if __name__ == "__main__":
    print("=" * 60)
    print("Officer Performance Import")
    print("=" * 60)
    asyncio.run(import_officer_performance())
    print("\nOfficer performance import complete!")
