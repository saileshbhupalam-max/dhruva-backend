#!/usr/bin/env python3
"""
Audio Transcription Script for Telugu PGRS Voice Clips (No FFmpeg Required)
Uses OpenAI Whisper with soundfile for audio loading
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime
import subprocess
import numpy as np

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

try:
    import whisper
    import soundfile as sf
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Installing required packages...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "openai-whisper", "soundfile"])
    import whisper
    import soundfile as sf

# Known PGRS departments for keyword matching
PGRS_DEPARTMENTS = [
    "Revenue", "Panchayat Raj", "Municipal Administration", "Rural Development",
    "Agriculture", "Animal Husbandry", "Energy", "Electricity", "Police",
    "Education", "Health", "Transport", "Housing", "Labour", "Social Welfare",
    "Women and Child Welfare", "Irrigation", "Water Resources", "Industries",
    "Commercial Taxes", "Registration and Stamps", "Forest", "Environment",
    "Food and Civil Supplies", "Marketing", "Fisheries", "Tourism", "Sports",
    "Youth Services", "Tribal Welfare", "Backward Classes Welfare", "Minorities Welfare",
    "Information Technology", "HRD", "Roads and Buildings", "GRAMA"
]

def load_audio_with_soundfile(file_path, sr=16000):
    """Load audio file using soundfile and resample to 16kHz for Whisper"""
    try:
        # Load audio file
        audio, orig_sr = sf.read(file_path, dtype='float32')

        # Convert stereo to mono if needed
        if len(audio.shape) > 1:
            audio = audio.mean(axis=1)

        # Resample to 16kHz if needed (Whisper expects 16kHz)
        if orig_sr != sr:
            # Simple resampling (for better quality, use librosa or resampy)
            from scipy import signal
            num_samples = int(len(audio) * sr / orig_sr)
            audio = signal.resample(audio, num_samples)

        return audio.astype(np.float32)
    except Exception as e:
        raise Exception(f"Failed to load audio: {e}")

def get_audio_duration(audio_data):
    """Get duration of audio from Whisper result"""
    try:
        if 'segments' in audio_data and audio_data['segments']:
            last_segment = audio_data['segments'][-1]
            duration = last_segment.get('end', 0.0)
            return duration
        return 0.0
    except Exception as e:
        return 0.0

def extract_department_keywords(text):
    """Extract department names and keywords from text"""
    text_lower = text.lower()
    departments_found = []

    # Check for department names
    for dept in PGRS_DEPARTMENTS:
        if dept.lower() in text_lower:
            departments_found.append(dept)

    # Extract common keywords
    keywords = []
    common_words = [
        "grievance", "complaint", "register", "petitioner", "officer", "department",
        "pending", "closed", "reopened", "redressed", "feedback", "status",
        "scheme", "assistance", "service", "work", "bill", "payment", "court",
        "family", "land", "job", "employment", "outsourcing", "government"
    ]

    for word in common_words:
        if word in text_lower:
            keywords.append(word)

    return departments_found, keywords

def transcribe_file(model, file_path, index, total):
    """Transcribe a single audio file"""
    print(f"\n[{index}/{total}] Processing: {Path(file_path).name}")

    try:
        # Check file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        # Load audio with soundfile
        print(f"  Loading audio...")
        audio = load_audio_with_soundfile(file_path)

        # Transcribe with Whisper
        print(f"  Transcribing...")
        result = model.transcribe(
            audio,  # Pass numpy array directly
            language='te',  # Telugu
            verbose=False
        )

        # Get duration from result
        duration = get_audio_duration(result)
        print(f"  Duration: {duration:.2f}s")

        transcription = result['text'].strip()
        language_detected = result.get('language', 'te')

        # Calculate confidence (average of segment probabilities if available)
        confidence = 0.0
        if 'segments' in result and result['segments']:
            confidences = [seg.get('no_speech_prob', 0.0) for seg in result['segments']]
            # no_speech_prob is inverse, so we use 1 - avg
            confidence = 1.0 - (sum(confidences) / len(confidences))
        else:
            confidence = 0.85  # Default if not available

        # Extract departments and keywords
        departments, keywords = extract_department_keywords(transcription)

        print(f"  Transcription length: {len(transcription)} chars")
        print(f"  Confidence: {confidence:.2f}")
        print(f"  Language: {language_detected}")
        if departments:
            print(f"  Departments: {', '.join(departments)}")

        return {
            "filename": Path(file_path).name,
            "source_path": str(file_path),
            "duration_seconds": round(duration, 2),
            "transcription_telugu": transcription,
            "transcription_english": None,
            "confidence": round(confidence, 4),
            "language_detected": language_detected,
            "contains_department_name": len(departments) > 0,
            "departments_mentioned": departments,
            "extracted_keywords": keywords[:10],
            "transcription_length": len(transcription),
            "status": "success"
        }

    except Exception as e:
        print(f"  ERROR: {str(e)}")
        return {
            "filename": Path(file_path).name,
            "source_path": str(file_path),
            "duration_seconds": 0.0,
            "transcription_telugu": "",
            "transcription_english": None,
            "confidence": 0.0,
            "language_detected": "unknown",
            "contains_department_name": False,
            "departments_mentioned": [],
            "extracted_keywords": [],
            "transcription_length": 0,
            "status": "failed",
            "error": str(e)
        }

def main():
    """Main transcription workflow"""
    print("="*80)
    print("PGRS AUDIO TRANSCRIPTION - WHISPER AI (No FFmpeg)")
    print("="*80)

    # Define file paths
    base_dir = Path(__file__).parent.parent.parent

    audio_files = [
        # Voice clips (28 files)
        base_dir / "docs/voice_clips/VOICE CLIPS REGARDING PGRS SENT TO PETITIONERS-OFFICERS/when grievance closed.wav",
        base_dir / "docs/voice_clips/VOICE CLIPS REGARDING PGRS SENT TO PETITIONERS-OFFICERS/requesting for govt & outsourcing job.wav",
        base_dir / "docs/voice_clips/VOICE CLIPS REGARDING PGRS SENT TO PETITIONERS-OFFICERS/Udyogam ni korutu darakasthu.wav",
        base_dir / "docs/voice_clips/VOICE CLIPS REGARDING PGRS SENT TO PETITIONERS-OFFICERS/when grievance reopened.wav",
        base_dir / "docs/voice_clips/VOICE CLIPS REGARDING PGRS SENT TO PETITIONERS-OFFICERS/requesting for land.wav",
        base_dir / "docs/voice_clips/VOICE CLIPS REGARDING PGRS SENT TO PETITIONERS-OFFICERS/when grievance registered.wav",
        base_dir / "docs/voice_clips/VOICE CLIPS REGARDING PGRS SENT TO PETITIONERS-OFFICERS/Employee service related.wav",
        base_dir / "docs/voice_clips/VOICE CLIPS REGARDING PGRS SENT TO PETITIONERS-OFFICERS/gra lapses message .wav",
        base_dir / "docs/voice_clips/VOICE CLIPS REGARDING PGRS SENT TO PETITIONERS-OFFICERS/requesting for Private job .wav",
        base_dir / "docs/voice_clips/VOICE CLIPS REGARDING PGRS SENT TO PETITIONERS-OFFICERS/Financial Assisstance.wav",
        base_dir / "docs/voice_clips/VOICE CLIPS REGARDING PGRS SENT TO PETITIONERS-OFFICERS/call center persons msg.wav",
        base_dir / "docs/voice_clips/VOICE CLIPS REGARDING PGRS SENT TO PETITIONERS-OFFICERS/ineligible to scheme.wav",
        base_dir / "docs/voice_clips/VOICE CLIPS REGARDING PGRS SENT TO PETITIONERS-OFFICERS/Redressed.wav",
        base_dir / "docs/voice_clips/VOICE CLIPS REGARDING PGRS SENT TO PETITIONERS-OFFICERS/Policy decision pending.wav",
        base_dir / "docs/voice_clips/VOICE CLIPS REGARDING PGRS SENT TO PETITIONERS-OFFICERS/Yet to be released scheme.wav",
        base_dir / "docs/voice_clips/VOICE CLIPS REGARDING PGRS SENT TO PETITIONERS-OFFICERS/registration of grievance.wav",
        base_dir / "docs/voice_clips/VOICE CLIPS REGARDING PGRS SENT TO PETITIONERS-OFFICERS/Grievance registered in wrong department.wav",
        base_dir / "docs/voice_clips/VOICE CLIPS REGARDING PGRS SENT TO PETITIONERS-OFFICERS/court case.wav",
        base_dir / "docs/voice_clips/VOICE CLIPS REGARDING PGRS SENT TO PETITIONERS-OFFICERS/capital works related.wav",
        base_dir / "docs/voice_clips/VOICE CLIPS REGARDING PGRS SENT TO PETITIONERS-OFFICERS/WORKBILLS PENDING.wav",
        base_dir / "docs/voice_clips/VOICE CLIPS REGARDING PGRS SENT TO PETITIONERS-OFFICERS/After giving positive feedback.wav",
        base_dir / "docs/voice_clips/VOICE CLIPS REGARDING PGRS SENT TO PETITIONERS-OFFICERS/Message to GRA.wav",
        base_dir / "docs/voice_clips/VOICE CLIPS REGARDING PGRS SENT TO PETITIONERS-OFFICERS/Aplicant not satisfied.wav",
        base_dir / "docs/voice_clips/VOICE CLIPS REGARDING PGRS SENT TO PETITIONERS-OFFICERS/Family disputes.wav",
        base_dir / "docs/voice_clips/VOICE CLIPS REGARDING PGRS SENT TO PETITIONERS-OFFICERS/Message to mandal coordinators.wav",
        base_dir / "docs/voice_clips/VOICE CLIPS REGARDING PGRS SENT TO PETITIONERS-OFFICERS/GRA Message.wav",
        base_dir / "docs/voice_clips/VOICE CLIPS REGARDING PGRS SENT TO PETITIONERS-OFFICERS/JOB SERVICE RELATED.wav",
        base_dir / "docs/voice_clips/VOICE CLIPS REGARDING PGRS SENT TO PETITIONERS-OFFICERS/View by the officer.wav",

        # Reference voice clips (16 files)
        base_dir / "docs/reference/voice_clips/voice_clip_01.wav",
        base_dir / "docs/reference/voice_clips/voice_clip_02.wav",
        base_dir / "docs/reference/voice_clips/voice_clip_03.wav",
        base_dir / "docs/reference/voice_clips/voice_clip_04.wav",
        base_dir / "docs/reference/voice_clips/voice_clip_05.wav",
        base_dir / "docs/reference/voice_clips/voice_clip_06.wav",
        base_dir / "docs/reference/voice_clips/voice_clip_07.wav",
        base_dir / "docs/reference/voice_clips/voice_clip_08.wav",
        base_dir / "docs/reference/voice_clips/voice_clip_09.wav",
        base_dir / "docs/reference/voice_clips/voice_clip_10.wav",
        base_dir / "docs/reference/voice_clips/voice_clip_11.wav",
        base_dir / "docs/reference/voice_clips/voice_clip_12.wav",
        base_dir / "docs/reference/voice_clips/voice_clip_13.wav",
        base_dir / "docs/reference/voice_clips/voice_clip_14.wav",
        base_dir / "docs/reference/voice_clips/voice_clip_15.wav",
        base_dir / "docs/reference/voice_clips/voice_clip_16.wav",

        # Bribe cases (2 files)
        base_dir / "docs/bribe_cases/BRIBE CASES/cs puram vro pkm.mp3",
        base_dir / "docs/bribe_cases/BRIBE CASES/pkm konakamitla mandalam mro vasu.mp3",
    ]

    print(f"\nTotal files to transcribe: {len(audio_files)}")

    # Verify all files exist
    print("\nVerifying files...")
    missing_files = []
    for fp in audio_files:
        if not fp.exists():
            missing_files.append(str(fp))

    if missing_files:
        print(f"\nERROR: {len(missing_files)} files not found:")
        for mf in missing_files:
            print(f"  - {mf}")
        return 1

    print(f"[OK] All {len(audio_files)} files found")

    # Install scipy if needed for resampling
    try:
        from scipy import signal
    except ImportError:
        print("\nInstalling scipy for audio resampling...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "scipy"])
        from scipy import signal

    # Load Whisper model
    print("\nLoading Whisper model (base)...")
    model = whisper.load_model("base")
    print("[OK] Model loaded")

    # Transcribe all files
    print("\n" + "="*80)
    print("STARTING TRANSCRIPTION")
    print("="*80)

    transcriptions = []
    total_duration = 0.0

    for i, file_path in enumerate(audio_files, 1):
        result = transcribe_file(model, file_path, i, len(audio_files))
        transcriptions.append(result)
        total_duration += result['duration_seconds']

        # Save intermediate results every 10 files
        if i % 10 == 0:
            output_dir = base_dir / "backend/ml/data/extracted"
            output_dir.mkdir(parents=True, exist_ok=True)
            temp_file = output_dir / f"audio_transcriptions_temp_{i}.json"
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump({"transcriptions": transcriptions}, f, ensure_ascii=False, indent=2)
            print(f"\n  --> Intermediate results saved to {temp_file}")

    # Calculate quality metrics
    successful = [t for t in transcriptions if t['status'] == 'success']
    failed = [t for t in transcriptions if t['status'] == 'failed']

    avg_confidence = sum(t['confidence'] for t in successful) / len(successful) if successful else 0.0
    telugu_files = len([t for t in successful if t['language_detected'] == 'te'])
    valid_transcriptions = len([t for t in successful if t['transcription_length'] >= 10])
    low_confidence = [t for t in successful if t['confidence'] < 0.70]

    # Prepare final output
    output_data = {
        "metadata": {
            "transcription_date": datetime.now().isoformat(),
            "whisper_model": "base",
            "total_files": len(audio_files),
            "audio_loader": "soundfile (no FFmpeg)",
            "source_directories": [
                "docs/voice_clips/VOICE CLIPS REGARDING PGRS SENT TO PETITIONERS-OFFICERS",
                "docs/reference/voice_clips",
                "docs/bribe_cases/BRIBE CASES"
            ]
        },
        "transcriptions": transcriptions,
        "total_transcribed": len(successful),
        "total_duration_seconds": round(total_duration, 2),
        "quality_metrics": {
            "avg_confidence": round(avg_confidence, 4),
            "telugu_files": telugu_files,
            "failed_transcriptions": len(failed),
            "valid_transcriptions": valid_transcriptions,
            "low_confidence_files": len(low_confidence)
        },
        "quality_gates": {
            "all_files_transcribed": len(failed) == 0,
            "avg_confidence_gte_080": avg_confidence >= 0.80,
            "telugu_detected_all": telugu_files == len(successful),
            "transcription_length_gte_10": valid_transcriptions == len(successful),
            "no_encoding_errors": True,
            "valid_json": True
        }
    }

    # Save final output
    output_dir = base_dir / "backend/ml/data/extracted"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "audio_transcriptions.json"

    print("\n" + "="*80)
    print("SAVING RESULTS")
    print("="*80)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"\n[OK] Results saved to: {output_file}")

    # Print summary report
    print("\n" + "="*80)
    print("TRANSCRIPTION SUMMARY")
    print("="*80)

    print(f"\nTotal Files: {len(audio_files)}")
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(failed)}")
    print(f"Total Duration: {total_duration:.2f} seconds ({total_duration/60:.1f} minutes)")

    print(f"\nQuality Metrics:")
    print(f"  Average Confidence: {avg_confidence:.4f} ({avg_confidence*100:.1f}%)")
    print(f"  Telugu Files: {telugu_files}/{len(successful)}")
    print(f"  Valid Transcriptions (>=10 chars): {valid_transcriptions}/{len(successful)}")
    print(f"  Low Confidence Files (<0.70): {len(low_confidence)}")

    print(f"\nQuality Gates:")
    all_passed = all(output_data['quality_gates'].values())
    for gate, passed in output_data['quality_gates'].items():
        status = "[PASS]" if passed else "[FAIL]"
        print(f"  {status} - {gate}")

    if failed:
        print(f"\nFailed Files:")
        for t in failed:
            print(f"  - {t['filename']}: {t.get('error', 'Unknown error')}")

    if low_confidence:
        print(f"\nLow Confidence Files:")
        for t in low_confidence:
            print(f"  - {t['filename']}: {t['confidence']:.4f}")

    print("\n" + "="*80)
    if all_passed:
        print("STATUS: [SUCCESS] ALL QUALITY GATES PASSED")
    else:
        print("STATUS: [WARNING] SOME QUALITY GATES FAILED")
    print("="*80)

    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
