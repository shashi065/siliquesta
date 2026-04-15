# SILIQUESTA Cross-Platform Deployment

## Structure

- `backend/` FastAPI + Celery + Redis/PostgreSQL services
- `frontend/` Next.js secondary frontend and marketing shell
- `mobile/` Capacitor wrapper
- `desktop/` Electron wrapper
- `shared/` runtime API configuration shared by every platform
- `dist/web/` generated static product bundle

## Build Commands

```bash
npm run build-web
npm run build-mobile
npm run build-desktop
```

## Local Web

1. Start backend services.
2. Serve `dist/web` or open the existing local static deployment.

## Mobile

1. `npm --prefix mobile install`
2. `npm run build-mobile`
3. `npm --prefix mobile run open:android`
4. `npm --prefix mobile run open:ios`

## Desktop

1. `npm --prefix desktop install`
2. `npm run build-desktop`
3. `npm --prefix desktop run dist`

## Backend

Use Docker Compose from `infra/docker/docker-compose.yml`, or run FastAPI/Celery locally with Redis and PostgreSQL.
