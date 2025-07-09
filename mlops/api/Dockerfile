# mlops/api/Dockerfile

# --- Base Image ---
# Use an official Python runtime as a parent image.
# The 'slim' version is smaller and good for production.
FROM python:3.9-slim

# --- Set Environment Variables ---
# Prevents Python from writing .pyc files to disc (improves performance in containers)
ENV PYTHONDONTWRITEBYTECODE 1
# Ensures Python output is sent straight to the terminal without buffering
ENV PYTHONUNBUFFERED 1

# --- Set Working Directory ---
# All subsequent commands will be run from this directory
WORKDIR /app

# --- Install Dependencies ---
# First, copy only the requirements.txt file.
# This takes advantage of Docker's layer caching. The dependencies will only be re-installed
# if the requirements.txt file changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- Copy Application Code ---
# Copy the rest of the application's code into the container
COPY . .

# --- Expose Port ---
# Tell Docker that the container listens on port 80
EXPOSE 80

# --- Run Application ---
# The command to run when the container starts.
# We use uvicorn to run our FastAPI application.
# --host 0.0.0.0 makes the server accessible from outside the container.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]

