import os
import glob
import re
import PyPDF2
import docx
from config import settings

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

def find_relevant_documents(query: str, data_path: str = None) -> list:
    """Find documents relevant to the query"""
    if data_path is None:
        data_path = settings.DATA_PATH
        
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

def list_documents(data_path: str = None):
    """List all available documents"""
    if data_path is None:
        data_path = settings.DATA_PATH
        
    try:
        supported_formats = ['*.pdf', '*.txt', '*.docx', '*.doc', '*.md', '*.json']
        all_files = []
        
        for format in supported_formats:
            all_files.extend(glob.glob(os.path.join(data_path, "**", format), recursive=True))
        
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
        raise Exception(f"Error listing documents: {str(e)}")