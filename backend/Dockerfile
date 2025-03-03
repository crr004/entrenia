FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt /app/

RUN pip install --no-cache-dir --upgrade -r requirements.txt

EXPOSE 8000

# CMD ["uvicorn", "backend.src.pruebas_tfg.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--proxy-headers"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]