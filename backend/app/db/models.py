"""
SQLAlchemy ORM models for the Inventory Simulation persistence layer.

Tables
------
datasets    – uploaded demand datasets (schema + data)
runs        – simulation run records
run_results – results and metrics produced by a completed run
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    BigInteger,
    ForeignKey,
    Integer,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Dataset(Base):
    """Stores uploaded datasets: inferred schema and raw data (for MVP)."""

    __tablename__ = "datasets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    source_type: Mapped[str] = mapped_column(Text, nullable=False)  # csv | xlsx | json
    schema_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    # data_json is nullable; large datasets may omit it (use storage_uri instead)
    data_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    row_count: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )

    runs: Mapped[list["Run"]] = relationship("Run", back_populates="dataset")


class Run(Base):
    """Records a simulation run configuration and its lifecycle status."""

    __tablename__ = "runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    dataset_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("datasets.id"), nullable=True
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    config_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="created")
    # status values: created | queued | running | done | failed
    progress: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
    started_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )

    dataset: Mapped["Dataset | None"] = relationship("Dataset", back_populates="runs")
    result: Mapped["RunResult | None"] = relationship(
        "RunResult", back_populates="run", uselist=False
    )


class RunResult(Base):
    """Stores the results and metrics produced by a completed simulation run."""

    __tablename__ = "run_results"

    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("runs.id"), primary_key=True
    )
    results_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    metrics_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )

    run: Mapped["Run"] = relationship("Run", back_populates="result")
