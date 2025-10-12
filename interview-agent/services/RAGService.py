# rag_store.py
import faiss, pickle, numpy as np
import dotenv
from openai import OpenAI

dotenv.load_dotenv()

client = OpenAI()
EMBED_MODEL = "text-embedding-3-small"

class RAGService:
    def __init__(self, vs_dir: str):
        self.vs_dir = vs_dir
        self.cache = {}  # case_id -> (index, chunks)

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