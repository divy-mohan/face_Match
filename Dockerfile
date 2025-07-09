FROM python:3.10-slim

# System packages for dlib + pip tools
RUN apt-get update && apt-get install -y \
    cmake \
    build-essential \
    libboost-all-dev \
    && rm -rf /var/lib/apt/lists/*

# Create app folder
WORKDIR /app

# Copy all project files to container
COPY . .

# Install dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Collect static files
RUN python manage.py collectstatic --noinput

# Expose port
EXPOSE 8000

# Run the app
CMD ["gunicorn", "face_attendance.wsgi:application", "--bind", "0.0.0.0:8000"]