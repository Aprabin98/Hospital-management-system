# Multi-stage Docker build for Hospital Management System
# Stage 1: Backend (Django)

FROM python:3.14-slim as backend-builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Backend final image
FROM python:3.14-slim as backend

WORKDIR /app

RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY --from=backend-builder /usr/local/lib/python3.14/site-packages /usr/local/lib/python3.14/site-packages
COPY backend/ /app/

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health/', timeout=5)" || exit 1

EXPOSE 8000

# Run Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "120", "hms_project.wsgi:application"]

# Stage 3: Frontend (Next.js)

FROM node:18-alpine as frontend-builder

WORKDIR /app

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ .

# Build Next.js
RUN npm run build

# Stage 4: Frontend production image
FROM node:18-alpine as frontend

WORKDIR /app

COPY --from=frontend-builder /app/node_modules ./node_modules
COPY --from=frontend-builder /app/.next ./.next
COPY --from=frontend-builder /app/public ./public
COPY frontend/next.config.ts ./
COPY frontend/package.json ./

RUN adduser -D -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost:3000/health || exit 1

EXPOSE 3000

CMD ["npm", "start"]

# Stage 5: Docker Compose orchestration
# Build: docker build -f Dockerfile -t hms-backend --target backend .
#        docker build -f Dockerfile -t hms-frontend --target frontend .
#
# Run:   docker-compose up -d (requires docker-compose.yml)
