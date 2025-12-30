import re
import json
import asyncio
import uuid
from datetime import datetime
from groq import Groq
from config import settings
from db.database import db

# Initialize Groq client
client = Groq(api_key=settings.GROQ_API_KEY)

# Natural conversation patterns
GREETING_PATTERNS = [
    r'\b(hi|hello|hey|greetings|good morning|good afternoon|good evening)\b',
    r'\b(how are you|howdy|what\'s up)\b',
    r'\b(hey there|hello there)\b'
]

FAREWELL_PATTERNS = [
    r'\b(bye|goodbye|see you|see ya|farewell|cya)\b',
    r'\b(thanks|thank you|thx|thankyou)\b',
    r'\b(have a good day|take care)\b'
]

CASUAL_PATTERNS = [
    r'\b(how are you|how do you do|what\'s new)\b',
    r'\b(what can you do|help|options)\b',
    r'\b(who are you|what are you|introduce yourself)\b'
]

def is_natural_conversation(query: str) -> bool:
    """Check if the query is a natural conversation rather than document-related"""
    query_lower = query.lower().strip()
    
    for pattern in GREETING_PATTERNS:
        if re.search(pattern, query_lower):
            return True
    
    for pattern in FAREWELL_PATTERNS:
        if re.search(pattern, query_lower):
            return True
    
    for pattern in CASUAL_PATTERNS:
        if re.search(pattern, query_lower):
            return True
    
    if len(query.split()) <= 3 and any(word in query_lower for word in ['hi', 'hello', 'hey', 'bye', 'thanks']):
        return True
    
    return False

def get_conversational_response(query: str) -> str:
    """Generate appropriate responses for natural conversation"""
    query_lower = query.lower().strip()
    
    import random
    
    if any(re.search(pattern, query_lower) for pattern in GREETING_PATTERNS):
        return random.choice([
            "Hello! I'm your AI Assistant. How can I help you today?",
            "Hi there! I'm ready to assist you with any questions.",
            "Greetings! What would you like to know?",
            "Hey! I'm here to help. What can I do for you?"
        ])
    
    if any(re.search(pattern, query_lower) for pattern in FAREWELL_PATTERNS):
        if any(word in query_lower for word in ['thank', 'thanks']):
            return random.choice([
                "You're welcome! Feel free to ask if you need more help.",
                "Happy to help! Let me know if you have any other questions.",
                "Glad I could assist! Don't hesitate to reach out if you need more information."
            ])
        else:
            return random.choice([
                "Goodbye! Feel free to come back if you need help.",
                "See you later! I'll be here if you have more questions.",
                "Take care! Don't hesitate to ask if you need assistance later."
            ])
    
    if re.search(r'\b(how are you|how do you do)\b', query_lower):
        return random.choice([
            "I'm doing great, thanks for asking! Ready to help you.",
            "I'm functioning well and ready to assist with your queries!",
            "Doing well! Excited to help you find information."
        ])
    
    if re.search(r'\b(what can you do|help|options)\b', query_lower):
        return "I can help you with:\n• Answering questions and providing information\n• Creative writing and brainstorming\n• Problem-solving and analysis\n• Document analysis (if you have files in D:/data)\n\nJust ask me anything!"
    
    if re.search(r'\b(who are you|what are you|introduce yourself)\b', query_lower):
        return "I'm an AI Assistant that can help you with various tasks including answering questions, creative work, and analyzing documents from your D:/data folder."
    
    return "I'm here to help! You can ask me about any topic, and I'll do my best to provide useful information."

def create_structured_prompt(user_query: str, documents: list) -> list:
    """Create a structured prompt that forces organized responses"""
    
    document_context = ""
    for doc in documents:
        document_context += f"\n\n--- {doc['filename']} ---\n{doc['content'][:3000]}"
    
    system_prompt = f"""You are a helpful AI assistant. You provide clear, structured answers based on the provided documents when available.

AVAILABLE DOCUMENTS:{document_context}

RESPONSE GUIDELINES:
1. **Start by referencing the specific document(s)** you're using (if applicable)
2. **Use clear section headers** with markdown (## Header)
3. **Provide bullet points** for lists and steps
4. **Include code examples** where relevant
5. **Mention specific details** from the documents
6. **Keep explanations practical and actionable**

If the documents don't contain the information, provide your best answer based on general knowledge."""

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_query}
    ]

# In services/chat_service.py, update the generate_streaming_response function

