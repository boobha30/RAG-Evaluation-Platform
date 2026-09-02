import json
from dataclasses import dataclass, field

from app.config import settings
from app.generation import get_client

JUDGE_SYSTEM_PROMPT = (
    "You are a strict fact-checking judge for a retrieval-augmented generation "
    "system. You will be given retrieved context passages and an answer "
    "generated from them. Judge ONLY whether the answer's claims are "
    "supported by the given context — do not use outside knowledge, and do "
    "not judge whether the answer is a good answer to the question.\n\n"
    "Respond with a JSON object with exactly these keys:\n"
    '  "faithfulness_score": float from 0.0 (no claims supported) to 1.0 (all claims supported)\n'
    '  "hallucinated": boolean, true if the answer contains at least one specific claim '
    "not supported by the context\n"
    '  "unsupported_claims": array of short strings, each an unsupported claim '
    "found in the answer (empty array if none)"
)


@dataclass
class JudgeResult:
    faithfulness_score: float
    hallucinated: bool
    unsupported_claims: list[str] = field(default_factory=list)


def _build_prompt(question: str, contexts: list[dict], answer: str) -> str:
    context_block = "\n\n".join(f"[{c['source']}]\n{c['text']}" for c in contexts)
    return (
        f"Context:\n{context_block}\n\n"
        f"Question: {question}\n\n"
        f"Answer to judge:\n{answer}"
    )


def judge_faithfulness(question: str, contexts: list[dict], answer: str) -> JudgeResult:
    client = get_client()
    response = client.chat.completions.create(
        model=settings.judge_model,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
            {"role": "user", "content": _build_prompt(question, contexts, answer)},
        ],
    )
    raw = response.choices[0].message.content
    data = json.loads(raw)
    return JudgeResult(
        faithfulness_score=float(data.get("faithfulness_score", 0.0)),
        hallucinated=bool(data.get("hallucinated", False)),
        unsupported_claims=list(data.get("unsupported_claims", [])),
    )
