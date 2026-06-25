"""
Gemma Director - Jarvis'in Google Gemma Model API entegrasyonu
OpenRouter üzerinden google/gemma-4-26b-a4b-it modeli kullanılır.
"""

import os
import json
import asyncio
import aiohttp
from typing import Dict, Any, Optional, List, AsyncIterator
from datetime import datetime
from dotenv import load_dotenv

# .env dosyasındaki değerler sistem ortam değişkenlerini override etsin
# Proje kök dizinindeki .env dosyasını yükle
_env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), ".env")
import sys
_is_testing = "pytest" in sys.modules or any("pytest" in arg for arg in sys.argv)
load_dotenv(_env_path, override=not _is_testing)

# Varsayılan Gemma modeli
DEFAULT_GEMMA_MODEL = "google/gemma-4-26b-a4b-it"


def is_gemini_model(model_name: str) -> bool:
    """Returns True if the model is a Gemini model."""
    if not model_name:
        return False
    return "gemini" in model_name.lower()


def _resolve_default_model() -> str:
    """Resolve the default model from config.GEMMA_MODEL or env."""
    try:
        from core.config import config as _cfg
        return _cfg.GEMMA_MODEL or os.getenv("GEMMA_MODEL", DEFAULT_GEMMA_MODEL)
    except Exception:
        return os.getenv("GEMMA_MODEL", DEFAULT_GEMMA_MODEL)


def _resolve_fast_model() -> str:
    """Resolve the fast model from config.GEMMA_MODEL_FAST or env."""
    try:
        from core.config import config as _cfg
        return _cfg.GEMMA_MODEL_FAST or os.getenv("GEMMA_MODEL_FAST", DEFAULT_GEMMA_MODEL)
    except Exception:
        return os.getenv("GEMMA_MODEL_FAST", DEFAULT_GEMMA_MODEL)


