from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

import pytest

from nature_academic_search.relay import OpenAICompatibleRelay, RelayUnavailable


def response(payload: object, status_code: int = 200) -> SimpleNamespace:
    return SimpleNamespace(
        status_code=status_code,
        text=str(payload),
        json=lambda: payload,
        raise_for_status=lambda: None,
    )


def test_relay_retries_malformed_json_once_and_returns_structured_payload() -> None:
    responses = [
        response({"output": [{"content": [{"text": "not-json"}]}]}),
        response({"output": [{"content": [{"text": '{"ok": true}' }]}]}),
    ]

    with patch("nature_academic_search.relay.requests.post", side_effect=responses) as post:
        relay = OpenAICompatibleRelay(
            base_url="https://api.wpironman.top/v1",
            api_key="secret-token",
            model="model-a",
            protocol="responses_http",
        )
        result = relay.generate_json("plan", {"question": "q"})

    assert result == {"ok": True}
    assert post.call_count == 2
    assert post.call_args.kwargs["headers"]["Authorization"] == "Bearer secret-token"


def test_relay_unavailable_never_exposes_api_key() -> None:
    with patch(
        "nature_academic_search.relay.requests.post",
        return_value=response({"error": "bad"}, status_code=401),
    ):
        relay = OpenAICompatibleRelay(
            base_url="https://api.wpironman.top/v1",
            api_key="secret-token",
            model="model-a",
        )
        with pytest.raises(RelayUnavailable) as error:
            relay.generate_json("plan", {"question": "q"})

    assert "secret-token" not in str(error.value)
