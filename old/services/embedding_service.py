from sentence_transformers import SentenceTransformer
import logging
import asyncio
from config import settings
import numpy as np
from typing import List, Dict, Any

class TextSplitter:
    """Simple text splitter to replace langchain dependency"""
    def __init__(self, chunk_size=1000, chunk_overlap=200):
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        if chunk_overlap < 0:
            raise ValueError("chunk_overlap cannot be negative")
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")
            
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def split_text(self, text: str) -> List[str]:
        """Split text into chunks with overlap and error handling"""
        if not text or not isinstance(text, str):
            return []
        
        if len(text.strip()) == 0:
            return []
        
        if len(text) <= self.chunk_size:
            return [text.strip()]
        
        try:
            chunks = []
            start = 0
            
            while start < len(text):
                # Calculate end position
                end = start + self.chunk_size
                
                # If this isn't the first chunk, include overlap
                if start > 0:
                    start = max(0, start - self.chunk_overlap)
                
                # Ensure we don't go beyond text length
                if end > len(text):
                    end = len(text)
                
                chunk = text[start:end].strip()
                if chunk:  # Only add non-empty chunks
                    chunks.append(chunk)
                
                # Break if we've reached the end
                if end == len(text):
                    break
                    
                start = end
            
            return chunks
            
        except Exception as e:
            logging.error(f"❌ Text splitting error: {e}")
            # Fallback: split by sentences or return entire text
            return [text.strip()]

