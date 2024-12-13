# Gunakan image Python sebagai base image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Salin file requirements.txt dan install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Salin seluruh aplikasi Flask
COPY . .

# Tentukan port yang akan digunakan oleh aplikasi
ENV PORT 8080

# Jalankan aplikasi Flask
CMD ["python", "app.py"]
