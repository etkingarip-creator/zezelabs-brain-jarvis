import os
import httpx
from typing import Optional, Dict, Any

class DeepSeekProvider:
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "deepseek-chat",
        base_url: str = "https://api.deepseek.com/v1",
    ):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        self.model = model
        self.base_url = base_url
        self.mock = (os.getenv("ZOM_MOCK_DEEPSEEK", "true").lower() == "true") or not self.api_key
    
    async def complete_async(
        self,
        prompt: str,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        if self.mock or not self.api_key:
            return self._mock_response(prompt)
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
            **kwargs
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                r = await client.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers
                )
                r.raise_for_status()
                data = r.json()
                return data["choices"][0]["message"]["content"]
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    raise Exception("Rate limit exceeded")
                elif e.response.status_code == 401:
                    raise Exception("Invalid API key")
                raise
            except httpx.TimeoutException:
                raise Exception("Request timeout")
    
    def complete(self, prompt: str, **kwargs) -> str:
        import asyncio
        return asyncio.run(self.complete_async(prompt, **kwargs))
    
    async def stream_complete(self, prompt: str, **kwargs):
        import asyncio
        if self.mock or not self.api_key:
            response = self._mock_response(prompt)
            for word in response.split(" "):
                yield word + " "
                await asyncio.sleep(0.01)
        else:
            response = await self.complete_async(prompt, **kwargs)
            for word in response.split(" "):
                yield word + " "
                await asyncio.sleep(0.01)
    
    def _mock_response(self, prompt: str) -> str:
        return f"Mock response for: {prompt[:50]}..."
    
    def health_check(self) -> Dict[str, Any]:
        return {
            "status": "mock" if self.mock else "ready",
            "model": self.model,
            "has_key": bool(self.api_key)
        }
