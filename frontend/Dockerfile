# ─────────────────────────────────────────────────────────
# DistriStore — Frontend Dockerfile (Multi-stage)
# Build: Node 18 + Vite → Production: Nginx Alpine
# ─────────────────────────────────────────────────────────

# ── Stage 1: Build ──────────────────────────────────────
FROM node:22-alpine AS build

WORKDIR /app

# Install deps first (cached layer)
COPY package.json package-lock.json ./
RUN npm ci --silent

# Copy source and build
COPY . .
RUN npm run build

# ── Stage 2: Production ────────────────────────────────
FROM nginx:alpine

# Copy built assets from build stage
COPY --from=build /app/dist /usr/share/nginx/html

# Custom nginx config for SPA routing (React Router)
RUN echo 'server { \
    listen 80; \
    server_name _; \
    root /usr/share/nginx/html; \
    index index.html; \
    location / { \
        try_files $uri $uri/ /index.html; \
    } \
}' > /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
