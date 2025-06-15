#!/usr/bin/env python3
"""
Local development script to run both FastAPI backend and Streamlit frontend
"""

import subprocess
import sys
import time
import threading
import os
from pathlib import Path

def run_backend():
    """Run the FastAPI backend server"""
    print("🚀 Starting FastAPI backend on http://localhost:8000")
    os.chdir(Path(__file__).parent / "backend")
    subprocess.run([sys.executable, "main.py"])

def run_frontend():
    """Run the Streamlit frontend"""
    # Wait a bit for backend to start
    time.sleep(3)
    print("🎨 Starting Streamlit frontend on http://localhost:8501")
    os.chdir(Path(__file__).parent / "frontend")
    subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"])

def main():
    print("🤖 Starting FAQ Bot Development Environment")
    print("=" * 50)
    
    # Check if required files exist
    backend_path = Path(__file__).parent / "backend" / "main.py"
    frontend_path = Path(__file__).parent / "frontend" / "app.py"
    
    if not backend_path.exists():
        print("❌ Backend main.py not found!")
        return
    
    if not frontend_path.exists():
        print("❌ Frontend app.py not found!")
        return
    
    print("✅ All files found. Starting servers...")
    
    # Start backend in a separate thread
    backend_thread = threading.Thread(target=run_backend, daemon=True)
    backend_thread.start()
    
    # Start frontend in main thread
    try:
        run_frontend()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down servers...")
        sys.exit(0)

if __name__ == "__main__":
    main()