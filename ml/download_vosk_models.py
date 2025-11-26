"""
Download Vosk speech recognition models for Telugu and Indian English.
Run this script once to download the models (~94MB total).
"""

import os
import sys
import requests
from pathlib import Path
from tqdm import tqdm

MODELS_DIR = Path(__file__).parent / "vosk_models"
MODELS_DIR.mkdir(exist_ok=True)

MODELS = [
    {
        "name": "vosk-model-small-te-0.42",
        "url": "https://alphacephei.com/vosk/models/vosk-model-small-te-0.42.zip",
        "size_mb": 58,
        "language": "Telugu"
    },
    {
        "name": "vosk-model-small-en-in-0.4",
        "url": "https://alphacephei.com/vosk/models/vosk-model-small-en-in-0.4.zip",
        "size_mb": 36,
        "language": "Indian English"
    }
]


def download_file(url: str, dest: Path, desc: str = "Downloading"):
    """Download a file with progress bar."""
    response = requests.get(url, stream=True, timeout=60)
    response.raise_for_status()

    total_size = int(response.headers.get('content-length', 0))

    with open(dest, 'wb') as f:
        with tqdm(total=total_size, unit='B', unit_scale=True, desc=desc) as pbar:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    pbar.update(len(chunk))


def main():
    print("=" * 60)
    print("VOSK Model Downloader for DHRUVA")
    print("=" * 60)
    print(f"\nModels will be saved to: {MODELS_DIR}")
    print()

    for model in MODELS:
        zip_path = MODELS_DIR / f"{model['name']}.zip"
        extracted_path = MODELS_DIR / model['name']

        if extracted_path.exists():
            print(f"[SKIP] {model['language']} model already extracted")
            continue

        if zip_path.exists():
            print(f"[SKIP] {model['language']} model ZIP already downloaded")
        else:
            print(f"\n[DOWNLOAD] {model['language']} model ({model['size_mb']}MB)...")
            try:
                download_file(model['url'], zip_path, f"{model['language']}")
                print(f"[OK] Downloaded {model['name']}")
            except Exception as e:
                print(f"[ERROR] Failed to download {model['name']}: {e}")
                continue

        # Extract
        print(f"[EXTRACT] Extracting {model['name']}...")
        import zipfile
        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                zf.extractall(MODELS_DIR)
            print(f"[OK] Extracted {model['name']}")
        except Exception as e:
            print(f"[ERROR] Failed to extract: {e}")

    print("\n" + "=" * 60)
    print("Download complete!")
    print("=" * 60)

    # Verify
    print("\nVerification:")
    for model in MODELS:
        extracted_path = MODELS_DIR / model['name']
        status = "READY" if extracted_path.exists() else "MISSING"
        print(f"  {model['language']}: {status}")


if __name__ == "__main__":
    main()
