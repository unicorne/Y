# Import necessary libraries
import logging
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware  # For handling Cross-Origin Resource Sharing
from sqlalchemy.orm import Session
from . import models, schemas, auth  # Import our custom modules

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("main")
from .database import engine, get_db  # Database connection and session management
from .routers import users, messages, websockets  # API route modules
from datetime import timedelta
from prometheus_client import make_asgi_app  # For exposing Prometheus metrics

# Initialize the database
# This creates all tables defined in models.py if they don't exist
# In production, you would use migrations instead (e.g., with Alembic)
models.Base.metadata.create_all(bind=engine)

# Create the FastAPI application instance
app = FastAPI(
    title="Social Media API",
    description="A simple social media API with user authentication, messages, and real-time updates"
)

# Add CORS middleware to allow cross-origin requests
# This is necessary for the frontend to communicate with the backend
# when they're served from different origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins for security
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allows all headers
)

# Add Prometheus metrics endpoint
# This exposes a /metrics endpoint that Prometheus can scrape
# to collect application metrics (like request counts, user activity, etc.)
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Include routers from separate modules
# This organizes API endpoints into logical groups
app.include_router(users.router)       # User-related endpoints (register, login, profile)
app.include_router(messages.router)    # Message-related endpoints (create, read, like)
app.include_router(websockets.router)  # WebSocket endpoint for real-time updates

# Authentication endpoint for obtaining JWT tokens
@app.post("/token", response_model=schemas.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    OAuth2 compatible token login, get an access token for future requests
    
    This endpoint:
    1. Receives username and password via form data
    2. Authenticates the user against the database
    3. If valid, generates a JWT token with an expiration time
    4. Returns the token to the client
    """
    # Authenticate user with provided credentials
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        # Return 401 Unauthorized if authentication fails
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Set token expiration time
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Create JWT token with user's username as the subject
    access_token = auth.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    # Return the token and its type
    return {"access_token": access_token, "token_type": "bearer"}

# Root endpoint - simple welcome message
@app.get("/")
async def root():
    """
    Root endpoint that returns a welcome message
    Useful for checking if the API is running
    """
    return {"message": "Welcome to the Social Media API"}

# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Health check endpoint
    Used by monitoring systems and container orchestrators (like Kubernetes)
    to verify the application is running correctly
    """
    return {"status": "healthy"}

# Entry point when running the application directly
if __name__ == "__main__":
    import uvicorn
    # Start the ASGI server with Uvicorn
    # - app.main:app refers to the app variable in app/main.py
    # - host="0.0.0.0" makes the server accessible from any IP
    # - port=8000 is the port the server listens on
    # - reload=True enables auto-reload on code changes (for development)
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)