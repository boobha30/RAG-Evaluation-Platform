from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class EvalRun(Base):
    __tablename__ = "eval_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, default="")
    config_name: Mapped[str] = mapped_column(String)  # e.g. "dense", "hybrid", "hybrid_rerank"
    use_hybrid: Mapped[bool] = mapped_column(Boolean, default=False)
    use_reranker: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    logs: Mapped[list["QueryLog"]] = relationship(back_populates="run")


class QueryLog(Base):
    __tablename__ = "query_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int | None] = mapped_column(ForeignKey("eval_runs.id"), nullable=True)

    query: Mapped[str] = mapped_column(Text)
    answer: Mapped[str] = mapped_column(Text)
    retrieved_sources: Mapped[list] = mapped_column(JSON, default=list)
    retrieved_chunks: Mapped[list] = mapped_column(JSON, default=list)

    # Retrieval metrics (only populated when ground-truth relevant_sources are known,
    # i.e. during a batch eval run against the labeled QA set)
    precision: Mapped[float | None] = mapped_column(Float, nullable=True)
    recall: Mapped[float | None] = mapped_column(Float, nullable=True)
    mrr: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Generation quality metrics
    faithfulness: Mapped[float | None] = mapped_column(Float, nullable=True)
    hallucinated: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    unsupported_claims: Mapped[list] = mapped_column(JSON, default=list)
    relevance: Mapped[float | None] = mapped_column(Float, nullable=True)

    latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    prompt_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    completion_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cost_usd: Mapped[float | None] = mapped_column(Float, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    run: Mapped["EvalRun | None"] = relationship(back_populates="logs")
