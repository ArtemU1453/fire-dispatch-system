# syntax=docker/dockerfile:1

# =========================================================================
# AI Dispatcher МЧС — backend image (Python 3.13).
# Multi-stage build: dependencies are installed into a virtualenv in the
# builder stage and copied into a slim runtime stage that runs as non-root.
# =========================================================================

# --------------------------------------------------------------- builder ---
FROM python:3.13-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Create an isolated virtualenv we can copy wholesale into the runtime stage.
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# --------------------------------------------------------------- runtime ---
FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    # Make `import app...` work: the package lives under ./backend.
    PYTHONPATH=/app/backend

WORKDIR /app

# Copy the pre-built virtualenv from the builder stage.
COPY --from=builder /opt/venv /opt/venv

# Copy project sources.
COPY backend/ ./backend/
COPY migrations/ ./migrations/
COPY alembic.ini ./alembic.ini

# Run as an unprivileged user.
RUN useradd --create-home --uid 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Default command: run the ASGI app with Uvicorn.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
