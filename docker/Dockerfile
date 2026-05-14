FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

# Copy application
COPY src/deepalpha/ /app/deepalpha/
COPY config.yaml /app/

EXPOSE 8000

CMD ["uvicorn", "deepalpha.api.main:app", "--host", "0.0.0.0", "--port", "8000"]