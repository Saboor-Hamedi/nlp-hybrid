import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from api.routers import home, search, topics, modeling
from db.db_connection import get_db_pool
from api.dependencies import templates

# Initialize Core API
app = FastAPI(
    title="Signal Forensic Suite", 
    description="High-performance, asynchronous NLP Document Analytics & Forensic Search API.",
    version="2.1.0"
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global catch-all for unhandled system exceptions."""
    err_msg = str(exc)
    print(f"🔥 CRITICAL SYSTEM ERROR: {err_msg}")
    
    # Check if request is for API
    is_api = request.url.path.startswith("/api/")
    
    if is_api:
        return JSONResponse(
            status_code=500,
            content={
                "message": "Neural Engine Error", 
                "detail": "Database connection pool is cycling. Please retry in a moment." if "pool is closing" in err_msg else err_msg
            }
        )
    
    # Fallback for HTML pages
    return templates.TemplateResponse("pages/content.html", {
        "request": request,
        "error": f"Forensic Engine Failure: {err_msg}"
    })

# Static Asset Configuration
app.mount("/static", StaticFiles(directory="static"), name="static")

# Module Registration (APIRouter)
from api.routers import home, topics, search, crud, synthesis, modeling, maintenance
app.include_router(synthesis.router)
app.include_router(search.router)
app.include_router(topics.router)
app.include_router(modeling.router)
app.include_router(maintenance.router)
app.include_router(crud.router)
app.include_router(home.router)

from db.operations.AsyncDocumentManager import AsyncDocumentManager

@app.on_event("startup")
async def startup_event():
    """Verify database connectivity and initialize forensic logic."""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        # Initialize the Modular Forensic Engine
        manager = AsyncDocumentManager(conn, None) # No model needed for SQL init
        await manager.initialize_engine()
    print("🚀 Neural Forensic Suite - System Ready.")

@app.on_event("shutdown")
async def shutdown_event():
    """Gracefully release database resources."""
    pool = await get_db_pool()
    if pool:
        await pool.close()
        print("🛑 Async database pool released.")

if __name__ == '__main__':
    # Entry point for development execution
    uvicorn.run("web:app", host="0.0.0.0", port=5000, reload=True)
