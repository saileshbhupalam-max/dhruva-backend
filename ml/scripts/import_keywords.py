"""Import PGRS keywords into database."""

import asyncio
import json
import sys
from pathlib import Path
from uuid import UUID

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.models import Department, DepartmentKeyword


async def import_pgrs_keywords():
    """Import PGRS keywords from JSON file."""
    # Create async engine
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Load JSON data
    json_path = Path(__file__).parent.parent / "data" / "extracted" / "pgrs_book_keywords.json"
    print(f"Loading PGRS keywords from: {json_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    departments_data = data.get("departments", [])
    print(f"Found {len(departments_data)} departments to process")

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
                dept_name_english = dept_data.get("name_english")
                dept_name_telugu = dept_data.get("name_telugu")
                subjects = dept_data.get("subjects", [])

                # Find matching department
                department = db_departments.get(dept_name_english)
                if not department:
                    print(f"WARNING: Department not found: {dept_name_english}")
                    skipped += len(subjects)
                    continue

                # Process each subject as a keyword entry
                for subject in subjects:
                    try:
                        # Each subject becomes a DepartmentKeyword
                        # We'll create one entry per keyword, linking to the subject
                        keywords_english = subject.get("keywords_english", [])
                        keywords_telugu = subject.get("keywords_telugu", [])

                        # Create a primary keyword entry for the subject itself
                        keyword = DepartmentKeyword(
                            department_id=department.id,
                            subject_english=subject.get("subject_english"),
                            subject_telugu=subject.get("subject_telugu"),
                            keyword_english=subject.get("subject_english"),  # Subject as primary keyword
                            keyword_telugu=subject.get("subject_telugu"),
                            sub_subjects=subject.get("sub_subjects", []),
                            weight=1.0,
                        )
                        session.add(keyword)
                        imported += 1

                        # Add additional keywords with reference to the subject
                        for idx, kw_eng in enumerate(keywords_english):
                            kw_tel = keywords_telugu[idx] if idx < len(keywords_telugu) else None

                            keyword_entry = DepartmentKeyword(
                                department_id=department.id,
                                subject_english=subject.get("subject_english"),
                                subject_telugu=subject.get("subject_telugu"),
                                keyword_english=kw_eng,
                                keyword_telugu=kw_tel,
                                sub_subjects=subject.get("sub_subjects", []),
                                weight=0.8,  # Secondary keywords get lower weight
                            )
                            session.add(keyword_entry)
                            imported += 1

                    except Exception as e:
                        print(f"ERROR importing keyword for {dept_name_english}/{subject.get('subject_english')}: {e}")
                        skipped += 1
                        continue

            # Commit transaction
            await session.commit()

            print(f"\nImport Summary:")
            print(f"  - Imported: {imported} keyword entries")
            print(f"  - Skipped: {skipped}")

    await engine.dispose()


if __name__ == "__main__":
    print("=" * 60)
    print("PGRS Keywords Import")
    print("=" * 60)
    asyncio.run(import_pgrs_keywords())
    print("\nPGRS keywords import complete!")
