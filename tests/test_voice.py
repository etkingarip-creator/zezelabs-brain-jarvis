import pytest
import asyncio
from core.audio.stt import TurkishSTT
from core.audio.tts import TurkishTTS
from desktop.voice_client import DesktopVoiceClient

def test_stt_transcription():
    async def _run():
        stt = TurkishSTT()
        # Provide a simple mock array size (representing silence / small amplitude)
        audio_data = b"\x00" * 3200  # 0.1 seconds of silence
        text = await stt.transcribe(audio_data)
        # The VAD should either filter it out as silence or run mock transcribing smoothly
        assert isinstance(text, str)
    asyncio.run(_run())

def test_tts_streaming():
    async def _run():
        tts = TurkishTTS()
        text = "Merhaba dünya"
        generator = tts.stream_speak(text)
        
        chunks = []
        async for chunk in generator:
            chunks.append(chunk)
            
        assert len(chunks) > 0
        assert isinstance(chunks[0], bytes)
        
        # Test awaitable form too
        full_audio = await tts.stream_speak(text)
        assert isinstance(full_audio, bytes)
        assert len(full_audio) >= sum(len(c) for c in chunks)
    asyncio.run(_run())

def test_voice_client_loop():
    async def _run():
        callback_triggered = False
        captured_data = None
        
        def on_pcm(data, peak):
            nonlocal callback_triggered, captured_data
            callback_triggered = True
            captured_data = data
            
        client = DesktopVoiceClient(on_pcm_captured=on_pcm)
        assert client.rate == 16000
        assert client.channels == 1
        assert not client.is_running
        
        # Run start in dry mode
        await client.start()
        client.set_mic(True)
        
        # Wait a brief moment to allow the background mic loop to run a tick
        await asyncio.sleep(0.05)
        
        # In simulated mode, it should successfully trigger the PCM callback
        assert callback_triggered
        assert captured_data is not None
        
        await client.stop()
    asyncio.run(_run())
