"""
SentinelAI — FastAPI Backend Entry Point

Autonomous Portfolio Monitoring, Impact Analysis & Multi-Channel Alerting Agent.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import init_db, SessionLocal
from app.core.logging import setup_logging, get_logger
from app.workers.polling_worker import start_polling, stop_polling
from app.workers.daily_report_worker import start_daily_report_worker, stop_daily_report_worker
from app.caspian.client import get_caspian
from app.caspian.listener import start_caspian_listener, stop_caspian_listener

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

    # Ensure default user exists (but don't seed fake portfolio)
    _ensure_default_user()

    # Initialize Caspian SDK (email + optional telegram)
    get_caspian().initialize()

    # Start live market data polling
    import asyncio
    asyncio.create_task(start_polling())
    asyncio.create_task(start_caspian_listener())
    asyncio.create_task(start_daily_report_worker())

    logger.info("SentinelAI ready.")
    yield

    # ── Shutdown ──
    logger.info("SentinelAI shutting down.")
    await stop_caspian_listener()
    await stop_daily_report_worker()
    await stop_polling()


def _ensure_default_user():
    """Create a default user if none exists."""
    from app.models.user import User
    from app.models.preference import NotificationPreference

    db = SessionLocal()
    try:
        user = db.query(User).first()
        if user:
            return

        user = User(email="investor@sentinel.ai", name="Demo Investor")
        db.add(user)
        db.flush()

        pref = NotificationPreference(
            user_id=user.id,
            warning_channel="email",
            high_channel="telegram",
            critical_channel="telegram,email",
        )
        db.add(pref)

        db.commit()
        logger.info("Created default user (investor@sentinel.ai).")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create default user: {e}")
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
from app.api import portfolio, alerts, events, simulation, notifications, setup  # noqa: E402
from app.caspian import handlers as caspian_handlers  # noqa: E402

app.include_router(setup.router, prefix="/api", tags=["Setup"])
app.include_router(portfolio.router, prefix="/api", tags=["Portfolio"])
app.include_router(alerts.router, prefix="/api", tags=["Alerts"])
app.include_router(events.router, prefix="/api", tags=["Events"])
app.include_router(simulation.router, prefix="/api", tags=["Simulation"])
app.include_router(notifications.router, prefix="/api", tags=["Notifications"])
app.include_router(caspian_handlers.router, prefix="/api", tags=["Caspian"])
