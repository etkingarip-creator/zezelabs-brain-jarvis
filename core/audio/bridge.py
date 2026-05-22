import asyncio
import websockets
import json
from core.audio.stt import TurkishSTT
from core.audio.tts import TurkishTTS
from core.ai.providers.deepseek import DeepSeekProvider

class AudioBridge:
    def __init__(self, host="localhost", port=8642):
        self.host = host
        self.port = port
        self.stt = TurkishSTT()
        self.tts = TurkishTTS()
        self.deepseek = DeepSeekProvider()
    
    async def start_server(self):
        async with websockets.serve(self.handle_client, self.host, self.port):
            print(f"🏛️ JARVIS: Sesli iletişim hattı aktif ws://{self.host}:{self.port}")
            await asyncio.Future()
    
    async def handle_client(self, websocket):
        deepseek = self.deepseek
        async for message in websocket:
            data = json.loads(message)
            
            if data.get("type") == "audio":
                audio_input = data.get("audio")
                if isinstance(audio_input, str):
                    import base64
                    try:
                        audio_bytes = base64.b64decode(audio_input)
                    except Exception:
                        audio_bytes = audio_input.encode('utf-8')
                else:
                    audio_bytes = b""
                
                text = await self.stt.transcribe(audio_bytes)
                async for token in deepseek.stream_complete(text):
                    audio_chunk = await self.tts.stream_speak(token)
                    
                    if isinstance(audio_chunk, bytes):
                        import base64
                        chunk_str = base64.b64encode(audio_chunk).decode('utf-8')
                    else:
                        chunk_str = str(audio_chunk)
                        
                    await websocket.send(json.dumps({
                        "type": "audio_chunk", 
                        "data": chunk_str
                    }))

if __name__ == "__main__":
    bridge = AudioBridge()
    try:
        asyncio.run(bridge.start_server())
    except KeyboardInterrupt:
        print("🏛️ JARVIS: Sesli iletişim hattı kapatıldı.")
