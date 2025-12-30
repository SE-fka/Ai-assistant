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
                        'content': doc.get('content', '')  # Limit content size   [:5000]
                    })
            
            return formatted_docs
        except Exception as e:
            print(f"Error searching documents in database: {e}")
            return []
    
    def create_human_friendly_prompt(self, user_query: str, documents: list) -> list:
        """Create a human-friendly prompt that encourages natural, conversational responses"""
        
        document_context = ""
        if documents:
            document_context = "\n\nHere's some information I found that might be helpful:\n"
            for doc in documents:
                content = doc['content']
                sentences = content.split('.')
                key_content = '. '.join(sentences[:5])
                document_context += f"\n- **From {doc['filename']}**:\n   * {key_content}\n"
        
        system_prompt = f"""You are a friendly, knowledgeable assistant having a conversation. Your goal is to be helpful, clear, and engaging. Your response should be in a conversational tone, incorporating the following guidelines:

        PERSONALITY GUIDELINES:
        * Be warm and approachable, like a helpful colleague.
        * Acknowledge the user's question in a friendly way.
        * Use "I" statements naturally (e.g., "I found...", "I think...").

        {document_context}

        IMPORTANT: Answer in a flowing, natural way as if we're having a conversation. Fill in gaps with your knowledge when necessary."""
        
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query}
        ]

    
    def create_structured_prompt(self, user_query: str, documents: list) -> list:
        """Create a structured prompt that forces organized responses"""
        
        document_context = ""
        for doc in documents:
            document_context += f"\n\n--- {doc['filename']} ---\n{doc['content']}"  #[:3000]
        
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
        """Generate streaming response with human-friendly conversation flow"""
        try:
            # Check if this is a greeting or casual conversation
            if self.is_casual_conversation(user_query):
                response_text = self.get_casual_response(user_query)
                for char in response_text:
                    yield f"data: {json.dumps({'type': 'content', 'content': char})}\n\n"
                    await asyncio.sleep(0.02)  # Slightly faster for casual chat
                yield f"data: {json.dumps({'type': 'complete', 'documents_used': []})}\n\n"
                return

            # For document queries with no results
            if not relevant_docs:
                # More natural "no docs found" message
                no_docs_messages = [
                    "I don't have specific documents on that, but based on what I know...",
                    "I couldn't find exact matches in my sources. From my understanding...",
                    "Let me share what I know about that topic..."
                ]
                
                intro = random.choice(no_docs_messages)
                for char in intro:
                    yield f"data: {json.dumps({'type': 'content', 'content': char})}\n\n"
                    await asyncio.sleep(0.015)
                
                # Now provide a general answer
                messages = [
                    {"role": "system", "content": "You're a friendly, knowledgeable assistant having a casual conversation. Keep it natural and conversational."},
                    {"role": "user", "content": user_query}
                ]
                
                stream = self.client.chat.completions.create(
                    messages=messages,
                    model=settings.GROQ_MODEL,
                    temperature=0.8,  # Higher for more natural variation
                    max_tokens=1200,
                    stream=True
                )
                
                for chunk in stream:
                    if chunk.choices[0].delta.content is not None:
                        content = chunk.choices[0].delta.content
                        yield f"data: {json.dumps({'type': 'content', 'content': content})}\n\n"
                
                yield f"data: {json.dumps({'type': 'complete', 'documents_used': []})}\n\n"
                return

            # Use human-friendly prompt for document queries
            messages = self.create_human_friendly_prompt(user_query, relevant_docs)
            doc_names = [doc['filename'] for doc in relevant_docs]
            
            # First, send document info
            yield f"data: {json.dumps({'type': 'documents', 'documents': doc_names})}\n\n"
            
            # Stream the response with natural pacing
            stream = self.client.chat.completions.create(
                messages=messages,
                model=settings.GROQ_MODEL,
                temperature=0.7,
                max_tokens=1500,
                stream=True
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    yield f"data: {json.dumps({'type': 'content', 'content': content})}\n\n"
                    # Vary delay slightly for more natural typing effect
                    await asyncio.sleep(random.uniform(0.01, 0.03))
            
            yield f"data: {json.dumps({'type': 'complete', 'documents_used': doc_names})}\n\n"
            
        except Exception as e:
            error_msg = f"Oops, I ran into a bit of a hiccup there: {str(e)}. Could you try asking again?"
            for char in error_msg:
                yield f"data: {json.dumps({'type': 'content', 'content': char})}\n\n"
                await asyncio.sleep(0.02)
            yield f"data: {json.dumps({'type': 'complete', 'documents_used': []})}\n\n"

    
    async def process_document_chat(self, user_query: str, human_friendly: bool = True):
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
                # Use human-friendly response even when no documents found
                messages = [
                    {
                        "role": "system", 
                        "content": "You are a helpful, friendly AI assistant. Provide clear, natural responses in a conversational tone. If you don't have specific document information, just share what you know in a helpful way."
                    },
                    {
                        "role": "user", 
                        "content": user_query
                    }
                ]
                
                response = self.client.chat.completions.create(
                    messages=messages,
                    model=settings.GROQ_MODEL,
                    temperature=0.7,
                    max_tokens=1500
                )
                
                bot_reply = response.choices[0].message.content
                
                return {
                    "response": bot_reply,
                    "documents_used": [],
                    "source": "general_knowledge"
                }
            
            # Choose prompt style based on preference
            if human_friendly:
                messages = self.create_human_friendly_prompt(user_query, relevant_docs)
            else:
                messages = self.create_structured_prompt(user_query, relevant_docs)
            
            response = self.client.chat.completions.create(
                messages=messages,
                model=settings.GROQ_MODEL,
                temperature=0.7,
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


# Global instance
chat_service = ChatService()