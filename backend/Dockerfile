FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app ./app

ENV PYTHONUNBUFFERED=1
ENV DATABASE_URL=postgresql://postgres.pnauqlmifcednipdbgda:uVCJ1hIC9onIrBnh@aws-0-sa-east-1.pooler.supabase.com:6543/postgres
ENV FERNET_KEY=8iKG44o_iy7RiQ0uKslnFJ3RuqcFsDFfg7QmaC1kjC4=
ENV HOST_API=https://evolution-evolution.6l3lit.easypanel.host/
ENV API_KEY=429683C4C977415CAAFCCE10F7D57E11

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
