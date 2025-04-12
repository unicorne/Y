from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from typing import List, Dict
import json
from datetime import datetime
import logging
from .. import models, schemas
from ..database import get_db
import asyncio
from json import JSONEncoder

# Custom JSON encoder to handle datetime objects
class DateTimeEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super(DateTimeEncoder, self).default(obj)
from prometheus_client import Gauge

# Configure logging
logger = logging.getLogger("websockets")

router = APIRouter(
    tags=["websockets"],
)

# Prometheus metrics
ACTIVE_CONNECTIONS = Gauge('websocket_active_connections', 'Number of active WebSocket connections')

# Store active connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        ACTIVE_CONNECTIONS.inc()
        logger.info(f"WebSocket client connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        ACTIVE_CONNECTIONS.dec()
        logger.info(f"WebSocket client disconnected. Total connections: {len(self.active_connections)}")
    async def broadcast(self, message: dict):
        logger.info(f"Broadcasting message to {len(self.active_connections)} clients: {message}")
        if not self.active_connections:
            logger.warning("No active connections to broadcast to!")
            return
            
        # Convert message to JSON string using our custom encoder
        try:
            json_str = json.dumps(message, cls=DateTimeEncoder)
            logger.debug(f"JSON serialized message: {json_str}")
        except Exception as e:
            logger.error(f"Error serializing message to JSON: {str(e)}")
            return
            
        for i, connection in enumerate(self.active_connections):
            try:
                logger.info(f"Sending message to client {i+1}/{len(self.active_connections)}")
                # Send the pre-serialized JSON string instead of the raw message
                await connection.send_text(json_str)
                logger.info(f"Message successfully sent to client {i+1}")
            except Exception as e:
                logger.error(f"Error sending message to client {i+1}: {str(e)}")

manager = ConnectionManager()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    logger.info(f"New WebSocket connection request from: {websocket.client}")
    await manager.connect(websocket)
    logger.info(f"WebSocket connection accepted. Total connections: {len(manager.active_connections)}")
    try:
        while True:
            # Keep the connection alive but also listen for any messages from client
            try:
                # Set a timeout for receiving messages to avoid blocking
                logger.debug(f"Waiting for message from client: {websocket.client}")
                data = await asyncio.wait_for(websocket.receive_text(), timeout=10)
                logger.debug(f"Received message from client: {data}")
                # You could process client messages here if needed
            except asyncio.TimeoutError:
                # This is expected - just continue the loop
                pass
    except WebSocketDisconnect:
        manager.disconnect(websocket)
@router.websocket("/ws/{token}")
async def authenticated_websocket_endpoint(websocket: WebSocket, token: str, db: Session = Depends(get_db)):
    from .. import auth
    logger.info(f"New authenticated WebSocket connection request with token from: {websocket.client}")
    try:
        # Validate the token
        username = auth.get_username_from_token(token)
        logger.info(f"Token validation result for {websocket.client}: username={username}")
        
        if not username:
            logger.warning(f"Invalid token from {websocket.client}, closing connection")
            await websocket.close(code=1008, reason="Invalid token")
            return
        
        
        # Get the user from the database
        user = db.query(models.User).filter(models.User.username == username).first()
        if not user:
            await websocket.close(code=1008, reason="User not found")
            return
            
        logger.info(f"Authenticated WebSocket connection for user: {username}")
        
        # Connect the websocket
        await manager.connect(websocket)
        try:
            while True:
                # Keep the connection alive but also listen for any messages
                try:
                    # Set a timeout for receiving messages to avoid blocking
                    data = await asyncio.wait_for(websocket.receive_text(), timeout=10)
                    logger.debug(f"Received message from user {username}: {data}")
                    # You could process client messages here if needed
                except asyncio.TimeoutError:
                    # This is expected - just continue the loop
                    pass
        except WebSocketDisconnect:
            manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"Error in authenticated websocket: {str(e)}")
        await websocket.close(code=1011, reason="Server error")

# Function to be called from other routers to broadcast updates
async def broadcast_message(message_type: str, data: dict):
    logger.info(f"Broadcasting message of type {message_type}")
    await manager.broadcast({
        "type": message_type,
        "data": data
    })

# Function to broadcast new message
async def broadcast_new_message(message: dict):
    logger.info(f"Broadcasting new message: {message.get('id')}")
    logger.info(f"Active connections before broadcast: {len(manager.active_connections)}")
    
    # Log details about each connection
    for i, conn in enumerate(manager.active_connections):
        logger.info(f"Connection {i+1}: {conn.client}")
    
    await broadcast_message("new_message", message)
    logger.info(f"Broadcast completed for message: {message.get('id')}")

# Function to broadcast new like
async def broadcast_new_like(like: dict):
    logger.info(f"Broadcasting new like for message: {like.get('message_id')}")
    await broadcast_message("new_like", like)