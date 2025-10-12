# rag_store.py
import faiss, pickle, numpy as np
import dotenv, os, io
import PyPDF2
from openai import OpenAI

dotenv.load_dotenv()

client = OpenAI()
EMBED_MODEL = "text-embedding-3-small"

class RAGService:
    def __init__(self, vs_dir: str):
        self.vs_dir = vs_dir
        self.cache = {}  # case_id -> (index, chunks)
    
    def create_from_pdf(self, case_id: str, pdf_content: bytes):
        """Create vector store from PDF binary content"""
        # Convert bytes to file-like object for PyPDF2
        pdf_file = io.BytesIO(pdf_content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        # Extract text from all pages
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        
        # Split into chunks
        chunks = self._chunk_text(text)
        
        # Create embeddings for each chunk
        embeddings = []
        for chunk in chunks:
            embedding = client.embeddings.create(
                model=EMBED_MODEL, 
                input=[chunk]
            ).data[0].embedding
            embeddings.append(embedding)
        
        # Create FAISS index
        embeddings_array = np.array(embeddings, dtype="float32")
        faiss.normalize_L2(embeddings_array)
        
        index = faiss.IndexFlatIP(len(embeddings[0]))
        index.add(embeddings_array)
        
        # Save to disk
        os.makedirs(self.vs_dir, exist_ok=True)
        faiss.write_index(index, f"{self.vs_dir}/{case_id}.faiss")
        with open(f"{self.vs_dir}/{case_id}.meta.pkl", "wb") as f:
            pickle.dump(chunks, f)
        
        # Cache for immediate use
        self.cache[case_id] = (index, chunks)
        
        return len(chunks)
    
    def _chunk_text(self, text, chunk_size=1000, overlap=200):
        """Split text into overlapping chunks"""
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            if chunk.strip():  # Only add non-empty chunks
                chunks.append(chunk)
            start = end - overlap
        return chunks
    
    def load(self, case_id: str):
        if case_id in self.cache: return
        index = faiss.read_index(f"{self.vs_dir}/{case_id}.faiss")
        with open(f"{self.vs_dir}/{case_id}.meta.pkl", "rb") as f:
            chunks = pickle.load(f)
        self.cache[case_id] = (index, chunks)

    def search(self, case_id: str, query: str, k: int = 6):
        self.load(case_id)
        index, chunks = self.cache[case_id]
        q = client.embeddings.create(model=EMBED_MODEL, input=[query]).data[0].embedding
        q = np.array([q], dtype="float32")
        faiss.normalize_L2(q)
        D, I = index.search(q, k)
        out = []
        for idx in I[0]:
            out.append(chunks[idx])
        return out

    def remove(self, case_id: str):
        if case_id in self.cache:
            del self.cache[case_id]
            os.remove(f"{self.vs_dir}/{case_id}.faiss")
            os.remove(f"{self.vs_dir}/{case_id}.meta.pkl")