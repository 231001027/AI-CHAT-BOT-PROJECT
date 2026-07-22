/**
 * HearConnect — Node.js API Gateway
 *
 * Acts as the single entry point for the React frontend.
 * Responsibilities:
 *   - Rate-limiting to protect the FastAPI service
 *   - Request / response logging (morgan)
 *   - CORS enforcement for the frontend origin
 *   - Reverse-proxy to FastAPI on all /api/* and /health routes
 *   - Gateway-level health check at /gateway/health
 */

import 'dotenv/config';
import express from 'express';
import cors from 'cors';
import morgan from 'morgan';
import rateLimit from 'express-rate-limit';
import { createProxyMiddleware } from 'http-proxy-middleware';

// ---------------------------------------------------------------------------
// Config (values come from .env; sensible defaults for local dev)
// ---------------------------------------------------------------------------
const PORT          = parseInt(process.env.GATEWAY_PORT   ?? '3000', 10);
const FASTAPI_URL   = process.env.FASTAPI_URL             ?? 'http://localhost:8000';
const FRONTEND_URL  = process.env.FRONTEND_URL            ?? 'http://localhost:5173';
const NODE_ENV      = process.env.NODE_ENV                ?? 'development';

// ---------------------------------------------------------------------------
// App
// ---------------------------------------------------------------------------
const app = express();

// Parse JSON bodies only for non-proxied routes (gateway/health).
// Do NOT apply globally — it consumes the request stream before the proxy can forward it.
app.use('/gateway', express.json());

// ---------------------------------------------------------------------------
// Logging
// ---------------------------------------------------------------------------
app.use(morgan(NODE_ENV === 'production' ? 'combined' : 'dev'));

// ---------------------------------------------------------------------------
// CORS — only the React dev server (or the deployed frontend) is allowed
// ---------------------------------------------------------------------------
app.use(
  cors({
    origin: FRONTEND_URL,
    methods: ['GET', 'POST', 'OPTIONS'],
    allowedHeaders: ['Content-Type', 'Authorization', 'X-Request-ID'],
    credentials: true,
  })
);

// ---------------------------------------------------------------------------
// Rate limiting
// ---------------------------------------------------------------------------

// Chat endpoint — stricter to prevent abuse
const chatLimiter = rateLimit({
  windowMs: 60 * 1000,   // 1 minute
  max: 30,               // 30 messages per minute per IP
  standardHeaders: true,
  legacyHeaders: false,
  message: { error: 'Too many requests. Please slow down.' },
});

// General API endpoints
const apiLimiter = rateLimit({
  windowMs: 60 * 1000,
  max: 120,
  standardHeaders: true,
  legacyHeaders: false,
  message: { error: 'Too many requests. Please slow down.' },
});

app.use('/api/chat',   chatLimiter);
app.use('/api',        apiLimiter);

// ---------------------------------------------------------------------------
// Gateway-level health check (does NOT proxy to FastAPI)
// ---------------------------------------------------------------------------
app.get('/gateway/health', (_req, res) => {
  res.json({
    status: 'ok',
    service: 'hearconnect-api-gateway',
    fastapi_target: FASTAPI_URL,
    timestamp: new Date().toISOString(),
  });
});

// ---------------------------------------------------------------------------
// Reverse proxy → FastAPI  (handles /api/* and /health)
// ---------------------------------------------------------------------------
const proxy = createProxyMiddleware({
  target: FASTAPI_URL,
  changeOrigin: true,
  on: {
    proxyReq: (proxyReq, req) => {
      proxyReq.setHeader('X-Forwarded-For', req.ip ?? 'unknown');
      proxyReq.setHeader('X-Gateway', 'hearconnect-node');
    },
    error: (err, _req, res) => {
      console.error('[proxy error]', err.message);
      res.status(502).json({
        error: 'Bad gateway — FastAPI service is unreachable.',
        detail: NODE_ENV === 'development' ? err.message : undefined,
      });
    },
  },
});

// Mount at root so Express does NOT strip any prefix.
// The full path (/api/chat, /health, /docs, /redoc) is forwarded unchanged.
app.use('/', proxy);

// ---------------------------------------------------------------------------
// 404 fallback
// ---------------------------------------------------------------------------
app.use((_req, res) => {
  res.status(404).json({ error: 'Route not found on API gateway.' });
});

// ---------------------------------------------------------------------------
// Start
// ---------------------------------------------------------------------------
app.listen(PORT, () => {
  console.log(`\n🚀  HearConnect API Gateway running on http://localhost:${PORT}`);
  console.log(`   Proxying /api/* → ${FASTAPI_URL}`);
  console.log(`   Allowed origin : ${FRONTEND_URL}`);
  console.log(`   Environment    : ${NODE_ENV}\n`);
});
