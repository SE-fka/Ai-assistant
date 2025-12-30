from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse
from dotenv import load_dotenv
import os
import glob
import re
import PyPDF2
import docx
import json
import asyncio

# Try to import better PDF libraries
try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False

try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False

# Try to import transformers for local model
try:
    from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False

load_dotenv()

app = FastAPI(title="AI Assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the local model
model = None
tokenizer = None
chat_pipeline = None

if HAS_TRANSFORMERS:
    try:
        print("Loading DeepSeek-R1 model...")
        model_name = "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B"
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            device_map="auto",
            torch_dtype="auto",
            trust_remote_code=True
        )
        chat_pipeline = pipeline(
            "text-generation",
            model=model,
            tokenizer=tokenizer,
            max_new_tokens=512,
            temperature=0.7,
            do_sample=True
        )
        print("DeepSeek-R1 model loaded successfully!")
    except Exception as e:
        print(f"Error loading model: {e}")
        chat_pipeline = None
else:
    print("Transformers not available. Install with: pip install transformers torch")

# Natural conversation patterns (keep your existing functions)
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

def generate_local_response(messages: list, max_tokens: int = 512) -> str:
    """Generate response using local DeepSeek model"""
    if not chat_pipeline:
        return "I'm currently unavailable. Please check if the local model is properly loaded."
    
    try:
        # Format messages for the model
        if len(messages) > 1:
            # Combine system and user messages
            formatted_text = ""
            for msg in messages:
                if msg["role"] == "system":
                    formatted_text += f"System: {msg['content']}\n\n"
                elif msg["role"] == "user":
                    formatted_text += f"User: {msg['content']}\n\nAssistant:"
        else:
            formatted_text = f"User: {messages[-1]['content']}\n\nAssistant:"
        
        # Generate response
        result = chat_pipeline(
            formatted_text,
            max_new_tokens=max_tokens,
            temperature=0.7,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id
        )
        
        response = result[0]['generated_text']
        
        # Extract only the assistant's response
        if "Assistant:" in response:
            response = response.split("Assistant:")[-1].strip()
        
        # Clean up the response
        response = response.split("User:")[0].strip()
        response = response.split("System:")[0].strip()
        
        return response
        
    except Exception as e:
        return f"I encountered an error while generating a response: {str(e)}"

