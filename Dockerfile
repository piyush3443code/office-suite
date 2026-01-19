# --- Builder Stage ---
FROM python:3.10-alpine as builder

WORKDIR /app

# Install build dependencies
RUN apk add --no-cache gcc musl-dev libffi-dev curl

# Install kubectl (copy to final stage later)
RUN curl -LO "https://dl.k8s.io/release/v1.28.0/bin/linux/amd64/kubectl" \
    && chmod +x kubectl

# Install python dependencies into a local directory
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# --- Final Stage ---
FROM python:3.10-alpine

WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Copy python dependencies from builder
COPY --from=builder /install /usr/local

# Copy kubectl binary from builder
COPY --from=builder /app/kubectl /usr/local/bin/

# Copy project files
COPY . .

# Expose port
EXPOSE 8000

# Run migrations and start server
CMD ["sh", "-c", "python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]
