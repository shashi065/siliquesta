import express from 'express';
import http from 'http';
import helmet from 'helmet';
import cors from 'cors';
import morgan from 'morgan';
import dotenv from 'dotenv';
import { rateLimit } from 'express-rate-limit';

import authRoutes from './routes/authRoutes.js';
import projectRoutes from './routes/projectRoutes.js';
import simulationRoutes from './routes/simulationRoutes.js';
import cloudRoutes from './routes/cloudRoutes.js';
import saasRoutes from './routes/saasRoutes.js';
import subscriptionRoutes from './routes/subscriptionRoutes.js';
import { errorHandler } from './middleware/errorHandler.js';
import { prisma } from './config/database.js';
import { initWebSocket } from './wsServer.js';

dotenv.config();

const app = express();
const server = http.createServer(app);
initWebSocket(server);
const PORT = process.env.PORT || 10000;
const NODE_ENV = process.env.NODE_ENV || 'development';
const HOST = process.env.HOST || '0.0.0.0';
const AI_URL = (process.env.AI_URL || 'http://localhost:8001').replace(/\/+$/, '');
const NORMALIZED_AI_URL = /^https?:\/\//i.test(AI_URL) ? AI_URL : `http://${AI_URL}`;

// ════════════════════════════════════════════════════════════
// SECURITY & MIDDLEWARE
// ════════════════════════════════════════════════════════════

app.use(helmet());

app.use(
  cors({
    origin: true,
    credentials: false,
    methods: ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'],
    allowedHeaders: ['Content-Type', 'Authorization'],
  })
);

app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ limit: '10mb', extended: true }));

app.use(
  morgan(NODE_ENV === 'production' ? 'combined' : 'dev')
);

const limiter = rateLimit({
  windowMs: parseInt(process.env.RATE_LIMIT_WINDOW_MS) || 15 * 60 * 1000,
  max: parseInt(process.env.RATE_LIMIT_MAX_REQUESTS) || 100,
  message: 'Too many requests from this IP, please try again later.',
  standardHeaders: true,
  legacyHeaders: false,
});

app.use('/api/v1', limiter);

// ════════════════════════════════════════════════════════════
// ROUTES
// ════════════════════════════════════════════════════════════

// 🔥 ROOT ROUTE (NEW — IMPORTANT)
app.get('/', (req, res) => {
  res.json({
    message: 'SILIQUESTA Backend API 🚀',
    status: 'running',
    docs: '/api/v1',
  });
});

// Health check
app.get('/health', (req, res) => {
  res.status(200).json({
    status: 'ok',
    timestamp: new Date().toISOString(),
    environment: NODE_ENV,
    api: '/api/v1',
    ai_url: NORMALIZED_AI_URL,
  });
});

app.get('/api/v1/health', (req, res) => {
  res.status(200).json({
    status: 'ok',
    timestamp: new Date().toISOString(),
    environment: NODE_ENV,
    api: '/api/v1',
    ai_url: NORMALIZED_AI_URL,
  });
});

// API Routes
app.use('/api/v1/auth', authRoutes);
app.use('/api/v1/projects', projectRoutes);
app.use('/api/v1/simulations', simulationRoutes);
app.use('/api/v1/subscriptions', subscriptionRoutes);
app.use('/api/v1', saasRoutes);
app.use('/api/v1', cloudRoutes);

// ════════════════════════════════════════════════════════════
// MONITORING & ANALYTICS ENDPOINTS
// ════════════════════════════════════════════════════════════

// Performance metrics in Prometheus format
app.get('/metrics', async (req, res) => {
  try {
    let { performanceMonitor } = await import('./utils/errorLogger.js');
    if (!performanceMonitor) {
      return res.status(503).json({ error: 'Performance monitor not available' });
    }
    res.setHeader('Content-Type', 'text/plain; charset=utf-8');
    res.send(performanceMonitor.exportMetrics());
  } catch (err) {
    res.status(500).json({ error: 'Failed to export metrics' });
  }
});

// Detailed performance report
app.get('/api/v1/performance/report', async (req, res) => {
  try {
    let { performanceMonitor } = await import('./utils/errorLogger.js');
    if (!performanceMonitor) {
      return res.status(503).json({ error: 'Performance monitor not available' });
    }
    res.json(performanceMonitor.getReport());
  } catch (err) {
    res.status(500).json({ error: 'Failed to get performance report' });
  }
});

// Analytics status
app.get('/api/v1/analytics/stats', async (req, res) => {
  try {
    let { analytics } = await import('./utils/errorLogger.js');
    if (!analytics) {
      return res.status(503).json({ error: 'Analytics not available' });
    }
    res.json(analytics.getStats());
  } catch (err) {
    res.status(500).json({ error: 'Failed to get analytics stats' });
  }
});

// API Docs
app.get('/api/v1', (req, res) => {
  res.status(200).json({
    name: 'SILIQUESTA Backend API',
    version: '1.0.0',
    description: 'Render-ready API gateway for the SILIQUESTA cloud platform',
    endpoints: {
      health: '/api/v1/health',
      auth: '/api/v1/auth',
      users: '/api/v1/users',
      projects: '/api/v1/projects',
      simulations: '/api/v1/simulations',
      subscriptions: '/api/v1/subscriptions',
      simulate: '/api/v1/simulate',
      pvt: '/api/v1/pvt/full-sweep',
      optimize: '/api/v1/optimize',
      twin: '/api/v1/twin/compute-aging',
      ai: '/api/v1/ai/chat',
    },
    monitoring: {
      metrics: '/metrics (Prometheus format)',
      performance: '/api/v1/performance/report (Performance metrics)',
      analytics: '/api/v1/analytics/stats (Analytics status)',
    },
    ai_service: NORMALIZED_AI_URL,
  });
});

// 404
app.use((req, res) => {
  res.status(404).json({
    error: 'Not Found',
    message: `Cannot ${req.method} ${req.originalUrl}`,
  });
});

// Error Handler
app.use(errorHandler);

// ════════════════════════════════════════════════════════════
// STARTUP
// ════════════════════════════════════════════════════════════

const startServer = async () => {
  try {
    await prisma.$queryRaw`SELECT 1`;
    console.log('✓ Database connection successful');

    server.listen(PORT, HOST, () => {
      console.log(`✓ Server running on ${HOST}:${PORT}`);
      console.log('✓ WebSocket optimizer attached');
      console.log(`✓ Environment: ${NODE_ENV}`);
      console.log(`✓ API root: /api/v1`);
      console.log(`✓ AI service target: ${NORMALIZED_AI_URL}`);
    });
  } catch (error) {
    console.error('✗ Failed to start server:', error);
    process.exit(1);
  }
};

process.on('SIGINT', async () => {
  console.log('\n✓ Gracefully shutting down...');
  await prisma.$disconnect();
  process.exit(0);
});

process.on('SIGTERM', async () => {
  console.log('\n✓ Gracefully shutting down...');
  await prisma.$disconnect();
  process.exit(0);
});

startServer();

export default app;
export { server };
