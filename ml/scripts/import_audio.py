"""Import audio transcriptions into database."""

import asyncio
import json
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.models import AudioClip


async def import_audio_transcriptions():
    """Import audio transcriptions from JSON file."""
    # Create async engine
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Load JSON data
    json_path = Path(__file__).parent.parent / "data" / "extracted" / "audio_transcriptions.json"
    print(f"Loading audio transcriptions from: {json_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    transcriptions = data.get("transcriptions", [])
    print(f"Found {len(transcriptions)} audio transcriptions to import")

    # Import data
    async with async_session() as session:
        async with session.begin():
            imported = 0
            skipped = 0

            for item in transcriptions:
                try:
                    # Create AudioClip instance
                    audio_clip = AudioClip(
                        filename=item.get("filename"),
                        source_path=item.get("source_path"),
                        duration_seconds=float(item.get("duration_seconds", 0)),
                        transcription_telugu=item.get("transcription_telugu", ""),
                        transcription_english=item.get("transcription_english"),
                        confidence=float(item.get("confidence", 0.0)),
                        language_detected=item.get("language_detected", "te"),
                        contains_department_name=item.get("contains_department_name", False),
                        departments_mentioned=item.get("departments_mentioned", []),
                        extracted_keywords=item.get("extracted_keywords", []),
                        transcription_length=item.get("transcription_length", 0),
                        status=item.get("status", "success"),
                    )

                    session.add(audio_clip)
                    imported += 1

                except Exception as e:
                    print(f"ERROR importing {item.get('filename')}: {e}")
                    skipped += 1
                    continue

            # Commit transaction
            await session.commit()

            print(f"\nImport Summary:")
            print(f"  - Imported: {imported}")
            print(f"  - Skipped: {skipped}")
            print(f"  - Total: {len(transcriptions)}")

    await engine.dispose()


if __name__ == "__main__":
    print("=" * 60)
    print("Audio Transcriptions Import")
    print("=" * 60)
    asyncio.run(import_audio_transcriptions())
    print("\nAudio transcriptions import complete!")
