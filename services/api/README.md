# SILIQUESTA Backend API

Production-ready Node.js backend for the SILIQUESTA AI-powered engineering platform.

## 🚀 Tech Stack

- **Express.js** - Modular web framework
- **PostgreSQL** - Database
- **Prisma** - ORM & database management
- **JWT** - Authentication
- **bcryptjs** - Password hashing
- **Helmet** - Security headers
- **Express Rate Limit** - API rate limiting
- **Morgan** - HTTP logging
- **Joi** - Input validation

## 📁 Project Structure

```
src/
├── controllers/           # Request handlers
│   ├── authController.js
│   ├── projectController.js
│   └── simulationController.js
├── routes/               # API route definitions
│   ├── authRoutes.js
│   ├── projectRoutes.js
│   └── simulationRoutes.js
├── services/            # Business logic
│   ├── authService.js
│   ├── projectService.js
│   └── simulationService.js
├── middleware/          # Express middleware
│   ├── auth.js
│   ├── errorHandler.js
│   └── validation.js
├── config/              # Configuration files
│   └── database.js
├── utils/               # Utility functions
│   └── validators.js
└── server.js            # Application entry point

prisma/
└── schema.prisma        # Database schema

.env.example             # Environment variable template
package.json             # Dependencies
```

## 🔧 Setup & Installation

### Prerequisites

- Node.js 18+
- npm 9+
- PostgreSQL 12+

### Installation Steps

1. **Clone and install dependencies:**
```bash
npm install
```

2. **Configure environment:**
```bash
cp .env.example .env
```

Edit `.env` with your configuration:
```env
NODE_ENV=development
PORT=5000
DATABASE_URL=postgresql://user:password@localhost:5432/siliquesta_db
JWT_SECRET=your_super_secret_key
CORS_ORIGIN=http://localhost:3000
```

3. **Setup database:**
```bash
# Run migrations
npm run db:push

# Optionally seed initial data
npm run db:seed

# Open Prisma Studio
npm run db:studio
```

4. **Start development server:**
```bash
npm run dev
```

The server will run on `http://localhost:5000`

## 📚 API Endpoints

### Authentication
```
POST   /api/auth/signup          - Register new user
POST   /api/auth/login           - Login user
GET    /api/auth/me              - Get current user (protected)
PATCH  /api/auth/profile         - Update profile (protected)
POST   /api/auth/refresh         - Refresh token
POST   /api/auth/logout          - Logout (protected)
POST   /api/auth/change-password - Change password (protected)
```

### Projects
```
POST   /api/projects             - Create project (protected)
GET    /api/projects             - List projects with pagination (protected)
GET    /api/projects/:id         - Get project details (protected)
PATCH  /api/projects/:id         - Update project (protected)
DELETE /api/projects/:id         - Delete project (protected)
GET    /api/projects/:id/stats   - Get project statistics (protected)
```

### Simulations
```
POST   /api/simulations          - Create simulation (protected)
GET    /api/simulations          - List simulations (protected)
GET    /api/simulations/:id      - Get simulation (protected)
PATCH  /api/simulations/:id      - Update simulation (protected)
DELETE /api/simulations/:id      - Delete simulation (protected)
POST   /api/simulations/:id/run  - Execute simulation (protected)
GET    /api/simulations/:id/results - Get results (protected)
```

## 🔐 Authentication

All protected endpoints require an `Authorization` header:
```
Authorization: Bearer <accessToken>
```

### JWT Token Structure
```json
{
  "userId": "user_id",
  "email": "user@example.com",
  "role": "user",
  "iat": 1234567890,
  "exp": 1234654290
}
```

## 📋 Database Models

### User
```javascript
{
  id: String (unique)
  email: String (unique)
  name: String
  password: String (hashed)
  avatar: String? (optional)
  bio: String? (optional)
  role: String (default: "user")
  isActive: Boolean (default: true)
  createdAt: DateTime
  updatedAt: DateTime
  lastLogin: DateTime?
}
```

