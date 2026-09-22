import json

from singed.openrouter import OpenRouterClient, OpenRouterConfig


class FakeResponse:
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return json.dumps({
            "model": "openai/gpt-5.6-sol",
            "provider": "test-provider",
            "choices": [{"message": {"role": "assistant", "content": "done"}}],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1},
        }).encode()


def test_all_models_use_openrouter_chat_completions(monkeypatch):
    captured = {}

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["authorization"] = request.headers["Authorization"]
        captured["payload"] = json.loads(request.data)
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    client = OpenRouterClient(OpenRouterConfig(api_key="test-key"))
    result = client.chat(
        model="openai/gpt-5.6-sol",
        messages=[{"role": "user", "content": "synthetic prompt"}],
        tools=[],
    )
    assert captured["url"] == "https://openrouter.ai/api/v1/chat/completions"
    assert captured["authorization"] == "Bearer test-key"
    assert captured["payload"]["model"] == "openai/gpt-5.6-sol"
    assert "temperature" not in captured["payload"]
    assert "top_p" not in captured["payload"]
    assert result["provider"] == "test-provider"
