"""
Local development startup script.
Runs the API server without Docker.
"""
import uvicorn
import os

# Set environment variables for local development
os.environ['DATABASE_URL'] = 'sqlite:///./transactions_local.db'
os.environ['GEMINI_API_KEY'] = 'AIzaSyDXuV8RN6ImQGXsChfsRWZLm3wBebON2Mq8Yk3iqySJo6u7aw0vng'
os.environ['UPLOAD_DIR'] = './uploads'

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Starting LOCAL Development Server")
    print("=" * 60)
    print("📝 Mode: LOCAL (No Docker, No Celery)")
    print("💾 Database: SQLite (transactions_local.db)")
    print("🤖 AI: Gemini 1.5 Flash")
    print("📂 Uploads: ./uploads")
    print("=" * 60)
    print("\n✨ Server starting at: http://localhost:8000")
    print("📚 API Docs: http://localhost:8000/docs")
    print("\n⚠️  Note: Processing is SYNCHRONOUS (may take 10-30 seconds)")
    print("=" * 60)
    print("\nPress Ctrl+C to stop\n")
    
    uvicorn.run(
        "app.main_local:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
