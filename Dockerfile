# --- Stage 1: Build the Frontend ---
FROM node:20-alpine AS frontend-builder
WORKDIR /app/Frontend
COPY Frontend/package*.json ./
RUN npm install
COPY Frontend/ ./
RUN npm run build

# --- Stage 2: Final Backend Image ---
FROM python:3.11-slim
WORKDIR /app

# Install system dependencies (needed for certain python packages)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Backend dependencies
COPY Backend/requirements.txt ./Backend/
RUN pip install --no-cache-dir -r Backend/requirements.txt

# Copy Backend source code
COPY Backend/ ./Backend/

# Copy the built Frontend files to the Backend's dist directory
# (FastAPI in Backend/main.py is configured to serve this)
COPY --from=frontend-builder /app/Frontend/dist ./Backend/dist

# Expose the API port (Hugging Face Spaces defaults to 8000/7860)
EXPOSE 7860

# Set the working directory to Backend for file imports to work
WORKDIR /app/Backend

# Command to run the application
CMD ["python", "main.py"]
