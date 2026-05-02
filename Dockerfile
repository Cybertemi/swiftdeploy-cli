FROM python:3.11-alpine

# Install wget for health check
RUN apk add --no-cache wget

# Create non-root user
RUN addgroup -S appgroup && \
    adduser -S appuser -G appgroup -u 1000

WORKDIR /app

# Install Python dependencies as root first
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/main.py .

# Give ownership to appuser
RUN chown -R appuser:appgroup /app

USER appuser

ENV MODE=stable
ENV APP_VERSION=1.0.0
ENV APP_PORT=3000

HEALTHCHECK --interval=10s --timeout=5s --start-period=15s --retries=6 \
  CMD wget -qO- http://localhost:3000/healthz || exit 1

EXPOSE 3000

CMD ["python", "main.py"]
