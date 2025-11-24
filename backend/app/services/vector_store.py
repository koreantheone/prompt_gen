try:
    import chromadb
    HAS_CHROMA = True
except ImportError:
    HAS_CHROMA = False
    print("ChromaDB not found. Using mock vector store.")

from typing import List, Dict

class VectorStore:
    def __init__(self, persist_directory: str = "./chroma_db"):
        if HAS_CHROMA:
            # Use PersistentClient to save data to disk
            self.client = chromadb.PersistentClient(path=persist_directory)
            self.collection = self.client.get_or_create_collection(name="keyword_data")
        else:
            self.client = None
            self.collection = None
            self.mock_data = {}

    def add_data(self, data_items: List[Dict]):
        """
        Adds keyword data to the vector store.
        data_items should be a list of dicts with 'keyword' and 'data'.
        """
        if HAS_CHROMA:
            documents = []
            metadatas = []
            ids = []

            for item in data_items:
                kw = item['keyword']
                # Convert complex data to string representation for embedding
                content = f"Keyword: {kw}\nData: {str(item['data'])}"
                
                documents.append(content)
                metadatas.append({"keyword": kw})
                ids.append(kw)

            if documents:
                self.collection.add(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )
        else:
            # Mock implementation
            for item in data_items:
                self.mock_data[item['keyword']] = str(item['data'])

    def query(self, query_text: str, n_results: int = 10) -> List[str]:
        """
        Retrieves relevant documents for a query.
        """
        if HAS_CHROMA:
            results = self.collection.query(
                query_texts=[query_text],
                n_results=n_results
            )
            return results['documents'][0]
        else:
            # Return random mock data
            return list(self.mock_data.values())[:n_results]
