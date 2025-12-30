import re
import json
import asyncio
import random
from groq import Groq
from config.settings import settings
from db.database import db

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

class ChatService:
    def __init__(self):
        self.client = Groq(api_key=settings.GROQ_API_KEY)
    
    def is_natural_conversation(self, query: str) -> bool:
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
    
    def get_conversational_response(self, query: str) -> str:
        """Generate appropriate responses for natural conversation"""
        query_lower = query.lower().strip()
        
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
            return "I can help you with:\n• Answering questions and providing information\n• Creative writing and brainstorming\n• Problem-solving and analysis\n• Document analysis (from the database)\n\nJust ask me anything!"
        
        if re.search(r'\b(who are you|what are you|introduce yourself)\b', query_lower):
            return "I'm an AI Assistant that can help you with various tasks including answering questions, creative work, and analyzing documents from the database."
        
        return "I'm here to help! You can ask me about any topic, and I'll do my best to provide useful information."
    
    def find_relevant_documents(self, query: str) -> list:
        """Find documents relevant to the query using the database"""
        try:
            # Use the database search function
            relevant_docs = db.search_documents(query, limit=3)
            
            # Format the results to match the expected structure
            formatted_docs = []
            for doc in relevant_docs:
                if doc and 'content' in doc:
                    formatted_docs.append({
                        'path': doc.get('file_path', 'database'),
                        'filename': doc.get('filename', 'Unknown'),
                        'relevance_score': doc.get('relevance_score', 0),
                        'content': doc.get('content', '')[:5000]  # Limit content size
                    })
            
            return formatted_docs
        except Exception as e:
            print(f"Error searching documents in database: {e}")
            return []
    
    def create_structured_prompt(self, user_query: str, documents: list) -> list:
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
    
    async def generate_streaming_response(self, user_query: str, relevant_docs: list = None):
        """Generate streaming response for both document and general queries"""
        try:
            # For natural conversation, stream the response character by character
            if self.is_natural_conversation(user_query):
                response_text = self.get_conversational_response(user_query)
                # Stream the response with slight delays to simulate typing
                for char in response_text:
                    yield f"data: {json.dumps({'type': 'content', 'content': char})}\n\n"
                    await asyncio.sleep(0.01)  # Small delay for natural typing effect
                yield f"data: {json.dumps({'type': 'complete', 'documents_used': []})}\n\n"
                return

            # For document queries
            if not relevant_docs:
                no_docs_response = "I couldn't find any relevant documents to answer your question. I'll provide a general answer based on my knowledge."
                for char in no_docs_response:
                    yield f"data: {json.dumps({'type': 'content', 'content': char})}\n\n"
                    await asyncio.sleep(0.01)
                
                # Now provide a general answer using Groq
                messages = [{"role": "user", "content": user_query}]
                stream = self.client.chat.completions.create(
                    messages=messages,
                    model=settings.GROQ_MODEL,
                    temperature=0.3,
                    max_tokens=1500,
                    stream=True
                )
                
                for chunk in stream:
                    if chunk.choices[0].delta.content is not None:
                        content = chunk.choices[0].delta.content
                        yield f"data: {json.dumps({'type': 'content', 'content': content})}\n\n"
                
                yield f"data: {json.dumps({'type': 'complete', 'documents_used': []})}\n\n"
                return

            # For document-based responses
            messages = self.create_structured_prompt(user_query, relevant_docs)
            
            # First, send document info
            doc_names = [doc['filename'] for doc in relevant_docs]
            yield f"data: {json.dumps({'type': 'documents', 'documents': doc_names})}\n\n"
            
            # Stream the Groq response
            stream = self.client.chat.completions.create(
                messages=messages,
                model=settings.GROQ_MODEL,
                temperature=0.3,
                max_tokens=1500,
                stream=True
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    yield f"data: {json.dumps({'type': 'content', 'content': content})}\n\n"
            
            yield f"data: {json.dumps({'type': 'complete', 'documents_used': doc_names})}\n\n"
            
        except Exception as e:
            error_msg = f"I apologize, but I encountered an error: {str(e)}"
            for char in error_msg:
                yield f"data: {json.dumps({'type': 'content', 'content': char})}\n\n"
                await asyncio.sleep(0.01)
            yield f"data: {json.dumps({'type': 'complete', 'documents_used': []})}\n\n"
    
    async def process_document_chat(self, user_query: str):
        """Process document-based chat request"""
        try:
            if not user_query:
                return {"response": "Please provide a question."}
            
            if self.is_natural_conversation(user_query):
                conversational_response = self.get_conversational_response(user_query)
                return {
                    "response": conversational_response,
                    "documents_used": [],
                    "source": "conversation"
                }
            
            relevant_docs = self.find_relevant_documents(user_query)
            
            if not relevant_docs:
                return {
                    "response": "I couldn't find any relevant documents to answer your question. Please try asking about something that might be covered in your documentation.",
                    "documents_used": [],
                    "source": "no_documents"
                }
            
            messages = self.create_structured_prompt(user_query, relevant_docs)
            
            response = self.client.chat.completions.create(
                messages=messages,
                model=settings.GROQ_MODEL,
                temperature=0.3,
                max_tokens=1500
            )
            
            bot_reply = response.choices[0].message.content
            
            return {
                "response": bot_reply,
                "documents_used": [doc['filename'] for doc in relevant_docs],
                "source": "documents"
            }
            
        except Exception as e:
            return {"response": f"I apologize, but I encountered an error: {str(e)}"}
    
    async def process_quick_chat(self, user_query: str):
        """Process quick chat without documents"""
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
            
            response = self.client.chat.completions.create(
                messages=messages,
                model=settings.GROQ_MODEL,
            )
            
            return {"response": response.choices[0].message.content}
            
        except Exception as e:
            return {"response": "I'm having trouble responding right now. Please try again."}

# Global instance
chat_service = ChatService()