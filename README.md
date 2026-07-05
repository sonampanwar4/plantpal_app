# 🌱 PlantPal AI Assistant

A smart, plant-only AI assistant for plant care, Q&A, and management. PlantPal helps you keep your plants healthy with personalized care recommendations, AI-powered diagnosis, and comprehensive plant management tools.

## ✨ Features

### 🌱 Plant Management
- **Plant Profiles**: Create detailed profiles for each plant with species, location, and care requirements
- **Care Tracking**: Log watering, fertilizing, pruning, and other care activities
- **Photo Storage**: Upload and store plant photos for diagnosis and history
- **Care Scheduling**: Set up automated care reminders and tasks

### 🤖 AI-Powered Assistance
- **Plant Diagnosis**: Analyze uploaded photos via AI (RAG-supported)
- **Care Recommendations**: Personalized, context-aware care advice
- **Q&A Chat**: Conversational assistant with session-aware context
- **Conversation History**: Persistent sessions for better continuity

### 📊 Dashboard & Analytics
- **Overview**: See all plants and their status at a glance
- **Care History**: Track activities and health over time
- **Task Management**: Create/complete scheduled care tasks

### 🔐 User Management
- **Auth**: Registration, login, and logout
- **Profiles**: Store user preferences and location

## 🏗️ Architecture

PlantPal is built with FastAPI following a layered architecture.

```
plantpal_app/
├── alembic/                 # Database migrations
├── forms/                   # Form parsing/validation
├── models/                  # SQLAlchemy ORM models
├── plant_pal_bot/           # AI bot + RAG pipeline
├── repositories/            # Data access layer
├── routers/                 # Feature routers (FastAPI)
├── schemas/                 # Pydantic models (I/O)
├── services/                # Business logic
├── static/                  # CSS, images, JS
├── templates/               # Jinja2 templates (UI)
├── utils/                   # Helpers, logging, markdown
├── database.py              # DB session + engine
├── main.py                  # FastAPI application
├── settings.py              # App config (env-based)
└── requirements.txt         # Python dependencies
```

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- PostgreSQL 12+
- OpenAI API key

### Installation

1. Clone the repository
   ```bash
   git clone <repository-url>
   cd plantpal_app
   ```

2. Create a virtual environment
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

3. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment
   - Copy `example.env` to `.env` and fill values:
   ```env
   # Database
   db_hostname=localhost
   db_port=5432
   db_username=your_username
   db_password=your_password
   db_name=plantpal

   # Security
   secret_key=your_secret_key_here
   algorithm=HS256
   access_token_expire_minutes=720

   # OpenAI / Embeddings
   open_ai_key=your_openai_api_key
   open_ai_model=gpt-4o-mini            # example
   embedding_model=text-embedding-3-small
   embedding_dim=1536

   # Storage
   gallery_dir=static/gallery
   thumbnail_dir=static/gallery/thumbnails
   ```

5. Initialize database
   ```bash
   createdb plantpal
   alembic upgrade head
   ```

6. Run the app
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

7. Access
   - UI Home: http://localhost:8000
   - Login: http://localhost:8000/login
   - Dashboard: http://localhost:8000/dashboard
   - AI Chat: http://localhost:8000/ai_chat
   - Photo Gallery: http://localhost:8000/photo_gallery
   - API Docs: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## 📚 Endpoints

### Authentication & User
- `GET /register` - Registration form
- `POST /register` - Register user
- `GET /login` - Login form
- `POST /login` - Authenticate user
- `GET /logout` - Logout

### Dashboard & Tasks (`/dashboard`)
- `GET /dashboard/` - Dashboard page
- `POST /dashboard/tasks` - Create care task (JSON)
- `POST /dashboard/tasks/{task_id}/complete` - Complete task (JSON)
- `POST /dashboard/add_plant` - Add plant (form)

### Plants API (`/plants`)
- `GET /plants/` - List current user's plants
- `GET /plants/{plant_id}` - Get plant details
- `PUT /plants/{plant_id}` - Update plant
- `DELETE /plants/{plant_id}` - Delete plant

### AI Chat (`/ai_chat`)
- `GET /ai_chat` - Chat page (renders history, plants)
- `POST /ai_chat` - Send message (supports optional photo upload; AJAX JSON supported)

### Photos & Analysis
- `GET /photo_gallery` - Photo gallery page
- `POST /analyze_photo/{photo_id}` - Analyze a specific photo (returns JSON)
- `DELETE /delete_photo/{photo_id}` - Delete a photo
- `GET /photo/{photo_id}/diagnosis` - Get diagnosis JSON for a photo

#### Integration Helpers
- `GET /api/user_photos?limit=20` - List recent photos with diagnosis flags
- `POST /api/quick_analyze` - Quick analyze most recent photo

## 🛠️ Development

### Structure
- **Models** (`models/`): SQLAlchemy entities
- **Schemas** (`schemas/`): Pydantic v2 models
- **Routers** (`routers/`): Route handlers per feature
- **Services** (`services/`): Orchestrate domain logic
- **Repositories** (`repositories/`): DB CRUD and queries
- **Templates/Static**: UI pages and assets

### Database Schema (high-level)
- `users`, `plants`, `plant_photos`
- `care_logs`, `plant_care_tasks`, `task_completion_history`
- `ai_logs`, `ai_responses`, `conversation_sessions`
- `photo_diagnoses`, `photo_embeddings`, `diagnosis_feedback`

## 📄 Configuration

### Environment Variables
| Variable | Description | Example/Default |
|----------|-------------|-----------------|
| `db_hostname` | DB host | Required |
| `db_port` | DB port | Required |
| `db_username` | DB user | Required |
| `db_password` | DB password | Required |
| `db_name` | DB name | Required |
| `secret_key` | JWT secret | Required |
| `algorithm` | JWT algorithm | HS256 |
| `access_token_expire_minutes` | Token TTL | 720 |
| `open_ai_key` | OpenAI API key | Required |
| `open_ai_model` | Chat model | gpt-4o-mini |
| `embedding_model` | Embedding model | text-embedding-3-small |
| `embedding_dim` | Embedding size | 1536 |
| `gallery_dir` | Photos folder | static/gallery |
| `thumbnail_dir` | Thumbs folder | static/gallery/thumbnails |

## 🤝 Contributing
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/<name>`)
3. Commit (`git commit -m "feat: ..."`), push, open a PR

### Guidelines
- Follow PEP 8 and add type hints
- Write docstrings and tests for new features
- Keep routes thin; prefer services/repositories

## 📄 License
MIT (see `LICENSE`)

## 🆘 Support
- Docs at `/docs`
- Open issues for bugs/requests

---

**Made with ❤️ for plant lovers everywhere**
