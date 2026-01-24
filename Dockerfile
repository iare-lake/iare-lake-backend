# Use Python base image
FROM python:3.9

# Install Chrome and dependencies
RUN apt-get update && apt-get install -y wget gnupg2 unzip
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
RUN sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'
RUN apt-get update && apt-get install -y google-chrome-stable

# Install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy App Code
COPY . .

# Run the App
CMD ["gunicorn", "-b", "0.0.0.0:10000", "app:app"]