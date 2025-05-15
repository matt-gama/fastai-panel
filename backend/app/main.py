from fastapi import FastAPI
from app.routers import webhook

app = FastAPI(title="Webhook API com Processamento em Background")

# Inclui as rotas definidas no router
app.include_router(webhook.router)
