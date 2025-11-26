"""Import lapse cases from audit reports into database."""

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
from app.models import Department, District, LapseCase


async def import_lapse_cases():
    """Import lapse cases from audit reports JSON file."""
    # Create async engine
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Load JSON data
    json_path = Path(__file__).parent.parent / "data" / "extracted" / "audit_reports.json"
    print(f"Loading audit reports from: {json_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Import data
    async with async_session() as session:
        async with session.begin():
            # Load existing departments and districts for mapping
            dept_result = await session.execute(select(Department))
            db_departments = {dept.dept_name: dept for dept in dept_result.scalars().all()}

            dist_result = await session.execute(select(District))
            db_districts = {dist.district_name: dist for dist in dist_result.scalars().all()}

            print(f"Found {len(db_departments)} departments and {len(db_districts)} districts in database")

            imported = 0
            skipped = 0

            # Process Guntur audit data
            guntur_data = data.get("guntur_audit", {})
            if guntur_data:
                district_name = guntur_data.get("district")
                district = db_districts.get(district_name)

                if not district:
                    print(f"WARNING: District not found: {district_name}")

                audit_date = guntur_data.get("audit_date")
                source_audit = f"guntur_{audit_date}"
                total_cases_audited = guntur_data.get("total_cases_audited")

                for lapse in guntur_data.get("lapse_categories", []):
                    try:
                        # Create LapseCase instance
                        lapse_case = LapseCase(
                            district_id=district.id if district else None,
                            department_id=None,  # Not specified in Guntur audit
                            lapse_category=lapse.get("category"),
                            lapse_category_telugu=lapse.get("telugu"),
                            lapse_type=lapse.get("type"),
                            severity=lapse.get("severity"),
                            officer_designation=None,
                            improper_percentage=float(lapse.get("percentage", 0.0)),
                            count=lapse.get("count", 0),
                            total_cases_audited=total_cases_audited,
                            examples=lapse.get("examples", []),
                            source_audit=source_audit,
                            audit_date=audit_date,
                            mandal=None,
                            notes=None,
                        )

                        session.add(lapse_case)
                        imported += 1

                    except Exception as e:
                        print(f"ERROR importing Guntur lapse {lapse.get('category')}: {e}")
                        skipped += 1
                        continue

            # Process other district audits
            other_audits = data.get("other_districts", {})
            for dist_name, dist_data in other_audits.items():
                district = db_districts.get(dist_name)

                if not district:
                    print(f"WARNING: District not found: {dist_name}")

                audit_date = dist_data.get("audit_date")
                source_audit = f"{dist_name.lower().replace(' ', '_')}_{audit_date}"

                for lapse in dist_data.get("lapse_categories", []):
                    try:
                        # Get department if specified
                        dept_name = lapse.get("department")
                        department = db_departments.get(dept_name) if dept_name else None

                        # Create LapseCase instance
                        lapse_case = LapseCase(
                            district_id=district.id if district else None,
                            department_id=department.id if department else None,
                            lapse_category=lapse.get("category"),
                            lapse_category_telugu=lapse.get("telugu"),
                            lapse_type=lapse.get("type"),
                            severity=lapse.get("severity"),
                            officer_designation=lapse.get("officer_designation"),
                            improper_percentage=float(lapse.get("percentage", 0.0)) if lapse.get("percentage") else None,
                            count=lapse.get("count", 1),
                            total_cases_audited=dist_data.get("total_cases_audited"),
                            examples=lapse.get("examples", []),
                            source_audit=source_audit,
                            audit_date=audit_date,
                            mandal=lapse.get("mandal"),
                            notes=lapse.get("notes"),
                        )

                        session.add(lapse_case)
                        imported += 1

                    except Exception as e:
                        print(f"ERROR importing {dist_name} lapse {lapse.get('category')}: {e}")
                        skipped += 1
                        continue

            # Commit transaction
            await session.commit()

            print(f"\nImport Summary:")
            print(f"  - Imported: {imported} lapse cases")
            print(f"  - Skipped: {skipped}")

    await engine.dispose()


if __name__ == "__main__":
    print("=" * 60)
    print("Lapse Cases Import (Audit Reports)")
    print("=" * 60)
    asyncio.run(import_lapse_cases())
    print("\nLapse cases import complete!")
