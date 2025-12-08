# Etapa 1: Builder
FROM python:3.11-slim as builder

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# Etapa 2: Runner (Imagen final ligera)
FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias de sistema necesarias para Postgres y Networking
RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq-dev netcat-openbsd && \
    rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/requirements.txt .

RUN pip install --no-cache /wheels/*

# Copiar el código fuente
COPY ./src ./src

# Usuario no root por seguridad
RUN useradd -m nexususer
USER nexususer

# Puerto expuesto
EXPOSE 8000

# Comando de arranque (usando ruta de módulo)
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]