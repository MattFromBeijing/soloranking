# injestorService.py
import os
import uuid
import faiss
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional
from pydantic import BaseModel
from PyPDF2 import PdfReader
from openai import OpenAI
import tiktoken
import pickle
import logging

logger = logging.getLogger(__name__)


class Chunk(BaseModel):
    id: str
    case_id: str
    page: int
    text: str


class IngestionConfig(BaseModel):
    embed_model: str = "text-embedding-3-small"
    chunk_tokens: int = 500
    chunk_overlap: int = 80
    encoding_name: str = "cl100k_base"


class PDFIntakeService:
    """Service for ingesting PDF documents into a vector database."""
    
    def __init__(self, config: Optional[IngestionConfig] = None, openai_client: Optional[OpenAI] = None):
        """
        Initialize the document ingestion service.
        
        Args:
            config: Configuration for the ingestion process
            openai_client: OpenAI client instance (will create default if not provided)
        """
        self.config = config or IngestionConfig()
        self.client = openai_client or OpenAI()
        self.tokenizer = tiktoken.get_encoding(self.config.encoding_name)
    
    def pdf_to_text(self, pdf_path: str) -> List[str]:
        """Extract text from PDF pages."""
        try:
            reader = PdfReader(pdf_path)
            return [page.extract_text() or "" for page in reader.pages]
        except Exception as e:
            logger.error(f"Error reading PDF {pdf_path}: {e}")
            raise
    
    def chunk_text(self, text: str) -> List[str]:
        """Split text into overlapping chunks based on token count."""
        toks = self.tokenizer.encode(text)
        chunks = []
        i = 0
        while i < len(toks):
            chunk = toks[i:i + self.config.chunk_tokens]
            chunks.append(self.tokenizer.decode(chunk))
            i += (self.config.chunk_tokens - self.config.chunk_overlap)
        return chunks
    
    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for a list of texts."""
        try:
            resp = self.client.embeddings.create(model=self.config.embed_model, input=texts)
            arr = np.array([d.embedding for d in resp.data], dtype="float32")
            return arr
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise
    
    def ingest_document(self, pdf_path: str, output_dir: str) -> str:
        """
        Ingest a PDF document into the vector database.
        
        Args:
            pdf_path: Path to the PDF file
            output_dir: Directory to save the vector index and metadata
            
        Returns:
            case_id: Unique identifier for the ingested document
        """
        case_id = str(uuid.uuid4())
        
        try:
            # Extract text from PDF
            pages = self.pdf_to_text(pdf_path)
            logger.info(f"Extracted {len(pages)} pages from {pdf_path}")
            
            # Create chunks
            chunks: List[Chunk] = []
            for page_num, page_text in enumerate(pages):
                for chunk_text in self.chunk_text(page_text):
                    if chunk_text.strip():
                        chunks.append(Chunk(
                            id=str(uuid.uuid4()),
                            case_id=case_id,
                            page=page_num + 1,
                            text=chunk_text
                        ))
            
            logger.info(f"Created {len(chunks)} chunks for document {case_id}")
            
            # Generate embeddings
            embeddings = self.embed_texts([chunk.text for chunk in chunks])
            
            # Create FAISS index
            dim = embeddings.shape[1]
            index = faiss.IndexFlatIP(dim)
            
            # Normalize for cosine similarity
            faiss.normalize_L2(embeddings)
            index.add(embeddings)
            
            # Save to disk
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            
            faiss_path = os.path.join(output_dir, f"{case_id}.faiss")
            metadata_path = os.path.join(output_dir, f"{case_id}.meta.pkl")
            
            faiss.write_index(index, faiss_path)
            with open(metadata_path, "wb") as f:
                pickle.dump(chunks, f)
            
            logger.info(f"Successfully ingested document {case_id} with {len(chunks)} chunks")
            return case_id
            
        except Exception as e:
            logger.error(f"Error ingesting document {pdf_path}: {e}")
            raise
    
    def load_document_index(self, case_id: str, index_dir: str) -> tuple[faiss.Index, List[Chunk]]:
        """
        Load a previously ingested document's index and metadata.
        
        Args:
            case_id: The case ID of the document
            index_dir: Directory containing the index files
            
        Returns:
            Tuple of (FAISS index, list of chunks)
        """
        try:
            faiss_path = os.path.join(index_dir, f"{case_id}.faiss")
            metadata_path = os.path.join(index_dir, f"{case_id}.meta.pkl")
            
            if not os.path.exists(faiss_path) or not os.path.exists(metadata_path):
                raise FileNotFoundError(f"Index files not found for case {case_id}")
            
            index = faiss.read_index(faiss_path)
            with open(metadata_path, "rb") as f:
                chunks = pickle.load(f)
            
            return index, chunks
            
        except Exception as e:
            logger.error(f"Error loading document index {case_id}: {e}")
            raise
    
    def search_similar_chunks(self, query: str, case_id: str, index_dir: str, 
                            top_k: int = 5) -> List[tuple[Chunk, float]]:
        """
        Search for similar chunks in an ingested document.
        
        Args:
            query: Search query
            case_id: The case ID of the document
            index_dir: Directory containing the index files
            top_k: Number of top results to return
            
        Returns:
            List of tuples (chunk, similarity_score)
        """
        try:
            # Load the index and chunks
            index, chunks = self.load_document_index(case_id, index_dir)
            
            # Generate query embedding
            query_embedding = self.embed_texts([query])
            faiss.normalize_L2(query_embedding)
            
            # Search
            scores, indices = index.search(query_embedding, top_k)
            
            # Return results
            results = []
            for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
                if idx < len(chunks):
                    results.append((chunks[idx], float(score)))
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching similar chunks: {e}")
            raise


if __name__ == "__main__":
    """
    Command line interface for the document ingestion service.
    Usage: python injestorService.py <pdf_path> <output_directory>
    """
    import sys
    
    if len(sys.argv) != 3:
        print("Usage: python injestorService.py <pdf_path> <output_directory>")
        sys.exit(1)
    
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Create service and ingest document
    service = PDFIntakeService()
    try:
        case_id = service.ingest_document(sys.argv[1], sys.argv[2])
        print(f"Successfully ingested document with case ID: {case_id}")
    except Exception as e:
        print(f"Error ingesting document: {e}")
        sys.exit(1)
