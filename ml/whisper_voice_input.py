"""
Whisper-based Voice Input for DHRUVA
====================================
Uses faster-whisper for high-accuracy Telugu + English speech recognition.
Runs 100% offline - no API calls.

Key improvements for Telugu:
1. Use medium model (better multilingual performance)
2. Prompt conditioning with Telugu text samples
3. Force language detection to prevent gibberish
4. Domain-specific vocabulary boosting
"""

import io
import wave
import tempfile
import os
from pathlib import Path
from typing import Optional, Tuple

# Check if faster-whisper is available
WHISPER_AVAILABLE = False
try:
    from faster_whisper import WhisperModel
    WHISPER_AVAILABLE = True
except ImportError:
    print("Warning: faster-whisper not installed. Run: pip install faster-whisper")


# Telugu prompt to condition the model - contains common grievance words
# This helps Whisper understand the domain and language
TELUGU_PROMPT = """
ఇది ఆంధ్ర ప్రదేశ్ ప్రజా ఫిర్యాదు వ్యవస్థ. పెన్షన్ రాలేదు. రేషన్ కార్డు సమస్య.
రోడ్డు మరమ్మత్తు చేయండి. నీటి సరఫరా లేదు. విద్యుత్ సమస్య. ఆసుపత్రి సేవలు.
టీచర్ హాజరు కావడం లేదు. పోలీస్ ఫిర్యాదు. భూమి రికార్డులు. లంచం అడిగారు.
"""

# English prompt for Indian English speakers
ENGLISH_PROMPT = """
This is a public grievance system for Andhra Pradesh government.
Common issues: pension not received, ration card problem, road repair needed,
water supply issue, electricity problem, hospital services, teacher absence,
police complaint, land records, bribe demanded, corruption complaint.
"""

# Hindi prompt (some AP citizens speak Hindi)
HINDI_PROMPT = """
यह आंध्र प्रदेश सरकार की जन शिकायत प्रणाली है।
पेंशन नहीं मिली, राशन कार्ड समस्या, सड़क मरम्मत, पानी की समस्या।
"""


