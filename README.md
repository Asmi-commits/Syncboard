# ⚡ SyncBoard — Real-Time Collaborative Task Manager

> FastAPI · React · WebSockets · PostgreSQL · Docker · GitHub Actions

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         NGINX (Reverse Proxy)                    │
│          Rate limiting · WebSocket upgrade · Static files        │
└──────────────┬─────────────────────────────┬────────────────────┘
               │ /api/*  /ws/*               │ /*
       ┌───────▼────────┐            ┌────────▼──────────┐
       │  FastAPI (4w)  │            │  React (nginx)     │
       │  JWT Auth      │            │  Zustand store     │
       │  REST + WS     │            │  WS client         │
       └───────┬────────┘            └───────────────────┘
               │
       ┌───────▼─────────┐    ┌─────────────────────┐
       │  PostgreSQL 16   │    │     Redis 7           │
       │  Async SQLAlch.  │    │  Pub/Sub (future)    │
       └─────────────────┘    └─────────────────────┘
```

## Quick Start

🔗 **Live Demo:** [syncboard-frontend-g65z.onrender.com](https://syncboard-frontend-g65z.onrender.com)
### Prerequisites
- Docker 24+ & Docker Compose v2
- Git

### 1. Clone & configure
```bash
git clone https://github.com/youruser/syncboard
cd syncboard
cp .env.example .env
# Edit .env — set SECRET_KEY to a random 32+ char string
```

### 2. Start everything
```bash
docker compose up --build -d
```

App: http://localhost:80  
API docs: http://localhost:8000/docs  
API redoc: http://localhost:8000/redoc

### 3. Development mode (hot reload)
```bash
make dev
# or:
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

## Running Tests
```bash
# All tests with coverage
make test

# Watch mode
make test-watch

# Locally (no Docker)
cd backend
pip install -r requirements.txt
pytest app/tests/ -v --cov=app --cov-report=term-missing
```

## API Endpoints (12 REST + WebSocket)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/auth/register` | ❌ | Register user |
| POST | `/api/auth/login` | ❌ | JWT login |
| POST | `/api/auth/refresh` | ❌ | Refresh token |
| GET | `/api/auth/me` | ✅ | Current user |
| GET/POST | `/api/boards/` | ✅ | List/Create boards |
| GET/PUT/DELETE | `/api/boards/{id}` | ✅ | Board CRUD |
| POST | `/api/boards/{id}/members` | ✅ Admin | Add member |
| POST | `/api/boards/{id}/columns` | ✅ | Create column |
| POST | `/api/tasks/` | ✅ | Create task |
| GET/PUT/DELETE | `/api/tasks/{id}` | ✅ | Task CRUD |
| POST | `/api/tasks/{id}/comments` | ✅ | Add comment |
| POST | `/api/tasks/{id}/labels` | ✅ | Add label |
| WS | `/ws/{board_id}?token=JWT` | ✅ | Real-time sync |

## WebSocket Events

```javascript
// Connect
const ws = new WebSocket(`ws://host/ws/1?token=<JWT>`);

// Server → Client events:
// connection_established, user_joined, user_left
// task_created, task_updated, task_deleted
// comment_added, board_updated, cursor_moved, user_typing

// Client → Server events:
ws.send(JSON.stringify({ type: 'ping' }));
ws.send(JSON.stringify({ type: 'cursor_move', x: 100, y: 200 }));
ws.send(JSON.stringify({ type: 'typing', task_id: 5, is_typing: true }));
```

## CI/CD Pipeline

```
Push to main
    ↓
┌─────────────────┐  ┌──────────────────┐
│  test-backend    │  │  test-frontend    │
│  28 pytest tests │  │  npm build       │
│  ≥90% coverage  │  │  TypeScript check │
└────────┬────────┘  └────────┬─────────┘
         └────────────────────┘
                   ↓
         ┌────────────────────┐
         │  build-push         │
         │  GHCR Docker images │
         └────────┬───────────┘
                   ↓
         ┌────────────────────┐
         │  deploy             │
         │  SSH to production  │
         │  docker compose up  │
         └────────────────────┘
```

## Database Schema

- **users**: JWT auth, bcrypt passwords, roles
- **boards**: Kanban boards with color + visibility
- **board_members**: Role-based access (admin/member/viewer)
- **board_columns**: Ordered columns per board
- **tasks**: Full task with status/priority/due date/position
- **comments**: Task discussions
- **task_labels**: Color-coded tags

## Production Deployment

```bash
# On your server
git clone https://github.com/youruser/syncboard /opt/syncboard
cd /opt/syncboard
cp .env.example .env
# Set SECRET_KEY, update ALLOWED_ORIGINS for your domain
docker compose up -d --build

# SSL with Certbot (recommended)
apt install certbot python3-certbot-nginx
certbot --nginx -d yourdomain.com
```

## GitHub Actions Secrets Required

| Secret | Description |
|--------|-------------|
| `PROD_HOST` | Server IP/hostname |
| `PROD_USER` | SSH username |
| `PROD_SSH_KEY` | Private SSH key |



<img width="1440" height="900" alt="Screenshot 2026-05-03 at 3 59 06 PM" src="https://github.com/user-attachments/assets/972de157-27b2-47e5-a1a9-1abea5e3f564" />
<img width="1440" height="900" alt="Screenshot 2026-05-03 at 3 58 58 PM" src="https://github.com/user-attachments/assets/7c0497d4-5781-4179-905f-46cf89127f1c" />
<img width="1440" height="900" alt="Screenshot 2026-05-03 at 3 56 06 PM" src="https://github.com/user-attachments/assets/7196e253-3aec-497b-8d1d-6e34861a15b7" />

