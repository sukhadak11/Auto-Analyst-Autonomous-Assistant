from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.auth.routes import router as auth_router
from src.db.database import Base, engine
from src.api import (
    jobs,
    admin,
    files,
    predictions,
    review,
)
#  Create FastAPI application
app = FastAPI(
    title="AutoAnalyst API"
)
# CORS
# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
# DATABASE
#Initialize database
Base.metadata.create_all(
    bind=engine
)
# ROUTES
# Register API routers
app.include_router(
    auth_router
)
app.include_router(
    jobs.router
)
app.include_router(
    admin.router
)
app.include_router(
    files.router
)
app.include_router(
    predictions.router
)
app.include_router(
    review.router
)

# APPLICATION ENTRY POINT
if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
    )