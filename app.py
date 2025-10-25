# Simple wrapper for Render deployment
from main import app

# For gunicorn compatibility
application = app

if __name__ == "__main__":
    import uvicorn
    import os
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))