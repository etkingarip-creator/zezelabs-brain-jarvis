import asyncio
import json

class DesktopVoiceClient:
    def __init__(self, uri="ws://localhost:8642"):
        self.uri = uri
        try:
            import pyaudio
            self.pyaudio = pyaudio.PyAudio()
        except ImportError:
            self.pyaudio = None
        
        self.websocket = None
        self.is_running = False
    
    async def start(self):
        if not self.pyaudio:
            print("[SIMULATION] PyAudio yok - simulation modunda")
            self.is_running = True
            await asyncio.sleep(0.1)
            return
        
        # Real PyAudio opening channel
        self.is_running = True
        
    async def play(self):
        if not self.pyaudio:
            print("[SIMULATION] Hoparlör simüle ediliyor")
            return
