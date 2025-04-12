# Social Media Application

A simple social media application with frontend, backend, databases, Docker, Kubernetes, WebSockets, and authentication for learning purposes.

## Overview

This project is a comprehensive social media application that demonstrates various technologies and concepts:

- **Frontend**: Plain JavaScript/HTML/CSS
- **Backend**: Python FastAPI with PostgreSQL database
- **Authentication**: JWT-based authentication
- **Real-time Updates**: WebSockets for live feed updates
- **Containerization**: Docker for all components
- **Orchestration**: Kubernetes for deployment and scaling
- **Monitoring**: Prometheus and Grafana for application metrics
- **Simulated Users**: Bot containers that post and like randomly

## Project Structure

```
social-media-app/
├── frontend/
│   ├── public/
│   │   ├── index.html
│   │   ├── styles.css
│   │   └── app.js
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
│   ├── namespace.yaml
│   ├── configmaps.yaml
│   ├── secrets.yaml
│   ├── database-deployment.yaml
│   ├── backend-deployment.yaml
│   ├── frontend-deployment.yaml
│   ├── bot-deployment.yaml
│   └── monitoring/
│       ├── prometheus-config.yaml
│       ├── prometheus-deployment.yaml
│       ├── grafana-deployment.yaml
│       └── grafana-dashboards/
├── docker-compose.yaml
└── README.md
```

## Features

- User registration and login
- Posting messages with hashtags
- Liking messages
- Real-time feed updates via WebSockets
- Containerized deployment with Docker
- Kubernetes orchestration
- Monitoring with Prometheus and Grafana
- Simulated user activity with bot containers

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Kubernetes cluster (local or remote)
- kubectl CLI tool

### Running with Docker Compose

1. Clone the repository:
   ```
   git clone <repository-url>
   cd social-media-app
   ```

2. Start the application:
   ```
   docker-compose up -d
   ```

3. Access the application:
   - Frontend: http://localhost
   - Backend API: http://localhost:8000
   - Prometheus: http://localhost:9090
   - Grafana: http://localhost:3000 (default credentials: admin/admin)

### Deploying to Kubernetes

1. Create the namespace:
   ```
   kubectl apply -f kubernetes/namespace.yaml
   ```

2. Apply ConfigMaps and Secrets:
   ```
   kubectl apply -f kubernetes/configmaps.yaml
   kubectl apply -f kubernetes/secrets.yaml
   ```

3. Deploy the database:
   ```
   kubectl apply -f kubernetes/database-deployment.yaml
   ```

4. Deploy the backend:
   ```
   kubectl apply -f kubernetes/backend-deployment.yaml
   ```

5. Deploy the frontend:
   ```
   kubectl apply -f kubernetes/frontend-deployment.yaml
   ```

6. Deploy the monitoring stack:
   ```
   kubectl apply -f kubernetes/monitoring/prometheus-deployment.yaml
   kubectl apply -f kubernetes/monitoring/grafana-deployment.yaml
   ```

7. Deploy the bots:
   ```
   kubectl apply -f kubernetes/bot-deployment.yaml
   ```

8. Access the application:
   - Frontend: http://social-media.local (add to your hosts file)
   - Grafana: http://grafana.social-media.local (add to your hosts file)

## Scaling

### Scaling with Docker Compose

```
docker-compose up -d --scale bot=5
```

### Scaling with Kubernetes

```
kubectl scale deployment bot -n social-media --replicas=10
```

## Monitoring

The application includes Prometheus and Grafana for monitoring:

- Prometheus collects metrics from the backend
- Grafana provides dashboards for visualizing metrics

Key metrics include:
- User activity (registrations, logins)
- Message posts and likes
- WebSocket connections
- System resource usage

## Architecture

For a detailed architecture overview, see [social_media_app_architecture.md](social_media_app_architecture.md).

## License

This project is licensed under the MIT License - see the LICENSE file for details.