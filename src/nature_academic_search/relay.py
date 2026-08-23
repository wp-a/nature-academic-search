"""Optional OpenAI-compatible HTTP model provider for workflow assistance."""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from typing import Any

import requests


class RelayUnavailable(RuntimeError):
    """Raised when the optional model gateway cannot provide a usable response."""


class OpenAICompatibleRelay:
    """Small HTTP adapter supporting Responses and Chat Completions JSON output."""

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        protocol: str = "responses_http",
        timeout: float = 45.0,
    ) -> None:
        if protocol not in {"responses_http", "chat_completions"}:
            raise ValueError("protocol must be 'responses_http' or 'chat_completions'")
        if not api_key.strip():
            raise ValueError("api_key must not be empty")
        if not model.strip():
            raise ValueError("model must not be empty")
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.protocol = protocol
        self.timeout = timeout

    @classmethod
    def from_env(cls) -> OpenAICompatibleRelay | None:
        api_key = os.environ.get("ACADEMIC_SEARCH_LLM_API_KEY", "").strip()
        model = os.environ.get("ACADEMIC_SEARCH_LLM_MODEL", "").strip()
        if not api_key or not model:
            return None
        return cls(
            base_url=os.environ.get(
                "ACADEMIC_SEARCH_LLM_BASE_URL", "https://api.wpironman.top/v1"
            ),
            api_key=api_key,
            model=model,
            protocol=os.environ.get("ACADEMIC_SEARCH_LLM_PROTOCOL", "responses_http"),
            timeout=float(os.environ.get("ACADEMIC_SEARCH_LLM_TIMEOUT", "45")),
        )

    def generate_json(
        self,
        task: str,
        payload: Mapping[str, Any],
        *,
        allow_full_text: bool = False,
    ) -> dict[str, Any]:
        safe_payload = _sanitize_payload(payload, allow_full_text=allow_full_text)
        prompt = (
            "You are an evidence-preserving research workflow assistant. "
            "Return one valid JSON object and no markdown fences.\n"
            f"Task: {task}\nPayload:\n{json.dumps(safe_payload, ensure_ascii=False)}"
        )
        for attempt in range(2):
            if attempt:
                prompt += "\nYour previous response was invalid. Return JSON only."
            body = self._request_body(prompt)
            response = self._post(body)
            text = _extract_text(response)
            try:
                parsed = json.loads(text)
            except (TypeError, json.JSONDecodeError) as exc:
                if attempt == 0:
                    continue
                raise RelayUnavailable("Relay returned malformed JSON") from exc
            if not isinstance(parsed, dict):
                if attempt == 0:
                    continue
                raise RelayUnavailable("Relay returned a JSON value, not an object")
            return parsed
        raise RelayUnavailable("Relay returned malformed JSON")

    def _request_body(self, prompt: str) -> dict[str, Any]:
        if self.protocol == "chat_completions":
            return {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "response_format": {"type": "json_object"},
            }
        return {
            "model": self.model,
            "input": [{"role": "user", "content": [{"type": "input_text", "text": prompt}]}],
            "text": {"format": {"type": "json_object"}},
        }

    def _post(self, body: Mapping[str, Any]) -> Any:
        endpoint = "/responses" if self.protocol == "responses_http" else "/chat/completions"
        try:
            response = requests.post(
                f"{self.base_url}{endpoint}",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=dict(body),
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise RelayUnavailable("Relay request failed") from exc
        if response.status_code in {401, 403, 404, 408, 409, 429} or response.status_code >= 500:
            raise RelayUnavailable(f"Relay unavailable (HTTP {response.status_code})")
        if response.status_code >= 400:
            raise RelayUnavailable(f"Relay rejected request (HTTP {response.status_code})")
        try:
            return response.json()
        except ValueError as exc:
            raise RelayUnavailable("Relay returned malformed response") from exc


def _extract_text(response: Any) -> str:
    if isinstance(response, dict):
        output_text = response.get("output_text")
        if isinstance(output_text, str):
            return output_text
        choices = response.get("choices")
        if isinstance(choices, list) and choices and isinstance(choices[0], dict):
            message = choices[0].get("message")
            if isinstance(message, dict) and isinstance(message.get("content"), str):
                return message["content"]
        output = response.get("output")
        if isinstance(output, list):
            for item in output:
                if not isinstance(item, dict):
                    continue
                content = item.get("content")
                if isinstance(content, list):
                    for block in content:
                        if isinstance(block, dict) and isinstance(block.get("text"), str):
                            return block["text"]
    raise RelayUnavailable("Relay response did not contain text")


def _sanitize_payload(value: Any, *, allow_full_text: bool, key: str = "") -> Any:
    lowered = key.casefold()
    if not allow_full_text and any(token in lowered for token in ("fulltext", "full_text", "pdf")):
        return None
    if any(
        token in lowered
        for token in ("api_key", "token", "secret", "password", "authorization")
    ):
        return "[REDACTED]"
    if isinstance(value, Mapping):
        output: dict[str, Any] = {}
        for child_key, child_value in value.items():
            sanitized = _sanitize_payload(
                child_value, allow_full_text=allow_full_text, key=str(child_key)
            )
            if sanitized is not None:
                output[str(child_key)] = sanitized
        return output
    if isinstance(value, list):
        return [_sanitize_payload(item, allow_full_text=allow_full_text) for item in value]
    return value
