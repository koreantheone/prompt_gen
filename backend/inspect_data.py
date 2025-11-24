#!/usr/bin/env python3
"""
Script to inspect data collected from DataForSEO API.
This script checks the vector store and displays stored keyword data.
"""

import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from services.vector_store import VectorStore
import json

def main():
    print("=" * 60)
    print("DataForSEO Data Inspection Tool")
    print("=" * 60)
    print()
    
    # Initialize vector store
    vs = VectorStore()
    
    # Check if using ChromaDB or mock
    if hasattr(vs, 'client') and vs.client is not None:
        print("✓ Using ChromaDB vector store")
        
        # Get collection info
        collection = vs.collection
        print(f"Collection name: {collection.name}")
        
        # Get count of items
        try:
            count = collection.count()
            print(f"Total items stored: {count}")
            print()
            
            if count > 0:
                # Retrieve all items
                print("Retrieving stored data...")
                print("-" * 60)
                
                # Get all documents
                results = collection.get()
                
                print(f"Found {len(results['ids'])} items:")
                print()
                
                for i, (doc_id, metadata, document) in enumerate(zip(
                    results['ids'], 
                    results['metadatas'], 
                    results['documents']
                ), 1):
                    print(f"{i}. ID: {doc_id}")
                    print(f"   Keyword: {metadata.get('keyword', 'N/A')}")
                    print(f"   Document preview: {document[:200]}...")
                    print()
                    
                # Save to file
                output_file = "dataforseo_data_dump.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump({
                        'count': count,
                        'ids': results['ids'],
                        'metadatas': results['metadatas'],
                        'documents': results['documents']
                    }, f, indent=2, ensure_ascii=False)
                print(f"✓ Full data saved to: {output_file}")
                
            else:
                print("⚠ No data found in vector store.")
                print("  The store is empty. You may need to:")
                print("  1. Run a search request through the API")
                print("  2. Check if the backend is using persistent storage")
                
        except Exception as e:
            print(f"✗ Error accessing collection: {e}")
            
    else:
        print("⚠ Using mock vector store (ChromaDB not installed)")
        if hasattr(vs, 'mock_data'):
            print(f"Mock data items: {len(vs.mock_data)}")
            if vs.mock_data:
                print()
                for keyword, data in vs.mock_data.items():
                    print(f"Keyword: {keyword}")
                    print(f"Data: {data[:200]}...")
                    print()
            else:
                print("⚠ No mock data found.")
    
    print()
    print("=" * 60)

if __name__ == "__main__":
    main()
