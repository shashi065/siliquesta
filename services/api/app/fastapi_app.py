"""
FastAPI Application Setup for Hybrid AI
========================================

Integrates hybrid edge/cloud AI routing into FastAPI.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.api.hybrid_routes import router as hybrid_router
from app.connectivity_detector import init_connectivity_detector
from app.hybrid_orchestrator import init_hybrid_orchestrator
from app.onnx_model_manager import init_onnx_manager

logger = logging.getLogger(__name__)


def create_app(config: dict = None) -> FastAPI:
    """
    Create and configure FastAPI application with hybrid AI support.
    
    Args:
        config: Configuration dictionary with keys:
            - enable_onnx: Enable ONNX edge models (default: True)
            - enable_cloud: Enable cloud backend (default: True)
            - connectivity_check_interval: Seconds between checks (default: 30)
            - cloud_api_timeout: Cloud request timeout (default: 30)
    
    Returns:
        Configured FastAPI app with hybrid routes
    """
    
    if config is None:
        config = {}
    
    app = FastAPI(
        title="SILIQUESTA Hybrid AI API",
        description="Edge + Cloud AI with automatic switching",
        version="1.0.0"
    )
    
    # ========================================================================
    # CORS Configuration
    # ========================================================================
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # ========================================================================
    # Initialize Hybrid System
    # ========================================================================
    
    @app.on_event("startup")
    async def startup_event():
        """Initialize hybrid AI system on startup"""
        logger.info("🚀 Starting SILIQUESTA Hybrid AI...")
        
        try:
            # Initialize components
            init_connectivity_detector(
                check_interval=config.get("connectivity_check_interval", 30),
                timeout=config.get("connectivity_timeout", 5)
            )
            logger.info("✓ Connectivity detector initialized")
            
            if config.get("enable_onnx", True):
                init_onnx_manager(
                    model_dir=config.get("onnx_model_dir", "models/edge/onnx")
                )
                logger.info("✓ ONNX model manager initialized")
            
            if config.get("enable_cloud", True):
                init_hybrid_orchestrator(
                    cloud_api_url=config.get("cloud_api_url"),
                    cloud_api_key=config.get("cloud_api_key"),
                    cloud_timeout=config.get("cloud_api_timeout", 30),
                    enable_fallback=config.get("enable_fallback", True)
                )
                logger.info("✓ Hybrid orchestrator initialized")
            
            logger.info("✓ Hybrid AI system ready!")
            
        except Exception as e:
            logger.error(f"✗ Startup failed: {e}")
            raise
    
    @app.on_event("shutdown")
    async def shutdown_event():
        """Cleanup on shutdown"""
        logger.info("🛑 Shutting down SILIQUESTA Hybrid AI...")
        # Cleanup resources as needed
        logger.info("✓ Shutdown complete")
    
    # ========================================================================
    # Register Routes
    # ========================================================================
    app.include_router(hybrid_router)
    
    # ========================================================================
    # Health Check Endpoint
    # ========================================================================
    
    @app.get("/")
    async def root():
        """API root endpoint"""
        return {
            "service": "SILIQUESTA Hybrid AI API",
            "status": "running",
            "version": "1.0.0",
            "docs": "/docs"
        }
    
    @app.get("/health")
    async def health():
        """Health check endpoint"""
        return {
            "status": "healthy",
            "service": "hybrid_ai"
        }
    
    return app


# ============================================================================
# Convenience function for running the app
# ============================================================================

def run_app(
    host: str = "0.0.0.0",
    port: int = 8000,
    reload: bool = False,
    config: dict = None
):
    """
    Run FastAPI app with hybrid AI support.
    
    Args:
        host: Host to bind to
        port: Port to bind to
        reload: Auto-reload on code changes
        config: Hybrid system configuration
    """
    import uvicorn
    
    app = create_app(config)
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )


if __name__ == "__main__":
    # Example configuration
    config = {
        "enable_onnx": True,
        "enable_cloud": True,
        "connectivity_check_interval": 30,
        "cloud_api_timeout": 30,
        "onnx_model_dir": "models/edge/onnx"
    }
    
    run_app(config=config)
