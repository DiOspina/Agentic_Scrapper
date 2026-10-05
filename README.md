# Agenttic AI Orchestration System

> A production-ready multi-agent AI orchestration platform for real-time data analysis and workflow automation.

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Agenttic Platform                        │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐   │
│  │ Scraper  │─▶│ Analyst  │─▶│Synthesizer│─▶│  Dashboard   │   │
│  │  Agent   │  │  Agent   │  │  Agent   │  │   (React)    │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────┘   │
│       │            │            │              ▲                │
│       ▼            ▼            ▼              │                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              LangGraph Orchestrator                       │  │
│  └──────────────────────────────────────────────────────────┘  │
│       │            │            │              │                │
│       ▼            ▼            ▼              ▼                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐   │
│  │ PostgreSQL│  │  Qdrant  │  │   n8n    │  │  Prometheus  │   │
│  │  +pgvector│  │  Vector  │  │ Workflows│  │  Monitoring  │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## ✨ Features

### 🤖 Multi-Agent System
- **Scraper Agent**: Dynamic web scraping with Playwright (JS rendering, tables, structured data)
- **Analyst Agent (RAG)**: Document processing with embeddings, key metrics extraction, pattern detection
- **Synthesizer Agent**: Executive report generation (JSON, Markdown, HTML)

### ⚙️ Workflow Automation (n8n)
- Visual workflow builder
- Webhook triggers
- Scheduled executions
- Multi-channel notifications (Email, Telegram, WhatsApp, Slack)

### 📊 Real-time Dashboard
- Execution monitoring & logs
- Document management with vector search
- Conversational RAG chat
- Analytics & metrics visualization

### 🔧 Technical Stack
| Layer | Technology |
|-------|------------|
| Backend | Python 3.11, FastAPI, LangChain, LangGraph |
| Vector DB | Qdrant / PostgreSQL + pgvector |
| Cache | Redis |
| Workflow | n8n |
| Frontend | React 18, TypeScript, TailwindCSS, Recharts |
| Monitoring | Prometheus, Grafana |
| Deployment | Docker Compose |

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- 8GB+ RAM recommended
- API keys for LLM providers (OpenAI/Anthropic)

### 1. Clone & Configure
```bash
git clone https://github.com/your-org/agenttic.git
cd agenttic
cp .env.example .env
# Edit .env with your API keys
```

### 2. Start Services
```bash
docker-compose up -d
```

### 3. Access Services
| Service | URL | Credentials |
|---------|-----|-------------|
| **Frontend Dashboard** | http://localhost:3000 | - |
| **Backend API** | http://localhost:8000 | - |
| **API Docs (Swagger)** | http://localhost:8000/docs | - |
| **n8n Workflows** | http://localhost:5678 | admin / admin123 |
| **Grafana** | http://localhost:3001 | admin / admin123 |
| **Prometheus** | http://localhost:9090 | - |
| **Qdrant** | http://localhost:6333 | - |

## 📁 Project Structure

```
agenttic/
├── backend/                 # FastAPI Backend
│   ├── app/
│   │   ├── agents/         # Multi-agent implementations
│   │   │   ├── base.py     # Base agent classes
│   │   │   ├── scraper.py  # Web scraper agent
│   │   │   ├── analyst.py  # RAG analyst agent
│   │   │   ├── synthesizer.py # Report generator
│   │   │   └── orchestrator.py # LangGraph orchestrator
│   │   ├── api/            # REST API endpoints
│   │   ├── core/           # Configuration
│   │   ├── db/             # Database models & connection
│   │   ├── models/         # SQLAlchemy models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── services/       # Business logic services
│   │   └── main.py         # FastAPI app entry
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/               # React Dashboard
│   ├── src/
│   │   ├── components/     # Reusable UI components
│   │   ├── pages/          # Page components
│   │   ├── services/       # API client
│   │   ├── stores/         # Zustand state management
│   │   ├── types/          # TypeScript types
│   │   └── utils/          # Helper functions
│   ├── Dockerfile
│   └── nginx.conf
│
├── n8n/
│   └── workflows/          # Pre-built workflow templates
│       ├── agenttic-data-pipeline.json
│       └── agenttic-scheduled-scraping.json
│
├── docker/                 # Docker configs
│   ├── prometheus.yml
│   └── grafana/
│       ├── dashboards/
│       └── datasources/
│
├── postgres/
│   └── init/               # DB initialization scripts
│
├── docker-compose.yml
├── .env.example
└── README.md
```

## 🔌 API Usage

### Run Scraper Agent
```bash
curl -X POST http://localhost:8000/api/v1/agents/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "urls": ["https://example.com"],
    "config": {"max_pages": 5, "max_depth": 2}
  }'
```

### Run Analyst Agent
```bash
curl -X POST http://localhost:8000/api/v1/agents/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "documents": [{"content": "Your document text...", "metadata": {}}],
    "queries": ["What are the key metrics?"],
    "analysis_types": ["summarization", "key_metrics", "anomaly_detection"]
  }'
```

