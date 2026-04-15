import logging
from datetime import datetime
from typing import Dict, Any
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import time

from config import (
    APP_NAME,
    APP_VERSION,
    APP_DESCRIPTION,
    CORS_ORIGINS,
    DEBUG,
    LOG_LEVEL,
    ENVIRONMENT,
)
from models import (
    OptimizeRequest,
    OptimizeResponse,
    OptimizedCircuitParameters,
    OptimizationMetrics,
    OptimizationMetricsComparison,
    HealthResponse,
    ErrorResponse,
)
from optimizer import CircuitOptimizer

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize optimizer
optimizer = CircuitOptimizer()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager"""
    logger.info(f"🚀 Starting {APP_NAME} v{APP_VERSION}")
    logger.info(f"Environment: {ENVIRONMENT}")
    logger.info(f"Debug mode: {DEBUG}")
    yield
    logger.info("🛑 Shutting down service")


# Create FastAPI app
app = FastAPI(
    title=APP_NAME,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
    debug=DEBUG,
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if "*" in [origin.strip() for origin in CORS_ORIGINS] else [origin.strip() for origin in CORS_ORIGINS],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ════════════════════════════════════════════════════════════
# Health & Status Endpoints
# ════════════════════════════════════════════════════════════

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check() -> HealthResponse:
    """
    Health check endpoint
    """
    return HealthResponse(
        status="healthy",
        version=APP_VERSION,
        environment=ENVIRONMENT,
        timestamp=datetime.utcnow().isoformat(),
    )


@app.get("/info", tags=["Info"])
async def service_info() -> Dict[str, Any]:
    """
    Get service information
    """
    return {
        "name": APP_NAME,
        "version": APP_VERSION,
        "description": APP_DESCRIPTION,
        "environment": ENVIRONMENT,
        "endpoints": {
            "health": "/health",
            "optimize": "/optimize",
            "docs": "/docs",
            "redoc": "/redoc",
        },
        "timestamp": datetime.utcnow().isoformat(),
    }


# ════════════════════════════════════════════════════════════
# Optimization Endpoints
# ════════════════════════════════════════════════════════════

@app.post(
    "/optimize",
    response_model=OptimizeResponse,
    status_code=status.HTTP_200_OK,
    tags=["Optimization"],
    summary="Optimize circuit parameters",
    description="Optimize circuit parameters using SciPy or ML-based methods"
)
async def optimize(request: OptimizeRequest) -> OptimizeResponse:
    """
    Optimize circuit parameters

    ### Request Body
    - **parameters**: Circuit parameters to optimize
    - **objectives**: Optimization objectives
    - **method**: Optimization method (scipy, ml, hybrid)
    - **max_iterations**: Maximum optimization iterations
    - **tolerance**: Convergence tolerance

    ### Response
    - **optimized_parameters**: Optimized circuit parameters
    - **metrics_comparison**: Original vs optimized metrics
    - **overall_improvement**: Overall improvement percentage
    - **iterations_used**: Number of iterations used
    - **convergence**: Whether algorithm converged

    ### Example Request
    ```json
    {
      "parameters": {
        "W_L_ratio": 10,
        "supply_voltage": 1.8,
        "operating_frequency": 1e9,
        "load_capacitance": 1e-12
      },
      "objectives": {
        "minimize_power": true,
        "maximize_speed": true
      }
    }
    ```

    ### Example Response
    ```json
    {
      "success": true,
      "optimized_parameters": {
        "W_L_ratio": 12.5,
        "supply_voltage": 1.5,
        "...": "..."
      },
      "overall_improvement": 25.3,
      "iterations_used": 125,
      "convergence": true
    }
    ```
    """
    try:
        logger.info("Starting optimization request")

        # Extract constraints
        constraints = {
            "power_budget": request.parameters.power_budget,
            "area_budget": request.parameters.area_budget,
        }

        # Convert objectives to dict
        objectives_dict = request.objectives.model_dump()

        # Start optimization
        start_time = time.time()

        optimized_params, optimized_metrics, iterations, converged = optimizer.optimize(
            initial_parameters=request.parameters.model_dump(exclude={"power_budget", "area_budget"}),
            objectives=objectives_dict,
            constraints=constraints,
            max_iterations=request.max_iterations,
            method=request.method.value,
        )

        execution_time = time.time() - start_time

        # Calculate original metrics
        original_metrics = optimizer.calculate_metrics(
            request.parameters.model_dump(exclude={"power_budget", "area_budget"}),
            {}
        )

        # Calculate improvements
        improvements, overall_improvement = CircuitOptimizer.calculate_improvement(
            original_metrics,
            optimized_metrics
        )

        # Build response
        response = OptimizeResponse(
            success=True,
            optimized_parameters=OptimizedCircuitParameters(
                W_L_ratio=optimized_params["W_L_ratio"],
                finger_ratio=optimized_params["finger_ratio"],
                supply_voltage=optimized_params["supply_voltage"],
                operating_frequency=optimized_params.get("operating_frequency"),
                bias_current=optimized_params.get("bias_current"),
                other_params={
                    k: v for k, v in optimized_params.items()
                    if k not in ["W_L_ratio", "finger_ratio", "supply_voltage", "operating_frequency", "bias_current"]
                }
            ),
            metrics_comparison=OptimizationMetricsComparison(
                original=OptimizationMetrics(
                    power_consumption=original_metrics["power_consumption"],
                    propagation_delay=original_metrics["propagation_delay"],
                    gain=original_metrics.get("gain"),
                    area=original_metrics.get("area"),
                    slew_rate=original_metrics.get("slew_rate"),
                    noise_margin=original_metrics.get("noise_margin"),
                ),
                optimized=OptimizationMetrics(
                    power_consumption=optimized_metrics["power_consumption"],
                    propagation_delay=optimized_metrics["propagation_delay"],
                    gain=optimized_metrics.get("gain"),
                    area=optimized_metrics.get("area"),
                    slew_rate=optimized_metrics.get("slew_rate"),
                    noise_margin=optimized_metrics.get("noise_margin"),
                ),
                improvements=improvements,
            ),
            overall_improvement=overall_improvement,
            iterations_used=iterations,
            convergence=converged,
            execution_time=execution_time,
            method_used=request.method,
            notes=f"Optimization completed in {execution_time:.2f}s" + 
                  (" with convergence" if converged else " without full convergence")
        )

        logger.info(f"Optimization completed - Improvement: {overall_improvement:.2f}%")
        return response

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except TimeoutError as e:
        logger.error(f"Optimization timeout: {e}")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Optimization timeout exceeded",
        )
    except Exception as e:
        logger.error(f"Optimization error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal optimization error",
        )


# ════════════════════════════════════════════════════════════
# Error Handlers
# ════════════════════════════════════════════════════════════

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions"""
    return {
        "error": exc.detail,
        "message": exc.detail,
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return {
        "error": "Internal Server Error",
        "message": str(exc) if DEBUG else "An unexpected error occurred",
        "timestamp": datetime.utcnow().isoformat(),
    }


# ════════════════════════════════════════════════════════════
# 404 Handler
# ════════════════════════════════════════════════════════════

@app.get("/{path:path}", tags=["Errors"])
async def not_found(path: str):
    """Handle 404 Not Found"""
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Endpoint '/{path}' not found",
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=PORT,
        reload=DEBUG,
        log_level=LOG_LEVEL,
    )
