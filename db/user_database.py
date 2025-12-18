# db/user_database.py
import os
from pymongo import MongoClient
from datetime import datetime, timedelta
import bcrypt
from bson import ObjectId
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)

# Role definitions with permissions
ROLES = {
    "super_admin": {
        "name": "Super Administrator",
        "permissions": ["*"],  # All permissions
        "description": "Full system access including user management, system settings, and all administrative functions",
        "level": 100
    },
    "admin": {
        "name": "Administrator",
        "permissions": [
            "manage_users", "view_users", "create_users", "edit_users", "delete_users",
            "manage_roles", "view_analytics", "system_settings", "export_data"
        ],
        "description": "Administrative access with user management capabilities",
        "level": 80
    },
    "moderator": {
        "name": "Moderator", 
        "permissions": [
            "view_users", "manage_content", "view_analytics", "moderate_chat"
        ],
        "description": "Limited management access for content moderation",
        "level": 60
    },
    "user": {
        "name": "User",
        "permissions": [
            "chat", "upload_documents", "view_own_documents", "view_profile", "edit_profile"
        ],
        "description": "Regular user access with basic functionalities",
        "level": 10
    }
}

class UserDatabase:
    def __init__(self):
        self.mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        self.db_name = os.getenv("DB_NAME", "ai_assistant")
        self.client = None
        self.db = None
        self.connect()

    def connect(self):
        """Connect to MongoDB"""
        try:
            self.client = MongoClient(self.mongo_uri)
            self.db = self.client[self.db_name]
            logger.info("Connected to MongoDB successfully")
            self.create_indexes()
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    def create_indexes(self):
        """Create necessary indexes for users collection"""
        try:
            # Users collection indexes
            self.db.users.create_index("username", unique=True)
            self.db.users.create_index("email", unique=True)
            self.db.users.create_index("role")
            self.db.users.create_index("is_active")
            self.db.users.create_index("created_at")
            self.db.users.create_index([("username", "text"), ("email", "text"), ("full_name", "text")])
        except Exception as e:
            logger.error(f"Error creating indexes: {e}")

    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
        except Exception as e:
            logger.error(f"Error verifying password: {e}")
            return False

    def get_available_roles(self) -> Dict[str, Any]:
        """Get available roles and their permissions"""
        return ROLES

    def get_role_permissions(self, role: str) -> List[str]:
        """Get permissions for a specific role"""
        return ROLES.get(role, {}).get("permissions", [])

    def can_user_perform(self, user_role: str, permission: str) -> bool:
        """Check if user with given role can perform an action"""
        user_permissions = self.get_role_permissions(user_role)
        return "*" in user_permissions or permission in user_permissions

    # User CRUD Operations
    def create_user(self, user_data: Dict[str, Any]) -> str:
        """Create a new user"""
        try:
            # Set default values
            user_data.setdefault('role', 'user')
            user_data.setdefault('is_active', True)
            user_data.setdefault('email_verified', False)
            user_data.setdefault('login_count', 0)
            user_data.setdefault('failed_login_attempts', 0)
            user_data.setdefault('preferences', {})
            
            # Set timestamps
            user_data['created_at'] = datetime.utcnow()
            user_data['updated_at'] = datetime.utcnow()
            user_data['last_login'] = None
            user_data['last_password_change'] = datetime.utcnow()
            
            # Set permissions based on role
            user_data['permissions'] = self.get_role_permissions(user_data['role'])
            
            # Hash password if provided
            if 'password' in user_data:
                user_data['password_hash'] = self.hash_password(user_data['password'])
                del user_data['password']
            
            result = self.db.users.insert_one(user_data)
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            raise

    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        try:
            user = self.db.users.find_one({"_id": ObjectId(user_id)})
            if user:
                user['id'] = str(user['_id'])
                # Remove sensitive fields
                user.pop('password_hash', None)
                user.pop('failed_login_attempts', None)
                user.pop('last_password_change', None)
            return user
        except Exception as e:
            logger.error(f"Error getting user {user_id}: {e}")
            return None

    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username"""
        try:
            user = self.db.users.find_one({"username": username})
            if user:
                user['id'] = str(user['_id'])
            return user
        except Exception as e:
            logger.error(f"Error getting user by username {username}: {e}")
            return None

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        try:
            user = self.db.users.find_one({"email": email})
            if user:
                user['id'] = str(user['_id'])
            return user
        except Exception as e:
            logger.error(f"Error getting user by email {email}: {e}")
            return None

    def get_all_users(self, skip: int = 0, limit: int = 100, active_only: bool = True) -> List[Dict[str, Any]]:
        """Get all users with pagination"""
        try:
            query = {"is_active": True} if active_only else {}
            cursor = self.db.users.find(query).sort("created_at", -1).skip(skip).limit(limit)
            users = list(cursor)
            
            # Convert ObjectId to string and remove sensitive fields
            for user in users:
                user['id'] = str(user['_id'])
                user.pop('password_hash', None)
                user.pop('failed_login_attempts', None)
            return users
        except Exception as e:
            logger.error(f"Error getting all users: {e}")
            return []

    def get_users_by_role(self, role: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get users by role"""
        try:
            users = list(self.db.users.find({"role": role}).sort("created_at", -1).skip(skip).limit(limit))
            for user in users:
                user['id'] = str(user['_id'])
                user.pop('password_hash', None)
            return users
        except Exception as e:
            logger.error(f"Error getting users by role {role}: {e}")
            return []

    def update_user(self, user_id: str, update_data: Dict[str, Any]) -> bool:
        """Update user data"""
        try:
            # Remove fields that shouldn't be updated directly
            update_data.pop('_id', None)
            update_data.pop('id', None)
            update_data.pop('created_at', None)
            update_data.pop('password_hash', None)
            
            update_data['updated_at'] = datetime.utcnow()
            
            # Update permissions if role changed
            if 'role' in update_data:
                update_data['permissions'] = self.get_role_permissions(update_data['role'])
            
            result = self.db.users.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating user {user_id}: {e}")
            return False

    def change_password(self, user_id: str, new_password: str) -> bool:
        """Change user password"""
        try:
            result = self.db.users.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {
                    "password_hash": self.hash_password(new_password),
                    "last_password_change": datetime.utcnow(),
                    "failed_login_attempts": 0,  # Reset failed attempts on password change
                    "updated_at": datetime.utcnow()
                }}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error changing password for user {user_id}: {e}")
            return False

    def delete_user(self, user_id: str) -> bool:
        """Soft delete user"""
        return self.update_user(user_id, {
            "is_active": False,
            "deleted_at": datetime.utcnow()
        })

    def hard_delete_user(self, user_id: str) -> bool:
        """Permanently delete user"""
        try:
            result = self.db.users.delete_one({"_id": ObjectId(user_id)})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting user {user_id}: {e}")
            return False

    def restore_user(self, user_id: str) -> bool:
        """Restore soft-deleted user"""
        return self.update_user(user_id, {
            "is_active": True,
            "deleted_at": None
        })

    # User Authentication & Session Management
    def update_login_stats(self, user_id: str) -> bool:
        """Update user login statistics"""
        try:
            result = self.db.users.update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$set": {"last_login": datetime.utcnow()},
                    "$inc": {"login_count": 1},
                    "$set": {"failed_login_attempts": 0}  # Reset on successful login
                }
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating login stats for user {user_id}: {e}")
            return False

    def increment_failed_login(self, username: str) -> bool:
        """Increment failed login attempts"""
        try:
            result = self.db.users.update_one(
                {"username": username},
                {
                    "$inc": {"failed_login_attempts": 1},
                    "$set": {"last_failed_login": datetime.utcnow()}
                }
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error incrementing failed login for {username}: {e}")
            return False

    def is_account_locked(self, username: str) -> bool:
        """Check if account is locked due to too many failed attempts"""
        try:
            user = self.get_user_by_username(username)
            if not user:
                return False
            
            max_attempts = 5
            lockout_duration = timedelta(minutes=30)
            
            failed_attempts = user.get('failed_login_attempts', 0)
            last_failed = user.get('last_failed_login')
            
            if failed_attempts >= max_attempts:
                if last_failed and datetime.utcnow() - last_failed < lockout_duration:
                    return True
                else:
                    # Reset attempts if lockout period has passed
                    self.db.users.update_one(
                        {"username": username},
                        {"$set": {"failed_login_attempts": 0}}
                    )
            return False
        except Exception as e:
            logger.error(f"Error checking account lock for {username}: {e}")
            return False

    # User Search and Analytics
    def search_users(self, query: str, skip: int = 0, limit: int = 50) -> List[Dict[str, Any]]:
        """Search users by username, email, or full name"""
        try:
            search_filter = {
                "$or": [
                    {"username": {"$regex": query, "$options": "i"}},
                    {"email": {"$regex": query, "$options": "i"}},
                    {"full_name": {"$regex": query, "$options": "i"}}
                ]
            }
            users = list(self.db.users.find(search_filter).sort("created_at", -1).skip(skip).limit(limit))
            for user in users:
                user['id'] = str(user['_id'])
                user.pop('password_hash', None)
            return users
        except Exception as e:
            logger.error(f"Error searching users: {e}")
            return []

    def get_user_stats(self) -> Dict[str, Any]:
        """Get user statistics"""
        try:
            total_users = self.db.users.count_documents({})
            active_users = self.db.users.count_documents({"is_active": True})
            verified_users = self.db.users.count_documents({"email_verified": True})
            
            # Users by role
            role_stats = {}
            for role in ROLES.keys():
                role_stats[role] = self.db.users.count_documents({"role": role, "is_active": True})
            
            # Recent users (last 7 days)
            week_ago = datetime.utcnow() - timedelta(days=7)
            recent_users = self.db.users.count_documents({
                "created_at": {"$gte": week_ago},
                "is_active": True
            })
            
            # Users with recent activity (last 24 hours)
            day_ago = datetime.utcnow() - timedelta(days=1)
            active_recently = self.db.users.count_documents({
                "last_login": {"$gte": day_ago},
                "is_active": True
            })
            
            return {
                "total_users": total_users,
                "active_users": active_users,
                "verified_users": verified_users,
                "recent_users": recent_users,
                "active_recently": active_recently,
                "by_role": role_stats
            }
        except Exception as e:
            logger.error(f"Error getting user stats: {e}")
            return {}

# Create global instance
user_db = UserDatabase()