### Run Synthesizer Agent
```bash
curl -X POST http://localhost:8000/api/v1/agents/synthesize \
  -H "Content-Type: application/json" \
  -d '{
    "analysis_results": [...],
    "report_config": {"report_type": "executive_summary", "formats": ["json", "markdown"]}
  }'
```

### Full Pipeline Execution
```bash
curl -X POST http://localhost:8000/api/v1/executions \
  -H "Content-Type: application/json" \
  -d '{
    "execution_type": "full_pipeline",
    "input_data": {
      "urls": ["https://example.com"],
      "queries": ["Summarize findings"]
    }
  }'
```

### Chat with RAG
```bash
curl -X POST http://localhost:8000/api/v1/chat/query \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are the key trends in the uploaded documents?",
    "use_rag": true,
    "top_k": 5
  }'
```

## 📦 n8n Workflow Templates

### 1. Data Processing Pipeline
**File**: `n8n/workflows/agenttic-data-pipeline.json`

Trigger: Webhook → Scrape → Analyze → Synthesize → Notify (Telegram/Email/Slack)

### 2. Scheduled Scraping
**File**: `n8n/workflows/agenttic-scheduled-scraping.json`

Trigger: Cron (every 6h) → Get URLs → Scrape Batch → Store → Analyze → Report

### Importing Workflows
1. Open n8n at http://localhost:5678
2. Go to Workflows → Import
3. Select the JSON file
4. Configure credentials (API keys, webhook URLs)
5. Activate the workflow

## 🐳 Docker Compose Services

```yaml
services:
  postgres:      # PostgreSQL 16 + pgvector
  qdrant:        # Vector database
  redis:         # Cache & sessions
  n8n:           # Workflow automation
  backend:       # FastAPI + Agents
  frontend:      # React + Nginx
  prometheus:    # Metrics collection
  grafana:       # Visualization
```

### Scaling
```bash
# Scale backend workers
docker-compose up -d --scale backend=3

# Scale with nginx load balancer (add to docker-compose)
```

## 🔧 Configuration

### Environment Variables (.env)
```bash
# Required
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# n8n
N8N_ENCRYPTION_KEY=your-32-char-key
N8N_API_KEY=your-n8n-api-key

# Database (auto-configured in Docker)
POSTGRES_PASSWORD=secure-password
```

### Agent Configuration
```python
# Scraper
ScrapingConfig(
    max_pages=10,
    max_depth=2,
    follow_links=True,
    extract_tables=True,
    wait_timeout=10000
)

# Analyst
AnalysisConfig(
    analysis_types=[AnalysisType.SUMMARIZATION, AnalysisType.KEY_METRICS],
    chunk_size=1000,
    top_k=5,
    similarity_threshold=0.7
)

# Synthesizer
ReportConfig(
    report_type=ReportType.EXECUTIVE_SUMMARY,
    formats=[ReportFormat.JSON, ReportFormat.MARKDOWN],
    include_charts=True
)
```

## 📈 Monitoring

### Prometheus Metrics
- `agenttic_requests_total` - HTTP request count
- `agenttic_request_duration_seconds` - Request latency
- `agenttic_executions_total` - Execution count by type/status
- `agenttic_execution_duration_seconds` - Execution duration
- `agenttic_agent_duration_seconds` - Agent execution time
- `agenttic_agent_tokens_total` - Token usage
- `agenttic_agent_cost_usd_total` - Cost tracking
- `agenttic_active_executions` - Current running executions

### Grafana Dashboards
Pre-configured dashboard at `docker/grafana/dashboards/agenttic-overview.json`

### Health Checks
```bash
# Backend
curl http://localhost:8000/api/v1/health

# n8n
curl http://localhost:5678/healthz

# All services
docker-compose ps
```

## 🧪 Development

### Backend Development
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium

# Run with hot reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development
```bash
cd frontend
npm install
npm run dev
# Runs on http://localhost:3000 with API proxy to backend
```

### Running Tests
```bash
cd backend
pytest tests/ -v --cov=app

cd ../frontend
npm run lint
npm run build
```

## 📚 API Documentation

Full API docs available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/executions` | Create execution |
| GET | `/api/v1/executions` | List executions |
| GET | `/api/v1/executions/{id}` | Get execution details |
| POST | `/api/v1/documents/upload` | Upload document |
| GET | `/api/v1/documents` | List documents |
| POST | `/api/v1/workflows` | Create workflow |
| POST | `/api/v1/workflows/{id}/execute` | Execute workflow |
| POST | `/api/v1/agents/scrape` | Run scraper |
| POST | `/api/v1/agents/analyze` | Run analyst |
| POST | `/api/v1/agents/synthesize` | Run synthesizer |
| POST | `/api/v1/chat/query` | Chat with RAG |
| GET | `/api/v1/metrics/summary` | System metrics |

## 🔐 Security

- JWT-based authentication
- API key management
- Webhook signature verification
- Rate limiting
- CORS configuration
- Secure headers (Helmet.js equivalent)
- Input validation & sanitization

## 📝 License

MIT License - see LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📞 Support

- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions
- **Email**: support@agenttic.ai

---

**Built with ❤️ for the AI Engineering community**