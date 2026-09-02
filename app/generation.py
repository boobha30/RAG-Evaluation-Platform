from dataclasses import dataclass
from functools import lru_cache

from openai import OpenAI

from app.config import settings

SYSTEM_PROMPT = (
    "You are a helpful assistant answering questions using only the provided context. "
    "If the context does not contain the answer, say you don't know. "
    "Cite sources inline using their [source] tag."
)


@lru_cache(maxsize=1)
def get_client() -> OpenAI:
    return OpenAI(
        api_key=settings.openai_api_key or "local",
        base_url=settings.openai_base_url or None,
    )


def _build_prompt(query: str, contexts: list[dict]) -> str:
    context_block = "\n\n".join(
        f"[{c['source']}]\n{c['text']}" for c in contexts
    )
    return f"Context:\n{context_block}\n\nQuestion: {query}\n\nAnswer:"


@dataclass
class GenerationResult:
    answer: str
    prompt_tokens: int
    completion_tokens: int


def generate_answer(query: str, contexts: list[dict]) -> GenerationResult:
    client = get_client()
    response = client.chat.completions.create(
        model=settings.generation_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": _build_prompt(query, contexts)},
        ],
    )
    usage = response.usage
    return GenerationResult(
        answer=response.choices[0].message.content,
        prompt_tokens=usage.prompt_tokens if usage else 0,
        completion_tokens=usage.completion_tokens if usage else 0,
    )
