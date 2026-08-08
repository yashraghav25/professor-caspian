# SentinelAI

Autonomous Portfolio Monitoring, Impact Analysis & Multi-Channel Alerting Agent.

## Architecture

1. **FastAPI Backend (`/backend`)**: Handles event ingestion, impact calculation, severity scoring, alert management, and agentic LLM (Groq) logic.
2. **Next.js Frontend (`/frontend`)**: Dynamic Glassmorphism UI showing live portfolio values, holdings, and active alerts.
3. **Caspian SDK**: Outbound and inbound (webhook) multi-channel notifications (Email, Telegram).
4. **Database**: Supabase PostgreSQL + SQLAlchemy models.

## Setup

### 1. Database
Ensure your Supabase `DATABASE_URL` is set in the `.env` file (see `.env.example`).

### 2. Backend
Run the backend in a virtual environment:
```bash
cd backend
python -m venv venv
# Windows: .\venv\Scripts\activate
# Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
*Note: The first time the backend runs, it will auto-create the DB tables and seed a default portfolio.*

### 3. Frontend
Run the frontend:
```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at [http://localhost:3000](http://localhost:3000).

## Simulation Engine
SentinelAI includes a powerful simulation engine to trigger market events deterministically.
From the frontend dashboard, you can trigger a "Rapid Crash" scenario to see the real-time impact analysis, severity scoring, and alert generation in action.
