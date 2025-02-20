# Use a lightweight Python image
FROM python:3.12-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the application files into the container
COPY ghostfile-gui.py index.html requirements.txt /app/

# Install dependencies in a virtual environment
RUN python -m venv venv && \
    . venv/bin/activate && \
    pip install --no-cache-dir -r requirements.txt

# Expose the port the server runs on
EXPOSE 5000

# Command to start the server
CMD ["/app/venv/bin/python", "/app/ghostfile-gui.py"]
