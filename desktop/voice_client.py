import asyncio
import json
import logging
import math
import time
import threading

log = logging.getLogger("jarvis_voice_client")

class DesktopVoiceClient:
    def __init__(self, uri="ws://localhost:5000/ws", on_pcm_captured=None):
        self.uri = uri
        self.on_pcm_captured = on_pcm_captured  # Dynamic PCM capture callback
        self.pyaudio = None
        self.mic_stream = None
        self.spk_stream = None
        self.is_running = False
        self.ws = None
        self.loop = None
        self.mic_enabled = False
        self.speaker_queue = asyncio.Queue()
        
        # Audio formatting rules (16kHz, 16-bit, Mono)
        self.rate = 16000
        self.channels = 1
        self.chunk = 512
        
        # Track last amplitude for waveform animations
        self.last_amplitude = 0.0
        
        try:
            import pyaudio
            self.pyaudio = pyaudio.PyAudio()
            log.info("PyAudio successfully initialized.")
        except Exception as e:
            log.warning(f"Could not load PyAudio ({e}). Voice client will run in simulated mode.")

    async def start(self, ws_connection=None):
        """
        Starts the voice client connection and audio loops.
        """
        self.is_running = True
        self.ws = ws_connection
        self.loop = asyncio.get_running_loop()
        
        if self.pyaudio:
            try:
                # Open mic stream (input)
                self.mic_stream = self.pyaudio.open(
                    format=self.pyaudio.get_format_from_width(2),  # 16-bit
                    channels=self.channels,
                    rate=self.rate,
                    input=True,
                    frames_per_buffer=self.chunk
                )
                
                # Open speaker stream (output)
                self.spk_stream = self.pyaudio.open(
                    format=self.pyaudio.get_format_from_width(2),
                    channels=self.channels,
                    rate=self.rate,
                    output=True,
                    frames_per_buffer=self.chunk
                )
                log.info("Real audio streams opened successfully.")
            except Exception as e:
                log.error(f"Failed to open hardware audio streams ({e}). Falling back to simulation.")
                self.mic_stream = None
                self.spk_stream = None
        
        # Launch background audio workers
        asyncio.create_task(self._mic_loop())
        asyncio.create_task(self._speaker_loop())
        
    async def stop(self):
        self.is_running = False
        self.mic_enabled = False
        
        # Clean up streams
        if self.mic_stream:
            try:
                self.mic_stream.stop_stream()
                self.mic_stream.close()
            except Exception: pass
            self.mic_stream = None
            
        if self.spk_stream:
            try:
                self.spk_stream.stop_stream()
                self.spk_stream.close()
            except Exception: pass
            self.spk_stream = None
            
        if self.pyaudio:
            try:
                self.pyaudio.terminate()
            except Exception: pass
            self.pyaudio = None
            
        log.info("Voice client stopped.")

    def set_mic(self, enabled: bool):
        self.mic_enabled = enabled
        log.info(f"Microphone toggled to: {enabled}")

    async def play_audio_chunk(self, audio_data: bytes):
        """
        Queue audio chunks to be played immediately through the speakers.
        """
        await self.speaker_queue.put(audio_data)

    async def _mic_loop(self):
        """
        Microphone capture and streaming loop.
        """
        t_last = 0.0
        
        while self.is_running:
            if self.mic_enabled:
                if self.mic_stream:
                    try:
                        # Non-blocking read or off-thread execution to avoid locking the loop
                        def _read():
                            try:
                                return self.mic_stream.read(self.chunk, exception_on_overflow=False)
                            except Exception:
                                return b""
                        data = await self.loop.run_in_executor(None, _read)
                        
                        if data:
                            # Calculate peak amplitude for volume telemetry
                            import numpy as np
                            audio_np = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
                            peak = float(np.max(np.abs(audio_np))) if len(audio_np) > 0 else 0.0
                            self.last_amplitude = peak
                            
                            # Invoke PCM capture callback (used by STT voice recorder buffer)
                            if self.on_pcm_captured:
                                self.on_pcm_captured(data, peak)
                            
                            # Stream PCM bytes to the WebSocket endpoint if active
                            if self.ws:
                                await self.ws.send_json({
                                    "type": "mic_pcm",
                                    "val": peak,
                                    "raw_len": len(data)
                                })
                    except Exception as e:
                        log.error(f"Mic loop read/send error: {e}")
                        await asyncio.sleep(0.05)
                else:
                    # Simulated Mic Wave amplitude oscillation
                    # Simulates talking peaks!
                    peak = abs(math.sin(time.time() * 8)) * 0.4 + (math.sin(time.time() * 45) * 0.1)
                    if peak < 0.15: peak = 0.05  # noise floor
                    self.last_amplitude = peak
                    
                    # Generate a block of silent PCM bytes to trigger VAD / VAD buffers in tests
                    data = b"\x00" * (self.chunk * 2)
                    if self.on_pcm_captured:
                        self.on_pcm_captured(data, peak)
                        
                    if self.ws:
                        try:
                            await self.ws.send_json({
                                                    "type": "mic_pcm",
                                "val": peak,
                                "raw_len": self.chunk * 2
                            })
                        except Exception: pass
                    await asyncio.sleep(float(self.chunk) / self.rate)
            else:
                self.last_amplitude = 0.0
                # Mic is off: send zero volume/silence telemetry at standard intervals
                if time.time() - t_last > 0.15:
                    if self.ws:
                        try:
                            await self.ws.send_json({
                                "type": "mic_pcm",
                                "val": 0.0,
                                "raw_len": 0
                            })
                        except Exception: pass
                    t_last = time.time()
                await asyncio.sleep(0.05)

    async def _speaker_loop(self):
        """
        Speaker queue consumer loop for playing audio.
        """
        while self.is_running:
            try:
                chunk = await self.speaker_queue.get()
                if not chunk:
                    self.speaker_queue.task_done()
                    continue
                    
                if self.spk_stream:
                    try:
                        # Play chunk on secondary thread to avoid GUI/async lags
                        def _write():
                            try:
                                self.spk_stream.write(chunk)
                            except Exception: pass
                        await self.loop.run_in_executor(None, _write)
                    except Exception as e:
                        log.error(f"Speaker stream write error: {e}")
                else:
                    # Simulation mode: log play action and simulate playback delay
                    duration = len(chunk) / (self.rate * 2)  # assuming 16-bit
                    await asyncio.sleep(duration)
                    
                self.speaker_queue.task_done()
            except Exception as e:
                log.error(f"Speaker loop error: {e}")
                await asyncio.sleep(0.05)
