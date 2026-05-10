# -*- coding: utf-8 -*-
import os
import glob
import chromadb
from sentence_transformers import SentenceTransformer

class RAGAssistant:
    def __init__(self, cache_dir=".ai_cache/rag"):
        self.cache_dir = cache_dir
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
        self.client = chromadb.PersistentClient(path=os.path.join(self.cache_dir, "db"))
        self.collection = self.client.get_or_create_collection("aras_docs")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
            
    def index_codebase(self):
        """Index manifest.py, GEMINI.md, and core logic."""
        docs = []
        # Index GEMINI.md
        if os.path.exists("GEMINI.md"):
            with open("GEMINI.md", "r") as f:
                docs.append({"path": "GEMINI.md", "content": f.read()})
                
        # Index manifest.py files
        for path in glob.glob("**/manifest.py", recursive=True):
            with open(path, "r") as f:
                docs.append({"path": path, "content": f.read()})
        
        # Index core libs
        for path in glob.glob("arasCore/lib/**/*.py", recursive=True):
            with open(path, "r") as f:
                docs.append({"path": path, "content": f.read()})
        
        # Add to vector store
        for i, doc in enumerate(docs):
            self.collection.add(
                documents=[doc['content']],
                metadatas=[{"path": doc['path']}],
                ids=[f"id_{i}"]
            )
        return len(docs)

    def query(self, user_query, n_results=3):
        """Perform vector-based retrieval."""
        # Ensure indexed
        if self.collection.count() == 0:
            self.index_codebase()
            
        results = self.collection.query(
            query_texts=[user_query],
            n_results=n_results
        )
        
        context = ""
        for doc, meta in zip(results['documents'][0], results['metadatas'][0]):
            context += f"--- {meta['path']} ---\n{doc}\n\n"
        
        return f"Retrieved Context from Aras Framework:\n\n{context}"

rag_assistant = RAGAssistant()
