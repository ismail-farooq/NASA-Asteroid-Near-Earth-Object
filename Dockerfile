FROM python:3.11-slim

# Use a safe WORKDIR inside the container
WORKDIR /app

# Copy only requirements first (better caching)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy everything into the container
COPY . .

# Expose Flask port
EXPOSE 5000

# Run your Flask app
CMD ["python", "./App/app.py"]
