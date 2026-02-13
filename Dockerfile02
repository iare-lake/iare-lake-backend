# Use a slim Python image (Uses less RAM)
FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy code
COPY . .

# Run Gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:10000", "app:app", "--timeout", "60"]
