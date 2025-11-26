#!/usr/bin/env python3
"""
Seed all 26 Andhra Pradesh districts into the database.

This script uses the District model from app.models to seed all districts
with proper district_code and district_name fields.

Usage:
    python -m scripts.seed_all_districts

Note: Run this from the backend directory.
"""

import asyncio
import sys
from pathlib import Path

# Add backend to Python path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.models.district import District
from app.core.config import settings


# All 26 Andhra Pradesh districts with codes
# Based on 2024 administrative divisions
DISTRICTS = [
    # Original 13 districts (pre-2022)
    {"code": "ANT", "name": "Anantapur"},
    {"code": "CHT", "name": "Chittoor"},
    {"code": "EG", "name": "East Godavari"},
    {"code": "GNT", "name": "Guntur"},
    {"code": "KDP", "name": "Kadapa"},
    {"code": "KRS", "name": "Krishna"},
    {"code": "KNL", "name": "Kurnool"},
    {"code": "NLR", "name": "Nellore"},
    {"code": "PKM", "name": "Prakasam"},
    {"code": "SKM", "name": "Srikakulam"},
    {"code": "VSP", "name": "Visakhapatnam"},
    {"code": "VZG", "name": "Vizianagaram"},
    {"code": "WG", "name": "West Godavari"},

    # New districts (post-2022 reorganization)
    {"code": "ARL", "name": "Alluri Sitharama Raju"},
    {"code": "ANA", "name": "Anakapalli"},
    {"code": "ANM", "name": "Annamaya"},
    {"code": "BAP", "name": "Bapatla"},
    {"code": "ELR", "name": "Eluru"},
    {"code": "KKN", "name": "Kakinada"},
    {"code": "KNR", "name": "Konaseema"},
    {"code": "NTR", "name": "NTR District"},
    {"code": "PLN", "name": "Palnadu"},
    {"code": "PVT", "name": "Parvathipuram Manyam"},
    {"code": "NAG", "name": "Sri Potti Sriramulu Nellore"},
    {"code": "STY", "name": "Sri Satya Sai"},
    {"code": "TPT", "name": "Tirupati"},
]


async def seed_districts(session: AsyncSession) -> None:
    """Seed all districts into the database."""
    print("\n" + "="*70)
    print("  SEEDING ANDHRA PRADESH DISTRICTS")
    print("="*70)

    # Check existing districts
    result = await session.execute(select(District))
    existing_districts = result.scalars().all()
    existing_codes = {d.district_code for d in existing_districts}

    print(f"\n[*] Found {len(existing_districts)} existing districts in database")

    # Seed districts
    added_count = 0
    skipped_count = 0

    for district_data in DISTRICTS:
        code = district_data["code"]
        name = district_data["name"]

        if code in existing_codes:
            print(f"  [SKIP] {name} ({code}) - already exists")
            skipped_count += 1
            continue

        # Create new district
        district = District(
            district_code=code,
            district_name=name,
        )
        session.add(district)
        print(f"  [ADD] {name} ({code})")
        added_count += 1

    # Commit changes
    if added_count > 0:
        await session.commit()
        print(f"\n[+] Successfully added {added_count} new districts")
    else:
        print(f"\n[+] No new districts to add")

    print(f"[+] Total districts in database: {len(existing_districts) + added_count}")

    # Verify final count
    result = await session.execute(select(District))
    all_districts = result.scalars().all()

    print("\n" + "="*70)
    print("  VERIFICATION")
    print("="*70)
    print(f"\n[+] Expected districts: {len(DISTRICTS)}")
    print(f"[+] Actual districts: {len(all_districts)}")

    if len(all_districts) == len(DISTRICTS):
        print("[SUCCESS] All districts seeded successfully!")
    else:
        print("[WARNING] District count mismatch!")

    print("\n" + "="*70)
    print("  DISTRICT LIST")
    print("="*70)
    for district in sorted(all_districts, key=lambda d: d.district_code):
        print(f"  {district.district_code:8} | {district.district_name}")
    print()


async def main():
    """Main entry point."""
    print("\nConnecting to database...")
    print(f"Database URL: {settings.DATABASE_URL[:50]}...")

    # Create async engine
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        future=True,
    )

    # Create session
    async_session = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    try:
        async with async_session() as session:
            await seed_districts(session)
    except Exception as e:
        print(f"\n[ERROR] Failed to seed districts: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
