"""
AI provider layer: one small client for any OpenAI-compatible chat API.

Providers (set in .env, see app/config.py):
  * gemini            Google Gemini through its OpenAI-compatible endpoint (GEMINI_API_KEY)
  * openai_compatible OpenAI, IBM watsonx/Granite gateways, Groq, Ollama ... (LLM_BASE_URL/KEY/MODEL)
  * none              no AI: callers use their rule-based engine and the UI says so

Every structured call asks for JSON and validates it with a Pydantic model. Timeouts,
retries (429 / 5xx / network) and readable error messages are handled here so the
features only deal with "an answer" or "LLMError(user_message)".
"""
import json
import logging
import time
from typing import TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from app.config import settings

log = logging.getLogger("careerpilot.llm")
T = TypeVar("T", bound=BaseModel)
RETRY_STATUS = {408, 409, 429, 500, 502, 503, 504}


class LLMError(Exception):
    """Raised when the AI call cannot produce a valid answer. .user_message is safe to show."""

    def __init__(self, user_message: str, detail: str = ""):
        super().__init__(detail or user_message)
        self.user_message = user_message


def llm_enabled() -> bool:
    return settings.llm_ready


def status() -> dict:
    """What the UI shows about AI (never the key)."""
    if not settings.llm_ready:
        return {"configured": False, "provider": settings.provider, "model": None}
    _, _, model = settings.llm_endpoint()
    return {"configured": True, "provider": settings.provider, "model": model}


def _send(url: str, headers: dict, body: dict, timeout: float) -> httpx.Response:
    """The single network call (tests replace this function with a fake)."""
    return httpx.post(url, headers=headers, json=body, timeout=timeout)


def complete(messages: list[dict], json_mode: bool = False, temperature: float = 0.2, max_tokens: int = 1500) -> str:
    """Send a chat completion and return the text. Raises LLMError."""
    if not settings.llm_ready:
        raise LLMError("AI is not configured on this server.")
    base, key, model = settings.llm_endpoint()
    url = base.rstrip("/") + "/chat/completions"
    body: dict = {"model": model, "messages": messages, "temperature": temperature, "max_tokens": max_tokens}
    if json_mode:
        body["response_format"] = {"type": "json_object"}
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    last = ""
    for attempt in range(settings.llm_max_retries + 1):
        started = time.monotonic()
        try:
            r = _send(url, headers, body, settings.llm_timeout_seconds)
        except httpx.TimeoutException:
            last = "timeout"
            log.warning("LLM timeout after %.1fs (attempt %d)", time.monotonic() - started, attempt + 1)
        except httpx.HTTPError as exc:
            last = f"network: {exc}"
            log.warning("LLM network error (attempt %d): %s", attempt + 1, exc)
        else:
            if r.status_code == 400 and json_mode and "response_format" in r.text:
                body.pop("response_format", None)  # provider does not support JSON mode; ask in the prompt only
                continue
            if r.status_code in (401, 403):
                log.error("LLM rejected the API key (%s)", r.status_code)
                raise LLMError("The AI provider rejected the API key. The site admin needs to check it.", r.text[:300])
            if r.status_code in RETRY_STATUS:
                last = f"http {r.status_code}"
                log.warning("LLM HTTP %s (attempt %d): %s", r.status_code, attempt + 1, r.text[:200])
            elif r.status_code >= 400:
                log.error("LLM HTTP %s: %s", r.status_code, r.text[:300])
                raise LLMError("The AI provider returned an error. Please try again.", r.text[:300])
            else:
                try:
                    content = r.json()["choices"][0]["message"]["content"]
                except (KeyError, IndexError, ValueError, TypeError):
                    last = "bad response shape"
                else:
                    if content and content.strip():
                        log.info("LLM ok in %.1fs (%s)", time.monotonic() - started, model)
                        return content
                    last = "empty answer"
        if attempt < settings.llm_max_retries:
            time.sleep(min(6.0, 0.8 * (2 ** attempt)))
    if last.startswith("http 429"):
        raise LLMError("The AI provider is busy (rate limit). Please wait a minute and try again.", last)
    if last == "timeout":
        raise LLMError("The AI took too long to answer. Please try again.", last)
    raise LLMError("The AI service is not reachable right now. Please try again.", last)


def _extract_json(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = text[text.find("{"):] if "{" in text else text
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end < start:
        raise ValueError("no JSON object in answer")
    return text[start:end + 1]


def structured(system: str, user: str, schema: type[T], temperature: float = 0.2, max_tokens: int = 2000) -> T:
    """Ask for JSON matching `schema`; validate it; one repair attempt. Raises LLMError."""
    hint = json.dumps(schema.model_json_schema())[:6000]
    messages = [
        {"role": "system", "content": system + "\n\nReply with ONE JSON object only (no markdown), matching this JSON schema:\n" + hint},
        {"role": "user", "content": user},
    ]
    for attempt in range(2):
        content = complete(messages, json_mode=True, temperature=temperature, max_tokens=max_tokens)
        try:
            return schema.model_validate_json(_extract_json(content))
        except (ValidationError, ValueError) as exc:
            log.warning("LLM JSON invalid for %s (attempt %d): %s", schema.__name__, attempt + 1, str(exc)[:300])
            messages = messages + [{"role": "assistant", "content": content[:4000]},
                                   {"role": "user", "content": f"That JSON was invalid: {str(exc)[:500]}. Reply again with corrected JSON only."}]
    raise LLMError("The AI answer could not be read. Please try again.")


def try_structured(system: str, user: str, schema: type[T], **kw) -> T | None:
    """Like structured() but returns None when AI is off or fails (caller falls back to rules)."""
    if not settings.llm_ready:
        return None
    try:
        return structured(system, user, schema, **kw)
    except LLMError as exc:
        log.warning("AI fallback to rules: %s", exc)
        return None
