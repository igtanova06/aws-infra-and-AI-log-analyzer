# ============================================================
# STAGE 1: Build the React frontend
# ============================================================
FROM node:18-alpine AS frontend-builder
WORKDIR /app/frontend

# Install dependencies
COPY frontend/package.json ./
RUN npm install

# Copy source code and build
COPY frontend/ ./
RUN npm run build

# ============================================================
# STAGE 2: Package the Node.js Express backend and serve
# ============================================================
FROM node:18-alpine
WORKDIR /app

# Create log directory inside container
RUN mkdir -p /var/log/app && chown -R node:node /var/log/app

# Install backend dependencies
COPY backend/package.json ./backend/
WORKDIR /app/backend
RUN npm install --only=production

# Copy backend source code
COPY backend/src/ ./src/

# Copy built frontend assets from Stage 1
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist

# Expose port 80 inside the container (maps to port 8080 of host)
EXPOSE 80

# Run the server
CMD ["npm", "start"]
