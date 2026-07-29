import json

import anthropic
from pydantic import BaseModel

MODEL = "claude-opus-5"

_client: anthropic.Anthropic | None = None


def get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic()
    return _client


def _forbid_additional_properties(node) -> None:
    """Recursively set additionalProperties: false on every object schema, including $defs —
    Claude's structured-output mode requires this on all nested objects, not just the top level."""
    if isinstance(node, dict):
        if node.get("type") == "object":
            node["additionalProperties"] = False
        for value in node.values():
            _forbid_additional_properties(value)
    elif isinstance(node, list):
        for item in node:
            _forbid_additional_properties(item)


def _json_schema_for(output_model: type[BaseModel]) -> dict:
    schema = output_model.model_json_schema()
    _forbid_additional_properties(schema)
    return schema


def call_structured(system: str, user: str, output_model: type[BaseModel], effort: str = "high", max_tokens: int = 8000):
    """Single-turn structured-output call using output_config.format. Returns a validated instance of output_model."""
    client = get_client()
    response = client.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        system=system,
        output_config={
            "effort": effort,
            "format": {"type": "json_schema", "schema": _json_schema_for(output_model)},
        },
        messages=[{"role": "user", "content": user}],
    )
    text = next(block.text for block in response.content if block.type == "text")
    return output_model.model_validate(json.loads(text))
