FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    librealsense2-dev \
    libportaudio2 \
    portaudio19-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies with uv
RUN uv pip install -r requirements.txt

# Copy the rest of the application
COPY src/ src/

# Command to run the application
CMD ["python", "-m", "src.piano.main"]