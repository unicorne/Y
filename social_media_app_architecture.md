# Social Media Application Architecture Plan

## Overview

We'll create a social media application with the following components:

1. **Frontend**: Plain JavaScript/HTML/CSS served from a Docker container
2. **Backend**: FastAPI with PostgreSQL database using SQLAlchemy ORM
3. **Authentication**: JWT-based authentication
4. **Real-time Updates**: WebSockets for live feed updates
5. **Containerization**: Docker for all components
6. **Orchestration**: Kubernetes for deployment and scaling
7. **Monitoring**: Prometheus and Grafana for application-specific metrics
8. **Simulated Users**: Simple bots in containers that post and like randomly

## System Architecture

Here's a high-level architecture diagram:

```mermaid
graph TD
    subgraph "Frontend Container"
        FE[HTML/JS/CSS Frontend]
    end
    
    subgraph "Backend Container"
        API[FastAPI Backend]
        WS[WebSocket Server]
    end
    
    subgraph "Database Container"
        DB[(PostgreSQL)]
    end
    
    subgraph "Monitoring"
        P[Prometheus]
        G[Grafana]
    end
    
    subgraph "Bot Containers"
        B1[Bot User 1]
        B2[Bot User 2]
        B3[Bot User 3]
        B4[Bot User n]
    end
    
    FE <--> API
    FE <--> WS
    API <--> DB
    WS <--> DB
    
    API --> P
    P --> G
    
    B1 --> API
    B2 --> API
    B3 --> API
    B4 --> API
```

## Component Details

### 1. Frontend

- Plain HTML/CSS/JavaScript
- Features:
  - User registration and login forms
  - Feed of messages with hashtags
  - Ability to post new messages with tags
  - Ability to like messages
  - Real-time updates via WebSockets
- Docker container with Nginx to serve static files

### 2. Backend

- FastAPI application with the following endpoints:
  - Authentication (register, login)
  - User management
  - Message posting and retrieval
  - Like functionality
- WebSocket endpoint for real-time updates
- SQLAlchemy ORM for database interactions
- Pydantic models for request/response validation
- JWT authentication middleware

### 3. Database

- PostgreSQL database with the following schema:

```mermaid
erDiagram
    USERS {
        int id PK
        string username
        string email
        string password_hash
        datetime created_at
    }
    
    MESSAGES {
        int id PK
        int user_id FK
        string content
        datetime created_at
    }
    
    TAGS {
        int id PK
        string name
    }
    
    MESSAGE_TAGS {
        int message_id FK
        int tag_id FK
    }
    
    LIKES {
        int user_id FK
        int message_id FK
        datetime created_at
    }
    
    USERS ||--o{ MESSAGES : posts
    USERS ||--o{ LIKES : gives
    MESSAGES ||--o{ LIKES : receives
    MESSAGES ||--o{ MESSAGE_TAGS : has
    TAGS ||--o{ MESSAGE_TAGS : belongs_to
```

### 4. Docker Containers

- Frontend container:
  - Nginx serving static files
  - Built with a multi-stage Dockerfile
- Backend container:
  - Python with FastAPI
  - Uvicorn as ASGI server
- Database container:
  - PostgreSQL with persistent volume
- Bot containers:
  - Python scripts that use the API to:
    - Register as users (if needed)
    - Post random messages with random hashtags
    - Like random messages
    - Run on a schedule (e.g., every few minutes)

### 5. Kubernetes Deployment

- Kubernetes manifests for:
  - Deployments for frontend, backend, and database
  - Services for networking
  - ConfigMaps for configuration
  - Secrets for sensitive data
  - Horizontal Pod Autoscaler for scaling bot users
- Basic pod deployment and scaling demonstration

### 6. Monitoring

- Prometheus for metrics collection:
  - Application instrumentation for custom metrics
  - Metrics for user activity, post counts, and like counts
- Grafana for visualization:
  - Dashboards for application metrics
  - User activity trends
  - Content creation and engagement metrics

## Implementation Plan

We'll implement this project in the following phases:

### Phase 1: Core Application Development

