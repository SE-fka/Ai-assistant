from pymongo import MongoClient, ASCENDING, DESCENDING
import logging
from datetime import datetime
from config.settings import settings

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
            self.db.documents.create_index([("filename", ASCENDING)])
            self.db.documents.create_index([("file_type", ASCENDING)])
            self.db.chat_sessions.create_index([("session_id", ASCENDING)])
            self.db.chat_sessions.create_index([("user_id", ASCENDING)])
            logger.info("✅ Database indexes created")
        except Exception as e:
            logger.error(f"❌ Index creation failed: {e}")
    
    # Document Methods
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
    
    # Chat Session Methods
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
    
    # Additional Methods
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

# Global instance
db = MongoDBManager()