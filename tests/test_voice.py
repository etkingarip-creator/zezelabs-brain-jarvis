import pytest

@pytest.mark.anyio
async def test_stt_transcribe():
    from core.audio.stt import TurkishSTT
    stt = TurkishSTT()
    result = await stt.transcribe(b"dummy_audio")
    assert result is not None

@pytest.mark.anyio
async def test_tts_stream():
    from core.audio.tts import TurkishTTS
    tts = TurkishTTS()
    chunks = [c async for c in tts.stream_speak("test")]
    assert len(chunks) > 0
