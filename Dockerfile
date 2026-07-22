# ── Security Champion Vulnerability Remediation Dashboard ──────────────────
# Multi-stage Docker build — minimal production image
# Build:   docker build -t security-champion-dashboard .
# Run:     docker run -p 3000:3000 security-champion-dashboard
# IBM CR:  docker tag security-champion-dashboard us.icr.io/<namespace>/security-champion-dashboard:latest
# ────────────────────────────────────────────────────────────────────────────

# Stage 1: dependency install
FROM node:20-alpine AS deps
WORKDIR /app
COPY package*.json ./
RUN npm ci --omit=dev

# Stage 2: production image
FROM node:20-alpine AS runner
WORKDIR /app

# Security: run as non-root
RUN addgroup -S appgroup && adduser -S appuser -G appgroup
USER appuser

# Copy only what is needed
COPY --from=deps /app/node_modules ./node_modules
COPY package.json ./
COPY server/ ./server/
COPY public/ ./public/

ENV NODE_ENV=production
ENV PORT=3000

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD wget -qO- http://localhost:3000/health || exit 1

CMD ["node", "server/app.js"]
