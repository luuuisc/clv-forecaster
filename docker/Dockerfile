# ---------- 1. Imagen base con Python 3.12 ----------
FROM python:3.12-slim

# ---------- 2. Paquetes de compilación (solo para build) ----------
RUN apt-get update && apt-get install -y build-essential \
    && rm -rf /var/lib/apt/lists/*

# ---------- 3. Copiar requirements e instalar ----------
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---------- 4. Copiar código y modelos ----------
COPY src src
COPY models models

# ---------- 5. Exponer puerto y comando ----------
EXPOSE 8000
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]