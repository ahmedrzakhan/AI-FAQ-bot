FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ ./backend/
COPY data/ ./data/
# Copy environment file (create a .env.docker for production)
COPY .env* ./

# Create directory for ChromaDB persistence
RUN mkdir -p /app/chroma_db

# Set proper permissions for the database directory
RUN chmod 755 /app/chroma_db

# Set environment variables
ENV PYTHONPATH=/app:/app/backend
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Expose the correct port
EXPOSE 8000

# Create a startup script to handle database initialization
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
echo "Starting FAQ Bot..."\n\
echo "Python path: $PYTHONPATH"\n\
echo "Working directory: $(pwd)"\n\
\n\
# Test database import\n\
python -c "import sys; sys.path.append(\"/app/backend\"); from database import FAQDatabase; print(\"Database import successful\")" || {\n\
    echo "Database import failed. Available files:"\n\
    ls -la /app/backend/\n\
    exit 1\n\
}\n\
\n\
# Initialize database if needed\n\
python -c "\n\
import sys\n\
sys.path.append(\"/app/backend\")\n\
from database import FAQDatabase\n\
import os\n\
\n\
db = FAQDatabase()\n\
if db.get_collection_count() == 0:\n\
    if os.path.exists(\"/app/data/faq_data.json\"):\n\
        db.populate_database(\"/app/data/faq_data.json\")\n\
        print(f\"Database initialized with {db.get_collection_count()} entries\")\n\
    else:\n\
        print(\"Warning: FAQ data file not found\")\n\
else:\n\
    print(f\"Database already contains {db.get_collection_count()} entries\")\n\
" || {\n\
    echo "Database initialization failed, but continuing..."\n\
}\n\
\n\
# Start the server\n\
exec python -m uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}\n\
' > /app/start.sh

# Make the startup script executable
RUN chmod +x /app/start.sh

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Use the startup script
CMD ["/app/start.sh"]