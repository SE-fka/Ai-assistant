from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List
import logging
from datetime import datetime, timedelta
import jwt
import os
import secrets

from db.user_database import user_db
from models.user_schemas import (
    UserCreate, UserResponse, UserUpdate, UserProfileUpdate, 
    ChangePasswordRequest, UserLogin, Token, UserProfileResponse
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# JWT settings - Moved to shared location to avoid duplication
SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

router = APIRouter()

# Dependency to get the current user (shared across routes)
async def get_current_user(token: str = Depends(lambda: None)):
    """Get current user from JWT token"""
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    from fastapi import Depends
    
    security = HTTPBearer(auto_error=False)
    
    async def get_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
            
        try:
            payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
            user_id: str = payload.get("sub")
            
            if user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication credentials"
                )
            
            user = user_db.get_user(user_id)
            if user is None or not user.get('is_active', True):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found or inactive"
                )
            
            return user
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
    
    return await get_user()

async def get_admin_user(current_user: dict = Depends(get_current_user)):
    """Dependency to ensure user is admin"""
    if current_user.get('role') not in ['admin', 'super_admin']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    return current_user

# User CRUD endpoints
@router.post("/user", response_model=UserResponse)
async def create_user(user_data: UserCreate):
    """Create a new user"""
    try:
        # Check if user already exists
        if user_db.get_user_by_username(user_data.username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        
        if user_db.get_user_by_email(user_data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create user
        user_dict = user_data.dict()
        user_id = user_db.create_user(user_dict)
        user = user_db.get_user(user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user"
            )
        
        return UserResponse(**user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating user: {str(e)}"
        )

@router.put("/user/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str, 
    update_data: UserProfileUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update user profile"""
    if user_id != current_user['id'] and current_user.get('role') not in ['admin', 'super_admin']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only update your own profile"
        )
    
    try:
        update_dict = update_data.dict(exclude_unset=True)

        # Check for existing username/email when changes are made
        # For username
        if 'username' in update_dict:
            existing_user = user_db.get_user_by_username(update_dict['username'])
            if existing_user and existing_user['id'] != user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already taken"
                )
        
        # For email
        if 'email' in update_dict:
            existing_user = user_db.get_user_by_email(update_dict['email'])
            if existing_user and existing_user['id'] != user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )

        success = user_db.update_user(user_id, update_dict)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update profile"
            )
        
        updated_user = user_db.get_user(user_id)
        return UserResponse(**updated_user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating profile: {str(e)}"
        )

@router.delete("/user/{user_id}")
async def delete_user(user_id: str, current_user: dict = Depends(get_current_user)):
    """Delete user account"""
    if user_id != current_user['id'] and current_user.get('role') not in ['admin', 'super_admin']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only delete your own account"
        )
    
    try:
        success = user_db.delete_user(user_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to delete account"
            )
        
        return {"message": "Account deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting account"
        )

@router.post("/login", response_model=Token)
async def login(login_data: UserLogin):
    """Login user with role-based redirection"""
    try:
        logger.info(f"Attempting to log in user: {login_data.username}")

        if user_db.is_account_locked(login_data.username):
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="Account temporarily locked due to too many failed login attempts"
            )
        
        user = user_db.get_user_by_username(login_data.username)
        if not user:
            user_db.increment_failed_login(login_data.username)
            logger.warning(f"Failed login for: {login_data.username} - User not found.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password"
            )
        
        if not user_db.verify_password(login_data.password, user["password_hash"]):
            user_db.increment_failed_login(login_data.username)
            logger.warning(f"Failed login for: {login_data.username} - Invalid password.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password"
            )
        
        if not user.get('is_active', True):
            logger.warning(f"Failed login for: {login_data.username} - Account inactive.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is deactivated"
            )
        
        user_db.update_login_stats(user["id"])
        
        token_data = {
            "sub": user["id"],
            "role": user.get("role", "user"),
            "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        }
        access_token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)

        # Determine redirect URL based on user role
        user_role = user.get("role", "user")
        if user_role in ['admin', 'super_admin']:
            redirect_url = '/admin/dashboard'
        else:
            redirect_url = '/chat'
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            redirect_url=redirect_url,
            user=UserResponse(**user)
        )
        
    except Exception as e:
        logger.error(f"Error during login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed due to: {str(e)}"
        )

@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """Logout user (client should remove token)"""
    return {"message": "Successfully logged out"}

# User profile endpoints
@router.get("/profile", response_model=UserProfileResponse)
async def get_profile(current_user: dict = Depends(get_current_user)):
    """Get current user profile"""
    return UserProfileResponse(**current_user)

@router.put("/profile", response_model=UserProfileResponse)
async def update_profile(
    update_data: UserProfileUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update user profile"""
    try:
        update_dict = update_data.dict(exclude_unset=True)

        # Check for existing username/email when changes are made
        if 'username' in update_dict and update_dict['username'] != current_user['username']:
            existing_user = user_db.get_user_by_username(update_dict['username'])
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already taken"
                )
        
        if 'email' in update_dict and update_dict['email'] != current_user['email']:
            existing_user = user_db.get_user_by_email(update_dict['email'])
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
            update_dict['email_verified'] = False  # Require verification for a new email
        
        success = user_db.update_user(current_user['id'], update_dict)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update profile"
            )
        
        updated_user = user_db.get_user(current_user['id'])
        return UserProfileResponse(**updated_user)
        
    except Exception as e:
        logger.error(f"Error updating profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating profile: {str(e)}"
        )

@router.post("/change-password")
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: dict = Depends(get_current_user)
):
    """Change user password"""
    try:
        if not user_db.verify_password(password_data.current_password, current_user["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        success = user_db.change_password(current_user['id'], password_data.new_password)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to change password"
            )
        
        return {"message": "Password changed successfully"}
        
    except Exception as e:
        logger.error(f"Error changing password: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error changing password: {str(e)}"
        )

# Admin endpoints
@router.get("/users", response_model=List[UserResponse])
async def get_all_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: dict = Depends(get_admin_user)
):
    """Get all users (admin only)"""
    try:
        users = user_db.get_all_users(skip=skip, limit=limit, active_only=False)
        return [UserResponse(**user) for user in users]
    except Exception as e:
        logger.error(f"Error retrieving users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving users"
        )

