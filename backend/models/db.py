from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, JSON, String, create_engine, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker


class Base(DeclarativeBase):
    pass


class ProjectRecord(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class OAuthTokenRecord(Base):
    __tablename__ = "oauth_tokens"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    user_email: Mapped[str] = mapped_column(String(255), nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    access_token: Mapped[str] = mapped_column(String(2048), nullable=False)
    refresh_token: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    scope: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


def build_session_factory(database_url: str):
    engine = create_engine(database_url, future=True)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True), engine


def init_database(database_url: str) -> None:
    _, engine = build_session_factory(database_url)
    Base.metadata.create_all(engine)
