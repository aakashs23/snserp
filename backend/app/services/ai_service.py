"""Provider-agnostic AI service layer with failover support.

Abstracts LLM and embedding interactions behind a common interface
so that business logic never depends on a specific AI provider.
Switching providers requires only configuration changes in .env.
"""

import asyncio
import logging
import re
from abc import ABC, abstractmethod
from functools import lru_cache
from typing import Optional

from app.config.settings import settings

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Abstract interfaces
# ─────────────────────────────────────────────────────────────────────────────
class LLMProvider(ABC):
    """Common interface for language model providers."""

    name: str = "base"

    @abstractmethod
    async def generate(self, prompt: str, *, temperature: float = 0.2) -> str:
        """Generate a text completion from the given prompt."""

    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        """Return an embedding vector for the given text."""

    async def is_available(self) -> bool:
        """Quick health-check; override per-provider."""
        try:
            await asyncio.wait_for(self.generate("Say OK"), timeout=15)
            return True
        except Exception:
            return False


# ─────────────────────────────────────────────────────────────────────────────
# Ollama provider
# ─────────────────────────────────────────────────────────────────────────────
class OllamaProvider(LLMProvider):
    name = "ollama"

    def __init__(self):
        from langchain_ollama import OllamaLLM, OllamaEmbeddings

        self._llm = OllamaLLM(
            base_url=settings.ollama_base_url,
            model=settings.llm_model,
            temperature=0.2,
        )
        self._embeddings = OllamaEmbeddings(
            base_url=settings.ollama_base_url,
            model=settings.embedding_model,
        )

    async def generate(self, prompt: str, *, temperature: float = 0.2) -> str:
        self._llm.temperature = temperature
        return await asyncio.to_thread(self._llm.invoke, prompt)

    async def embed(self, text: str) -> list[float]:
        return await asyncio.to_thread(self._embeddings.embed_query, text)

    async def is_available(self) -> bool:
        import httpx

        try:
            async with httpx.AsyncClient(timeout=5) as client:
                r = await client.get(settings.ollama_base_url)
                return r.status_code == 200
        except Exception:
            return False


# ─────────────────────────────────────────────────────────────────────────────
# Gemini provider
# ─────────────────────────────────────────────────────────────────────────────
class GeminiProvider(LLMProvider):
    name = "gemini"

    def __init__(self):
        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY not configured")
        try:
            import google.genai as genai
        except Exception as exc:
            raise RuntimeError(
                "google-genai package is not installed. Install it with 'pip install google-genai'."
            ) from exc

        self._client = genai.Client(api_key=settings.gemini_api_key)
        self._model = settings.gemini_model

    async def generate(self, prompt: str, *, temperature: float = 0.2) -> str:
        try:
            import google.genai as genai
        except Exception as exc:
            raise RuntimeError(
                "google-genai package is not installed. Install it with 'pip install google-genai'."
            ) from exc

        config = genai.types.GenerateContentConfig(temperature=temperature)
        response = await asyncio.to_thread(
            self._client.models.generate_content,
            model=self._model,
            contents=prompt,
            config=config,
        )
        return response.text or ""

    async def embed(self, text: str) -> list[float]:
        try:
            response = await asyncio.to_thread(
                self._client.models.embed_content,
                model="gemini-embedding-001",
                contents=text,
            )
            return response.embeddings[0].values
        except Exception as exc:
            raise RuntimeError(f"Gemini embedding failed: {exc}") from exc

    async def is_available(self) -> bool:
        try:
            result = await asyncio.wait_for(
                self.generate("Say OK"),
                timeout=15,
            )
            return bool(result)
        except Exception:
            return False


# ─────────────────────────────────────────────────────────────────────────────
# Grok provider (xAI – OpenAI-compatible API)
# ─────────────────────────────────────────────────────────────────────────────
class GrokProvider(LLMProvider):
    name = "grok"

    def __init__(self):
        if not settings.xai_api_key:
            raise ValueError("XAI_API_KEY not configured")
        from openai import OpenAI

        self._client = OpenAI(
            api_key=settings.xai_api_key,
            base_url="https://api.x.ai/v1",
        )
        self._model = settings.grok_model

    async def generate(self, prompt: str, *, temperature: float = 0.2) -> str:
        def _call():
            resp = self._client.chat.completions.create(
                model=self._model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
            )
            return resp.choices[0].message.content or ""

        return await asyncio.to_thread(_call)

    async def embed(self, text: str) -> list[float]:
        def _call():
            resp = self._client.embeddings.create(
                model="text-embedding-3-small",
                input=text,
            )
            return resp.data[0].embedding

        return await asyncio.to_thread(_call)

    async def is_available(self) -> bool:
        try:
            result = await asyncio.wait_for(
                self.generate("Say OK"),
                timeout=15,
            )
            return bool(result)
        except Exception:
            return False


