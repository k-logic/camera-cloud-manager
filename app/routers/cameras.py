from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_admin_user, get_current_user
from app.models.user import User
from app.models.company import Company
from app.models.camera import Camera, CameraSettings, CommandLog
from app.services import mqtt_service, redis_service
from app.schemas.camera import (
    CameraCreate, CameraUpdate, CameraResponse, CameraListItem,
    CameraSettingsUpdate, CameraSettingsResponse, CameraDetailResponse,
    CameraStatusResponse,
    CommandLogResponse,
)

router = APIRouter(prefix="/api", tags=["cameras"])


# ============================
# Admin: 全カメラ操作
# ============================

@router.get("/companies/{company_id}/cameras", response_model=list[CameraListItem])
def list_cameras_by_company(
    company_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """企業のカメラ一覧。adminは全企業、企業ユーザーは自社のみ。"""
    if not user.is_admin and user.company_id != company_id:
        raise HTTPException(status_code=403, detail="Access denied")
    cameras = db.query(Camera).filter(Camera.company_id == company_id).order_by(Camera.id).all()
    company = db.query(Company).filter(Company.id == company_id).first()
    company_name = company.name if company else None
    return [
        CameraListItem(
            id=c.id, company_id=c.company_id, name=c.name,
            is_active=c.is_active, company_name=company_name,
        )
        for c in cameras
    ]


@router.post("/companies/{company_id}/cameras", response_model=CameraResponse, status_code=201)
def create_camera(
    company_id: int,
    req: CameraCreate,
    db: Session = Depends(get_db),
    _user: User = Depends(get_admin_user),
):
    """カメラ作成（admin専用）。camera_keyはデバイスに書き込み済みのものを入力。"""
    existing = db.query(Camera).filter(Camera.camera_key == req.camera_key).first()
    if existing:
        raise HTTPException(status_code=400, detail="このCamera Keyは既に登録されています")
    camera = Camera(company_id=company_id, name=req.name, camera_key=req.camera_key)
    db.add(camera)
    db.commit()
    db.refresh(camera)
    # デフォルト設定を自動作成
    settings = CameraSettings(camera_id=camera.id)
    db.add(settings)
    db.commit()
    return camera


@router.get("/cameras/{camera_id}", response_model=CameraDetailResponse)
def get_camera(
    camera_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """カメラ詳細（設定・ステータス込み）。ステータスはRedisから取得。"""
    camera = db.query(Camera).filter(Camera.id == camera_id).first()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    if not user.is_admin and user.company_id != camera.company_id:
        raise HTTPException(status_code=403, detail="Access denied")

    # ステータスはRedisから取得（キーなし=オフライン）
    redis_data = redis_service.get_status(camera_id)
    if redis_data:
        status_response = CameraStatusResponse(
            is_online=True,
            last_seen=redis_data.get("last_seen"),
            stream_running=redis_data.get("stream_running", False),
            stream_fps=redis_data.get("stream_fps"),
            stream_bitrate=redis_data.get("stream_bitrate"),
            stream_started_at=redis_data.get("stream_started_at"),
            stream_quality=redis_data.get("stream_quality"),
            cpu_usage=redis_data.get("cpu_usage"),
            gpu_usage=redis_data.get("gpu_usage"),
            mem_used=redis_data.get("mem_used"),
            mem_total=redis_data.get("mem_total"),
            temperature=redis_data.get("temperature"),
            disk_used=redis_data.get("disk_used"),
            disk_total=redis_data.get("disk_total"),
            uptime=redis_data.get("uptime"),
        )
    else:
        status_response = CameraStatusResponse(
            is_online=False,
            last_seen=None,
            stream_running=False,
        )
        # オフライン時にstream_running=Trueのままなら自動停止
        # （再起動時にRetained Messageで即配信再開するのを防止）
        if camera.settings and camera.settings.stream_running:
            camera.settings.stream_running = False
            camera.settings.settings_version += 1
            db.commit()
            db.refresh(camera.settings)
            mqtt_service.publish_settings(camera.camera_key, camera.settings)

    return CameraDetailResponse(
        id=camera.id,
        company_id=camera.company_id,
        name=camera.name,
        camera_key=camera.camera_key,
        is_active=camera.is_active,
        pending_command=camera.pending_command,
        settings=camera.settings,
        status=status_response,
        created_at=camera.created_at,
        updated_at=camera.updated_at,
    )


@router.put("/cameras/{camera_id}", response_model=CameraResponse)
def update_camera(
    camera_id: int,
    req: CameraUpdate,
    db: Session = Depends(get_db),
    _user: User = Depends(get_admin_user),
):
    """カメラ情報更新（admin専用）"""
    camera = db.query(Camera).filter(Camera.id == camera_id).first()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    if req.name is not None:
        camera.name = req.name
    if req.is_active is not None:
        camera.is_active = req.is_active
    db.commit()
    db.refresh(camera)
    return camera


@router.delete("/cameras/{camera_id}", status_code=204)
def delete_camera(
    camera_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(get_admin_user),
):
    """カメラ削除（admin専用）"""
    camera = db.query(Camera).filter(Camera.id == camera_id).first()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    mqtt_service.clear_retained(camera.camera_key)
    db.delete(camera)
    db.commit()


# ============================
# カメラ設定
# ============================

@router.get("/cameras/{camera_id}/settings", response_model=CameraSettingsResponse)
def get_camera_settings(
    camera_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """カメラ設定取得"""
    camera = db.query(Camera).filter(Camera.id == camera_id).first()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    if not user.is_admin and user.company_id != camera.company_id:
        raise HTTPException(status_code=403, detail="Access denied")
    if not camera.settings:
        raise HTTPException(status_code=404, detail="Settings not found")
    return camera.settings


@router.put("/cameras/{camera_id}/settings", response_model=CameraSettingsResponse)
def update_camera_settings(
    camera_id: int,
    req: CameraSettingsUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """カメラ設定更新（admin or 自社カメラのクライアント、settings_version自動インクリメント）"""
    camera = db.query(Camera).filter(Camera.id == camera_id).first()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    if not user.is_admin and user.company_id != camera.company_id:
        raise HTTPException(status_code=403, detail="Access denied")
    settings = camera.settings
    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found")

    updated = False
    for field in ["camera_source", "width", "height", "output_width", "output_height", "fps", "bitrate", "audio_bitrate", "audio_sample_rate", "audio_channels", "stream_url"]:
        val = getattr(req, field)
        if val is not None:
            setattr(settings, field, val)
            updated = True

    # stream_running (desired state)
    if req.stream_running is not None and req.stream_running != settings.stream_running:
        if req.stream_running and not settings.stream_url:
            raise HTTPException(status_code=400, detail="配信URLが設定されていません")
        settings.stream_running = req.stream_running
        updated = True
        command = "start" if req.stream_running else "stop"
        db.add(CommandLog(camera_id=camera.id, command=command, issued_by=user.id))

    if updated:
        settings.settings_version += 1

    db.commit()
    db.refresh(settings)

    if updated:
        mqtt_service.publish_settings(camera.camera_key, settings)

    return settings


# ============================
# 配信制御
# ============================


@router.get("/cameras/{camera_id}/commands", response_model=list[CommandLogResponse])
def get_command_logs(
    camera_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """コマンド履歴取得"""
    camera = db.query(Camera).filter(Camera.id == camera_id).first()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    if not user.is_admin and user.company_id != camera.company_id:
        raise HTTPException(status_code=403, detail="Access denied")

    logs = (
        db.query(CommandLog)
        .filter(CommandLog.camera_id == camera_id)
        .order_by(CommandLog.issued_at.desc())
        .limit(50)
        .all()
    )
    return logs
