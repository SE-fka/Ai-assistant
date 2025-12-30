import os
import aiofiles
import logging
from pathlib import Path
from typing import Dict, Any
from models.schemas import FileType

class FileProcessor:
    def __init__(self):
        self.supported_formats = {
            # Document formats
            '.pdf': FileType.PDF,
            '.doc': FileType.DOC,
            '.docx': FileType.DOCX,
            '.txt': FileType.TXT,
            '.rtf': FileType.RTF,
            '.odt': FileType.ODT,
            '.md': FileType.MD,
            
            # Spreadsheet formats
            '.xls': FileType.XLS,
            '.xlsx': FileType.XLSX,
            '.csv': FileType.CSV,
            
            # Presentation formats
            '.ppt': FileType.PPT,
            '.pptx': FileType.PPTX,
            
            # Image formats
            '.jpg': FileType.JPG,
            '.jpeg': FileType.JPEG,
            '.png': FileType.PNG,
            '.gif': FileType.GIF,
            '.bmp': FileType.BMP,
            '.tiff': FileType.TIFF,
            '.tif': FileType.TIFF,
            
            # Web and data formats
            '.html': FileType.HTML,
            '.htm': FileType.HTML,
            '.json': FileType.JSON,
            '.xml': FileType.XML,
        }
        
        # Patterns for temporary files to exclude
        self.temporary_file_patterns = [
            '~$',           # Office temporary files
            '._',           # Mac OS temporary files
            '.tmp',         # General temporary files
            '.temp',        # General temporary files
            'Thumbs.db',    # Windows thumbnail cache
            '.DS_Store',    # Mac OS directory metadata
        ]
        
        # Check available dependencies at initialization
        self._check_dependencies()
    
    def _check_dependencies(self):
        """Check and log available dependencies"""
        dependencies = {
            'PyMuPDF (fitz)': self._check_fitz(),
            'pypdf/PyPDF2': self._check_pypdf(),
            'python-docx': self._check_docx(),
            'docx2txt': self._check_docx2txt(),
            'pandas': self._check_pandas(),
            'python-pptx': self._check_pptx(),
            'pytesseract': self._check_pytesseract(),
            'PIL (Pillow)': self._check_pillow(),
            'BeautifulSoup': self._check_beautifulsoup(),
        }
        
        available = [name for name, available in dependencies.items() if available]
        missing = [name for name, available in dependencies.items() if not available]
        
        logging.info(f"✅ Available dependencies: {', '.join(available)}")
        if missing:
            logging.warning(f"⚠️ Missing dependencies: {', '.join(missing)}")
    
    def _check_fitz(self):
        try:
            import fitz
            return True
        except ImportError:
            return False
    
    def _check_pypdf(self):
        try:
            import pypdf
            return True
        except ImportError:
            try:
                import PyPDF2
                return True
            except ImportError:
                return False
    
    def _check_docx(self):
        try:
            from docx import Document
            return True
        except ImportError:
            return False
    
    def _check_docx2txt(self):
        try:
            import docx2txt
            return True
        except ImportError:
            return False
    
    def _check_pandas(self):
        try:
            import pandas
            return True
        except ImportError:
            return False
    
    def _check_pptx(self):
        try:
            from pptx import Presentation
            return True
        except ImportError:
            return False
    
    def _check_pytesseract(self):
        try:
            import pytesseract
            return True
        except ImportError:
            return False
    
    def _check_pillow(self):
        try:
            from PIL import Image
            return True
        except ImportError:
            return False
    
    def _check_beautifulsoup(self):
        try:
            from bs4 import BeautifulSoup
            return True
        except ImportError:
            return False
    
    def is_temporary_file(self, filename: str) -> bool:
        """Check if a file is a temporary/system file that should be skipped"""
        filename_lower = filename.lower()
        
        for pattern in self.temporary_file_patterns:
            if pattern.lower() in filename_lower:
                return True
        
        # Additional checks for hidden files
        if filename.startswith('.') or filename.startswith('~'):
            return True
            
        return False
    
    async def process_file(self, file_path: str, filename: str) -> dict:
        """Process a file and extract its content with comprehensive error handling"""
        try:
            # Validate inputs
            if not file_path or not filename:
                raise ValueError("File path and filename cannot be empty")
            
            file_path = Path(file_path)
            
            # Check if file is temporary and should be skipped
            if self.is_temporary_file(filename):
                raise ValueError(f"Temporary file skipped: {filename}")
            
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            
            if not file_path.is_file():
                raise ValueError(f"Path is not a file: {file_path}")
            
            # Get file size without limits
            file_size = file_path.stat().st_size
            
            file_ext = Path(filename).suffix.lower()
            file_type = self.supported_formats.get(file_ext)
            
            if not file_type:
                raise ValueError(f"Unsupported file format: {file_ext}. Supported: {list(self.supported_formats.keys())}")
            
            # Process file based on type
            content = await self._process_file_by_type(file_path, file_type, filename)
            
            # Validate content was extracted
            if not content or not content.strip():
                logging.warning(f"⚠️ No content extracted from file: {filename}")
                content = f"File processed but no extractable content found: {filename}"
            
            return {
                "filename": filename,
                "file_type": file_type.value,
                "content": content,
                "file_size": file_size,
                "file_extension": file_ext,
                "processing_success": True
            }
            
        except Exception as e:
            logging.error(f"❌ Error processing {filename}: {e}", exc_info=True)
            return {
                "filename": filename,
                "file_type": "unknown",
                "content": f"Error processing file: {str(e)}",
                "file_size": 0,
                "file_extension": Path(filename).suffix.lower(),
                "processing_success": False,
                "error": str(e)
            }
    
    async def _process_file_by_type(self, file_path: Path, file_type: FileType, filename: str) -> str:
        """Route file processing based on type with error handling"""
        try:
            content = ""
            
            # Document processing
            if file_type == FileType.PDF:
                content = await self._process_pdf(file_path)
            elif file_type == FileType.DOCX:
                content = await self._process_docx(file_path)
            elif file_type == FileType.DOC:
                content = await self._process_doc(file_path)
            elif file_type in [FileType.TXT, FileType.MD, FileType.RTF, FileType.ODT]:
                content = await self._process_text(file_path)
            
            # Spreadsheet processing
            elif file_type in [FileType.CSV, FileType.XLS, FileType.XLSX]:
                content = await self._process_tabular(file_path, file_type)
            
            # Presentation processing
            elif file_type in [FileType.PPT, FileType.PPTX]:
                content = await self._process_presentation(file_path, file_type)
            
            # Image processing
            elif file_type in [FileType.JPG, FileType.JPEG, FileType.PNG, FileType.GIF, 
                             FileType.BMP, FileType.TIFF]:
                content = await self._process_image(file_path, file_type)
            
            # Web and data formats
            elif file_type == FileType.HTML:
                content = await self._process_html(file_path)
            elif file_type == FileType.JSON:
                content = await self._process_json(file_path)
            elif file_type == FileType.XML:
                content = await self._process_xml(file_path)
            
            else:
                # Fallback to text processing
                content = await self._process_text(file_path)
            
            return content
            
        except Exception as e:
            logging.error(f"❌ Error in _process_file_by_type for {filename}: {e}")
            raise
    
    async def _process_pdf(self, file_path: Path) -> str:
        """Process PDF files using available PDF libraries"""
        # Try PyMuPDF first for better performance
        if self._check_fitz():
            try:
                import fitz
                text = ""
                doc = fitz.open(str(file_path))
                for page in doc:
                    text += page.get_text() + "\n"
                doc.close()
                if text.strip():
                    logging.info("✅ PDF processed successfully with PyMuPDF")
                    return text
                else:
                    logging.warning(f"⚠️ PyMuPDF extracted no text from PDF: {file_path}")
            except Exception as e:
                logging.error(f"PyMuPDF processing error: {e}")
        
        # Try pypdf (new name for PyPDF2)
        if self._check_pypdf():
            try:
                # Try pypdf first (new package name)
                try:
                    from pypdf import PdfReader
                except ImportError:
                    # Fallback to PyPDF2
                    from PyPDF2 import PdfReader
                
                text = ""
                reader = PdfReader(str(file_path))
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                logging.info("✅ PDF processed successfully with pypdf/PyPDF2")
                return text
            except Exception as e:
                logging.error(f"pypdf/PyPDF2 processing error: {e}")
        
        # If no PDF libraries are available
        logging.error("No PDF processing libraries available")
        return "Error: No PDF processing libraries available. Install PyMuPDF or pypdf: pip install pymupdf"
    
    async def _process_docx(self, file_path: Path) -> str:
        if not self._check_docx():
            return "DOCX processing requires python-docx library. Install with: pip install python-docx"
        
        try:
            from docx import Document
            doc = Document(str(file_path))
            text = "\n".join([p.text for p in doc.paragraphs])
            if not text.strip():
                logging.warning(f"⚠️ DOCX file appears to be empty: {file_path}")
            else:
                logging.info("✅ DOCX file processed successfully")
            return text
        except Exception as e:
            # Check for specific temporary file errors
            error_msg = str(e).lower()
            if "package not found" in error_msg or "cannot open" in error_msg:
                logging.warning(f"⚠️ Skipping temporary/corrupted DOCX file: {file_path.name}")
                return f"Skipped temporary or corrupted DOCX file: {file_path.name}"
            else:
                logging.error(f"DOCX processing error for {file_path}: {e}")
                return f"Error processing Word document: {str(e)}"
    
    async def _process_doc(self, file_path: Path) -> str:
        # For .doc files, use docx2txt or fallback to text extraction
        if self._check_docx2txt():
            try:
                import docx2txt
                text = docx2txt.process(str(file_path))
                if text.strip():
                    logging.info("✅ DOC file processed successfully with docx2txt")
                    return text
                else:
                    logging.warning(f"⚠️ docx2txt extracted no text from DOC: {file_path}")
            except Exception as e:
                logging.error(f"docx2txt processing error: {e}")
        
        # Fallback to text extraction
        logging.warning("docx2txt not available or failed, falling back to text extraction for .doc file")
        return await self._process_text(file_path)
    
    async def _process_text(self, file_path: Path) -> str:
        """Process text files with multiple encoding fallbacks"""
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1', 'utf-16']
        
        for encoding in encodings:
            try:
                async with aiofiles.open(file_path, 'r', encoding=encoding) as f:
                    content = await f.read()
                if content.strip():
                    logging.info(f"✅ Text file processed successfully with {encoding} encoding")
                    return content
            except UnicodeDecodeError:
                continue
            except Exception as e:
                logging.error(f"Text file processing error with {encoding}: {e}")
                continue
        
        # If all encodings fail, try binary read
        try:
            async with aiofiles.open(file_path, 'rb') as f:
                binary_content = await f.read()
            # Try to decode with replace for invalid characters
            content = binary_content.decode('utf-8', errors='replace')
            logging.info("✅ Text file processed with binary fallback")
            return content
        except Exception as e:
            logging.error(f"All text processing attempts failed for {file_path}: {e}")
            return f"Error reading text file: Unable to decode with any supported encoding"
    
    async def _process_tabular(self, file_path: Path, file_type: FileType) -> str:
        if not self._check_pandas():
            return "Tabular data processing requires pandas. Install with: pip install pandas openpyxl xlrd"
        
        try:
            import pandas as pd
            
            # Read file based on type
            if file_type == FileType.CSV:
                df = pd.read_csv(str(file_path))
            else:
                # Handle both .xls and .xlsx files
                df = pd.read_excel(str(file_path))
            
            # Validate dataframe
            if df.empty:
                return f"Tabular file is empty: {file_path.name}"
            
            # Create summary text
            text = f"Data from {file_path.name}:\n"
            text += f"Shape: {df.shape[0]} rows, {df.shape[1]} columns\n"
            text += "Columns: " + ", ".join(df.columns.astype(str)) + "\n\n"
            text += "Sample data (first 5 rows):\n" + df.head().to_string()
            
            logging.info("✅ Tabular file processed successfully")
            return text
            
        except Exception as e:
            logging.error(f"Tabular data processing error for {file_path}: {e}")
            return f"Error processing data file: {str(e)}"
    
    async def _process_presentation(self, file_path: Path, file_type: FileType) -> str:
        if not self._check_pptx():
            return "PPT processing requires python-pptx library. Install with: pip install python-pptx"
        
        try:
            if file_type == FileType.PPTX:
                from pptx import Presentation
                prs = Presentation(str(file_path))
                text_parts = []
                for slide_number, slide in enumerate(prs.slides, 1):
                    slide_text = []
                    for shape in slide.shapes:
                        if hasattr(shape, "text") and shape.text.strip():
                            slide_text.append(shape.text.strip())
                    if slide_text:
                        text_parts.append(f"Slide {slide_number}: " + " | ".join(slide_text))
                
                if text_parts:
                    logging.info("✅ Presentation file processed successfully")
                    return "\n".join(text_parts)
                else:
                    return f"Presentation file contains no extractable text: {file_path.name}"
            else:
                return f"Presentation file detected: {file_path.name}. For .ppt files, consider converting to .pptx for better text extraction."
                
        except Exception as e:
            logging.error(f"Presentation processing error for {file_path}: {e}")
            return f"Error processing presentation file: {str(e)}"
    
    async def _process_image(self, file_path: Path, file_type: FileType) -> str:
        if not self._check_pytesseract() or not self._check_pillow():
            return f"Image OCR requires pytesseract and PIL. Install with: pip install pytesseract pillow"
        
        try:
            import pytesseract
            from PIL import Image
            
            image = Image.open(str(file_path))
            text = pytesseract.image_to_string(image)
            
            if text.strip():
                logging.info("✅ Image processed successfully with OCR")
                return text
            else:
                return f"Image file: {file_path.name}. No text detected via OCR."
                    
        except Exception as e:
            logging.error(f"Image processing error for {file_path}: {e}")
            return f"Error processing image file: {str(e)}"
    
    async def _process_html(self, file_path: Path) -> str:
        if not self._check_beautifulsoup():
            logging.warning("BeautifulSoup not available, falling back to text extraction for HTML file")
            return await self._process_text(file_path)
        
        try:
            from bs4 import BeautifulSoup
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                html_content = await f.read()
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style elements
            for element in soup(["script", "style", "meta", "link"]):
                element.decompose()
            
            text = soup.get_text(separator='\n', strip=True)
            if text.strip():
                logging.info("✅ HTML file processed successfully")
                return text
            else:
                return f"HTML file contains no extractable text: {file_path.name}"
                
        except Exception as e:
            logging.error(f"HTML processing error for {file_path}: {e}")
            return f"Error processing HTML file: {str(e)}"
    
    async def _process_json(self, file_path: Path) -> str:
        try:
            import json
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
            
            data = json.loads(content)
            formatted_json = json.dumps(data, indent=2, ensure_ascii=False)
            
            if len(formatted_json) > 10000:  # Limit very large JSON output for display
                return f"JSON file too large to display fully. First 10,000 chars:\n{formatted_json[:10000]}..."
            else:
                logging.info("✅ JSON file processed successfully")
                return formatted_json
                
        except json.JSONDecodeError as e:
            return f"Invalid JSON file: {str(e)}"
        except Exception as e:
            logging.error(f"JSON processing error for {file_path}: {e}")
            return f"Error processing JSON file: {str(e)}"
    
    async def _process_xml(self, file_path: Path) -> str:
        if not self._check_beautifulsoup():
            logging.warning("BeautifulSoup not available, falling back to text extraction for XML file")
            return await self._process_text(file_path)
        
        try:
            from bs4 import BeautifulSoup
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                xml_content = await f.read()
            
            soup = BeautifulSoup(xml_content, 'xml')
            text = soup.get_text(separator='\n', strip=True)
            
            if text.strip():
                logging.info("✅ XML file processed successfully")
                return text
            else:
                return f"XML file contains no extractable text: {file_path.name}"
                
        except Exception as e:
            logging.error(f"XML processing error for {file_path}: {e}")
            return f"Error processing XML file: {str(e)}"
    
    def get_supported_formats(self) -> list:
        """Return list of supported file extensions"""
        return list(self.supported_formats.keys())
    
    def get_temporary_file_patterns(self) -> list:
        """Return list of temporary file patterns that will be skipped"""
        return self.temporary_file_patterns.copy()
    
    def get_available_dependencies(self) -> dict:
        """Return information about available dependencies"""
        return {
            'PyMuPDF (fitz)': self._check_fitz(),
            'pypdf/PyPDF2': self._check_pypdf(),
            'python-docx': self._check_docx(),
            'docx2txt': self._check_docx2txt(),
            'pandas': self._check_pandas(),
            'python-pptx': self._check_pptx(),
            'pytesseract': self._check_pytesseract(),
            'PIL (Pillow)': self._check_pillow(),
            'BeautifulSoup': self._check_beautifulsoup(),
        }
    
    def validate_file(self, file_path: str) -> tuple[bool, str]:
        """Validate if a file can be processed"""
        try:
            path = Path(file_path)
            if not path.exists():
                return False, "File does not exist"
            if not path.is_file():
                return False, "Path is not a file"
            if path.stat().st_size == 0:
                return False, "File is empty"
            if self.is_temporary_file(path.name):
                return False, "File is a temporary/system file"
            if path.suffix.lower() not in self.supported_formats:
                return False, f"Unsupported file format. Supported: {list(self.supported_formats.keys())}"
            return True, "File is valid"
        except Exception as e:
            return False, f"Validation error: {str(e)}"

file_processor = FileProcessor()