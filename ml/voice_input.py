"""
Offline Voice Input using Vosk
==============================
Telugu + Indian English speech recognition without any external API calls.
Uses Vosk open-source models (Apache 2.0 license).

Models required:
- vosk-model-small-te-0.42 (58MB) - Telugu
- vosk-model-small-en-in-0.4 (36MB) - Indian English
"""

import json
import os
import wave
import zipfile
from pathlib import Path
from typing import Optional, Tuple

# Check if vosk is available
try:
    from vosk import Model, KaldiRecognizer
    VOSK_AVAILABLE = True
except ImportError:
    VOSK_AVAILABLE = False
    print("Warning: vosk not installed. Run: pip install vosk")

BASE_DIR = Path(__file__).parent
MODELS_DIR = BASE_DIR / "vosk_models"

# Model paths
TELUGU_MODEL_NAME = "vosk-model-small-te-0.42"
ENGLISH_MODEL_NAME = "vosk-model-small-en-in-0.4"


class VoiceRecognizer:
    """Offline speech recognition for Telugu and Indian English."""

    def __init__(self):
        self.telugu_model: Optional[Model] = None
        self.english_model: Optional[Model] = None
        self._loaded = False

    def _ensure_model_extracted(self, model_name: str) -> Optional[Path]:
        """Extract model if needed, return path."""
        model_dir = MODELS_DIR / model_name
        zip_file = MODELS_DIR / f"{model_name}.zip"

        # Already extracted
        if model_dir.exists():
            return model_dir

        # Need to extract
        if zip_file.exists():
            print(f"Extracting {model_name}...")
            with zipfile.ZipFile(zip_file, 'r') as zf:
                zf.extractall(MODELS_DIR)
            if model_dir.exists():
                return model_dir

        return None

    def load_models(self) -> Tuple[bool, str]:
        """
        Load Vosk models for Telugu and English.

        Returns:
            (success: bool, message: str)
        """
        if not VOSK_AVAILABLE:
            return False, "Vosk not installed. Run: pip install vosk"

        if self._loaded:
            return True, "Models already loaded"

        messages = []

        # Load Telugu model
        te_path = self._ensure_model_extracted(TELUGU_MODEL_NAME)
        if te_path:
            try:
                self.telugu_model = Model(str(te_path))
                messages.append(f"Telugu model loaded")
            except Exception as e:
                messages.append(f"Telugu model failed: {e}")
        else:
            messages.append(f"Telugu model not found. Download from alphacephei.com/vosk/models")

        # Load English model
        en_path = self._ensure_model_extracted(ENGLISH_MODEL_NAME)
        if en_path:
            try:
                self.english_model = Model(str(en_path))
                messages.append(f"Indian English model loaded")
            except Exception as e:
                messages.append(f"English model failed: {e}")
        else:
            messages.append(f"English model not found. Download from alphacephei.com/vosk/models")

        self._loaded = self.telugu_model is not None or self.english_model is not None

        return self._loaded, "; ".join(messages)

    def transcribe_audio(
        self,
        audio_data: bytes,
        sample_rate: int = 16000,
        language: str = "auto"
    ) -> Tuple[str, str, float]:
        """
        Transcribe audio to text.

        Args:
            audio_data: Raw PCM audio bytes (16-bit, mono)
            sample_rate: Audio sample rate (should be 16000)
            language: "telugu", "english", or "auto" (tries both)

        Returns:
            (text: str, detected_language: str, confidence: float)
        """
        if not self._loaded:
            success, msg = self.load_models()
            if not success:
                return "", "error", 0.0

        results = []

        # Try Telugu
        if language in ("telugu", "auto") and self.telugu_model:
            rec = KaldiRecognizer(self.telugu_model, sample_rate)
            rec.AcceptWaveform(audio_data)
            result = json.loads(rec.FinalResult())
            text = result.get("text", "").strip()
            if text:
                # Check if it contains Telugu characters
                has_telugu = any('\u0C00' <= c <= '\u0C7F' for c in text)
                results.append((text, "telugu" if has_telugu else "telugu-transliterated", 0.8))

        # Try English
        if language in ("english", "auto") and self.english_model:
            rec = KaldiRecognizer(self.english_model, sample_rate)
            rec.AcceptWaveform(audio_data)
            result = json.loads(rec.FinalResult())
            text = result.get("text", "").strip()
            if text:
                results.append((text, "english", 0.85))

        # Return best result
        if not results:
            return "", "none", 0.0

        # If auto, prefer longer transcription (usually more accurate)
        if language == "auto" and len(results) > 1:
            results.sort(key=lambda x: len(x[0]), reverse=True)

        return results[0]

    def transcribe_wav_file(self, wav_path: str, language: str = "auto") -> Tuple[str, str, float]:
        """Transcribe a WAV file."""
        with wave.open(wav_path, 'rb') as wf:
            if wf.getnchannels() != 1 or wf.getsampwidth() != 2:
                return "", "error", 0.0
            sample_rate = wf.getframerate()
            audio_data = wf.readframes(wf.getnframes())

        return self.transcribe_audio(audio_data, sample_rate, language)

    @property
    def is_ready(self) -> bool:
        """Check if at least one model is loaded."""
        return self._loaded and (self.telugu_model is not None or self.english_model is not None)

    @property
    def available_languages(self) -> list:
        """Get list of available languages."""
        langs = []
        if self.telugu_model:
            langs.append("telugu")
        if self.english_model:
            langs.append("english")
        return langs


# Singleton instance
_recognizer: Optional[VoiceRecognizer] = None


def get_voice_recognizer() -> VoiceRecognizer:
    """Get or create the voice recognizer singleton."""
    global _recognizer
    if _recognizer is None:
        _recognizer = VoiceRecognizer()
    return _recognizer


def check_models_available() -> dict:
    """Check which Vosk models are available."""
    status = {
        "vosk_installed": VOSK_AVAILABLE,
        "models_dir": str(MODELS_DIR),
        "telugu": {
            "model": TELUGU_MODEL_NAME,
            "extracted": (MODELS_DIR / TELUGU_MODEL_NAME).exists(),
            "zip_available": (MODELS_DIR / f"{TELUGU_MODEL_NAME}.zip").exists(),
        },
        "english": {
            "model": ENGLISH_MODEL_NAME,
            "extracted": (MODELS_DIR / ENGLISH_MODEL_NAME).exists(),
            "zip_available": (MODELS_DIR / f"{ENGLISH_MODEL_NAME}.zip").exists(),
        }
    }
    return status


# Test
if __name__ == "__main__":
    print("=" * 60)
    print("VOSK Voice Recognition Status")
    print("=" * 60)

    status = check_models_available()
    print(f"\nVosk installed: {status['vosk_installed']}")
    print(f"Models directory: {status['models_dir']}")

    print(f"\nTelugu model ({TELUGU_MODEL_NAME}):")
    print(f"  - Extracted: {status['telugu']['extracted']}")
    print(f"  - ZIP available: {status['telugu']['zip_available']}")

    print(f"\nIndian English model ({ENGLISH_MODEL_NAME}):")
    print(f"  - Extracted: {status['english']['extracted']}")
    print(f"  - ZIP available: {status['english']['zip_available']}")

    if status['vosk_installed']:
        print("\n" + "=" * 60)
        print("Loading models...")
        recognizer = get_voice_recognizer()
        success, msg = recognizer.load_models()
        print(f"Result: {msg}")
        print(f"Ready: {recognizer.is_ready}")
        print(f"Available languages: {recognizer.available_languages}")
