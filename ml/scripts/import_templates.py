"""Import message templates into database."""

import asyncio
import json
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.models import MessageTemplate


async def import_message_templates():
    """Import message templates from JSON file."""
    # Create async engine
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Load JSON data
    json_path = Path(__file__).parent.parent / "data" / "extracted" / "message_templates.json"
    print(f"Loading message templates from: {json_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    templates_data = data.get("templates", [])
    print(f"Found {len(templates_data)} message templates to import")

    # Import data
    async with async_session() as session:
        async with session.begin():
            imported = 0
            skipped = 0
            seen_ids = set()

            for template_data in templates_data:
                try:
                    template_id = template_data.get("template_id")

                    # Skip duplicates
                    if template_id in seen_ids:
                        print(f"Skipping duplicate template_id: {template_id}")
                        skipped += 1
                        continue

                    seen_ids.add(template_id)
                    # Extract variables
                    variables_dict = template_data.get("variables", {})
                    variables_list = [
                        {"key": k, "value": v}
                        for k, v in variables_dict.items()
                        if v is not None
                    ]

                    # Create MessageTemplate instance
                    template = MessageTemplate(
                        template_id=template_data.get("template_id"),
                        category=template_data.get("category"),
                        status=template_data.get("grievance_status"),
                        text_telugu=template_data.get("text_telugu"),
                        text_english=template_data.get("text_english"),
                        contains_department=template_data.get("contains_department", False),
                        extracted_departments=template_data.get("extracted_departments", []),
                        extracted_keywords=template_data.get("extracted_keywords", []),
                        officer_designations=template_data.get("officer_designations", []),
                        character_count=template_data.get("character_count", 0),
                        variables=variables_list,
                    )

                    session.add(template)
                    imported += 1

                except Exception as e:
                    print(f"ERROR importing template {template_data.get('template_id')}: {e}")
                    skipped += 1
                    continue

            # Commit transaction
            await session.commit()

            print(f"\nImport Summary:")
            print(f"  - Imported: {imported}")
            print(f"  - Skipped: {skipped}")
            print(f"  - Total: {len(templates_data)}")

    await engine.dispose()


if __name__ == "__main__":
    print("=" * 60)
    print("Message Templates Import")
    print("=" * 60)
    asyncio.run(import_message_templates())
    print("\nMessage templates import complete!")
