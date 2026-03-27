from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.user import User
from app.models.camera import Camera
from app.services.auth_service import decode_token

security = HTTPBearer()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    payload = decode_token(credentials.credentials)
    if not payload or payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = db.query(User).filter(User.id == int(payload["sub"])).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user")
    return user


def get_admin_user(user: User = Depends(get_current_user)) -> User:
    """管理者専用エンドポイント用"""
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user


def get_client_user(user: User = Depends(get_current_user)) -> User:
    """企業ユーザー専用エンドポイント用"""
    if user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Client access only")
    if not user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No company assigned")
    return user


def get_camera_by_key(
    x_camera_key: str = Header(..., alias="X-Camera-Key"),
    db: Session = Depends(get_db),
) -> Camera:
    """カメラキーヘッダーでカメラデバイスを認証"""
    camera = db.query(Camera).filter(Camera.camera_key == x_camera_key).first()
    if not camera:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid camera key")
    if not camera.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Camera is deactivated")
    return camera
