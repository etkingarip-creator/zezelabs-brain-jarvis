import time
import pytest

def test_import_speed():
    # Record starting timestamp
    start_t = time.perf_counter()
    
    # Import core audio and launcher modules
    from core.audio.stt import TurkishSTT
    from core.audio.tts import TurkishTTS
    from desktop.voice_client import DesktopVoiceClient
    from desktop.backend_launcher import BackendLauncher
    
    duration = time.perf_counter() - start_t
    print(f"\nImport performance latency: {duration:.4f}s")
    
    # Assert imports are fast (< 550ms) to ensure lightweight app footprint
    assert duration < 0.55
