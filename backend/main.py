from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

try:
    from .core import compute_core
    from .optimizer import run_optimizer
    from .twin import digital_twin
    from .agent import ai_agent
except ImportError:
    from core import compute_core
    from optimizer import run_optimizer
    from twin import digital_twin
    from agent import ai_agent

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return JSONResponse(
        {
            "status": "ok",
            "service": "SILIQUESTA AI EDA backend",
            "docs": "/docs",
            "endpoints": ["/simulate", "/optimize", "/twin", "/ai", "/health"],
        }
    )


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/favicon.ico")
def favicon():
    return Response(status_code=204)


@app.post("/simulate")
def simulate(state: dict):
    return compute_core(state)


@app.get("/optimize")
def optimize():
    return run_optimizer()


@app.post("/twin")
def twin(data: dict):
    return digital_twin(data)


@app.post("/ai")
def ai(data: dict):
    return ai_agent(data["prompt"], data["state"])
