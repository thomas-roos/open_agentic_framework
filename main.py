#!/usr/bin/env python3
# main.py - FIXED SIMPLIFIED VERSION

import os
import sys
import logging
from datetime import datetime

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging FIRST
os.makedirs('/app/data/logs', exist_ok=True)

logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/data/logs/application.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Import and create the FastAPI app
from api.rest_server import create_app

app = create_app()

logger.info("✅ Multi-Agent System API started successfully")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("API_PORT", "8080")),
        reload=False,
        log_level="info"
    )