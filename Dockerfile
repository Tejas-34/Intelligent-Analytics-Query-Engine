# Multi-platform production-grade Docker image
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

WORKDIR /app

# Install curl for health checks
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies first (leverages Docker layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code and data files
COPY . .

# Ensure dataset directory is concrete (resolve symlink if present)
RUN if [ -L dataset ]; then cp -rL dataset dataset_dir && rm dataset && mv dataset_dir dataset; fi

# Expose FastAPI (8000) and Streamlit (8501) ports
EXPOSE 8000 8501

# Default command runs the FastAPI backend
CMD ["python3", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
