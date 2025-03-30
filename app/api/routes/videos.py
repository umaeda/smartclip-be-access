from typing import List, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.logger import get_logger

logger = get_logger("videos")

from app.api.deps import get_db, has_permission, get_current_verified_user
from app.core.exceptions import VideoNotValidatedException
from app.core.csrf import csrf_protect
from app.models.user import User
from app.models.video import Video
from app.schemas.video import VideoCreate, Video as VideoSchema

router = APIRouter()

@router.post("/", response_model=VideoSchema, dependencies=[Depends(csrf_protect())])
def create_video(
    *,
    db: Session = Depends(get_db),
    video_in: VideoCreate,
    current_user: User = Depends(has_permission("criar_videos"))
) -> Any:
    """Create a new video"""
    
    # Create video object
    video = Video(
        title=video_in.title,
        description=video_in.description,
        url=video_in.url,
        is_validated=False,  # Videos start as not validated
        user_id=current_user.id
    )
    
    db.add(video)
    db.commit()
    db.refresh(video)
    
    logger.info(f"Video created: {video.id} by user {current_user.id} - {current_user.email}")
    
    # Business logic: Raise exception if video is not validated
    # This is just to demonstrate the exception, in a real scenario
    # you might have a validation process before allowing access
    if not video.is_validated:
        logger.warning(f"Video not validated: {video.id}")
        raise VideoNotValidatedException()
    
    return video

@router.get("/", response_model=List[VideoSchema])
def get_videos(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
    skip: int = 0,
    limit: int = 100
) -> Any:
    logger.info(f"User {current_user.id} - {current_user.email} requested video list (skip={skip}, limit={limit})")
    """Get all videos for the current user"""
    videos = db.query(Video).filter(Video.user_id == current_user.id).offset(skip).limit(limit).all()
    return videos

@router.get("/{video_id}", response_model=VideoSchema)
def get_video(
    *,
    db: Session = Depends(get_db),
    video_id: int,
    current_user: User = Depends(get_current_verified_user)
) -> Any:
    """Get a specific video by ID"""
    video = db.query(Video).filter(Video.id == video_id, Video.user_id == current_user.id).first()
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found"
        )
    return video