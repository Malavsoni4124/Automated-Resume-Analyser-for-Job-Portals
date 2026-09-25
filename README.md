# Aero ATS — AI-Powered Applicant Tracking System

> An intelligent, multi-tenant applicant tracking system powered by BERT semantic embeddings, multi-dimensional resume scoring, and a real-time React pipeline interface.

---

## 🚀 Features

| Feature | Status |
|---|---|
| AI resume parsing (PDF, DOCX, TXT) | ✅ |
| BERT semantic similarity scoring | ✅ |
| Skill matching with synonym/alias ontology | ✅ |
| Multi-tenant isolation with JWT auth | ✅ |
| Drag-and-drop Kanban pipeline | ✅ |
| Bulk candidate actions (shortlist/hire/reject/delete) | ✅ |
| Duplicate candidate detection | ✅ |
| GitHub profile import | ✅ |
| CSV export | ✅ |
| Analytics dashboard | ✅ |
| Celery async processing with Redis | ✅ |
| Docker Compose deployment | ✅ |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                   React Frontend (Vite)             │
│   Dashboard │ Job Pipeline │ Analytics │ Talent Pool │
└─────────────────────┬───────────────────────────────┘
                      │ REST API
┌─────────────────────▼───────────────────────────────┐
│                  FastAPI Backend                     │
│  Auth │ Jobs │ Candidates │ Analytics │ Bulk Actions │
└──────┬───────────────┬──────────────────────────────┘
       │               │
┌──────▼──────┐  ┌─────▼──────────────────────────────┐
│  SQLite /   │  │  Resume Processing Pipeline         │
│  PostgreSQL │  │  PDF/DOCX → Segmenter → Extractor   │
└─────────────┘  │  → SkillMatcher → BERT Embeddings   │
                 │  → MatchingEngine → Score + Explain  │
                 └──────────────┬─────────────────────┘
                                │
                 ┌──────────────▼──────────────────────┐
                 │  Celery Worker + Redis               │
                 │  (async processing with fallback)    │
                 └─────────────────────────────────────┘
```

---

## ⚡ Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- Redis (optional, for async processing)

### 1. Initial Setup (One-time)

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install backend dependencies
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# Install frontend dependencies
cd frontend && npm install && cd ..
```

### 2. Run the Application

Start both the FastAPI backend and Vite frontend with a single command:

```bash
./start.sh
```

- **Frontend:** http://localhost:5173
- **Backend API Docs:** http://localhost:8000/docs
- **Test Credentials:** `admin@aerocorp.com` / `password123`

---

## 🐳 Docker Deployment

```bash
# Copy and configure environment
cp .env.example .env
# Edit .env with your values

# Start all services
docker-compose up -d

# Access the app
open http://localhost
```

---

## 🔧 Configuration

| Variable | Description | Default |
|---|---|---|
| `DATABASE_URL` | SQLAlchemy DB URL | `sqlite+aiosqlite:///./ats.db` |
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379/0` |
| `JWT_SECRET` | JWT signing secret (CHANGE IN PROD!) | — |
| `GEMINI_API_KEY` | Google Gemini API key for LLM extraction | — |
| `VITE_API_URL` | Frontend → Backend URL | `http://localhost:8000` |

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_api.py -v
pytest tests/test_matching.py -v
```

---

## 📊 Scoring Model

Candidate scores are computed as a weighted composite:

| Dimension | Weight | Description |
|---|---|---|
| Semantic Similarity | 40% | BERT embedding cosine similarity between JD and resume |
| Skill Match | 30% | Canonical skill recall — % of JD skills found in resume (with alias matching) |
| Experience Fit | 20% | Years of experience vs. requirement (with interval union deduplication) |
| Education Fit | 10% | Degree level vs. requirement |

Weights are configurable in `config/matching_weights.yaml`.

---

## 🗂️ Project Structure

```
.
├── src/                    # Backend Python source
│   ├── api/               # FastAPI routes, auth, dependencies
│   ├── database/          # SQLAlchemy models, session
│   ├── extractors/        # Regex, spaCy, Gemini extractors
│   ├── matching/          # MatchingEngine, JDParser, Explainer
│   ├── ontology/          # skills.json — 70+ skills with synonyms
│   ├── parser.py          # ResumeParser orchestrator
│   ├── schema.py          # Pydantic data schemas
│   └── worker/            # Celery task definitions
├── frontend/              # React (Vite) frontend
│   ├── src/
│   │   ├── App.jsx        # Main app (components + routing)
│   │   └── index.css      # Design system tokens + components
│   └── index.html
├── scripts/               # DB migration, seed, fairness audit
├── tests/                 # pytest test suite
├── config/                # matching_weights.yaml
├── docker-compose.yml
└── requirements.txt
```

---

## 🛡️ Security Notes

- **Change `JWT_SECRET`** before any deployment
- Never commit real `.env` files (use `.env.example` as template)
- File upload limit: **10MB** per resume
- Rate limiting enabled via `fastapi-limiter` (configurable)

---

## 📄 License

MIT