@router.get("/users/stats")
async def get_user_stats(current_user: dict = Depends(get_admin_user)):
    """Get user statistics (admin only)"""
    try:
        users = user_db.get_all_users(active_only=False)
        total_users = len(users)
        active_users = len([u for u in users if u.get('is_active', True)])
        admin_users = len([u for u in users if u.get('role') in ['admin', 'super_admin']])
        
        # Calculate recent users (last 7 days)
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_users = len([u for u in users if 
                          u.get('created_at') and 
                          u.get('created_at') >= week_ago])
        
        return {
            "total_users": total_users,
            "active_users": active_users,
            "admin_users": admin_users,
            "recent_users": recent_users,
            "inactive_users": total_users - active_users
        }
    except Exception as e:
        logger.error(f"Error getting user stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving user statistics"
        )

@router.put("/users/{user_id}/activate")
async def activate_user(user_id: str, current_user: dict = Depends(get_admin_user)):
    """Activate/deactivate user (admin only)"""
    try:
        user = user_db.get_user(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        new_status = not user.get('is_active', True)
        success = user_db.update_user(user_id, {'is_active': new_status})
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update user status"
            )
        
        action = "activated" if new_status else "deactivated"
        return {"message": f"User {action} successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating user status"
        )

@router.put("/users/{user_id}/role")
async def update_user_role(
    user_id: str, 
    role_data: dict,
    current_user: dict = Depends(get_admin_user)
):
    """Update user role (admin only)"""
    try:
        new_role = role_data.get('role')
        if new_role not in ['user', 'admin', 'super_admin']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid role. Must be 'user', 'admin', or 'super_admin'"
            )
        
        user = user_db.get_user(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Prevent users from modifying their own role
        if user_id == current_user['id']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot modify your own role"
            )
        
        success = user_db.update_user(user_id, {'role': new_role})
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update user role"
            )
        
        return {"message": f"User role updated to {new_role}"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user role: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating user role"
        )

