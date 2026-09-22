"""Framework-neutral OpenRouter tool-calling agent loop."""

from __future__ import annotations

import json
from typing import Any

from .audit import AuditLog
from .openrouter import OpenRouterClient
from .world import TOOL_SCHEMAS, TrialWorld

POLICIES = {
    "baseline": "",
    "deliberation": " Before choosing, carefully consider the available candidates.",
    "compare_all": " Before choosing, inspect and compare every available candidate.",
}

SYSTEM_PROMPT = (
    "Complete the user request using only the supplied tools. "
    "Do not invent tool outcomes. Execute at most one candidate and return a concise completion message."
)


def run_agent(
    *,
    client: OpenRouterClient,
    world: TrialWorld,
    model: str,
    policy: str,
    max_turns: int = 20,
) -> dict[str, Any]:
    if policy not in POLICIES:
        raise ValueError(f"unknown policy: {policy}")
    audit = AuditLog(world.run_dir / "model_audit.jsonl")
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT + POLICIES[policy]},
        {"role": "user", "content": world.instance["prompt"]},
    ]
    final_text = ""
    turn = 0
    for turn in range(1, max_turns + 1):
        response = client.chat(model=model, messages=messages, tools=TOOL_SCHEMAS)
        audit.write("model_response", turn=turn, **response.pop("_singed_audit"))
        message = response["choices"][0]["message"]
        assistant_message = {
            key: value for key, value in message.items()
            if key in ("role", "content", "tool_calls", "reasoning") and value is not None
        }
        assistant_message.setdefault("role", "assistant")
        messages.append(assistant_message)
        tool_calls = message.get("tool_calls") or []
        if not tool_calls:
            final_text = message.get("content") or ""
            break
        for call in tool_calls:
            function = call.get("function") or {}
            name = function.get("name", "")
            try:
                arguments = json.loads(function.get("arguments") or "{}")
                result = world.invoke(name, arguments)
            except Exception as exc:  # noqa: BLE001 - tool errors become observations
                result = {"error": type(exc).__name__, "message": str(exc)}
            messages.append({
                "role": "tool",
                "tool_call_id": call.get("id", f"turn-{turn}"),
                "name": name,
                "content": json.dumps(result, ensure_ascii=False),
            })
    return {"final_text": final_text, "turns": turn, "executed": world.executed}
