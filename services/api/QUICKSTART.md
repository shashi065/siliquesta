# Quick Start Guide - SILIQUESTA Backend

Get your production-ready backend running in 5 minutes!

## ⚡ Quick Setup

### 1. Install Dependencies
```bash
npm install
```

### 2. Configure Database
Create a `.env` file from the template:
```bash
cp .env.example .env
```

Update the `DATABASE_URL` in `.env`:
```
DATABASE_URL=postgresql://postgres:password@localhost:5432/siliquesta_db
```

### 3. Initialize Database
```bash
npm run db:push
```

Optionally, seed with test data:
```bash
npm run db:seed
```

### 4. Start Development Server
```bash
npm run dev
```

✅ Server running at `http://localhost:5000`

## 🧪 Test the API

### Register a User
```bash
curl -X POST http://localhost:5000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "name": "Test User",
    "password": "Test123!@#",
    "confirmPassword": "Test123!@#"
  }'
```

### Login
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Test123!@#"
  }'
```

Save the `accessToken` from the response!

### Create a Project
```bash
curl -X POST http://localhost:5000/api/projects \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "title": "My First Project",
    "description": "Testing the backend",
    "parameters": {
      "type": "thermal"
    }
  }'
```

### Get Your Projects
```bash
curl http://localhost:5000/api/projects \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## 📊 Useful Commands

```bash
# Development
npm run dev                 # Start with auto-reload
npm run lint              # Run ESLint
npm run format            # Format code with Prettier

# Database
npm run db:push           # Sync schema with database
npm run db:migrate        # Create migration
npm run db:studio         # Open Prisma Studio GUI
npm run db:seed           # Seed test data

# Testing
npm test                  # Run test suite

# Production
npm start                 # Start server
NODE_ENV=production npm start
```

## 🔑 Environment Variables

**Development (.env)**
```env
NODE_ENV=development
PORT=5000
DATABASE_URL=postgresql://user:password@localhost:5432/siliquesta_db
JWT_SECRET=dev_secret_key_change_in_prod
JWT_EXPIRES_IN=7d
CORS_ORIGIN=http://localhost:3000,http://localhost:3001
```

**Production (.env.prod)**
```env
NODE_ENV=production
PORT=5000
DATABASE_URL=postgresql://prod_user:prod_pass@prod_host/siliquesta_prod
JWT_SECRET=<generate_secure_random_key>
JWT_EXPIRES_IN=7d
CORS_ORIGIN=https://yourdomain.com
RATE_LIMIT_MAX_REQUESTS=1000
```

## 📚 API Overview

### Authentication
- `POST /api/auth/signup` - Create account
- `POST /api/auth/login` - Login
- `GET /api/auth/me` - Get profile
- `PATCH /api/auth/profile` - Update profile
- `POST /api/auth/refresh` - Refresh token

### Projects
- `POST /api/projects` - Create
- `GET /api/projects` - List (paginated)
- `GET /api/projects/:id` - Get one
- `PATCH /api/projects/:id` - Update
- `DELETE /api/projects/:id` - Delete
- `GET /api/projects/:id/stats` - Statistics

### Simulations
- `POST /api/simulations` - Create
- `GET /api/simulations?projectId=:id` - List
- `GET /api/simulations/:id` - Get one
- `POST /api/simulations/:id/run` - Execute
- `GET /api/simulations/:id/results` - Get results
- `PATCH /api/simulations/:id` - Update
- `DELETE /api/simulations/:id` - Delete

## 🚀 Deployment

### Using Docker
```bash
docker build -t siliquesta-backend .
docker run -p 5000:5000 \
  -e DATABASE_URL=postgresql://... \
  -e JWT_SECRET=... \
  siliquesta-backend
```

### Using Railway/Heroku
```bash
# Add PostgreSQL addon
# Set environment variables
# Deploy from git

git push
```

### Using PM2
```bash
npm install -g pm2
pm2 start src/server.js --name "siliquesta-api"
pm2 save
pm2 startup
```

## 🐛 Troubleshooting

### Database Connection Failed
- Check `.env` DATABASE_URL
- Ensure PostgreSQL is running
- Verify credentials

### Port Already in Use
```bash
# Change PORT in .env or
lsof -i :5000  # Find process
kill -9 <PID>  # Kill process
```

### JWT Errors
- Clear browser cookies/localStorage
- Regenerate tokens
- Check JWT_SECRET is set

### CORS Issues
- Update CORS_ORIGIN in `.env`
- Verify frontend URL matches

## 📖 Full Documentation

See [README.md](./README.md) for comprehensive documentation.

## 💡 Next Steps

1. Implement custom simulation logic in `services/simulationService.js`
2. Add email notifications
3. Setup monitoring and logging
4. Configure CI/CD pipeline
5. Deploy to production

Happy coding! 🚀
