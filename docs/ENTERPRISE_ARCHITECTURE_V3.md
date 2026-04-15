# SILIQUESTA Enterprise Architecture V3

## Runtime Topology

```text
Browser / Desktop / PWA
  -> Frontend shell (Next.js or static product shell)
  -> FastAPI API gateway
     -> Auth layer
        -> JWT bearer auth
        -> API-key auth
     -> SaaS policy layer
        -> plans
        -> credits
        -> rate limiting
        -> audit events
     -> Core EDA services
        -> SPICE engine (ngspice transient path, PVT sweeps)
        -> Zero-simulation CMOS engine
        -> Digital Twin surrogate
        -> Hybrid AI router
        -> Design DNA vector memory
     -> Async execution plane
        -> Celery broker/result backend via Redis
        -> worker tasks for simulation, PVT, AI, and twin jobs
     -> Persistence
        -> PostgreSQL/SQLite via SQLAlchemy async
        -> Redis rate limiting / queue transport
        -> FAISS or numpy-backed vector index
        -> model registry artifacts
```

## Backend Structure

```text
backend/app/
  api/
    auth.py
    api_keys.py
    billing.py
    jobs.py
    design_dna.py
    simulation.py
    pvt.py
    optimizer.py
    digital_twin.py
    ai_service.py
  services/
    spice_engine.py
    pvt_spice_service.py
    cmos_engine.py
    digital_twin_ml.py
    model_registry.py
    design_dna.py
    ai_router.py
    local_reasoner.py
    local_llm.py
    rag_system.py
    saas.py
    api_keys.py
    job_dispatcher.py
  tasks/
    compute.py
  config.py
  database.py
  models.py
  main.py
  observability.py
  celery_app.py
```

## Database Domains

- `users`: human tenant identity
- `api_keys`: machine-to-machine access
- `subscriptions`: SaaS plan lifecycle
- `credit_ledger`: monetization and compute charging
- `compute_jobs`: async/sync compute tracking
- `rate_limit_events`: abuse and burst tracking
- `projects`: named user workspaces
- `design_dna_records`: vectorized reusable design memory
- `model_artifacts`: model lineage and activation history
- `audit_events`: security/compliance trail

## Production Intent

- Local mode:
  - SQLite + optional Redis
  - sync fallback still supported
- Production mode:
  - PostgreSQL + Redis + Celery worker
  - API keys for service integrations
  - structured request metrics from `/metrics`
  - model/dataset lineage in artifact registry

## Remaining Gaps After This Pass

- ADA is still not NSGA-III/Bayesian-grade
- Stripe webhooks are not wired yet
- worker tasks exist, but API routes still execute inline by default
- frontend is still not migrated to a full production React dashboard everywhere
- observability is basic metrics/logging, not full Prometheus/OpenTelemetry
- SPICE support is still strongest for inverter-centric flows, not full multi-circuit signoff