async def generate_streaming_response(user_query: str, relevant_docs: list = None, session_id: str = None):
    """Generate streaming response for both document and general queries"""
    try:
        # For natural conversation, stream the response character by character
        if is_natural_conversation(user_query):
            response_text = get_conversational_response(user_query)
            
            # Stream the response with slight delays to simulate typing
            for char in response_text:
                yield f"data: {json.dumps({'type': 'content', 'content': char})}\n\n"
                await asyncio.sleep(0.01)  # Small delay for natural typing effect
            
            # Send completion message with session ID
            yield f"data: {json.dumps({'type': 'complete', 'documents_used': [], 'session_id': session_id})}\n\n"
            return

        # For document queries
        if not relevant_docs:
            no_docs_response = "I couldn't find any relevant documents to answer your question. I'll provide a general answer based on my knowledge."
            
            # Stream the no documents message
            for char in no_docs_response:
                yield f"data: {json.dumps({'type': 'content', 'content': char})}\n\n"
                await asyncio.sleep(0.01)
            
            # Now provide a general answer using Groq
            messages = [{"role": "user", "content": user_query}]
            stream = client.chat.completions.create(
                messages=messages,
                model="llama-3.3-70b-versatile",
                temperature=0.3,
                max_tokens=1500,
                stream=True
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    yield f"data: {json.dumps({'type': 'content', 'content': content})}\n\n"
            
            # Send completion message with session ID
            yield f"data: {json.dumps({'type': 'complete', 'documents_used': [], 'session_id': session_id})}\n\n"
            return

        # For document-based responses
        messages = create_structured_prompt(user_query, relevant_docs)
        
        # First, send document info
        doc_names = [doc['filename'] for doc in relevant_docs]
        yield f"data: {json.dumps({'type': 'documents', 'documents': doc_names})}\n\n"
        
        # Stream the Groq response
        stream = client.chat.completions.create(
            messages=messages,
            model="llama-3.3-70b-versatile",
            temperature=0.3,
            max_tokens=1500,
            stream=True
        )
        
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                content = chunk.choices[0].delta.content
                yield f"data: {json.dumps({'type': 'content', 'content': content})}\n\n"
        
        # Send completion message with session ID and documents used
        yield f"data: {json.dumps({'type': 'complete', 'documents_used': doc_names, 'session_id': session_id})}\n\n"
        
    except Exception as e:
        error_msg = f"I apologize, but I encountered an error: {str(e)}"
        
        # Stream the error message
        for char in error_msg:
            yield f"data: {json.dumps({'type': 'content', 'content': char})}\n\n"
            await asyncio.sleep(0.01)
        
        # Send completion message with error and session ID
        yield f"data: {json.dumps({'type': 'complete', 'documents_used': [], 'session_id': session_id, 'error': str(e)})}\n\n"

def document_chat(user_query: str, session_id: str = None, user_id: str = "default_user"):
    """Main function for document-based chat with structured responses and session management"""
    try:
        if not user_query.strip():
            return {"response": "Please provide a question."}
        
        # Create or get session
        if not session_id:
            session_id = str(uuid.uuid4())
            db.create_chat_session(session_id, user_id)
        
        # Add user message to session
        user_message = {
            "role": "user",
            "content": user_query,
            "timestamp": datetime.utcnow().isoformat()
        }
        db.add_message_to_session(session_id, user_message)
        
        if is_natural_conversation(user_query):
            conversational_response = get_conversational_response(user_query)
            
            # Add bot response to session
            bot_message = {
                "role": "assistant",
                "content": conversational_response,
                "timestamp": datetime.utcnow().isoformat(),
                "source": "conversation"
            }
            db.add_message_to_session(session_id, bot_message)
            
            return {
                "response": conversational_response,
                "session_id": session_id,
                "documents_used": [],
                "source": "conversation"
            }
        
        # Search in MongoDB for relevant documents
        relevant_docs = db.search_documents(user_query)
        
        if not relevant_docs:
            # Try searching in chat sessions
            chat_results = db.search_in_chat_sessions(user_query)
            if chat_results:
                # Use previous chat responses
                # Extract relevant responses from chat history
                previous_responses = []
                for result in chat_results:
                    for msg in result.get("messages", []):
                        if msg.get("role") == "assistant" and user_query.lower() in msg.get("content", "").lower():
                            previous_responses.append(msg.get("content"))
                
                if previous_responses:
                    response = "Based on our previous conversations:\n\n" + "\n\n".join(previous_responses[:3])
                    
                    # Add bot response to session
                    bot_message = {
                        "role": "assistant",
                        "content": response,
                        "timestamp": datetime.utcnow().isoformat(),
                        "source": "chat_history"
                    }
                    db.add_message_to_session(session_id, bot_message)
                    
                    return {
                        "response": response,
                        "session_id": session_id,
                        "documents_used": [],
                        "source": "chat_history"
                    }
            
            # No documents or chat history found
            response = "I couldn't find any relevant documents or previous conversations to answer your question. Please try asking about something that might be covered in your documentation."
            
            # Add bot response to session
            bot_message = {
                "role": "assistant",
                "content": response,
                "timestamp": datetime.utcnow().isoformat(),
                "source": "no_documents"
            }
            db.add_message_to_session(session_id, bot_message)
            
            return {
                "response": response,
                "session_id": session_id,
                "documents_used": [],
                "source": "no_documents"
            }
        
        # Convert MongoDB documents to the format expected by create_structured_prompt
        formatted_docs = []
        for doc in relevant_docs:
            formatted_docs.append({
                'filename': doc['filename'],
                'content': doc['content']
            })
        
        messages = create_structured_prompt(user_query, formatted_docs)
        
        response = client.chat.completions.create(
            messages=messages,
            model="llama-3.3-70b-versatile",
            temperature=0.3,
            max_tokens=1500
        )
        
        bot_reply = response.choices[0].message.content
        
        # Add bot response to session
        bot_message = {
            "role": "assistant",
            "content": bot_reply,
            "timestamp": datetime.utcnow().isoformat(),
            "source": "documents",
            "documents_used": [doc['filename'] for doc in relevant_docs]
        }
        db.add_message_to_session(session_id, bot_message)
        
        return {
            "response": bot_reply,
            "session_id": session_id,
            "documents_used": [doc['filename'] for doc in relevant_docs],
            "source": "documents"
        }
        
    except Exception as e:
        error_response = f"I apologize, but I encountered an error: {str(e)}"
        
        # Try to add error message to session if session_id exists
        if session_id:
            error_message = {
                "role": "assistant",
                "content": error_response,
                "timestamp": datetime.utcnow().isoformat(),
                "source": "error"
            }
            db.add_message_to_session(session_id, error_message)
        
        return {"response": error_response, "session_id": session_id}

def quick_chat(user_query: str):
    """Quick chat without documents"""
    try:
        messages = [
            {
                "role": "system", 
                "content": "You are a helpful AI assistant. Provide clear, concise answers."
            },
            {
                "role": "user", 
                "content": user_query
            }
        ]
        
        response = client.chat.completions.create(
            messages=messages,
            model="llama-3.3-70b-versatile",
        )
        
        return {"response": response.choices[0].message.content}
        
    except Exception as e:
        return {"response": "I'm having trouble responding right now. Please try again."}

def get_chat_history(session_id: str):
    """Get chat history for a session"""
    try:
        messages = db.get_chat_session_messages(session_id)
        return {
            "session_id": session_id,
            "messages": messages
        }
    except Exception as e:
        return {"error": str(e)}

def get_recent_sessions(user_id: str = "default_user", limit=10):
    """Get recent chat sessions for a user"""
    try:
        sessions = db.get_user_sessions(user_id, limit)
        return {
            "user_id": user_id,
            "sessions": sessions
        }
    except Exception as e:
        return {"error": str(e)}

def get_chat_stats():
    """Get statistics about chat sessions and usage"""
    try:
        # Get database stats
        db_stats = db.get_stats()
        
        # Get recent sessions for additional stats
        recent_sessions = db.get_recent_chat_sessions(100)
        
        # Calculate average messages per session
        total_messages = 0
        sessions_with_messages = 0
        
        for session in recent_sessions:
            messages = session.get("messages", [])
            if messages:
                total_messages += len(messages)
                sessions_with_messages += 1
        
        avg_messages_per_session = total_messages / sessions_with_messages if sessions_with_messages > 0 else 0
        
        return {
            "database_stats": db_stats,
            "chat_specific_stats": {
                "total_sessions": db_stats.get("total_sessions", 0),
                "recent_sessions": len(recent_sessions),
                "average_messages_per_session": round(avg_messages_per_session, 2),
                "total_messages_analyzed": total_messages
            }
        }
    except Exception as e:
        return {"error": str(e)}