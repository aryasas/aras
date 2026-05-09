# -*- coding: utf-8 -*-
import os
import glob
from flask import current_app

class RAGAssistant:
    def __init__(self, cache_dir=".ai_cache/rag"):
        self.cache_dir = cache_dir
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
            
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
                
        # TODO: Implement vector storage (chromadb/faiss)
        # For prototype: simple flat file cache
        with open(os.path.join(self.cache_dir, "index.txt"), "w") as f:
            for doc in docs:
                f.write(f"--- {doc['path']} ---\n{doc['content']}\n\n")
        return len(docs)

    def query(self, user_query):
        """Perform simple text-based retrieval."""
        index_path = os.path.join(self.cache_dir, "index.txt")
        if not os.path.exists(index_path):
            self.index_codebase()
            
        # Very basic retrieval: keyword match or return full context
        with open(index_path, "r") as f:
            content = f.read()
        
        # In a real RAG: query embeddings here
        return f"Context from Aras Framework Docs:\n\n{content[:2000]}..."

rag_assistant = RAGAssistant()
