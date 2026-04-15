# SILIQUESTA Production Gap Checklist

Status baseline: `2026-04-08`

This checklist is based on the requested launch scope from `mjor update.md` and the current codebase state.

## Summary

- `Done`: local web shell, FastAPI backend, auth base, subscription base, credits/jobs base, hybrid AI base, ngspice-backed simulation path, SPICE-backed PVT path, digital twin ML pipeline base
- `Partial`: dashboard polish, AI experience, no-Docker local run path, SaaS backend, exports, offline behavior, deployment docs, installability
- `Missing`: zero-setup installers, real payment gateway/webhooks, distributed queue workers, Redis-backed/global rate limiting, live sync/backup, Electron packaging pipeline, Android/iOS delivery, full production observability, full public-launch hardening

## Checklist

### Core Product Experience

- `Partial` Interactive dashboard tool as the primary interface
- `Partial` All clicks mapped to real computation
- `Partial` All graphs backed by validated live data
- `Partial` AI execution tied to current design context
- `Partial` Error-free interaction at 100% zoom

### Simulation / EDA Engine

- `Done` Real ngspice-backed inverter simulation path
- `Partial` Real-time graph updates on parameter changes
- `Done` SPICE-backed PVT sweep path
- `Partial` ADA optimizer is wired, but still needs stronger production-grade optimization validation
- `Missing` Full AC analysis endpoint
- `Missing` Full DC analysis endpoint
- `Missing` Waveform export endpoint and frontend viewer
- `Missing` Multi-circuit parser coverage beyond the current inverter-centric path

### AI

- `Done` Hybrid routing: local deterministic engine + retrieval + optional local LLM
- `Partial` AI chat UX and answer quality
- `Partial` RAG knowledge base expansion and grounding depth
- `Missing` full continuous-learning loop
- `Missing` production-grade local LLM packaging and model bootstrap

### Digital Twin

- `Done` Train/inference pipeline exists
- `Partial` calibrated surrogate quality for trustable signoff use
- `Partial` frontend digital twin visualizations
- `Missing` production-calibrated model validation target (<3% error) on large SPICE dataset

### SaaS Backend

- `Done` DB-backed auth
- `Done` subscriptions/credit ledger/job history data model
- `Done` credit consumption on compute routes
- `Partial` rate limiting
- `Partial` job queue
- `Missing` real payment provider integration and webhook verification
- `Missing` admin/billing reconciliation flows
- `Missing` production multi-instance queue workers

### Storage / Sync / Offline

- `Partial` local persistence in browser/local workspace
- `Missing` IndexedDB/SQLite-backed app-level offline sync strategy
- `Missing` cloud sync + backup
- `Missing` conflict resolution and account-linked workspace restore across devices

### Packaging / Distribution

- `Partial` web app can run locally without Docker
- `Missing` zero-setup desktop installers (`.exe`, `.dmg`, `.AppImage`)
- `Missing` packaged PWA/offline release flow
- `Missing` Android APK deliverable
- `Missing` iOS project/TestFlight-ready deliverable

### Deployment / Operations

- `Partial` deployment docs and infra skeleton
- `Missing` proven public deployment pipeline for frontend + backend
- `Missing` production secrets management and environment separation
- `Missing` monitoring, analytics, traces, alerting
- `Missing` backup/restore runbooks
- `Missing` public-launch QA signoff checklist

### Trust / Safety

- `Partial` auth and basic credit controls
- `Missing` “SPICE verified” trust display everywhere it matters
- `Missing` error margin / model confidence display across product surfaces
- `Missing` production abuse protection and distributed rate limiting

## Highest-Impact Remaining Production Blockers

1. Distributed rate limiting and queueing for multi-user backend safety
2. Real payment gateway and webhook-based subscription activation
3. AC/DC/waveform SPICE endpoints and richer trust surfaces
4. Public deployment hardening and monitoring
5. Packaging/installability for desktop/mobile

## Execution Order

- `In progress` Blocker 1: replace in-process limiter with Redis-backed distributed limiting
- `Next` Blocker 2: real payment activation flow
- `Next` Blocker 3: AC/DC/waveform backend completion
- `Next` Blocker 4: queue worker + async processing hardening
- `Next` Blocker 5: deployable packaging and release flow
