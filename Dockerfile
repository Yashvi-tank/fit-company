FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y build-essential libpq-dev

# Copy requirements and install
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy app code
COPY . .

# Set environment variables for Flask
ENV FLASK_APP=src/fit/app.py
ENV FLASK_ENV=development

# Run the Flask app
CMD ["python", "-m", "src.fit.wait_for_db"]



