from datetime import datetime
from pydantic import BaseModel, field_validator


# --- Camera ---
class CameraCreate(BaseModel):
    name: str
    camera_key: str


class CameraUpdate(BaseModel):
    name: str | None = None
    is_active: bool | None = None


class CameraResponse(BaseModel):
    id: int
    company_id: int
    name: str
    camera_key: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CameraListItem(BaseModel):
    id: int
    company_id: int
    name: str
    is_active: bool
    company_name: str | None = None

    model_config = {"from_attributes": True}


# --- Settings ---
class CameraSettingsUpdate(BaseModel):
    camera_source: str | None = None
    width: int | None = None
    height: int | None = None
    output_width: int | None = None
    output_height: int | None = None
    fps: int | None = None
    bitrate: int | None = None
    stream_url: str | None = None
    stream_running: bool | None = None

    @field_validator("stream_url")
    @classmethod
    def validate_stream_url(cls, v):
        if v is not None and not v.startswith(("rtmp://", "rtmps://", "srt://")):
            raise ValueError("配信URLは rtmp:// rtmps:// srt:// で始まる必要があります")
        return v


class CameraSettingsResponse(BaseModel):
    camera_source: str
    width: int
    height: int
    output_width: int
    output_height: int
    fps: int
    bitrate: int
    stream_url: str | None
    stream_running: bool
    settings_version: int
    updated_at: datetime

    model_config = {"from_attributes": True}


# --- Status ---
class CameraStatusResponse(BaseModel):
    is_online: bool
    last_seen: datetime | None
    stream_running: bool
    stream_fps: float | None
    stream_bitrate: int | None
    stream_time: str | None
    stream_quality: str | None
    cpu_usage: float | None
    gpu_usage: float | None
    mem_used: int | None
    mem_total: int | None
    temperature: float | None
    disk_used: float | None
    disk_total: float | None
    uptime: int | None
    updated_at: datetime

    model_config = {"from_attributes": True}


# --- Camera Detail (camera + settings + status) ---
class CameraDetailResponse(BaseModel):
    id: int
    company_id: int
    name: str
    camera_key: str
    is_active: bool
    pending_command: str | None
    settings: CameraSettingsResponse | None
    status: CameraStatusResponse | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# --- Command ---
class CommandRequest(BaseModel):
    command: str = "reboot"


class CommandLogResponse(BaseModel):
    id: int
    camera_id: int
    command: str
    issued_by: int
    issued_at: datetime

    model_config = {"from_attributes": True}
