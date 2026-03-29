from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_camera_by_key
from app.models.camera import Camera
from app.schemas.polling import PollSyncRequest, PollSyncResponse, PollSettingsData
from app.services import redis_service

router = APIRouter(prefix="/api/poll", tags=["polling"])


@router.post("/sync", response_model=PollSyncResponse)
def poll_sync(
    req: PollSyncRequest,
    camera: Camera = Depends(get_camera_by_key),
    db: Session = Depends(get_db),
):
    """カメラ→クラウド同期エンドポイント。Jetsonが定期的に呼び出す。"""

    # 全ステータス → Redis
    redis_service.save_status(camera.id, {
        "stream_running": req.stream_status.running,
        "stream_fps": req.stream_status.fps,
        "stream_bitrate": req.stream_status.bitrate,
        "stream_quality": req.stream_status.stream_quality,
        "cpu_usage": req.system_status.cpu_usage,
        "gpu_usage": req.system_status.gpu_usage,
        "mem_used": req.system_status.mem_used,
        "mem_total": req.system_status.mem_total,
        "temperature": req.system_status.temperature,
        "disk_used": req.system_status.disk_used,
        "disk_total": req.system_status.disk_total,
        "uptime": req.system_status.uptime,
    })

    # pending_command取得＆クリア
    pending_command = camera.pending_command
    if pending_command:
        camera.pending_command = None
        db.commit()

    # settings_version比較
    settings_data = None
    if camera.settings and req.settings_version < camera.settings.settings_version:
        settings_data = PollSettingsData.model_validate(camera.settings)

    return PollSyncResponse(
        camera_id=camera.id,
        pending_command=pending_command,
        settings=settings_data,
        poll_interval=2,
    )
