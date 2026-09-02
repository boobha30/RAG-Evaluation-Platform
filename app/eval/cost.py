"""Rough USD cost estimates for OpenAI usage, for the dashboard's cost
breakdown. Prices are per-1M-tokens and only cover the models this project
uses by default; update as needed if you change GENERATION_MODEL/JUDGE_MODEL."""

from app.config import settings

PRICE_PER_1M_TOKENS = {
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4o": {"input": 2.50, "output": 10.00},
}

_DEFAULT_PRICE = {"input": 0.15, "output": 0.60}


def estimate_cost_usd(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    # A configured base_url means generation is running against a
    # local/self-hosted OpenAI-compatible server (e.g. Ollama), which is
    # free — OpenAI's per-token pricing doesn't apply there.
    if settings.openai_base_url:
        return 0.0
    price = PRICE_PER_1M_TOKENS.get(model, _DEFAULT_PRICE)
    return (prompt_tokens * price["input"] + completion_tokens * price["output"]) / 1_000_000
