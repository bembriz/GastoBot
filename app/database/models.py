"""Modelos SQLAlchemy para Gastos IA — 9 tablas del PRD 18."""

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        }
    )


def utcnow() -> datetime:
    return datetime.now(UTC)


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="standard")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failed_attempts: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    password_change_required: Mapped[bool] = mapped_column(Boolean, default=True)

    expense_records: Mapped[list["ExpenseRecord"]] = relationship(back_populates="owner")
    audit_events: Mapped[list["AuditEvent"]] = relationship(
        back_populates="actor", foreign_keys="AuditEvent.actor_id"
    )

    __table_args__ = (CheckConstraint("role IN ('admin', 'standard')", name="ck_users_role"),)


class ExpenseRecord(Base):
    __tablename__ = "expense_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    image_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    transaction_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    amount: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    ticket_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    bank: Mapped[str | None] = mapped_column(String(100), nullable=True)
    transaction_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    confidence_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    group_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    consecutive: Mapped[int | None] = mapped_column(Integer, nullable=True)
    final_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("catalog_cache.id", ondelete="SET NULL"), nullable=True
    )
    account_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("catalog_cache.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="DETECTADO", index=True)
    sheet_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    sheet_row: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_filename: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    owner: Mapped["User"] = relationship(back_populates="expense_records")
    image_file: Mapped["ImageFile | None"] = relationship(back_populates="record")
    extraction_runs: Mapped[list["ExtractionRun"]] = relationship(back_populates="record")
    queue_entry: Mapped["ProcessingQueue | None"] = relationship(back_populates="record")
    sync_info: Mapped["SheetSync | None"] = relationship(back_populates="record")

    __table_args__ = (
        CheckConstraint(
            "status IN ('DETECTADO','ESPERANDO_ARCHIVO_ESTABLE','EN_COLA','ANALIZANDO',"
            "'LISTO_PARA_REVISION','REQUIERE_REVISION','PENDIENTE_DE_ENVIO','ENVIANDO',"
            "'ENVIADO','ACTUALIZANDO','ACTUALIZADO','DUPLICADO_EXACTO',"
            "'DUPLICADO_PROBABLE','ERROR_PROCESAMIENTO','ERROR_SHEETS')",
            name="ck_expense_records_status",
        ),
        CheckConstraint(
            "transaction_type IS NULL OR transaction_type IN ('Transferencia', 'Credito')",
            name="ck_expense_records_transaction_type",
        ),
        Index(
            "ix_expense_records_group_consecutive",
            "group_code",
            "consecutive",
            unique=True,
            postgresql_where=text("group_code IS NOT NULL AND consecutive IS NOT NULL"),
        ),
    )


class ImageFile(Base):
    __tablename__ = "image_files"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    record_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("expense_records.id", ondelete="RESTRICT"), unique=True, nullable=False
    )
    original_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    optimized_path: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    sha256_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    file_size: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    exif_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    owner_folder: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    record: Mapped["ExpenseRecord"] = relationship(back_populates="image_file")

    __table_args__ = (
        CheckConstraint("owner_folder IN ('Ruben', 'Esme')", name="ck_image_files_owner_folder"),
    )


class ExtractionRun(Base):
    __tablename__ = "extraction_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    record_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("expense_records.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    model_name: Mapped[str] = mapped_column(String(50), nullable=False)
    prompt_version: Mapped[str | None] = mapped_column(String(20), nullable=True)
    raw_response: Mapped[str | None] = mapped_column(Text, nullable=True)
    parsed_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    is_valid_json: Mapped[bool] = mapped_column(Boolean, default=False)
    elapsed_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    record: Mapped["ExpenseRecord"] = relationship(back_populates="extraction_runs")


class ProcessingQueue(Base):
    __tablename__ = "processing_queue"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    record_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("expense_records.id", ondelete="RESTRICT"), unique=True, nullable=False
    )
    enqueued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    claimed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    worker_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="EN_COLA")
    priority: Mapped[int] = mapped_column(Integer, default=0)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    record: Mapped["ExpenseRecord"] = relationship(back_populates="queue_entry")

    __table_args__ = (
        Index("ix_processing_queue_fifo", "status", "enqueued_at", "id"),
        CheckConstraint(
            "status IN ('EN_COLA', 'ANALIZANDO', 'COMPLETADO', 'ERROR_PERMANENTE')",
            name="ck_processing_queue_status",
        ),
    )


class CatalogCache(Base):
    __tablename__ = "catalog_cache"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    catalog_type: Mapped[str] = mapped_column(String(20), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("catalog_cache.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    parent: Mapped["CatalogCache | None"] = relationship(
        "CatalogCache", remote_side=[id], back_populates="children"
    )
    children: Mapped[list["CatalogCache"]] = relationship("CatalogCache", back_populates="parent")

    __table_args__ = (
        UniqueConstraint("catalog_type", "code", name="uq_catalog_cache_type_code"),
        Index("ix_catalog_cache_type_active", "catalog_type", "is_active"),
        CheckConstraint("catalog_type IN ('categoria', 'cuenta')", name="ck_catalog_cache_type"),
    )


class SheetSync(Base):
    __tablename__ = "sheet_sync"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    record_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("expense_records.id", ondelete="RESTRICT"), unique=True, nullable=False
    )
    sheet_name: Mapped[str] = mapped_column(String(100), nullable=False)
    sheet_row: Mapped[int] = mapped_column(Integer, nullable=False)
    synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    sync_status: Mapped[str] = mapped_column(String(20), nullable=False)
    sync_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    record: Mapped["ExpenseRecord"] = relationship(back_populates="sync_info")

    __table_args__ = (
        Index("ix_sheet_sync_name_row", "sheet_name", "sheet_row"),
        CheckConstraint(
            "sync_status IN ('inserted', 'updated', 'deleted', 'error')",
            name="ck_sheet_sync_status",
        ),
    )


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    record_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("expense_records.id", ondelete="SET NULL"), nullable=True, index=True
    )
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    old_state: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    new_state: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, index=True
    )

    actor: Mapped["User | None"] = relationship(
        back_populates="audit_events", foreign_keys=[actor_id]
    )


class SystemSetting(Base):
    __tablename__ = "system_settings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )
    updated_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
