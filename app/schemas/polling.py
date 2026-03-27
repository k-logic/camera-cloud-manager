from pydantic import BaseModel


class StreamStatus(BaseModel):
    running: bool = False
    width: int | None = None
    height: int | None = None
    fps: float | None = None
    bitrate: int | None = None
    stream_time: str | None = None
    stream_quality: str | None = None


class SystemStatus(BaseModel):
    cpu_usage: float | None = None
    gpu_usage: float | None = None
    mem_used: int | None = None
    mem_total: int | None = None
    temperature: float | None = None
    disk_used: float | None = None
    disk_total: float | None = None
    uptime: int | None = None


class PollSyncRequest(BaseModel):
    settings_version: int = 0
    stream_status: StreamStatus = StreamStatus()
    system_status: SystemStatus = SystemStatus()


class PollSettingsData(BaseModel):
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

    model_config = {"from_attributes": True}


class PollSyncResponse(BaseModel):
    camera_id: int
    pending_command: str | None = None
    settings: PollSettingsData | None = None
    poll_interval: int = 10