class EmbeddingService:
    def __init__(self):
        self.embedder = None
        self.text_splitter = None
        self._initialize_services()
    
    def _initialize_services(self):
        """Initialize embedding model and text splitter with error handling"""
        try:
            # Initialize text splitter first
            chunk_size = getattr(settings, 'CHUNK_SIZE', 1000)
            chunk_overlap = getattr(settings, 'CHUNK_OVERLAP', 200)
            
            self.text_splitter = TextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )
            logging.info(f"✅ Text splitter initialized: chunk_size={chunk_size}, chunk_overlap={chunk_overlap}")
            
        except Exception as e:
            logging.error(f"❌ Failed to initialize text splitter: {e}")
            # Fallback text splitter
            self.text_splitter = TextSplitter(1000, 200)
        
        try:
            # Try to load the specified embedding model
            model_name = getattr(settings, 'EMBEDDING_MODEL', 'all-MiniLM-L6-v2')
            self.embedder = SentenceTransformer(model_name)
            logging.info(f"✅ Embedding model loaded: {model_name}")
            
        except Exception as e:
            logging.error(f"❌ Failed to load embedding model {getattr(settings, 'EMBEDDING_MODEL', 'unknown')}: {e}")
            try:
                # Fallback to a reliable model
                self.embedder = SentenceTransformer("all-MiniLM-L6-v2")
                logging.info("🔄 Using fallback embedding model: all-MiniLM-L6-v2")
            except Exception as fallback_error:
                logging.error(f"💥 Critical: Failed to load fallback embedding model: {fallback_error}")
                raise RuntimeError("Could not load any embedding model") from fallback_error
    
    async def chunk_and_embed(self, content: str, metadata: dict = None) -> List[Dict[str, Any]]:
        """Chunk text and generate embeddings with comprehensive error handling"""
        try:
            # Validate inputs
            if not content or not isinstance(content, str):
                logging.warning("⚠️ Empty or invalid content provided for chunking")
                return []
            
            if metadata is None:
                metadata = {}
            
            # Split text into chunks
            try:
                chunks = self.text_splitter.split_text(content)
                if not chunks:
                    logging.warning("⚠️ No chunks created from content")
                    return []
                
                logging.info(f"📚 Created {len(chunks)} chunks from document")
                
            except Exception as e:
                logging.error(f"❌ Text splitting error: {e}")
                # Fallback: use the entire content as one chunk
                chunks = [content]
            
            # Generate embeddings
            try:
                # Run embedding generation in thread pool to avoid blocking
                embeddings = await asyncio.get_event_loop().run_in_executor(
                    None, self._generate_embeddings, chunks
                )
                
                if not embeddings:
                    logging.error("❌ No embeddings generated")
                    return []
                
            except Exception as e:
                logging.error(f"❌ Embedding generation error: {e}")
                return []
            
            # Prepare chunk data
            chunk_data = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                try:
                    chunk_info = {
                        "chunk_id": i,
                        "content": chunk,
                        "embedding": embedding.tolist() if hasattr(embedding, 'tolist') else embedding,
                        "token_count": len(chunk.split()),
                        "char_count": len(chunk),
                        "metadata": metadata.copy()  # Create a copy to avoid mutation issues
                    }
                    chunk_data.append(chunk_info)
                    
                except Exception as e:
                    logging.error(f"❌ Error preparing chunk {i}: {e}")
                    continue
            
            if not chunk_data:
                logging.error("❌ No valid chunk data created")
                return []
            
            logging.info(f"✅ Successfully created {len(chunk_data)} embedded chunks")
            return chunk_data
            
        except Exception as e:
            logging.error(f"💥 Critical error in chunk_and_embed: {e}", exc_info=True)
            return []
    
    def _generate_embeddings(self, chunks: List[str]) -> List[np.ndarray]:
        """Generate embeddings for chunks with error handling"""
        try:
            if not chunks:
                return []
            
            # Filter out empty chunks
            valid_chunks = [chunk for chunk in chunks if chunk and chunk.strip()]
            if not valid_chunks:
                return []
            
            embeddings = self.embedder.encode(valid_chunks)
            
            # Ensure we return a list for each input chunk
            result = []
            chunk_idx = 0
            for chunk in chunks:
                if chunk and chunk.strip():
                    result.append(embeddings[chunk_idx])
                    chunk_idx += 1
                else:
                    # For empty chunks, create a zero vector
                    empty_embedding = np.zeros(self.embedder.get_sentence_embedding_dimension())
                    result.append(empty_embedding)
            
            return result
            
        except Exception as e:
            logging.error(f"❌ Error in _generate_embeddings: {e}")
            # Return zero vectors as fallback
            embedding_dim = self.embedder.get_sentence_embedding_dimension()
            return [np.zeros(embedding_dim) for _ in chunks]
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the embedding model"""
        try:
            if not self.embedder:
                return {"error": "Embedding model not initialized"}
            
            return {
                "model_name": self.embedder._modules['0'].auto_model.config.name_or_path,
                "embedding_dimension": self.embedder.get_sentence_embedding_dimension(),
                "max_sequence_length": self.embedder.get_max_seq_length(),
                "text_splitter_config": {
                    "chunk_size": self.text_splitter.chunk_size,
                    "chunk_overlap": self.text_splitter.chunk_overlap
                }
            }
        except Exception as e:
            logging.error(f"❌ Error getting model info: {e}")
            return {"error": str(e)}
    
    async def validate_embedding_quality(self, text: str) -> Dict[str, Any]:
        """Validate embedding quality for a sample text"""
        try:
            chunks = self.text_splitter.split_text(text)
            if not chunks:
                return {"error": "No chunks created from sample text"}
            
            embeddings = await asyncio.get_event_loop().run_in_executor(
                None, self.embedder.encode, chunks
            )
            
            # Calculate some basic statistics
            embedding_norms = [np.linalg.norm(emb) for emb in embeddings]
            
            return {
                "chunk_count": len(chunks),
                "embedding_dimension": embeddings[0].shape[0],
                "average_embedding_norm": np.mean(embedding_norms),
                "embedding_norm_std": np.std(embedding_norms),
                "status": "success"
            }
            
        except Exception as e:
            logging.error(f"❌ Embedding quality validation error: {e}")
            return {"error": str(e), "status": "failed"}

# Global instance with error handling
try:
    embedding_service = EmbeddingService()
except Exception as e:
    logging.error(f"💥 Failed to initialize EmbeddingService: {e}")
    # Create a placeholder that will fail gracefully
    class FailedEmbeddingService:
        async def chunk_and_embed(self, content: str, metadata: dict = None):
            logging.error("Embedding service unavailable")
            return []
    
    embedding_service = FailedEmbeddingService()