"""Assistant (free-form, RAG) and the LLM layer (providers, retries, validation, errors)."""
import json

import httpx
import pytest
from pydantic import BaseModel

from app.services import llm


def test_assistant_answers_free_form_without_ai(client, student):
    r = client.post("/api/assistant", headers=student, json={"message": "What is a deadlock in operating systems?"})
    assert r.status_code == 200
    body = r.json()
    assert body["meta"]["engine"] == "rules"
    assert "ask one of the questions" not in body["content"].lower()
    assert "deadlock" in body["content"].lower() and body["meta"]["citations"]


def test_assistant_company_question_uses_company_sources(client, student):
    body = client.post("/api/assistant", headers=student, json={"message": "What does the Infosys online test cover?"}).json()
    titles = [c["title"] for c in body["meta"]["citations"]]
    assert titles and titles[0].startswith("Infosys")


def test_assistant_history_is_saved_and_cleared(client, student):
    client.post("/api/assistant", headers=student, json={"message": "hello"})
    hist = client.get("/api/assistant", headers=student).json()
    assert [m["role"] for m in hist[-2:]] == ["user", "assistant"]
    assert client.delete("/api/assistant", headers=student).status_code in (200, 204)
    assert client.get("/api/assistant", headers=student).json() == []


def test_assistant_with_ai_grounds_and_cites(client, student, fake_llm):
    seen = {}

    def handler(body):
        seen["system"] = body["messages"][0]["content"]
        return "The Infosys online test has several sections including pseudocode [1]. Practise one section a day."
    fake_llm.handler = handler
    body = client.post("/api/assistant", headers=student, json={"message": "What does the Infosys online test cover?"}).json()
    assert body["meta"]["engine"] == "llm" and "[1]" in body["content"]
    assert body["meta"]["citations"][0]["title"].startswith("Infosys")
    assert "Never invent company facts" in seen["system"] and "SOURCES" in seen["system"]
    assert fake_llm.calls[0]["url"].startswith("https://generativelanguage.googleapis.com/v1beta/openai")


def test_assistant_ai_error_is_reported_with_fallback(client, student, fake_llm):
    fake_llm.handler = lambda body: httpx.Response(401, text="bad key")
    body = client.post("/api/assistant", headers=student, json={"message": "Explain normalisation"}).json()
    assert body["meta"]["engine"] == "rules" and "API key" in body["meta"]["ai_error"]


class _Pick(BaseModel):
    answer: str
    score: int


def test_structured_validates_and_repairs(fake_llm):
    replies = iter(['{"answer": "x"}', '```json\n{"answer": "fixed", "score": 3}\n```'])
    fake_llm.handler = lambda body: next(replies)
    out = llm.structured("system", "user", _Pick)
    assert out.answer == "fixed" and out.score == 3 and len(fake_llm.calls) == 2


def test_retries_then_succeeds_on_429(fake_llm, monkeypatch):
    monkeypatch.setattr(llm.settings, "llm_max_retries", 2)
    replies = iter([httpx.Response(429, text="slow down"), httpx.Response(503, text="busy"), "done"])
    fake_llm.handler = lambda body: next(replies)
    assert llm.complete([{"role": "user", "content": "hi"}]) == "done"
    assert len(fake_llm.calls) == 3


def test_rate_limit_error_message(fake_llm, monkeypatch):
    monkeypatch.setattr(llm.settings, "llm_max_retries", 1)
    fake_llm.handler = lambda body: httpx.Response(429, text="quota")
    with pytest.raises(llm.LLMError) as e:
        llm.complete([{"role": "user", "content": "hi"}])
    assert "rate limit" in e.value.user_message


def test_json_mode_falls_back_when_unsupported(fake_llm):
    def handler(body):
        if "response_format" in body:
            return httpx.Response(400, text="response_format is not supported")
        return json.dumps({"answer": "ok", "score": 1})
    fake_llm.handler = handler
    assert llm.structured("s", "u", _Pick).answer == "ok"


def test_provider_selection(monkeypatch):
    from app.config import Settings
    s = Settings(llm_provider="auto", gemini_api_key="g", llm_api_key="", secret_key="x" * 40)
    assert s.provider == "gemini" and s.llm_ready and s.llm_endpoint()[2] == "gemini-flash-latest"
    s = Settings(llm_provider="openai", llm_api_key="k", llm_base_url="https://api.example.com/v1", llm_model="m", secret_key="x" * 40)
    assert s.provider == "openai_compatible" and s.llm_endpoint() == ("https://api.example.com/v1", "k", "m")
    s = Settings(llm_provider="auto", gemini_api_key="", llm_api_key="", secret_key="x" * 40)
    assert s.provider == "none" and not s.llm_ready


def test_meta_reports_ai_status_without_secrets(client, fake_llm):
    m = client.get("/api/meta").json()
    assert m["ai_configured"] is True and m["ai_provider"] == "gemini"
    assert "test-key" not in json.dumps(m)