### Project
```javascript
{
  id: String (unique)
  title: String
  description: String?
  slug: String (unique)
  status: String (default: "active")
  parameters: Json? (configuration)
  metadata: Json? (custom data)
  userId: String (foreign key)
  simulationCount: Int
  createdAt: DateTime
  updatedAt: DateTime
}
```

### Simulation
```javascript
{
  id: String (unique)
  title: String
  description: String?
  status: String (pending|running|completed|failed)
  input: Json (simulation input)
  output: Json?
  parameters: Json?
  config: Json?
  results: Json?
  error: String?
  duration: Int? (milliseconds)
  projectId: String (foreign key)
  userId: String (foreign key)
  createdAt: DateTime
  updatedAt: DateTime
  startedAt: DateTime?
  completedAt: DateTime?
}
```

## 🧪 Testing

Run tests with:
```bash
npm test
```

## 📦 Production Deployment

### Build for production:
```bash
npm run build
```

### Start production server:
```bash
NODE_ENV=production npm start
```

### Environment Variables (Production)
```env
NODE_ENV=production
PORT=5000
DATABASE_URL=postgresql://prod_user:prod_pass@prod_host:5432/siliquesta_prod
JWT_SECRET=<long_random_secret_key>
JWT_REFRESH_SECRET=<long_random_refresh_secret>
CORS_ORIGIN=https://siliquesta.com
RATE_LIMIT_MAX_REQUESTS=1000
```

## 🔒 Security Features

✅ **Helmet** - HTTP header security
✅ **CORS** - Cross-origin resource sharing
✅ **JWT** - Secure token-based authentication
✅ **bcryptjs** - Password hashing with salt rounds
✅ **Rate Limiting** - DDoS protection
✅ **Input Validation** - Joi schema validation
✅ **Error Handling** - Proper error responses
✅ **HTTPS** - Force HTTPS in production

## 📝 Validation Examples

### Register User
```json
POST /api/auth/signup
{
  "email": "user@example.com",
  "name": "John Doe",
  "password": "SecurePassword123!",
  "confirmPassword": "SecurePassword123!"
}
```

### Create Project
```json
POST /api/projects
{
  "title": "Thermal Simulation 2024",
  "description": "Advanced heat transfer analysis",
  "parameters": {
    "material": "copper",
    "temperature": 500
  }
}
```

### Create Simulation
```json
POST /api/simulations
{
  "title": "FEA Analysis Run 1",
  "description": "First iteration of mesh refinement",
  "input": {
    "meshSize": 0.1,
    "iterations": 100
  },
  "projectId": "proj_123abc"
}
```

## 🚨 Error Handling

All errors follow a consistent format:
```json
{
  "error": "Error Type",
  "message": "Human readable message",
  "details": {} // Optional validation details
}
```

Common HTTP Status Codes:
- `200` - OK
- `201` - Created
- `400` - Bad Request (validation error)
- `401` - Unauthorized (auth required)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `409` - Conflict (duplicate email, etc)
- `500` - Internal Server Error

## 📊 Performance Optimization

- Database indexing on frequently queried fields
- Pagination for list endpoints
- Rate limiting to prevent abuse
- Connection pooling via Prisma
- Graceful error handling
- Proper response caching headers

## 🔄 Workflow Examples

### Register & Login Flow
```
1. POST /api/auth/signup       → Get accessToken & refreshToken
2. Store tokens securely
3. Include token in subsequent requests
4. When token expires, POST /api/auth/refresh
```

### Project Creation & Simulation Flow
```
1. POST /api/projects          → Create project
2. POST /api/simulations       → Create simulation
3. POST /api/simulations/:id/run → Execute simulation
4. GET /api/simulations/:id/results → Retrieve results
```

## 📞 Support & Documentation

For more information:
- API Documentation: http://localhost:5000/api
- Health Check: http://localhost:5000/health
- Prisma Docs: https://www.prisma.io/docs/
- Express Docs: https://expressjs.com/

## 📄 License

MIT License - See LICENSE file for details