1. Set up project structure
2. Implement database models with SQLAlchemy
3. Create FastAPI backend with core endpoints
4. Develop frontend with HTML/CSS/JavaScript
5. Implement JWT authentication
6. Add WebSocket support for real-time updates

### Phase 2: Containerization

1. Create Dockerfiles for each component
2. Set up Docker Compose for local development
3. Implement bot containers with random posting/liking logic
4. Test the complete containerized application locally

### Phase 3: Kubernetes Deployment

1. Create Kubernetes manifests for all components
2. Set up local Kubernetes cluster (e.g., with minikube or kind)
3. Deploy the application to Kubernetes
4. Implement basic pod scaling

### Phase 4: Monitoring

1. Instrument the application with Prometheus metrics
2. Set up Prometheus and Grafana in Kubernetes
3. Create dashboards for application-specific metrics
4. Test monitoring with simulated load

## Directory Structure

```
social-media-app/
├── frontend/
│   ├── public/
│   │   ├── index.html
│   │   ├── styles.css
│   │   ├── app.js
│   │   └── components/
│   ├── Dockerfile
│   └── nginx.conf
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── database.py
│   │   ├── auth.py
│   │   └── routers/
│   │       ├── users.py
│   │       ├── messages.py
│   │       └── websockets.py
│   ├── requirements.txt
│   └── Dockerfile
├── bots/
│   ├── bot.py
│   ├── requirements.txt
│   └── Dockerfile
├── kubernetes/
│   ├── frontend-deployment.yaml
│   ├── backend-deployment.yaml
│   ├── database-deployment.yaml
│   ├── bot-deployment.yaml
│   ├── services.yaml
│   ├── configmaps.yaml
│   ├── secrets.yaml
│   └── monitoring/
│       ├── prometheus-config.yaml
│       ├── prometheus-deployment.yaml
│       ├── grafana-deployment.yaml
│       └── grafana-dashboards/
├── docker-compose.yaml
└── README.md
```

## Technical Considerations

### Authentication Flow

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant Backend
    participant Database
    
    User->>Frontend: Enter credentials
    Frontend->>Backend: POST /auth/login
    Backend->>Database: Verify credentials
    Database-->>Backend: User exists
    Backend->>Backend: Generate JWT
    Backend-->>Frontend: Return JWT
    Frontend->>Frontend: Store JWT in localStorage
    Frontend-->>User: Show authenticated UI
    
    Note over Frontend,Backend: For subsequent requests
    Frontend->>Backend: Request with JWT in header
    Backend->>Backend: Validate JWT
    Backend-->>Frontend: Protected resource
```

### WebSocket Real-time Updates

```mermaid
sequenceDiagram
    participant User1
    participant Frontend1
    participant User2
    participant Frontend2
    participant WebSocketServer
    participant API
    participant Database
    
    User1->>Frontend1: Post new message
    Frontend1->>API: POST /messages
    API->>Database: Save message
    Database-->>API: Success
    API->>WebSocketServer: Notify new message
    WebSocketServer-->>Frontend1: Update feed
    WebSocketServer-->>Frontend2: Update feed
    Frontend2-->>User2: Show new message
```

### Kubernetes Scaling

```mermaid
graph TD
    subgraph "Kubernetes Cluster"
        API1[Backend Pod 1]
        API2[Backend Pod 2]
        API3[Backend Pod n]
        
        SVC[Backend Service]
        
        B1[Bot Pod 1]
        B2[Bot Pod 2]
        B3[Bot Pod 3]
        B4[Bot Pod n]
        
        HPA[Horizontal Pod Autoscaler]
    end
    
    SVC --> API1
    SVC --> API2
    SVC --> API3
    
    B1 --> SVC
    B2 --> SVC
    B3 --> SVC
    B4 --> SVC
    
    HPA --> B1
    HPA --> B2
    HPA --> B3
    HPA --> B4
```

## Learning Outcomes

By completing this project, you'll gain experience with:

1. Building a full-stack web application
2. Working with FastAPI and SQLAlchemy
3. Implementing JWT authentication
4. Using WebSockets for real-time updates
5. Containerizing applications with Docker
6. Deploying to Kubernetes and basic scaling
7. Monitoring application metrics with Prometheus and Grafana
8. Creating simulated users for testing and demonstration