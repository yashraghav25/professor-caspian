"""
SentinelAI — FastAPI Backend Entry Point

Autonomous Portfolio Monitoring, Impact Analysis & Multi-Channel Alerting Agent.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import init_db
from app.core.logging import setup_logging, get_logger

logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # ── Startup ──
    setup_logging()
    logger.info("SentinelAI starting up...")

    # Initialize database tables
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialized.")

    # Seed default user and portfolio if empty
    _seed_default_data()

    logger.info("SentinelAI ready.")
    yield

    # ── Shutdown ──
    logger.info("SentinelAI shutting down.")


def _seed_default_data():
    """Create a default user and demo portfolio if the DB is empty."""
    from app.core.database import SessionLocal
    from app.models.user import User
    from app.models.portfolio import Portfolio
    from app.models.holding import Holding

    db = SessionLocal()
    try:
        # Check if default user exists
        user = db.query(User).first()
        if user:
            logger.info(f"Default user already exists: {user.email}")
            return

        # Create default user
        user = User(email="investor@sentinel.ai", name="Demo Investor")
        db.add(user)
        db.flush()

        # Create demo portfolio (PRD Section 7.1)
        portfolio = Portfolio(user_id=user.id, name="Main Portfolio", base_currency="USD")
        db.add(portfolio)
        db.flush()

        # Add default holdings — $100,000 portfolio
        demo_holdings = [
            {"symbol": "NVDA", "quantity": 166, "average_price": 120.48, "current_price": 120.48},  # ~20%
            {"symbol": "AAPL", "quantity": 78, "average_price": 192.31, "current_price": 192.31},   # ~15%
            {"symbol": "MSFT", "quantity": 28, "average_price": 428.57, "current_price": 428.57},   # ~12%
            {"symbol": "TSLA", "quantity": 32, "average_price": 250.00, "current_price": 250.00},   # ~8%
            {"symbol": "AMD", "quantity": 31, "average_price": 161.29, "current_price": 161.29},    # ~5%
        ]

        for h in demo_holdings:
            holding = Holding(portfolio_id=portfolio.id, **h)
            db.add(holding)

        # Create default notification preferences
        from app.models.preference import NotificationPreference
        pref = NotificationPreference(user_id=user.id)
        db.add(pref)

        db.commit()
        logger.info("Seeded default user, portfolio, and 5 holdings (~$60k invested, $40k cash).")

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to seed default data: {e}")
    finally:
        db.close()


# ── Create FastAPI App ──
app = FastAPI(
    title="SentinelAI",
    description="Autonomous Portfolio Monitoring, Impact Analysis & Multi-Channel Alerting Agent",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — allow frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Health Check ──
@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "sentinel-ai"}


# ── Register API Routers ──
from app.api import portfolio, alerts, events, simulation, notifications  # noqa: E402

app.include_router(portfolio.router, prefix="/api", tags=["Portfolio"])
app.include_router(alerts.router, prefix="/api", tags=["Alerts"])
app.include_router(events.router, prefix="/api", tags=["Events"])
app.include_router(simulation.router, prefix="/api", tags=["Simulation"])
app.include_router(notifications.router, prefix="/api", tags=["Notifications"])
