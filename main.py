import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from api.routes import router
from config.settings import settings

# Create FastAPI app
app = FastAPI(
    title="AI Assistant API",
    description="A sophisticated AI assistant with document search capabilities",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router)

# Serve static files
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse("static/favicon.ico")

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    print("🚀 AI Assistant API starting up...")
    print(f"📊 Database: {settings.MONGODB_URI}")
    print(f"🤖 AI Model: {settings.GROQ_MODEL}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("👋 AI Assistant API shutting down...")

# Only run this if the script is executed directly
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.APP_HOST)  # Removing port settings