class GemmaDirector:
    """Google Gemma model erişimi yöneten sınıf (OpenRouter üzerinden)"""

    def __init__(self):
        # .env yüklemesi - config'ten önce import edilse bile çalışsın
        _env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), ".env")
        import sys
        _is_testing = "pytest" in sys.modules or any("pytest" in arg for arg in sys.argv)
        load_dotenv(_env_path, override=not _is_testing)
        
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.base_url = os.getenv("OPENROUTER_API_BASE", "https://openrouter.ai/api/v1")
        self.default_model = _resolve_default_model()
        self.fast_model = _resolve_fast_model()
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Kullanım istatistikleri
        self.request_count = 0
        self.total_tokens = 0
        self.estimated_cost = 0.0
        
        logger = __import__('logging').getLogger(__name__)
        self.logger = logger
    
    def _parse_affordable_tokens(self, error_text: str) -> Optional[int]:
        """Extracts the number of affordable tokens from OpenRouter's 402 error message."""
        import re
        message = ""
        try:
            data = json.loads(error_text)
            if isinstance(data, dict):
                error_obj = data.get("error", {})
                if isinstance(error_obj, dict):
                    message = error_obj.get("message", "")
                elif isinstance(error_obj, str):
                    message = error_obj
        except Exception:
            pass
        
        if not message:
            message = error_text

        # Match "can only afford 10139" or similar
        match = re.search(r"can only afford\s+(\d+)", message, re.IGNORECASE)
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                pass
        return None

    def _convert_messages_to_gemini(self, messages: list) -> dict:
        gemini_contents = []
        system_text = ""
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content") or ""
            if role == "system":
                system_text = content
            else:
                gemini_role = "model" if role == "assistant" else "user"
                gemini_contents.append({
                    "role": gemini_role,
                    "parts": [{"text": content}]
                })
        
        payload = {"contents": gemini_contents}
        if system_text:
            payload["systemInstruction"] = {"parts": [{"text": system_text}]}
        return payload

    async def _get_session(self) -> aiohttp.ClientSession:
        """Merkezi LLMClient session'ını kullan — ayrı connection pool açma."""
        try:
            from core.ai.llm_client import LLMClient
            return await LLMClient.get_session()
        except Exception:
            if self.session is None or self.session.closed:
                self.session = aiohttp.ClientSession()
            return self.session
    
    async def close(self):
        """Session LLMClient tarafından yönetilir — sadece fallback session'ı kapat."""
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None

    async def chat(
        self,
        message: str,
        *,
        context: Optional[Dict[str, Any]] = None,
        system: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        use_fast: bool = False,
        **kwargs,
    ) -> str:
        """High-level wrapper used by the FastAPI chat endpoint and departments.

        Args:
            use_fast: If True, uses the fast model (llama-3.2-3b) for quick responses.
        """
        messages: List[Dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        if context and isinstance(context, dict):
            history = context.get("history") or []
            for turn in history[-6:]:  # cap context window — token cimrisi
                role = turn.get("role", "user")
                content = turn.get("content", "")
                if content:
                    messages.append({"role": role, "content": str(content)[:2000]})
        messages.append({"role": "user", "content": message})

        # Use fast model if requested
        actual_model = self.fast_model if use_fast else (model or self.default_model)
        result = await self.chat_completion(messages, model=actual_model, temperature=temperature, **kwargs)
        choices = result.get("choices") or []
        if not choices:
            return ""
        return choices[0].get("message", {}).get("content", "") or ""

    async def stream_chat(
        self,
        message: str,
        *,
        context: Optional[Dict[str, Any]] = None,
        system: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        use_fast: bool = False,
        **kwargs,
    ) -> AsyncIterator[str]:
        """Streaming version of chat - yields chunks as they arrive."""
        messages: List[Dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        if context and isinstance(context, dict):
            history = context.get("history") or []
            for turn in history[-6:]:
                role = turn.get("role", "user")
                content = turn.get("content", "")
                if content:
                    messages.append({"role": role, "content": str(content)[:2000]})
        messages.append({"role": "user", "content": message})

        actual_model = self.fast_model if use_fast else (model or self.default_model)
        async for chunk in self.stream_completion(messages, model=actual_model, temperature=temperature, **kwargs):
            yield chunk

    async def stream_completion(
        self,
        messages: list[dict],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = 15000,
        retry_count: int = 0,
    ) -> AsyncIterator[str]:
        """Gemma streaming completion - yields text chunks."""
        actual_model = model or self.default_model
        
        if is_gemini_model(actual_model):
            from dotenv import load_dotenv
            load_dotenv(_env_path, override=not _is_testing)
            gemini_key = os.getenv("GEMINI_API_KEY")
            if not gemini_key:
                raise ValueError("GEMINI_API_KEY not found in environment for Gemini model.")
            gemini_model_name = actual_model if "gemini-" in actual_model else "gemini-2.5-flash"
            gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/{gemini_model_name}:streamGenerateContent?key={gemini_key}&alt=sse"
            gemini_payload = self._convert_messages_to_gemini(messages)
            session = await self._get_session()
            async with session.post(
                gemini_url,
                json=gemini_payload,
                headers={"Content-Type": "application/json"},
                timeout=aiohttp.ClientTimeout(total=60)
            ) as resp:
                if resp.status != 200:
                    resp_text = await resp.text()
                    raise Exception(f"Gemini API returned status {resp.status}: {resp_text}")
                
                async for line in resp.content:
                    line = line.decode("utf-8").strip()
                    if not line:
                        continue
                    if line.startswith("data: "):
                        data = json.loads(line[6:])
                        candidates = data.get("candidates", [])
                        if candidates:
                            parts = candidates[0].get("content", {}).get("parts", [])
                            if parts:
                                text = parts[0].get("text", "")
                                if text:
                                    yield text
            return
        
        # Z.ai / GLM model routing support
        from core.ai.llm_client import is_zai_model, _get_zai_url_and_headers
        
        if is_zai_model(actual_model):
            try:
                url, headers = _get_zai_url_and_headers(coding=False)
            except ValueError as val_err:
                raise Exception(f"Z.ai configuration error: {val_err}")
        else:
            if not self.api_key:
                raise ValueError("GEMMA_API_KEY environment variable not set")
            url = f"{self.base_url}/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://jarvis.zom.core",
                "X-Title": "Jarvis ZOM Core"
            }

        session = await self._get_session()

        # Headroom: mesajları API'ye göndermeden önce sıkıştır (HEADROOM_OUTPUT_SHAPER=1 ise)
        messages = await self.compress(messages, model=actual_model)

        request_model = "z-ai/glm-4.5-air:free" if actual_model == "z-ai/glm-5.2-free" else actual_model
        payload = {
            "model": request_model,
            "messages": messages,
            "temperature": temperature,
            "stream": True,
            "max_tokens": max_tokens
        }

        try:
            async with session.post(
                url,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=300)
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    if response.status == 429 and payload["model"] != "openrouter/free" and retry_count < 2:
                        self.logger.warning(f"OpenRouter 429 rate limit hit in stream. Retrying with openrouter/free fallback...")
                        async for chunk in self.stream_completion(
                            messages=messages,
                            model="openrouter/free",
                            temperature=temperature,
                            max_tokens=max_tokens,
                            retry_count=retry_count + 1
                        ):
                            yield chunk
                        return
                    if response.status == 402 and retry_count < 2:
                        if "insufficient credits" in error_text.lower() or "never purchased" in error_text.lower():
                            self.logger.warning(f"OpenRouter 402 insufficient credits in stream. Retrying with openrouter/free fallback...")
                            async for chunk in self.stream_completion(
                                messages=messages,
                                model="openrouter/free",
                                temperature=temperature,
                                max_tokens=max_tokens,
                                retry_count=retry_count + 1
                            ):
                                yield chunk
                            return
                        affordable = self._parse_affordable_tokens(error_text)
                        if affordable and affordable > 0 and (max_tokens is None or affordable < max_tokens):
                            self.logger.warning(f"OpenRouter 429 model rate-limited. Retrying with reduced max_tokens={affordable}")
                            async for chunk in self.stream_completion(
                                messages=messages,
                                model=model,
                                temperature=temperature,
                                max_tokens=affordable,
                                retry_count=retry_count + 1
                            ):
                                yield chunk
                            return
                        elif max_tokens is not None and max_tokens > 2000:
                            self.logger.warning(f"OpenRouter 429 model rate-limited. Retrying with safe max_tokens=2000")
                            async for chunk in self.stream_completion(
                                messages=messages,
                                model=model,
                                temperature=temperature,
                                max_tokens=2000,
                                retry_count=retry_count + 1
                            ):
                                yield chunk
                            return
                    
                    raise Exception(f"Gemma API error: {response.status} - {error_text}")

                async for line in response.content:
                    line = line.decode("utf-8").strip()
                    if not line or line == "data: [DONE]":
                        continue
                    if line.startswith("data: "):
                        data = json.loads(line[6:])
                        delta = data.get("choices", [{}])[0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            yield content

        except Exception as e:
            if retry_count > 0:
                raise e
            
            from dotenv import load_dotenv
            load_dotenv(_env_path, override=not _is_testing)
            gemini_key = os.getenv("GEMINI_API_KEY")
            if gemini_key:
                self.logger.warning(f"Gemma streaming error: {e}. Trying Gemini API fallback...")
                try:
                    gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}"
                    gemini_payload = self._convert_messages_to_gemini(messages)
                    async with session.post(
                        gemini_url,
                        json=gemini_payload,
                        headers={"Content-Type": "application/json"},
                        timeout=aiohttp.ClientTimeout(total=60)
                    ) as resp:
                        if resp.status == 200:
                            res_json = await resp.json()
                            text = res_json["candidates"][0]["content"]["parts"][0]["text"]
                            self.logger.info("Gemini API fallback stream successful.")
                            yield text
                            return
                        else:
                            resp_text = await resp.text()
                            raise Exception(f"Gemini API returned status {resp.status}: {resp_text}")
                except Exception as gemini_err:
                    self.logger.error(f"Gemini API fallback stream also failed: {gemini_err}")

            self.logger.warning(f"Gemma streaming error: {e}. Trying local Ollama fallback...")
            try:
                from core.ai.llm_client import get_local_model_for_department
                ollama_url = os.getenv("OLLAMA_API_BASE", "http://127.0.0.1:11434/v1/chat/completions")
                agent_id = kwargs.get("agent_id") or kwargs.get("department")
                local_model = get_local_model_for_department(agent_id)
                
                payload = {
                    "model": local_model,
                    "messages": messages,
                    "temperature": temperature,
                    "stream": True
                }
                
                self.logger.info(f"Calling local Ollama stream fallback with model {local_model}...")
                async with session.post(
                    ollama_url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as resp:
                    if resp.status == 200:
                        async for line in resp.content:
                            line = line.decode("utf-8").strip()
                            if not line:
                                continue
                            if line.startswith("data: "):
                                if line == "data: [DONE]":
                                    continue
                                data = json.loads(line[6:])
                                delta = data.get("choices", [{}])[0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    yield content
                        self.logger.info("Local Ollama stream fallback successful.")
                    else:
                        raise Exception(f"Ollama stream fallback returned status {resp.status}")
            except Exception as ollama_err:
                self.logger.error(f"Local Ollama stream fallback also failed: {ollama_err}")
                raise e

    async def compress(
        self,
        messages: List[Dict[str, str]],
        *,
        model: Optional[str] = None,
        target_tokens: Optional[int] = None,
    ) -> List[Dict[str, str]]:
        """Headroom ile mesaj listesini API'ye gönderilmeden önce sıkıştır.

        HEADROOM_OUTPUT_SHAPER=1 değilse veya headroom-ai kurulu değilse
        orijinal listeyi olduğu gibi döner (no-op). Kümülatif tasarruf
        istatistiklerini ``self.headroom_*`` üzerinde tutar.
        """
        if os.getenv("HEADROOM_OUTPUT_SHAPER", "0") != "1":
            return messages
        if not messages:
            return messages
        try:
            from headroom import compress as _headroom_compress
        except ImportError:
            self.logger.warning("headroom-ai kurulu değil; compress() atlanıyor")
            return messages
        try:
            kwargs: Dict[str, Any] = {"model": model or self.default_model}
            if target_tokens:
                kwargs["model_limit"] = target_tokens
            result = _headroom_compress(list(messages), **kwargs)
            # Kümülatif tasarruf (output-savings raporu / dashboard için)
            self.headroom_tokens_saved = getattr(self, "headroom_tokens_saved", 0) + (result.tokens_saved or 0)
            self.headroom_calls = getattr(self, "headroom_calls", 0) + 1
            self.logger.info(
                "Headroom compress: %s->%s token (%%%.0f tasarruf), %s->%s mesaj",
                result.tokens_before,
                result.tokens_after,
                (result.compression_ratio or 0.0) * 100,
                len(messages),
                len(result.messages),
            )
            return result.messages
        except Exception as e:
            self.logger.warning(f"Headroom compress başarısız: {e}; orijinal döndürülüyor")
            return messages

    async def credits(self) -> Dict[str, Any]:
        """Return current API credits/balance. Used by dashboard."""
        if not self.api_key:
            return {"available": False, "reason": "no_api_key"}
        session = await self._get_session()
        try:
            async with session.get(
                f"{self.base_url}/credits",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                return {"available": False, "status": resp.status}
        except Exception as e:
            return {"available": False, "error": str(e)}
    
    async def chat_completion(
        self, 
        messages: list[dict], 
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = 15000,  # Varsayılan 15K token - bütçe dostu
        retry_count: int = 0,
        **kwargs
    ) -> Dict[str, Any]:
        """Gemma model üzerinden sohbet tamamlama"""
        actual_model = model or self.default_model
        
        if is_gemini_model(actual_model):
            from dotenv import load_dotenv
            load_dotenv(_env_path, override=not _is_testing)
            gemini_key = os.getenv("GEMINI_API_KEY")
            if not gemini_key:
                raise ValueError("GEMINI_API_KEY not found in environment for Gemini model.")
            gemini_model_name = actual_model if "gemini-" in actual_model else "gemini-2.5-flash"
            gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/{gemini_model_name}:generateContent?key={gemini_key}"
            gemini_payload = self._convert_messages_to_gemini(messages)
            session = await self._get_session()
            async with session.post(
                gemini_url,
                json=gemini_payload,
                headers={"Content-Type": "application/json"},
                timeout=aiohttp.ClientTimeout(total=60)
            ) as resp:
                if resp.status == 200:
                    res_json = await resp.json()
                    text = res_json["candidates"][0]["content"]["parts"][0]["text"]
                    usage = res_json.get("usageMetadata", {})
                    return {
                        "choices": [
                            {
                                "message": {
                                    "role": "assistant",
                                    "content": text
                                },
                                "finish_reason": "stop",
                                "index": 0
                            }
                        ],
                        "usage": {
                            "prompt_tokens": usage.get("promptTokenCount", 0),
                            "completion_tokens": usage.get("candidatesTokenCount", 0),
                            "total_tokens": usage.get("totalTokenCount", 0)
                        },
                        "model": gemini_model_name
                    }
                else:
                    resp_text = await resp.text()
                    raise Exception(f"Gemini API returned status {resp.status}: {resp_text}")
        
        # Z.ai / GLM model routing support
        from core.ai.llm_client import is_zai_model, _get_zai_url_and_headers
        
        if is_zai_model(actual_model):
            try:
                url, headers = _get_zai_url_and_headers(coding=False)
            except ValueError as val_err:
                raise Exception(f"Z.ai configuration error: {val_err}")
        else:
            if not self.api_key:
                raise ValueError("GEMMA_API_KEY environment variable not set")
            url = f"{self.base_url}/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://jarvis.zom.core",
                "X-Title": "Jarvis ZOM Core"
            }
        
        session = await self._get_session()
        
        # Headroom: mesajları API'ye göndermeden önce sıkıştır (HEADROOM_OUTPUT_SHAPER=1 ise)
        messages = await self.compress(messages, model=actual_model)

        request_model = "z-ai/glm-4.5-air:free" if actual_model == "z-ai/glm-5.2-free" else actual_model
        payload = {
            "model": request_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,  # Her zaman limit uygula
            **kwargs
        }
        
        try:
            self.logger.info(f"Making Gemma API call to {payload['model']}")
            async with session.post(
                url,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=300)
            ) as response:
                
                if response.status != 200:
                    error_text = await response.text()
                    self.logger.error(f"Gemma API error {response.status}: {error_text}")
                    if response.status == 429 and payload["model"] != "openrouter/free" and retry_count < 2:
                        self.logger.warning(f"OpenRouter 429 rate limit hit. Retrying with openrouter/free fallback...")
                        return await self.chat_completion(
                            messages=messages,
                            model="openrouter/free",
                            temperature=temperature,
                            max_tokens=max_tokens,
                            retry_count=retry_count + 1,
                            **kwargs
                        )
                    if response.status == 402 and retry_count < 2:
                        if "insufficient credits" in error_text.lower() or "never purchased" in error_text.lower():
                            self.logger.warning(f"OpenRouter 402 insufficient credits. Retrying with openrouter/free fallback...")
                            return await self.chat_completion(
                                messages=messages,
                                model="openrouter/free",
                                temperature=temperature,
                                max_tokens=max_tokens,
                                retry_count=retry_count + 1,
                                **kwargs
                            )
                        affordable = self._parse_affordable_tokens(error_text)
                        if affordable and affordable > 0 and (max_tokens is None or affordable < max_tokens):
                            self.logger.warning(f"OpenRouter 402 credit limit hit. Retrying with reduced max_tokens={affordable}")
                            return await self.chat_completion(
                                messages=messages,
                                model=model,
                                temperature=temperature,
                                max_tokens=affordable,
                                retry_count=retry_count + 1,
                                **kwargs
                            )
                        elif max_tokens is not None and max_tokens > 2000:
                            self.logger.warning(f"OpenRouter 402 credit limit hit. Retrying with safe max_tokens=2000")
                            return await self.chat_completion(
                                messages=messages,
                                model=model,
                                temperature=temperature,
                                max_tokens=2000,
                                retry_count=retry_count + 1,
                                **kwargs
                            )
                    raise Exception(f"Gemma API error: {response.status} - {error_text}")
                
                result = await response.json()
                
                # Kullanım istatistiklerini güncelle
                self.request_count += 1
                usage = result.get("usage", {})
                prompt_tokens = usage.get("prompt_tokens", 0)
                completion_tokens = usage.get("completion_tokens", 0)
                total_tokens = prompt_tokens + completion_tokens
                self.total_tokens += total_tokens
                
                # Tahmini maliyet (basitleştirilmiş)
                if "free" in (model or self.default_model).lower():
                    cost = 0.0
                else:
                    # Tahmini $0.001 per 1K token
                    cost = (total_tokens / 1000) * 0.001
                self.estimated_cost += cost
                
                self.logger.info(f"Gemma API call successful. Tokens: {total_tokens}, Cost: ${cost:.4f}")
                
                return result
                
        except asyncio.TimeoutError:
            self.logger.error("Gemma API request timeout")
            raise Exception("Gemma API request timeout")
        except Exception as e:
            if retry_count > 0:
                raise e
            
            from dotenv import load_dotenv
            load_dotenv(_env_path, override=not _is_testing)
            gemini_key = os.getenv("GEMINI_API_KEY")
            if gemini_key:
                self.logger.warning(f"Gemma API request failed: {e}. Trying Gemini API fallback...")
                try:
                    gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}"
                    gemini_payload = self._convert_messages_to_gemini(messages)
                    async with session.post(
                        gemini_url,
                        json=gemini_payload,
                        headers={"Content-Type": "application/json"},
                        timeout=aiohttp.ClientTimeout(total=60)
                    ) as resp:
                        if resp.status == 200:
                            res_json = await resp.json()
                            text = res_json["candidates"][0]["content"]["parts"][0]["text"]
                            usage = res_json.get("usageMetadata", {})
                            self.logger.info("Gemini API fallback call successful.")
                            return {
                                "choices": [
                                    {
                                        "message": {
                                            "role": "assistant",
                                            "content": text
                                        },
                                        "finish_reason": "stop",
                                        "index": 0
                                    }
                                ],
                                "usage": {
                                    "prompt_tokens": usage.get("promptTokenCount", 0),
                                    "completion_tokens": usage.get("candidatesTokenCount", 0),
                                    "total_tokens": usage.get("totalTokenCount", 0)
                                },
                                "model": "gemini-2.5-flash"
                            }
                        else:
                            resp_text = await resp.text()
                            raise Exception(f"Gemini API returned status {resp.status}: {resp_text}")
                except Exception as gemini_err:
                    self.logger.error(f"Gemini API fallback also failed: {gemini_err}")

            self.logger.warning(f"Gemma API request failed: {e}. Trying local Ollama fallback...")
            try:
                from core.ai.llm_client import get_local_model_for_department
                ollama_url = os.getenv("OLLAMA_API_BASE", "http://127.0.0.1:11434/v1/chat/completions")
                agent_id = kwargs.get("agent_id") or kwargs.get("department")
                local_model = get_local_model_for_department(agent_id)
                
                payload = {
                    "model": local_model,
                    "messages": messages,
                    "temperature": temperature
                }
                
                self.logger.info(f"Calling local Ollama fallback with model {local_model}...")
                async with session.post(
                    ollama_url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        self.logger.info("Local Ollama fallback call successful.")
                        return data
                    else:
                        raise Exception(f"Ollama fallback returned status {resp.status}")
            except Exception as ollama_err:
                self.logger.error(f"Local Ollama fallback also failed: {ollama_err}")
                raise e

# Global instance - lazy loaded to ensure .env is loaded first
_gemma_director = None

def get_gemma_director() -> GemmaDirector:
    """Lazy singleton for GemmaDirector - ensures .env is loaded first."""
    global _gemma_director
    if _gemma_director is None:
        _gemma_director = GemmaDirector()
    return _gemma_director

# Backward compatibility alias (eski kodlar için)
OpenRouterDirector = GemmaDirector
openrouter_director = None  # Will be replaced by lazy getter
get_openrouter_director = get_gemma_director

if __name__ == "__main__":
    # Test
    async def test():
        try:
            director = get_gemma_director()
            result = await director.chat_completion([
                {"role": "user", "content": "Hello, Jarvis!"}
            ])
            print("Success:", json.dumps(result, indent=2))
        except Exception as e:
            print("Error:", e)
        finally:
            await get_gemma_director().close()
    
    import asyncio
    asyncio.run(test())
