FROM python:3.10-slim

# Install system dependencies for dlib and OpenCV
RUN apt-get update && apt-get install -y \
    cmake \
    build-essential \
    libboost-all-dev \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy project files
COPY . .

# Upgrade pip and install dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Collect static files (if using Django)
RUN python manage.py collectstatic --noinput

# Expose the application port
EXPOSE 8000

# Start server using gunicorn
CMD ["gunicorn", "face_attendance.wsgi:application", "--bind", "0.0.0.0:8000"]
