"""Database models for storage component."""
from __future__ import annotations

import datetime
from typing import Callable, Dict, Optional

from sqlalchemy import DateTime, Float, Integer, String, and_, cast, func, or_, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

ColumnMeta = Dict[str, str]


class Base(DeclarativeBase):
    """Base class for database models."""

    type_annotation_map = {ColumnMeta: JSONB}


class Files(Base):
    """Database model for files."""

    __tablename__ = "files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tier_id: Mapped[int] = mapped_column(Integer)
    camera_identifier: Mapped[str] = mapped_column(String)
    category: Mapped[str] = mapped_column(String)
    path: Mapped[str] = mapped_column(String, unique=True)
    directory: Mapped[str] = mapped_column(String)
    filename: Mapped[str] = mapped_column(String)
    size: Mapped[int] = mapped_column(Integer)
    created_at = mapped_column(
        DateTime(timezone=False),
        server_default=func.now(),  # pylint: disable=not-callable
    )
    updated_at = mapped_column(
        DateTime(timezone=False),
        onupdate=func.now(),  # pylint: disable=not-callable
    )


class FilesMeta(Base):
    """Database model for files metadata.

    Used to store arbitrary metadata about files.
    """

    __tablename__ = "files_meta"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    path: Mapped[str] = mapped_column(String, unique=True)
    meta: Mapped[ColumnMeta] = mapped_column(JSONB)
    created_at = mapped_column(
        DateTime(timezone=False),
        server_default=func.now(),  # pylint: disable=not-callable
    )
    updated_at = mapped_column(
        DateTime(timezone=False),
        onupdate=func.now(),  # pylint: disable=not-callable
    )


class Recordings(Base):
    """Database model for recordings."""

    __tablename__ = "recordings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    camera_identifier: Mapped[str] = mapped_column(String)
    start_time: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=False))
    end_time: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=False), nullable=True
    )
    created_at = mapped_column(
        DateTime(timezone=False),
        server_default=func.now(),  # pylint: disable=not-callable
    )
    updated_at = mapped_column(
        DateTime(timezone=False),
        onupdate=func.now(),  # pylint: disable=not-callable
    )

    trigger_type: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    trigger_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    thumbnail_path: Mapped[str] = mapped_column(String)

    def get_files(
        self, lookback: float, get_session: Callable[[], Session]
    ) -> list[tuple[Files, FilesMeta]]:
        """Get all files for this recording."""
        start = self.start_time.timestamp() - lookback
        if self.end_time is None:
            end = datetime.datetime.now().timestamp()
        else:
            end = self.end_time.timestamp()
        with get_session() as session:
            stmt = (
                select(Files, FilesMeta)
                .join(FilesMeta, Files.path == FilesMeta.path)
                .where(Files.camera_identifier == self.camera_identifier)
                .where(Files.category == "recorder")
                .where(Files.path.endswith(".m4s"))
                .where(
                    or_(
                        # Fetch all files that start within the recording
                        func.substr(Files.filename, 1, 10).between(
                            str(int(start)), str(int(end))
                        ),
                        # Fetch the first file that starts before the recording but
                        # ends during the recording
                        and_(
                            start >= cast(func.substr(Files.filename, 1, 10), Float),
                            start
                            <= cast(func.substr(Files.filename, 1, 10), Float)
                            + cast(FilesMeta.meta["m3u8"]["EXTINF"], Float),
                        ),
                    )
                )
                .order_by(Files.filename.asc())
            )
            fragments = session.execute(stmt)
            return [(row[0], row[1]) for row in fragments]


class Objects(Base):
    """Database model for objects."""

    __tablename__ = "objects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    camera_identifier: Mapped[str] = mapped_column(String)
    label: Mapped[str] = mapped_column(String)
    confidence: Mapped[float] = mapped_column(Float)
    width: Mapped[float] = mapped_column(Float)
    height: Mapped[float] = mapped_column(Float)
    x1: Mapped[float] = mapped_column(Float)
    y1: Mapped[float] = mapped_column(Float)
    x2: Mapped[float] = mapped_column(Float)
    y2: Mapped[float] = mapped_column(Float)
    zone: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at = mapped_column(
        DateTime(timezone=False),
        server_default=func.now(),  # pylint: disable=not-callable
    )
    updated_at = mapped_column(
        DateTime(timezone=False),
        onupdate=func.now(),  # pylint: disable=not-callable
    )


class Motion(Base):
    """Database model for motion."""

    __tablename__ = "motion"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    camera_identifier: Mapped[str] = mapped_column(String)
    start_time: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=False))
    created_at = mapped_column(
        DateTime(timezone=False),
        server_default=func.now(),  # pylint: disable=not-callable
    )
    updated_at = mapped_column(
        DateTime(timezone=False),
        onupdate=func.now(),  # pylint: disable=not-callable
    )
