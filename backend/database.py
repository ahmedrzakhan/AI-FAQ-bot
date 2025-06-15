import chromadb
import json
from typing import List, Dict
import os

class FAQDatabase:
    def __init__(self, persist_directory: str = "./chroma_db"):
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.collection = self.client.get_or_create_collection(
            name="faq_collection",
            metadata={"hnsw:space": "cosine"}
        )
    
    def populate_database(self, faq_data_path: str):
        """Load FAQ data from JSON file and populate ChromaDB"""
        with open(faq_data_path, 'r') as f:
            faq_data = json.load(f)
        
        documents = []
        metadatas = []
        ids = []
        
        for i, faq in enumerate(faq_data):
            documents.append(f"Q: {faq['question']} A: {faq['answer']}")
            metadatas.append({
                "question": faq['question'],
                "answer": faq['answer']
            })
            ids.append(f"faq_{i}")
        
        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        
        print(f"Added {len(documents)} FAQ entries to ChromaDB")
    
    def search_faqs(self, query: str, n_results: int = 3) -> List[Dict]:
        """Search for relevant FAQs based on query"""
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        faqs = []
        if results['metadatas'][0]:
            for metadata in results['metadatas'][0]:
                faqs.append({
                    "question": metadata['question'],
                    "answer": metadata['answer']
                })
        
        return faqs
    
    def get_collection_count(self) -> int:
        """Get the number of documents in the collection"""
        return self.collection.count()

if __name__ == "__main__":
    # Initialize and populate database
    db = FAQDatabase()
    
    # Check if database is already populated
    if db.get_collection_count() == 0:
        faq_data_path = os.path.join(os.path.dirname(__file__), "../data/faq_data.json")
        db.populate_database(faq_data_path)
    else:
        print(f"Database already contains {db.get_collection_count()} entries")