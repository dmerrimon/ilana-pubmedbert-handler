# Simple import for Render deployment
from main import app

# Direct reference for gunicorn
application = app

if __name__ == "__main__":
    import uvicorn
    import os
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))