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

router = APIRouter()
engine = SimulationEngine()


class SimulationStatus(BaseModel):
    running: bool
    scenario: str | None
    progress: int
    latest_event: str | None


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
