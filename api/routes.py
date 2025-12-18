import json
from fastapi import APIRouter, HTTPException, Query, Depends, status, BackgroundTasks
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse, JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from models.schemas import StatsResponse
from db.database import db
from datetime import datetime
import uuid
from bson import ObjectId
from typing import Optional, List
import jwt
from pydantic import BaseModel
import secrets
import logging
import os
from services.data_loader import data_loader

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Password hashing
security = HTTPBearer()

# Pydantic models for requests/responses
class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    full_name: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    full_name: str
    created_at: datetime

class Token(BaseModel):
    access_token: str
    token_type: str
    user: dict

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

class ChatMessage(BaseModel):
    content: str
    session_id: Optional[str] = None

class DocumentUpload(BaseModel):
    filename: str
    content: str
    file_type: str = "text"

# JWT settings
SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"

router = APIRouter()

# Dependency to get current user
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        user = db.get_user(user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.PyJWTError as e:
        logger.error(f"JWT error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

@router.post("/login", response_model=Token)
async def login(login_data: UserLogin):
    """Login user."""
    try:
        user = db.get_user_by_username(login_data.username)
        if not user:
            # Don't reveal that username doesn't exist for security
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password"
            )
        
        if not db.verify_password(login_data.password, user["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password"
            )
        
        # Create token
        token_data = {"sub": str(user["_id"])}
        access_token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": str(user["_id"]),
                "username": user["username"],
                "email": user["email"],
                "role": user["role"]
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed due to server error"
        )

@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """Logout user (client should remove token)."""
    return {"message": "Successfully logged out"}


@router.post("/change-password")
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: dict = Depends(get_current_user)
):
    """Change user password."""
    try:
        # Verify current password
        if not db.verify_password(password_data.current_password, current_user["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Validate new password
        if len(password_data.new_password) < 6:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password must be at least 6 characters long"
            )
        
        # Check if new password is same as current password
        if db.verify_password(password_data.new_password, current_user["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password must be different from current password"
            )
        
        success = db.change_password(str(current_user["_id"]), password_data.new_password)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to change password"
            )
        
        return {"message": "Password changed successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password change error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error changing password"
        )


# Public routes
@router.get("/", response_class=HTMLResponse)
async def read_root():
    """Landing page."""
    try:
        with open("templates/home.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        # Fallback simple landing page
        return HTMLResponse("""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>AI Assistant - Smart Document Chat</title>
            <style>
                * { margin: 0; padding: 0; box-sizing: border-box; }
                body { 
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh; 
                    display: flex; 
                    align-items: center; 
                    justify-content: center;
                    color: white;
                }
                .container { 
                    text-align: center; 
                    padding: 40px; 
                    max-width: 600px;
                }
                h1 { 
                    font-size: 3em; 
                    margin-bottom: 20px; 
                    text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
                }
                p { 
                    font-size: 1.2em; 
                    margin-bottom: 30px; 
                    opacity: 0.9;
                    line-height: 1.6;
                }
                .btn { 
                    display: inline-block; 
                    padding: 15px 30px; 
                    margin: 10px; 
                    background: rgba(255,255,255,0.2); 
                    color: white; 
                    text-decoration: none; 
                    border-radius: 25px; 
                    border: 2px solid rgba(255,255,255,0.3);
                    transition: all 0.3s;
                    font-weight: 600;
                }
                .btn:hover {
                    background: rgba(255,255,255,0.3);
                    transform: translateY(-2px);
                }
                .features {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                    gap: 20px;
                    margin-top: 40px;
                }
                .feature {
                    background: rgba(255,255,255,0.1);
                    padding: 20px;
                    border-radius: 15px;
                    backdrop-filter: blur(10px);
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🤖 AI Assistant</h1>
                <p>Intelligent document search and conversational AI powered by advanced machine learning</p>
                <div>
                    <a href="/dashboard" class="btn">🚀 Get Started</a>
                    <a href="/login" class="btn">🔐 Login</a>
                </div>
                <div class="features">
                    <div class="feature">
                        <h3>🔍 Smart Search</h3>
                        <p>Find answers in your documents instantly</p>
                    </div>
                    <div class="feature">
                        <h3>💬 Natural Conversations</h3>
                        <p>Chat naturally with advanced AI</p>
                    </div>
                    <div class="feature">
                        <h3>📚 Chat History</h3>
                        <p>All your conversations saved securely</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """)

@router.get("/dashboard", response_class=HTMLResponse)
async def admin_dashboard():
    """Admin dashboard page (requires login)"""
    try:
        with open("templates/dashboard.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return HTMLResponse("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Admin Dashboard</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
                .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; }
                .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }
                .stat-card { background: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Admin Dashboard</h1>
                <p>Welcome, Administrator!</p>
                <div class="stats">
                    <div class="stat-card">
                        <h3>Total Users</h3>
                        <p id="total-users">Loading...</p>
                    </div>
                    <div class="stat-card">
                        <h3>Active Sessions</h3>
                        <p id="active-sessions">Loading...</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """)

# Document management endpoints
@router.get("/documents")
async def list_documents(current_user: dict = Depends(get_current_user)): 
    """List all available documents from the database."""
    try:
        all_docs = db.get_all_documents()
        
        # Convert ObjectId to string and format response
        formatted_docs = []
        for doc in all_docs:
            if '_id' in doc:
                doc['_id'] = str(doc['_id'])
            formatted_docs.append({
                "id": doc.get("_id"),
                "name": doc.get("filename", "Unknown"),
                "path": doc.get("file_path", "database"),
                "size": doc.get("file_size", 0),
                "type": doc.get("file_type", "Unknown"),
                "chunks": doc.get("chunk_count", 0),
                "uploaded_at": doc.get("uploaded_at")
            })
        
        return {
            "total_documents": len(formatted_docs),
            "documents": formatted_docs
        }
    except Exception as e:
        logger.error(f"List documents error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error listing documents"
        )
    
# Document load and preprocessing endpoint
@router.post("/data/load")
async def load_data(current_user: dict = Depends(get_current_user)):
    """Load and process all files from the data directory and save results to a JSON file."""
    try:
        results = await data_loader.process_all_files()
        
        # Save results to results.json
        with open('static/results.json', 'w') as json_file:
            json.dump(results, json_file, indent=4)  # indent for pretty formatting
        
        return {
            "message": "Data loading completed and results saved to results.json",
            "results": results
        }
    except Exception as e:
        logging.error(f"Data loading error: {e}")
        raise HTTPException(500, f"Data loading error: {str(e)}")
    
# Get json data from static file 
@router.get("/data/results")
async def get_results(current_user: dict = Depends(get_current_user)):
    # Define the path to your JSON file
    file_path = os.path.join("static", "results.json")
    return FileResponse(file_path)
    
# Search endpoints
@router.get("/search/documents")
async def search_documents(
    query: str = Query(..., description="Search query"),
    limit: int = Query(5, ge=1, le=20, description="Number of results"),
    current_user: dict = Depends(get_current_user)
):
    """Search for documents by content."""
    try:
        if not query.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Search query cannot be empty"
            )
        
        documents = db.search_documents(query, limit)
        
        # Convert ObjectId to string for JSON serialization
        for doc in documents:
            if '_id' in doc:
                doc['_id'] = str(doc['_id'])
        
        return {
            "query": query,
            "results": documents,
            "total_found": len(documents)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search documents error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error searching documents"
        )

@router.get("/stats", response_model=StatsResponse)
async def get_stats(current_user: dict = Depends(get_current_user)):
    """Get system statistics"""
    try:
        stats = db.get_stats()
        return StatsResponse(**stats)
    except Exception as e:
        logging.error(f"Error getting stats: {e}")
        raise HTTPException(500, f"Error getting stats: {str(e)}")
    

# Health and info endpoints
@router.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Test database connection
        db.client.admin.command('ping')
        database_status = "connected"
    except Exception as e:
        database_status = f"disconnected: {str(e)}"
    
    return {
        "status": "healthy", 
        "message": "AI Assistant API is running",
        "timestamp": datetime.utcnow().isoformat(),
        "database": database_status,
        "authentication": "JWT",
        "version": "1.0.0"
    }

@router.get("/info")
async def api_info():
    """Get API information."""
    return {
        "name": "AI Assistant API",
        "version": "1.0.0",
        "description": "Intelligent document search and conversational AI",
        "endpoints": {
            "authentication": ["/register", "/login", "/logout"],
            "user_management": ["/profile", "/change-password", "/account"],
            "chat": ["/document-chat", "/chat-stream", "/chat-sessions"],
            "documents": ["/documents", "/search/documents"],
            "system": ["/health", "/info"]
        }
    }


