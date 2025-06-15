#!/bin/bash
# Docker ChromaDB Explorer Script
# Save as explore_docker_db.sh and run with: bash explore_docker_db.sh

echo "🐳 Docker ChromaDB Explorer"
echo "=========================="

# Check if container is running
CONTAINER_ID=$(docker ps -q --filter ancestor=faq-bot)

if [ -z "$CONTAINER_ID" ]; then
    echo "❌ No faq-bot container running!"
    echo "💡 Start your container first: docker run -p 8000:8000 --env-file .env faq-bot"
    exit 1
fi

echo "✅ Found container: $CONTAINER_ID"

echo "
🔍 What would you like to do?
1) Show database files
2) Show collection info
3) List all documents
4) Test search functionality
5) Copy database to local
6) Interactive shell

Enter choice (1-6): "

read choice

case $choice in
    1)
        echo "📁 Database files:"
        docker exec $CONTAINER_ID ls -la /app/chroma_db/
        ;;
    2)
        echo "📊 Collection info:"
        docker exec $CONTAINER_ID python3 -c "
import chromadb
client = chromadb.PersistentClient(path='/app/chroma_db')
collections = client.list_collections()
print(f'Collections: {[c.name for c in collections]}')
if collections:
    collection = client.get_collection('faq_collection')
    print(f'Documents: {collection.count()}')
"
        ;;
    3)
        echo "📄 All documents:"
        docker exec $CONTAINER_ID python3 -c "
import chromadb
client = chromadb.PersistentClient(path='/app/chroma_db')
collection = client.get_collection('faq_collection')
results = collection.get(include=['documents', 'metadatas'])
for i, doc_id in enumerate(results['ids']):
    print(f'\\n{i+1}. ID: {doc_id}')
    print(f'   Q: {results[\"metadatas\"][i][\"question\"]}')
    print(f'   A: {results[\"metadatas\"][i][\"answer\"]}')
"
        ;;
    4)
        echo "🔍 Testing search:"
        docker exec $CONTAINER_ID python3 -c "
import chromadb
client = chromadb.PersistentClient(path='/app/chroma_db')
collection = client.get_collection('faq_collection')

queries = ['help with returns', 'shipping time', 'payment methods']
for query in queries:
    results = collection.query(query_texts=[query], n_results=1, include=['metadatas', 'distances'])
    if results['metadatas'][0]:
        distance = results['distances'][0][0]
        similarity = (1 - distance) * 100
        question = results['metadatas'][0][0]['question']
        print(f'Query: \"{query}\" → \"{question}\" ({similarity:.1f}% match)')
"
        ;;
    5)
        echo "📋 Copying database to local directory..."
        docker cp $CONTAINER_ID:/app/chroma_db ./docker_chroma_db
        echo "✅ Database copied to ./docker_chroma_db/"
        echo "💡 You can now explore it locally with Python"
        ;;
    6)
        echo "🚀 Starting interactive shell in container..."
        echo "💡 You're now inside the container. Type 'exit' to return."
        echo "💡 Database is at: /app/chroma_db"
        docker exec -it $CONTAINER_ID bash
        ;;
    *)
        echo "❌ Invalid choice"
        ;;
esac

echo "
✅ Done!
💡 Your FAQ data is stored in the Docker container at /app/chroma_db/"