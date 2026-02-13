# Use a lightweight Python image
FROM python:3.9-slim

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the code
COPY . .

# Run the app (No strict timeout needed anymore)
CMD ["gunicorn", "-b", "0.0.0.0:10000", "app:app"]