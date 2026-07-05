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
- RAG pipeline
- chromaDB
- LLM API

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
   - Copy `example.env` to `.env` and fill values

5. Initialize database
   ```bash
   createdb plantpal
   alembic revision --autogenerate -m "Your migration message"
   alembic upgrade head
   ```

6. Run the app
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

## 🛠️ Development

### Structure
- **Models** (`models/`): SQLAlchemy entities
- **Schemas** (`schemas/`): Pydantic v2 models
- **Routers** (`routers/`): Route handlers per feature
- **Services** (`services/`): Orchestrate domain logic
- **Repositories** (`repositories/`): DB CRUD and queries
- **Templates/Static**: UI pages and assets


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

## 🆘 Support
- Open issues for bugs/requests

---

**Made with ❤️ for plant lovers everywhere**
