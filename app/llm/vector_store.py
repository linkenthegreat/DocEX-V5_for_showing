"""Simple vector store for testing RAG capabilities"""

import os
from pathlib import Path
import numpy as np
from typing import List, Dict, Any, Optional
try:
    from langchain_community.vectorstores import Chroma
    from langchain_community.embeddings import FastEmbedEmbeddings
except ImportError:
    print("Warning: langchain packages not installed. Install with: pip install langchain langchain-community chromadb")

class SimpleVectorStore:
    """Lightweight vector store for RAG testing"""
    
    def __init__(self, persist_dir="/vector_db"):
        self.persist_dir = persist_dir
        os.makedirs(persist_dir, exist_ok=True)
        
        # Initialize embeddings model
        self.embeddings = FastEmbedEmbeddings()
        self.db = None
        
    def add_documents(self, documents, collection_name="test_collection"):
        """Add documents to the vector store"""
        # Create a Chroma instance
        self.db = Chroma.from_documents(
            documents=documents,
            embedding=self.embeddings,
            persist_directory=os.path.join(self.persist_dir, collection_name)
        )
        self.db.persist()
        return len(documents)
        
    def search(self, query, k=3):
        """Search for relevant documents"""
        if not self.db:
            return []
        
        results = self.db.similarity_search(query, k=k)
        return results