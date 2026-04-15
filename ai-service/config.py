import os
from dotenv import load_dotenv

load_dotenv()

# Application Settings
APP_NAME = "SILIQUESTA AI Optimization Service"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "AI-powered circuit parameter optimization microservice"

# Server Configuration
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 10000))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "info")

# Environment
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# CORS Configuration
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

# Optimization Parameters
OPTIMIZATION_MAX_ITERATIONS = int(os.getenv("OPTIMIZATION_MAX_ITERATIONS", "500"))
OPTIMIZATION_TIMEOUT = int(os.getenv("OPTIMIZATION_TIMEOUT", "30000"))  # milliseconds
OPTIMIZATION_METHOD = os.getenv("OPTIMIZATION_METHOD", "scipy")  # scipy or ml

# ML Model Configuration
ML_MODEL_PATH = os.getenv("ML_MODEL_PATH", "models/optimizer_model.pkl")
USE_GPU = os.getenv("USE_GPU", "False").lower() == "true"

# API Configuration
API_TIMEOUT = int(os.getenv("API_TIMEOUT", "60"))  # seconds
MAX_WORKERS = int(os.getenv("MAX_WORKERS", "4"))
