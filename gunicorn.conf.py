# Gunicorn configuration for FastAPI
bind = "0.0.0.0:10000"
workers = 1
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
timeout = 30
keepalive = 2