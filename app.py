"""
ASGI application entry point for Render deployment
This ensures FastAPI works properly with various deployment methods
"""
import os
from main import app

# ASGI application for modern deployment
application = app

# For gunicorn compatibility (if needed)
def application_wsgi(environ, start_response):
    """WSGI wrapper for legacy deployment systems"""
    import asyncio
    from asgiref.wsgi import WsgiToAsgi
    
    asgi_app = WsgiToAsgi(app)
    return asgi_app(environ, start_response)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")