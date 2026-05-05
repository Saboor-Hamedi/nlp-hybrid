from fastapi import APIRouter, Depends, Body
from typing import Dict
from api.dependencies import get_async_db, get_nlp_model
from db.operations.AsyncDocumentManager import AsyncDocumentManager

router = APIRouter(tags=["Maintenance"])

@router.post("/api/maintenance/sweep")
async def forensic_sweep(
    config: Dict[str, bool] = Body(...),
    conn = Depends(get_async_db),
    model = Depends(get_nlp_model)
):
    """
    Trigger a database-wide modular forensic sweep.
    Accepts toggle configuration from the settings modal.
    """
    manager = AsyncDocumentManager(conn, model)
    result = await manager.apply_forensic_sweep(config)
    return result