# ─────────────────────────────────────────────────────────────────────────────
# Provider registry & singleton orchestrator
# ─────────────────────────────────────────────────────────────────────────────
_PROVIDER_CLASSES: dict[str, type[LLMProvider]] = {
    "ollama": OllamaProvider,
    "gemini": GeminiProvider,
    "grok": GrokProvider,
}

_provider_cache: dict[str, LLMProvider] = {}


def _get_provider(name: str) -> Optional[LLMProvider]:
    """Instantiate a provider lazily and cache it."""
    if name in _provider_cache:
        return _provider_cache[name]
    cls = _PROVIDER_CLASSES.get(name)
    if cls is None:
        logger.warning(f"Unknown AI provider: {name}")
        return None
    try:
        instance = cls()
        _provider_cache[name] = instance
        return instance
    except Exception as e:
        logger.error(f"Failed to initialize provider '{name}': {e}")
        return None


def get_primary_provider() -> Optional[LLMProvider]:
    return _get_provider(settings.ai_primary_provider)


def get_fallback_provider() -> Optional[LLMProvider]:
    if settings.ai_fallback_provider in ("none", ""):
        return None
    return _get_provider(settings.ai_fallback_provider)


# ─────────────────────────────────────────────────────────────────────────────
# Orchestrated calls with automatic failover and retry
# ─────────────────────────────────────────────────────────────────────────────
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

_TRANSIENT_EXCEPTIONS = (
    ConnectionError,
    TimeoutError,
    OSError,
    RuntimeError,
)


async def _call_provider_with_retry(
    provider: LLMProvider,
    method: str,
    *args,
    **kwargs,
):
    """Call a provider method with up to 3 retries and exponential backoff."""

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(_TRANSIENT_EXCEPTIONS),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    async def _inner():
        fn = getattr(provider, method)
        return await fn(*args, **kwargs)

    return await _inner()


async def ai_generate(prompt: str, *, temperature: float = 0.2) -> tuple[str, str]:
    """Generate text using primary provider with automatic fallback.

    Returns:
        (response_text, provider_name)
    """
    primary = get_primary_provider()
    fallback = get_fallback_provider()

    if primary:
        try:
            result = await _call_provider_with_retry(
                primary, "generate", prompt, temperature=temperature,
            )
            return result, primary.name
        except Exception as e:
            logger.warning(f"Primary provider '{primary.name}' failed after retries: {e}")

    if fallback:
        try:
            result = await _call_provider_with_retry(
                fallback, "generate", prompt, temperature=temperature,
            )
            logger.info(f"Fallback provider '{fallback.name}' succeeded.")
            return result, fallback.name
        except Exception as e:
            logger.error(f"Fallback provider '{fallback.name}' also failed: {e}")

    raise RuntimeError("All AI providers are unavailable.")


async def ai_embed(text: str) -> list[float]:
    """Embed text using primary provider with automatic fallback.

    Returns:
        embedding vector
    """
    primary = get_primary_provider()
    fallback = get_fallback_provider()

    if primary:
        try:
            return await _call_provider_with_retry(primary, "embed", text)
        except Exception as e:
            logger.warning(f"Primary embedding provider '{primary.name}' failed after retries: {e}")

    if fallback:
        try:
            return await _call_provider_with_retry(fallback, "embed", text)
        except Exception as e:
            logger.error(f"Fallback embedding provider '{fallback.name}' also failed: {e}")

    raise RuntimeError("All AI embedding providers are unavailable.")


# ─────────────────────────────────────────────────────────────────────────────
# Confidence extraction helper
# ─────────────────────────────────────────────────────────────────────────────
def extract_confidence(answer: str) -> tuple[str, Optional[float]]:
    """Extract a [CONFIDENCE: X.X] tag from the answer if present.

    Returns:
        (cleaned_answer, confidence_float_or_None)
    """
    match = re.search(r"\[CONFIDENCE:\s*([\d.]+)\]", answer)
    if match:
        try:
            score = float(match.group(1))
            cleaned = answer[: match.start()] + answer[match.end() :]
            return cleaned.strip(), min(max(score, 0.0), 1.0)
        except ValueError:
            pass
    return answer, None
