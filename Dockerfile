FROM python:3.12.3-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# This command runs in production without hot reloading
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
