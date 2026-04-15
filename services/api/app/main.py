"""SILIQUESTA Backend - FastAPI main application."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
from app.config import settings
from app.observability import ObservabilityMiddleware, metrics_registry

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)

# API Routers
from app.api import simulation, pvt, optimizer, digital_twin, ai_service, auth, user, billing, jobs, api_keys, design_dna, design_memory, validation, results, projects, project_sharing, production, ml_predictions, nsga2_routes, execution_routes, memory_management, saas_infrastructure, gpu_acceleration_routes, orchestrator_routes
from app.api import testing as testing_api

# Middleware
from app.middleware import UsageTrackingMiddleware

# GPU Acceleration
from app.gpu_acceleration import initialize_gpu_acceleration

# Database
from app.database import database_healthcheck, init_db
from app.healthcheck import assert_startup_dependencies, gather_health


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    logger.info("🚀 SILIQUESTA Backend Starting...")
    
    # Initialize GPU acceleration
    try:
        initialize_gpu_acceleration(use_gpu=True)
        logger.info("✓ GPU acceleration initialized")
    except Exception as e:
        logger.warning(f"⚠ GPU acceleration initialization failed: {e} - using CPU")
    
    await init_db()
    await assert_startup_dependencies()
    logger.info("✓ Database initialized")
    yield
    logger.info("🛑 SILIQUESTA Backend Shutdown")


# Create FastAPI app
app = FastAPI(
    title="SILIQUESTA API",
    description="AI-Native EDA Platform - Production Backend",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS middleware
allowed_origins = [
    "http://localhost:3000",
    "http://localhost:8000",
    "https://localhost:3000",
    "https://localhost:8000",
]

# Add production origins if configured
if settings.APP_ENV.lower() == "production":
    # Add your production domain here
    allowed_origins.extend([
        "https://siliquesta.app",
        "https://www.siliquesta.app",
    ])

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["Content-Type", "Authorization", "X-Total-Count"],
    max_age=600,
)

# Add usage tracking middleware (early in stack for comprehensive tracking)
try:
    from app.services.saas_infrastructure import SaaSInfrastructure
    from app.database import get_async_session
    from app.config import redis_client
    app.add_middleware(UsageTrackingMiddleware, saas_service=SaaSInfrastructure(), session_maker=get_async_session, redis_client=redis_client)
    logger.info("✓ Usage tracking middleware enabled")
except Exception as e:
    logger.warning(f"⚠ Could not initialize usage tracking middleware: {e}")

if settings.metrics_enabled:
    app.add_middleware(ObservabilityMiddleware)


# Health check
@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <html>
      <head><title>SILIQUESTA Backend</title></head>
      <body style="font-family:Arial,sans-serif;padding:32px;background:#f6f9ff;color:#12203a">
        <h1>SILIQUESTA Backend</h1>
        <p>The backend is running.</p>
        <ul>
          <li><a href="/health">/health</a></li>
          <li><a href="/docs">/docs</a></li>
          <li><a href="/api/v1">/api/v1</a></li>
        </ul>
      </body>
    </html>
    """

@app.get("/health")
async def health():
    health_snapshot = await gather_health()
    overall = "ok" if all(item["status"] == "ok" for item in health_snapshot.values()) else "degraded"
    return {
        "status": overall,
        "service": "siliquesta-backend",
        "version": "2.0.0",
        "api": "ok",
        "db": health_snapshot["db"]["status"],
        "redis": health_snapshot["redis"]["status"],
        "celery": health_snapshot["celery"]["status"],
        "ml": health_snapshot["ml"]["status"],
        "details": health_snapshot,
    }


@app.get("/metrics")
async def metrics():
    return {
        "service": "siliquesta-backend",
        "env": settings.APP_ENV,
        "metrics": metrics_registry.snapshot(),
    }


@app.get("/api/v1")
async def api_root():
    return {
        "name": "SILIQUESTA API",
        "version": "2.0.0",
        "health": "/health",
        "docs": "/docs",
        "routes": {
            "auth": "/api/v1/auth",
            "saas": "/api/v1/saas",
            "gpu": "/api/v1/gpu",
            "users": "/api/v1/users",
            "api_keys": "/api/v1/api-keys",
            "simulate": "/api/v1/simulate",
            "pvt": "/api/v1/pvt",
            "optimize": "/api/v1/optimize",
            "twin": "/api/v1/twin",
            "ai": "/api/v1/ai",
            "design_dna": "/api/v1/design-dna",
            "validate": "/api/v1/validate",
            "predict": "/api/v1/predict",
            "results": "/api/v1/results/{job_id}",
            "orchestrator": "/api/v1/orchestrator",
        },
    }


# API Routes
router = APIRouter(prefix="/api/v1")

# Include all API routers
router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
router.include_router(saas_infrastructure.router, prefix="/saas", tags=["SaaS Infrastructure"])
router.include_router(gpu_acceleration_routes.router, tags=["GPU Acceleration"])
router.include_router(user.router, prefix="/users", tags=["Users"])
router.include_router(api_keys.router, prefix="/api-keys", tags=["API Keys"])
router.include_router(billing.router, prefix="/billing", tags=["Billing"])
router.include_router(jobs.router, prefix="/jobs", tags=["Jobs"])
router.include_router(results.router, prefix="/results", tags=["Results"])
router.include_router(projects.router, prefix="/projects", tags=["Projects"])
router.include_router(project_sharing.router, prefix="/projects", tags=["Project Sharing"])
router.include_router(simulation.router, prefix="/simulate", tags=["Simulation"])
router.include_router(pvt.router, prefix="/pvt", tags=["PVT Analysis"])
router.include_router(optimizer.router, prefix="/optimize", tags=["ADA Optimizer"])
router.include_router(digital_twin.router, prefix="/twin", tags=["Digital Twin"])
router.include_router(ai_service.router, prefix="/ai", tags=["AI Services"])
router.include_router(design_dna.router, prefix="/design-dna", tags=["Design DNA"])
router.include_router(design_memory.router, tags=["Design Memory"])
router.include_router(memory_management.router, tags=["Memory Management"])
router.include_router(validation.router, prefix="/validate", tags=["Validation"])
router.include_router(ml_predictions.router, tags=["ML Predictions"])
router.include_router(nsga2_routes.router, tags=["NSGA-II Optimization"])
router.include_router(execution_routes.router, tags=["Execution Engine"])
router.include_router(orchestrator_routes.router, tags=["Agentic Orchestrator"])
router.include_router(production.router, tags=["Production Features"])
if settings.APP_ENV.lower() in {"test", "testing"}:
    router.include_router(testing_api.router, prefix="/testing", tags=["Testing"])

app.include_router(router)


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
