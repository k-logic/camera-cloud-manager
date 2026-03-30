from datetime import datetime, timezone
from sqlalchemy import Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Camera(Base):
    __tablename__ = "cameras"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    camera_key: Mapped[str] = mapped_column(
        String(32), nullable=False, unique=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    pending_command: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    company = relationship("Company", backref="cameras")
    settings = relationship("CameraSettings", back_populates="camera", uselist=False, cascade="all, delete-orphan")
    command_logs = relationship("CommandLog", back_populates="camera", cascade="all, delete-orphan")


class CameraSettings(Base):
    __tablename__ = "camera_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    camera_id: Mapped[int] = mapped_column(Integer, ForeignKey("cameras.id"), nullable=False, unique=True)
    camera_source: Mapped[str] = mapped_column(String(10), nullable=False, default="mipi")
    width: Mapped[int] = mapped_column(Integer, nullable=False, default=1920)
    height: Mapped[int] = mapped_column(Integer, nullable=False, default=1080)
    output_width: Mapped[int] = mapped_column(Integer, nullable=False, default=1920)
    output_height: Mapped[int] = mapped_column(Integer, nullable=False, default=1080)
    fps: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    bitrate: Mapped[int] = mapped_column(Integer, nullable=False, default=4000)
    audio_bitrate: Mapped[str] = mapped_column(String(20), nullable=False, default="128k")
    audio_sample_rate: Mapped[int] = mapped_column(Integer, nullable=False, default=44100)
    audio_channels: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    stream_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    stream_running: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    settings_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    camera = relationship("Camera", back_populates="settings")


class CommandLog(Base):
    __tablename__ = "command_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    camera_id: Mapped[int] = mapped_column(Integer, ForeignKey("cameras.id"), nullable=False)
    command: Mapped[str] = mapped_column(String(50), nullable=False)
    issued_by: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    issued_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    camera = relationship("Camera", back_populates="command_logs")
    user = relationship("User")
