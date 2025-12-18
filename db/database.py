from pymongo import MongoClient, ASCENDING, DESCENDING, TEXT
import logging
from datetime import datetime
from config.settings import settings
from bson import ObjectId
from passlib.context import CryptContext
import bcrypt

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MongoDBManager:
    def __init__(self):
        self.client = None
        self.db = None
        self.connect()
        self.create_indexes()
    
    def connect(self):
        """Connect to MongoDB."""
        try:
            self.client = MongoClient(settings.MONGODB_URI)
            self.db = self.client[settings.DATABASE_NAME]
            self.client.admin.command('ping')  # Ping for connection check
            logger.info("✅ Connected to MongoDB")
        except Exception as e:
            logger.error(f"❌ MongoDB connection failed: {e}")
            raise
    
    def create_indexes(self):
        """Create necessary indexes for efficient querying."""
        try:
            # Document indexes
            self.db.documents.create_index([("filename", ASCENDING)])
            self.db.documents.create_index([("file_type", ASCENDING)])
            self.db.documents.create_index([("content", TEXT)])
            
            # Chat session indexes
            self.db.chat_sessions.create_index([("session_id", ASCENDING)])
            self.db.chat_sessions.create_index([("user_id", ASCENDING)])
            self.db.chat_sessions.create_index([("user_id", ASCENDING), ("created_at", DESCENDING)])
            
            # User indexes
            self.db.users.create_index([("username", ASCENDING)], unique=True)
            self.db.users.create_index([("email", ASCENDING)], unique=True)
            
            logger.info("✅ Database indexes created")
        except Exception as e:
            logger.error(f"❌ Index creation failed: {e}")
    
    # User Management Methods
    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt."""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        try:
            return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False
    
    def get_user(self, user_id):
        """Get user by ID."""
        try:
            if isinstance(user_id, str):
                user_id = ObjectId(user_id)
            return self.db.users.find_one({"_id": user_id})
        except Exception as e:
            logger.error(f"Error getting user {user_id}: {e}")
            return None
    
    def get_user_by_username(self, username):
        """Get user by username."""
        try:
            return self.db.users.find_one({"username": username})
        except Exception as e:
            logger.error(f"Error getting user by username {username}: {e}")
            return None
    
    def get_user_by_email(self, email):
        """Get user by email."""
        try:
            return self.db.users.find_one({"email": email})
        except Exception as e:
            logger.error(f"Error getting user by email {email}: {e}")
            return None
    
    def change_password(self, user_id, new_password):
        """Change user password."""
        try:
            if isinstance(user_id, str):
                user_id = ObjectId(user_id)
            
            result = self.db.users.update_one(
                {"_id": user_id},
                {"$set": {
                    "password_hash": self.hash_password(new_password),
                    "updated_at": datetime.utcnow()
                }}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error changing password for user {user_id}: {e}")
            return False

    # Document Methods (your existing methods)
    def insert_document(self, document_data):
        """Insert a document into the documents collection."""
        try:
            result = self.db.documents.insert_one(document_data)
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Error inserting document: {e}")
            return None
    
    def get_document(self, document_id):
        """Get a document by ID."""
        try:
            if isinstance(document_id, str):
                document_id = ObjectId(document_id)
            return self.db.documents.find_one({"_id": document_id})
        except Exception as e:
            logger.error(f"Error getting document {document_id}: {e}")
            return None
    
    def get_all_documents(self):
        """Get all documents from the collection."""
        try:
            return list(self.db.documents.find())
        except Exception as e:
            logger.error(f"Error getting all documents: {e}")
            return []
    
    def search_documents(self, query: str, limit: int = 5):
        """Search for documents by content using text search."""
        try:
            # Use MongoDB text search if text index exists
            results = self.db.documents.find(
                {"$text": {"$search": query}},
                {"score": {"$meta": "textScore"}}
            ).sort([("score", {"$meta": "textScore"})]).limit(limit)
            
            documents = list(results)
            
            # If no results from text search, fall back to regex search
            if not documents:
                pattern = {"$regex": query, "$options": "i"}
                documents = list(self.db.documents.find({
                    "$or": [
                        {"filename": pattern},
                        {"content": pattern},
                        {"file_type": pattern}
                    ]
                }).limit(limit))
            
            logger.info(f"Found {len(documents)} documents for query: {query}")
            return documents
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            # Fallback to simple search if text index is not available
            try:
                pattern = {"$regex": query, "$options": "i"}
                documents = list(self.db.documents.find({
                    "$or": [
                        {"filename": pattern},
                        {"content": pattern}
                    ]
                }).limit(limit))
                return documents
            except Exception as fallback_error:
                logger.error(f"Fallback search also failed: {fallback_error}")
                return []
    
    def get_documents_by_ids(self, document_ids: list):
        """Get multiple documents by their IDs."""
        try:
            object_ids = [ObjectId(doc_id) if isinstance(doc_id, str) else doc_id 
                         for doc_id in document_ids]
            return list(self.db.documents.find({"_id": {"$in": object_ids}}))
        except Exception as e:
            logger.error(f"Error getting documents by IDs: {e}")
            return []
    
    def update_document(self, document_id, update_data):
        """Update a document."""
        try:
            if isinstance(document_id, str):
                document_id = ObjectId(document_id)
            result = self.db.documents.update_one(
                {"_id": document_id},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating document {document_id}: {e}")
            return False
    
    def delete_document(self, document_id):
        """Delete a document by ID."""
        try:
            if isinstance(document_id, str):
                document_id = ObjectId(document_id)
            result = self.db.documents.delete_one({"_id": document_id})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting document {document_id}: {e}")
            return False

    # Chat Session Methods (your existing methods)
    def create_chat_session(self, session_id: str, user_id: str):
        """Create a new chat session (compatibility method for router)."""
        try:
            session_data = {
                "session_id": session_id,
                "user_id": user_id,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "messages": []
            }
            result = self.db.chat_sessions.insert_one(session_data)
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Error creating chat session: {e}")
            return None
    
    def insert_chat_session(self, session_data):
        """Insert a new chat session with full data."""
        try:
            result = self.db.chat_sessions.insert_one(session_data)
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Error inserting chat session: {e}")
            return None
    
    def get_chat_session(self, session_id):
        """Get a chat session by its ID."""
        try:
            return self.db.chat_sessions.find_one({"session_id": session_id})
        except Exception as e:
            logger.error(f"Error getting chat session {session_id}: {e}")
            return None
    
    def delete_chat_session(self, session_id):
        """Delete a chat session by its ID."""
        try:
            result = self.db.chat_sessions.delete_one({"session_id": session_id})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting chat session {session_id}: {e}")
            return False
    
    def delete_all_chat_sessions(self, user_id: str):
        """Delete all chat sessions for a specific user."""
        try:
            result = self.db.chat_sessions.delete_many({"user_id": user_id})
            return result.deleted_count
        except Exception as e:
            logger.error(f"Error deleting all chat sessions for user {user_id}: {e}")
            return 0
    
    def get_user_sessions(self, user_id: str, limit=10):
        """Retrieve a user's chat sessions."""
        try:
            return list(self.db.chat_sessions.find({"user_id": user_id})
                       .sort("created_at", DESCENDING)
                       .limit(limit))
        except Exception as e:
            logger.error(f"Error getting user sessions for {user_id}: {e}")
            return []
    
    def add_message_to_session(self, session_id: str, message: dict):
        """Add a message to a specific chat session."""
        try:
            self.db.chat_sessions.update_one(
                {"session_id": session_id},
                {"$push": {"messages": message}, "$set": {"updated_at": datetime.utcnow()}}
            )
            return True
        except Exception as e:
            logger.error(f"Error adding message to session {session_id}: {e}")
            return False
    
    def get_chat_session_messages(self, session_id: str):
        """Retrieve all messages from a chat session."""
        try:
            session = self.get_chat_session(session_id)
            return session.get("messages", []) if session else []
        except Exception as e:
            logger.error(f"Error getting messages for session {session_id}: {e}")
            return []
    
    def search_in_chat_sessions(self, query: str, limit=10):
        """Search for messages in chat sessions."""
        try:
            pattern = {"$regex": query, "$options": "i"}
            pipeline = [
                {"$unwind": "$messages"},
                {"$match": {
                    "$or": [
                        {"messages.content": pattern},
                        {"messages.role": pattern}
                    ]
                }},
                {"$sort": {"updated_at": DESCENDING}},
                {"$limit": limit}
            ]
            results = list(self.db.chat_sessions.aggregate(pipeline))
            return results
        except Exception as e:
            logger.error(f"Error searching in chat sessions: {e}")
            return []
        
    def get_stats(self):
        total_docs = self.db.documents.count_documents({})
        total_sessions = self.db.chat_sessions.count_documents({})
        
        pipeline = [
            {"$group": {
                "_id": "$file_type",
                "count": {"$sum": 1},
                "total_chunks": {"$sum": "$chunk_count"}
            }}
        ]
        file_stats = list(self.db.documents.aggregate(pipeline))
        
        return {
            "total_documents": total_docs,
            "total_sessions": total_sessions,
            "file_statistics": file_stats
        }

# Global instance
db = MongoDBManager()