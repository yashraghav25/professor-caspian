"""
SentinelAI Configuration

All thresholds, API keys, and settings loaded from environment.
Configurable per PRD Section 76.
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load .env from project root
_env_path = Path(__file__).resolve().parents[3] / ".env"
load_dotenv(_env_path)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # ── Database ──
    database_url: str = "sqlite:///./sentinel.db"

    # ── Groq LLM ──
    groq_api_key: str = ""
    llm_model: str = "llama-3.3-70b-versatile"

    # ── Caspian SDK ──
    caspian_api_key: str = ""
    caspian_base_url: str = "https://api.trycaspianai.com"
    caspian_email_username: str = "sentinel"

    # ── Notification delivery ──
    investor_notify_email: str = "investor@sentinel.ai"
    # Optional safety contact for an unacknowledged high-severity incident.
    # Defaults to the investor address, keeping the demo usable without setup.
    escalation_notify_email: str = ""
    investor_telegram_chat_id: str = ""
    telegram_bot_token: str = ""
    daily_report_hour: int = 18  # 24h UTC hour to send end-of-day email

    # ── Server ──
    backend_port: int = 8000
    frontend_url: str = "http://localhost:3000"

    # ── Severity Thresholds (PRD Section 76) ──
    warning_price_change: float = 5.0
    high_price_change: float = 8.0
    critical_price_change: float = 12.0

    warning_portfolio_impact: float = 1.0
    high_portfolio_impact: float = 2.0
    critical_portfolio_impact: float = 4.0

    # ── Severity Score Weights (PRD Section 31) ──
    # Total should sum to 100
    weight_price_movement: float = 30.0
    weight_velocity: float = 15.0
    weight_portfolio_exposure: float = 25.0
    weight_news_impact: float = 20.0
    weight_confidence: float = 10.0

    # ── Timing ──
    alert_cooldown_seconds: int = 300
    escalation_delay_seconds: int = 120

    @property
    def escalation_recipient(self) -> str:
        return self.escalation_notify_email or self.investor_notify_email

    # ── Severity Score Ranges (PRD Section 30) ──
    info_max: int = 20
    low_max: int = 40
    warning_max: int = 60
    high_max: int = 80
    # 81-100 = CRITICAL

    class Config:
        env_file = ".env"
        case_sensitive = False


# Singleton
settings = Settings()
