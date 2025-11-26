#!/usr/bin/env python3
"""
Test Whisper transcription on a single file
"""

import sys
import whisper
from pathlib import Path

# Test with one file
test_file = r"D:\projects\dhruva\docs\reference\voice_clips\voice_clip_01.wav"

print(f"Testing Whisper with: {test_file}")
print(f"File exists: {Path(test_file).exists()}")

try:
    print("\nLoading Whisper model...")
    model = whisper.load_model("base")
    print("Model loaded successfully")

    print(f"\nTranscribing {Path(test_file).name}...")
    result = model.transcribe(test_file, language='te', verbose=True)

    print(f"\n{'='*80}")
    print("RESULT:")
    print(f"{'='*80}")
    print(f"Text: {result['text']}")
    print(f"Language: {result.get('language', 'unknown')}")
    print(f"\nSegments: {len(result.get('segments', []))}")

    if 'segments' in result:
        for i, seg in enumerate(result['segments'][:3], 1):
            print(f"\nSegment {i}:")
            print(f"  Start: {seg.get('start', 0):.2f}s")
            print(f"  End: {seg.get('end', 0):.2f}s")
            print(f"  Text: {seg.get('text', '')}")

    print("\n[SUCCESS] Transcription complete!")

except Exception as e:
    print(f"\n[ERROR] {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