def extract_pdf_content(file_path: str) -> str:
    """Extract text from PDF using best available method"""
    content = ""
    
    if HAS_PYMUPDF:
        try:
            doc = fitz.open(file_path)
            for page in doc:
                content += page.get_text()
            doc.close()
            if content.strip():
                return content
        except Exception as e:
            print(f"PyMuPDF failed: {e}")
    
    if HAS_PDFPLUMBER:
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        content += page_text + "\n"
            if content.strip():
                return content
        except Exception as e:
            print(f"pdfplumber failed: {e}")
    
    try:
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page_num, page in enumerate(reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text:
                        content += page_text + "\n"
                except Exception as e:
                    print(f"PyPDF2 page {page_num} failed: {e}")
                    continue
    except Exception as e:
        print(f"PyPDF2 failed: {e}")
    
    return content

def smart_read_file(file_path: str) -> str:
    """Read files with robust error handling"""
    try:
        content = ""
        
        if file_path.endswith('.pdf'):
            content = extract_pdf_content(file_path)
        
        elif file_path.endswith(('.docx', '.doc')):
            doc = docx.Document(file_path)
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    content += paragraph.text + "\n"
        
        elif file_path.endswith(('.txt', '.md', '.json', '.yaml', '.yml')):
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                content = file.read()
        
        if content:
            content = re.sub(r'•|·||‣|⁃', '-', content)
            content = re.sub(r'\n\s*\n', '\n\n', content)
            content = re.sub(r'[ \t]+', ' ', content)
        
        return content.strip() if content.strip() else f"Could not extract content from {file_path}"
        
    except Exception as e:
        return f"Error reading {file_path}: {str(e)}"

def find_relevant_documents(query: str, data_path: str = "D:/data") -> list:
    """Find documents relevant to the query"""
    relevant_files = []
    supported_formats = ['*.pdf', '*.txt', '*.docx', '*.doc', '*.md', '*.json']
    
    query_keywords = query.lower().split()
    
    for format in supported_formats:
        for file_path in glob.glob(os.path.join(data_path, "**", format), recursive=True):
            filename = os.path.basename(file_path).lower()
            
            filename_score = sum(1 for keyword in query_keywords if keyword in filename)
            
            try:
                content_sample = smart_read_file(file_path)[:2000].lower()
                content_score = sum(1 for keyword in query_keywords if keyword in content_sample)
                
                if filename_score > 0 or content_score > 0:
                    relevant_files.append({
                        'path': file_path,
                        'filename': os.path.basename(file_path),
                        'relevance_score': filename_score + content_score,
                        'content': smart_read_file(file_path)
                    })
            except:
                continue
    
    relevant_files.sort(key=lambda x: x['relevance_score'], reverse=True)
    return relevant_files[:3]

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

async def generate_streaming_response(user_query: str, relevant_docs: list = None):
    """Generate streaming response for both document and general queries"""
    try:
        # For natural conversation, stream the response character by character
        if is_natural_conversation(user_query):
            response_text = get_conversational_response(user_query)
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
            
            # Now provide a general answer using local model
            messages = [{"role": "user", "content": user_query}]
            response_text = generate_local_response(messages)
            
            for char in response_text:
                yield f"data: {json.dumps({'type': 'content', 'content': char})}\n\n"
                await asyncio.sleep(0.01)
            
            yield f"data: {json.dumps({'type': 'complete', 'documents_used': []})}\n\n"
            return

        # For document-based responses
        messages = create_structured_prompt(user_query, relevant_docs)
        
        # First, send document info
        doc_names = [doc['filename'] for doc in relevant_docs]
        yield f"data: {json.dumps({'type': 'documents', 'documents': doc_names})}\n\n"
        
        # Generate response using local model
        response_text = generate_local_response(messages)
        
        # Stream the response
        for char in response_text:
            yield f"data: {json.dumps({'type': 'content', 'content': char})}\n\n"
            await asyncio.sleep(0.01)
        
        yield f"data: {json.dumps({'type': 'complete', 'documents_used': doc_names})}\n\n"
        
    except Exception as e:
        error_msg = f"I apologize, but I encountered an error: {str(e)}"
        for char in error_msg:
            yield f"data: {json.dumps({'type': 'content', 'content': char})}\n\n"
            await asyncio.sleep(0.01)
        yield f"data: {json.dumps({'type': 'complete', 'documents_used': []})}\n\n"

@app.get("/", response_class=HTMLResponse)
async def read_root():
    with open("chat_interface.html", "r", encoding="utf-8") as f:
        return f.read()

# Keep the original endpoint for compatibility
@app.post("/document-chat")
async def document_chat(chat_message: dict):
    """Main endpoint for document-based chat with structured responses"""
    try:
        user_query = chat_message.get("content", "").strip()
        
        if not user_query:
            return {"response": "Please provide a question."}
        
        if is_natural_conversation(user_query):
            conversational_response = get_conversational_response(user_query)
            return {
                "response": conversational_response,
                "documents_used": [],
                "source": "conversation"
            }
        
        relevant_docs = find_relevant_documents(user_query)
        
        if not relevant_docs:
            messages = [{"role": "user", "content": user_query}]
            response_text = generate_local_response(messages)
            return {
                "response": response_text,
                "documents_used": [],
                "source": "general_knowledge"
            }
        
        messages = create_structured_prompt(user_query, relevant_docs)
        
        response_text = generate_local_response(messages)
        
        return {
            "response": response_text,
            "documents_used": [doc['filename'] for doc in relevant_docs],
            "source": "documents"
        }
        
    except Exception as e:
        return {"response": f"I apologize, but I encountered an error: {str(e)}"}

# New streaming endpoint
@app.post("/chat-stream")
async def chat_stream(chat_message: dict):
    """Streaming endpoint for real-time responses"""
    user_query = chat_message.get("content", "").strip()
    
    if not user_query:
        return {"error": "Please provide a question."}
    
    # Find relevant documents for the query
    relevant_docs = find_relevant_documents(user_query) if not is_natural_conversation(user_query) else None
    
    return StreamingResponse(
        generate_streaming_response(user_query, relevant_docs),
        media_type="text/event-stream"
    )

@app.get("/list-documents")
async def list_documents():
    """List all available documents"""
    try:
        supported_formats = ['*.pdf', '*.txt', '*.docx', '*.doc', '*.md', '*.json']
        all_files = []
        
        for format in supported_formats:
            all_files.extend(glob.glob(os.path.join("D:/data", "**", format), recursive=True))
        
        return {
            "total_documents": len(all_files),
            "documents": [
                {
                    "name": os.path.basename(f),
                    "path": f,
                    "size": os.path.getsize(f)
                } for f in all_files
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing documents: {str(e)}")

@app.post("/quick-chat")
async def quick_chat(chat_message: dict):
    """Quick chat without documents"""
    try:
        user_query = chat_message.get("content", "")
        
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
        
        response_text = generate_local_response(messages)
        
        return {"response": response_text}
        
    except Exception as e:
        return {"response": f"I'm having trouble responding right now: {str(e)}"}

@app.get("/health")
async def health_check():
    """Check if the local model is loaded"""
    return {
        "status": "healthy" if chat_pipeline else "unhealthy",
        "model_loaded": chat_pipeline is not None,
        "model_name": "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B" if chat_pipeline else None
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)