class WhisperRecognizer:
    """
    High-accuracy speech recognition using faster-whisper.
    Optimized for Telugu, English, and Hindi with domain-specific prompts.
    """

    # Model options: tiny, base, small, medium, large-v2, large-v3
    # medium model - reasonable balance of accuracy and speed
    # Note: Telugu transcription has known limitations with Whisper
    DEFAULT_MODEL = "medium"

    def __init__(self, model_size: str = None):
        self.model_size = model_size or self.DEFAULT_MODEL
        self.model: Optional[WhisperModel] = None
        self._loaded = False

    def load_model(self) -> Tuple[bool, str]:
        """
        Load the Whisper model.
        Downloads on first run (~1.5GB for medium).
        """
        if not WHISPER_AVAILABLE:
            return False, "faster-whisper not installed. Run: pip install faster-whisper"

        if self._loaded and self.model is not None:
            return True, f"Model {self.model_size} already loaded"

        try:
            # int8 quantization for lower memory (works on CPU)
            self.model = WhisperModel(
                self.model_size,
                device="cpu",  # or "cuda" for GPU
                compute_type="int8",  # int8 for CPU, float16 for GPU
                download_root=str(Path(__file__).parent / "whisper_models")
            )
            self._loaded = True
            return True, f"Whisper {self.model_size} model loaded successfully"
        except Exception as e:
            return False, f"Failed to load Whisper model: {e}"

    def _get_prompt_for_language(self, language: str) -> str:
        """Get domain-specific prompt for the language."""
        prompts = {
            "te": TELUGU_PROMPT,
            "en": ENGLISH_PROMPT,
            "hi": HINDI_PROMPT,
        }
        return prompts.get(language, "")

    def transcribe_audio(
        self,
        audio_data: bytes,
        sample_rate: int = 16000,
        language: str = None
    ) -> Tuple[str, str, float]:
        """
        Transcribe audio to text.

        Args:
            audio_data: Raw PCM audio bytes (16-bit, mono)
            sample_rate: Audio sample rate
            language: "te" for Telugu, "en" for English, "hi" for Hindi
                      None for auto-detect (less accurate for Telugu)

        Returns:
            (text: str, detected_language: str, confidence: float)
        """
        if not self._loaded:
            success, msg = self.load_model()
            if not success:
                return "", "error", 0.0

        # Save audio to temp WAV file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = tmp.name
            with wave.open(tmp, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)  # 16-bit
                wf.setframerate(sample_rate)
                wf.writeframes(audio_data)

        try:
            # Get prompt for language conditioning
            initial_prompt = self._get_prompt_for_language(language) if language else ""

            # Transcription settings optimized for Telugu/Indian languages
            # Key changes for Telugu:
            # - Use temperature fallback (0.0, 0.2, 0.4) for better handling of uncertainty
            # - Higher beam_size for better search
            # - word_timestamps helps with alignment
            segments, info = self.model.transcribe(
                tmp_path,
                language=language,  # Force language if specified
                initial_prompt=initial_prompt,  # Domain conditioning
                beam_size=5,
                best_of=5,
                patience=2.0,  # Higher patience for non-English
                temperature=(0.0, 0.2, 0.4, 0.6),  # Fallback temperatures for uncertain segments
                compression_ratio_threshold=2.4,
                log_prob_threshold=-1.0,
                no_speech_threshold=0.5,  # Lower threshold - more sensitive
                condition_on_previous_text=False,  # Disable for Telugu - prevents hallucination loops
                word_timestamps=True,  # Better alignment for Indian languages
                vad_filter=True,  # Voice activity detection
                vad_parameters=dict(
                    threshold=0.3,  # Lower threshold - more sensitive to speech
                    min_speech_duration_ms=100,  # Shorter minimum
                    min_silence_duration_ms=300,  # Shorter silence
                    speech_pad_ms=200,
                    max_speech_duration_s=float("inf"),
                )
            )

            # Collect transcription
            text_parts = []
            for segment in segments:
                text_parts.append(segment.text.strip())

            full_text = " ".join(text_parts).strip()

            # Map language codes to readable names
            lang_map = {
                "te": "telugu",
                "en": "english",
                "hi": "hindi",
            }
            detected_lang = lang_map.get(info.language, info.language)

            return full_text, detected_lang, info.language_probability

        except Exception as e:
            print(f"Transcription error: {e}")
            return "", "error", 0.0
        finally:
            try:
                os.unlink(tmp_path)
            except:
                pass

    def transcribe_wav_file(
        self,
        wav_path: str,
        language: str = None
    ) -> Tuple[str, str, float]:
        """Transcribe a WAV file directly."""
        if not self._loaded:
            success, msg = self.load_model()
            if not success:
                return "", "error", 0.0

        try:
            initial_prompt = self._get_prompt_for_language(language) if language else ""

            segments, info = self.model.transcribe(
                wav_path,
                language=language,
                initial_prompt=initial_prompt,
                beam_size=5,
                best_of=5,
                temperature=0.0,
                condition_on_previous_text=True,
                vad_filter=True
            )

            text_parts = [seg.text.strip() for seg in segments]
            full_text = " ".join(text_parts).strip()

            lang_map = {"te": "telugu", "en": "english", "hi": "hindi"}
            detected_lang = lang_map.get(info.language, info.language)

            return full_text, detected_lang, info.language_probability
        except Exception as e:
            print(f"Transcription error: {e}")
            return "", "error", 0.0

    @property
    def is_ready(self) -> bool:
        """Check if model is loaded."""
        return self._loaded and self.model is not None


# Singleton instances for different model sizes
_recognizers: dict = {}


def get_whisper_recognizer(model_size: str = None) -> WhisperRecognizer:
    """Get or create a Whisper recognizer for the given model size."""
    global _recognizers
    size = model_size or WhisperRecognizer.DEFAULT_MODEL
    if size not in _recognizers:
        _recognizers[size] = WhisperRecognizer(size)
    return _recognizers[size]


def check_whisper_available() -> dict:
    """Check Whisper availability status."""
    models_dir = Path(__file__).parent / "whisper_models"
    return {
        "faster_whisper_installed": WHISPER_AVAILABLE,
        "models_dir": str(models_dir),
        "models_dir_exists": models_dir.exists(),
    }


# Test
if __name__ == "__main__":
    print("=" * 60)
    print("Faster-Whisper Voice Recognition Status")
    print("=" * 60)

    status = check_whisper_available()
    print(f"\nFaster-whisper installed: {status['faster_whisper_installed']}")
    print(f"Models directory: {status['models_dir']}")

    if status['faster_whisper_installed']:
        print("\n" + "=" * 60)
        print("Loading Whisper medium model (first run downloads ~1.5GB)...")
        print("=" * 60)

        recognizer = get_whisper_recognizer("medium")
        success, msg = recognizer.load_model()
        print(f"Result: {msg}")
        print(f"Ready: {recognizer.is_ready}")
