"""
Simulation API endpoints — PRD Section 37.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.simulation.engine import SimulationEngine
from app.simulation.scenarios import SCENARIOS
from app.schemas.event import CustomEventInject
from app.workers.polling_worker import pause_for_demo

router = APIRouter()
engine = SimulationEngine()


class SimulationStatus(BaseModel):
    running: bool
    scenario: str | None
    progress: int
    latest_event: str | None
    latest_ai_summary: str | None = None
    agent_busy: bool = False


@router.get("/simulation/scenarios")
def list_scenarios():
    """Return available scenarios."""
    return {
        "scenarios": [
            {"id": k, "name": k.replace("_", " ").title()} 
            for k in SCENARIOS.keys()
        ]
    }


@router.get("/simulation/status", response_model=SimulationStatus)
def get_status():
    """Get the current simulation status."""
    return engine.get_status()


@router.post("/simulation/start/{scenario}")
async def start_scenario(scenario: str, db: Session = Depends(get_db)):
    """Start a scenario."""
    try:
        await engine.start_scenario(scenario, db)
        return {"success": True, "message": f"Started scenario {scenario}"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/simulation/demo-crash")
async def start_demo_crash(db: Session = Depends(get_db)):
    """Start the demo crash and pause live polling so prices don't immediately overwrite."""
    try:
        # Pause live polling for 45 seconds (enough time for crash + alert)
        pause_for_demo(duration_seconds=45)
        # Start the dramatic rapid crash
        await engine.start_scenario("rapid_crash", db)
        return {"success": True, "message": "Demo crash started. Polling paused."}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/simulation/stop")
async def stop_simulation():
    """Stop the current simulation."""
    await engine.stop()
    return {"success": True, "message": "Simulation stopped"}


@router.post("/simulation/reset")
async def reset_simulation(db: Session = Depends(get_db)):
    """Reset the simulation state."""
    await engine.reset(db)
    return {"success": True, "message": "Simulation reset"}


@router.post("/simulation/events")
async def inject_event(event: CustomEventInject, db: Session = Depends(get_db)):
    """Inject a custom event immediately."""
    await engine.inject_custom_event(event.model_dump(), db)
    return {"success": True, "message": "Event injected"}
