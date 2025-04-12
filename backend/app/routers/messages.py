from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import logging
from .. import models, schemas, auth
from ..database import get_db
from sqlalchemy import func
from prometheus_client import Counter, Gauge
from .websockets import broadcast_new_message, broadcast_new_like

# Configure logging
logger = logging.getLogger("messages")

router = APIRouter(
    prefix="/messages",
    tags=["messages"],
    responses={404: {"description": "Not found"}},
)

# Prometheus metrics
MESSAGE_POSTS = Counter('message_posts_total', 'Total number of messages posted')
MESSAGE_LIKES = Counter('message_likes_total', 'Total number of likes given')
ACTIVE_MESSAGES = Gauge('active_messages', 'Number of active messages')

@router.post("/", response_model=schemas.Message, status_code=status.HTTP_201_CREATED)
def create_message(message: schemas.MessageCreate, background_tasks: BackgroundTasks,
                  db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_active_user)):
    # Create new message
    db_message = models.Message(content=message.content, user_id=current_user.id)
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    
    # Process tags
    if message.tags:
        for tag_name in message.tags:
            # Check if tag exists, create if not
            tag = db.query(models.Tag).filter(models.Tag.name == tag_name).first()
            if not tag:
                tag = models.Tag(name=tag_name)
                db.add(tag)
                db.commit()
                db.refresh(tag)
            
            # Add tag to message
            db_message.tags.append(tag)
        
        db.commit()
        db.refresh(db_message)
    
    # Increment message counter
    MESSAGE_POSTS.inc()
    ACTIVE_MESSAGES.inc()
    
    # Prepare message data for broadcasting
    message_data = {
        "id": db_message.id,
        "content": db_message.content,
        "user_id": db_message.user_id,
        "created_at": db_message.created_at.isoformat(),  # Convert datetime to ISO format string
        "username": current_user.username,
        "like_count": 0,
        "tags": [{"id": tag.id, "name": tag.name} for tag in db_message.tags]
    }
    # Add the broadcast task to background tasks
    logger.info(f"Adding broadcast task for new message: {db_message.id}")
    logger.info(f"Message data to broadcast: {message_data}")
    
    # Check if we have active WebSocket connections
    from .websockets import manager
    logger.info(f"Current active WebSocket connections: {len(manager.active_connections)}")
    
    background_tasks.add_task(broadcast_new_message, message_data)
    
    
    return db_message

@router.get("/", response_model=List[schemas.MessageWithUser])
def read_messages(skip: int = 0, limit: int = 100, tag: str = None, db: Session = Depends(get_db)):
    # Base query
    query = db.query(
        models.Message,
        models.User.username,
        func.count(models.likes.c.user_id).label("like_count")
    ).join(
        models.User, models.Message.user_id == models.User.id
    ).outerjoin(
        models.likes, models.Message.id == models.likes.c.message_id
    ).group_by(
        models.Message.id, models.User.username
    )
    
    # Filter by tag if provided
    if tag:
        query = query.join(
            models.message_tags, models.Message.id == models.message_tags.c.message_id
        ).join(
            models.Tag, models.message_tags.c.tag_id == models.Tag.id
        ).filter(
            models.Tag.name == tag
        )
    
    # Apply pagination
    messages = query.order_by(models.Message.created_at.desc()).offset(skip).limit(limit).all()
    
    # Convert to response model
    result = []
    for message, username, like_count in messages:
        message_dict = {
            "id": message.id,
            "content": message.content,
            "user_id": message.user_id,
            "created_at": message.created_at,
            "username": username,
            "like_count": like_count,
            "tags": [{"id": tag.id, "name": tag.name} for tag in message.tags]
        }
        result.append(message_dict)
    
    return result

@router.get("/{message_id}", response_model=schemas.MessageWithUser)
def read_message(message_id: int, db: Session = Depends(get_db)):
    message_data = db.query(
        models.Message,
        models.User.username,
        func.count(models.likes.c.user_id).label("like_count")
    ).join(
        models.User, models.Message.user_id == models.User.id
    ).outerjoin(
        models.likes, models.Message.id == models.likes.c.message_id
    ).filter(
        models.Message.id == message_id
    ).group_by(
        models.Message.id, models.User.username
    ).first()
    
    if message_data is None:
        raise HTTPException(status_code=404, detail="Message not found")
    
    message, username, like_count = message_data
    
    message_dict = {
        "id": message.id,
        "content": message.content,
        "user_id": message.user_id,
        "created_at": message.created_at,
        "username": username,
        "like_count": like_count,
        "tags": [{"id": tag.id, "name": tag.name} for tag in message.tags]
    }
    
    return message_dict

@router.post("/{message_id}/like", response_model=schemas.Like)
def like_message(message_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db),
                current_user: models.User = Depends(auth.get_current_active_user)):
    # Check if message exists
    message = db.query(models.Message).filter(models.Message.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    # Check if user already liked this message
    like = db.query(models.likes).filter(
        models.likes.c.user_id == current_user.id,
        models.likes.c.message_id == message_id
    ).first()
    
    if like:
        raise HTTPException(status_code=400, detail="You already liked this message")
    
    # Add like
    like_data = {"user_id": current_user.id, "message_id": message_id}
    db.execute(models.likes.insert().values(**like_data))
    db.commit()
    
    # Increment like counter
    MESSAGE_LIKES.inc()
    
    # Get the created like with timestamp
    like = db.query(models.likes).filter(
        models.likes.c.user_id == current_user.id,
        models.likes.c.message_id == message_id
    ).first()
    
    # Get message data for the broadcast
    message_data = db.query(
        models.Message,
        models.User.username,
        func.count(models.likes.c.user_id).label("like_count")
    ).join(
        models.User, models.Message.user_id == models.User.id
    ).outerjoin(
        models.likes, models.Message.id == models.likes.c.message_id
    ).filter(
        models.Message.id == message_id
    ).group_by(
        models.Message.id, models.User.username
    ).first()
    
    _, _, like_count = message_data
    
    # Add the broadcast task to background tasks
    like_data = {
        "message_id": message_id,
        "user_id": current_user.id,
        "username": current_user.username,
        "like_count": like_count,
        "timestamp": datetime.now().isoformat()  # Add timestamp in ISO format
    }
    logger.info(f"Adding broadcast task for new like: {message_id}")
    logger.info(f"Like data to broadcast: {like_data}")
    background_tasks.add_task(broadcast_new_like, like_data)
    
    return like

@router.delete("/{message_id}/like", status_code=status.HTTP_204_NO_CONTENT)
def unlike_message(message_id: int, db: Session = Depends(get_db),
                  current_user: models.User = Depends(auth.get_current_active_user)):
    # Check if message exists
    message = db.query(models.Message).filter(models.Message.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    # Check if like exists
    like = db.query(models.likes).filter(
        models.likes.c.user_id == current_user.id,
        models.likes.c.message_id == message_id
    ).first()
    
    if not like:
        raise HTTPException(status_code=404, detail="Like not found")
    
    # Remove like
    db.execute(models.likes.delete().where(
        models.likes.c.user_id == current_user.id,
        models.likes.c.message_id == message_id
    ))
    db.commit()
    
    return None

@router.delete("/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_message(message_id: int, db: Session = Depends(get_db),
                  current_user: models.User = Depends(auth.get_current_active_user)):
    # Check if message exists
    message = db.query(models.Message).filter(models.Message.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    # Check if user is the owner
    if message.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this message")
    
    # Delete message
    db.delete(message)
    db.commit()
    
    # Decrement active messages counter
    ACTIVE_MESSAGES.dec()
    
    return None