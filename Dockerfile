# Use an official Python runtime as a parent image
FROM python:3.8-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir \
    torch==1.11.0 \
    torchvision==0.12.0 \
    torchaudio==0.11.0 \
    opencv-python==4.6.0.66 \
    lpips==0.1.4 \
    face_alignment==1.3.5 \
    kornia==0.6.7 \
    matplotlib \
    flask \
    gunicorn \
    google-cloud-storage

# Make port 8080 available to the world outside this container
EXPOSE 8080

# Run app.py when the container launches
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]