# Use full Python image to ensure all system libraries are present
FROM python:3.9

# 1. Install basic tools
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# 2. Install Google Chrome (Direct Download Method)
# This skips the 'apt-key' error by downloading the .deb file directly
RUN wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && apt-get update \
    && apt-get install -y ./google-chrome-stable_current_amd64.deb \
    && rm google-chrome-stable_current_amd64.deb

# 3. Setup Application
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the code
COPY . .

# 4. Run the app
# Increased timeout to 120s because Selenium takes time to start
CMD ["gunicorn", "-b", "0.0.0.0:10000", "app:app", "--timeout", "120"]
