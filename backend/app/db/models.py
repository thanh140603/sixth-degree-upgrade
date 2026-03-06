import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Node(Base):
    __tablename__ = "nodes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    page_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, unique=True)

    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    outgoing: Mapped[list["Edge"]] = relationship("Edge", foreign_keys="Edge.src_id", back_populates="src")
    incoming: Mapped[list["Edge"]] = relationship("Edge", foreign_keys="Edge.dst_id", back_populates="dst")


class Edge(Base):
    __tablename__ = "edges"

    src_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("nodes.id", ondelete="CASCADE"), primary_key=True)
    dst_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("nodes.id", ondelete="CASCADE"), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    src: Mapped[Node] = relationship("Node", foreign_keys=[src_id], back_populates="outgoing")
    dst: Mapped[Node] = relationship("Node", foreign_keys=[dst_id], back_populates="incoming")

    __table_args__ = (
        Index("ix_edges_src_id", "src_id"),
        Index("ix_edges_dst_id", "dst_id"),
    )


class CrawlState(Base):
    __tablename__ = "crawl_state"

    node_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("nodes.id", ondelete="CASCADE"), primary_key=True)
    last_crawled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    etag: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_modified: Mapped[str | None] = mapped_column(String(255), nullable=True)
    error_count: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default="0")

    node: Mapped[Node] = relationship("Node")


class CrawlRun(Base):
    __tablename__ = "crawl_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="running")

    nodes_scanned: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default="0")
    nodes_updated: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default="0")
    edges_added: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default="0")

    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        UniqueConstraint("id", name="uq_crawl_runs_id"),
    )

