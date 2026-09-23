# Multi-platform production-grade Docker image
FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

WORKDIR /app

# Install curl for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code and data files
COPY . .

# Ensure dataset directory is concrete (resolve symlink if present)
RUN if [ -L dataset ]; then cp -rL dataset dataset_dir && rm dataset && mv dataset_dir dataset; fi

# Ensure startup script has execution permissions
RUN chmod +x start.sh

# Expose Streamlit frontend (8501) and FastAPI backend (8000)
EXPOSE 8501 8000

# Container healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Default entrypoint runs both services
CMD ["./start.sh"]
