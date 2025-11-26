"""Master script to import all ML training data into database."""

import asyncio
import sys
import time
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from import_audio import import_audio_transcriptions
from import_keywords import import_pgrs_keywords
from import_officers import import_officer_performance
from import_satisfaction import import_satisfaction_metrics
from import_templates import import_message_templates
from import_lapses import import_lapse_cases


async def import_all_data():
    """Import all ML training data in sequence."""
    print("=" * 80)
    print("DHRUVA ML Training Data Import - Master Script")
    print("=" * 80)
    print()

    start_time = time.time()
    results = {}

    # Import sequence
    imports = [
        ("Audio Transcriptions", import_audio_transcriptions),
        ("Message Templates", import_message_templates),
        ("Call Center Satisfaction", import_satisfaction_metrics),
        ("Officer Performance", import_officer_performance),
        ("PGRS Keywords", import_pgrs_keywords),
        ("Lapse Cases (Audit Reports)", import_lapse_cases),
    ]

    for idx, (name, import_func) in enumerate(imports, 1):
        print(f"\n[{idx}/{len(imports)}] Starting: {name}")
        print("-" * 80)

        try:
            import_start = time.time()
            await import_func()
            import_time = time.time() - import_start

            results[name] = {"status": "SUCCESS", "time": import_time}
            print(f"[OK] {name} completed in {import_time:.2f} seconds")

        except Exception as e:
            import_time = time.time() - import_start
            error_msg = str(e).encode('ascii', 'ignore').decode('ascii')[:200]
            results[name] = {"status": "FAILED", "time": import_time, "error": error_msg}
            print(f"[FAIL] {name} FAILED: {error_msg}")

        print()

    # Final summary
    total_time = time.time() - start_time

    print("=" * 80)
    print("IMPORT SUMMARY")
    print("=" * 80)
    print()

    success_count = sum(1 for r in results.values() if r["status"] == "SUCCESS")
    fail_count = sum(1 for r in results.values() if r["status"] == "FAILED")

    for name, result in results.items():
        status_icon = "[OK]" if result["status"] == "SUCCESS" else "[X]"
        print(f"{status_icon} {name:40s} {result['status']:8s} ({result['time']:.2f}s)")
        if "error" in result:
            print(f"  Error: {result['error']}")

    print()
    print(f"Total: {len(imports)} imports")
    print(f"  - Success: {success_count}")
    print(f"  - Failed:  {fail_count}")
    print(f"  - Time:    {total_time:.2f} seconds")
    print()

    if fail_count > 0:
        print("WARNING: Some imports failed. Please check the errors above.")
        return False
    else:
        print("All imports completed successfully!")
        return True


if __name__ == "__main__":
    success = asyncio.run(import_all_data())
    sys.exit(0 if success else 1)
