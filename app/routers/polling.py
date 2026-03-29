from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_camera_by_key
from app.models.camera import Camera, CameraStatus
from app.schemas.polling import PollSyncRequest, PollSyncResponse, PollSettingsData

router = APIRouter(prefix="/api/poll", tags=["polling"])


@router.post("/sync", response_model=PollSyncResponse)
def poll_sync(
    req: PollSyncRequest,
    camera: Camera = Depends(get_camera_by_key),
    db: Session = Depends(get_db),
):
    """カメラ→クラウド同期エンドポイント。Jetsonが定期的に呼び出す。"""
    now = datetime.now(timezone.utc)

    # 1. camera_status upsert
    camera_status = camera.status
    if camera_status is None:
        camera_status = CameraStatus(camera_id=camera.id)
        db.add(camera_status)

    camera_status.is_online = True
    camera_status.last_seen = now
    camera_status.stream_running = req.stream_status.running
    camera_status.stream_fps = req.stream_status.fps
    camera_status.stream_bitrate = req.stream_status.bitrate
    camera_status.stream_time = req.stream_status.stream_time
    camera_status.stream_quality = req.stream_status.stream_quality
    camera_status.cpu_usage = req.system_status.cpu_usage
    camera_status.gpu_usage = req.system_status.gpu_usage
    camera_status.mem_used = req.system_status.mem_used
    camera_status.mem_total = req.system_status.mem_total
    camera_status.temperature = req.system_status.temperature
    camera_status.disk_used = req.system_status.disk_used
    camera_status.disk_total = req.system_status.disk_total
    camera_status.uptime = req.system_status.uptime

    # 2. pending_command取得＆クリア
    pending_command = camera.pending_command
    if pending_command:
        camera.pending_command = None

    # 3. settings_version比較
    settings_data = None
    if camera.settings and req.settings_version < camera.settings.settings_version:
        settings_data = PollSettingsData.model_validate(camera.settings)

    # 4. poll_interval決定
    poll_interval = 2

    db.commit()

    return PollSyncResponse(
        camera_id=camera.id,
        pending_command=pending_command,
        settings=settings_data,
        poll_interval=poll_interval,
    )
