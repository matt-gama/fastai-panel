from fastapi import APIRouter, BackgroundTasks, status
from app.service.process import process_webhook_data

router = APIRouter()

@router.post("/webhook", status_code=status.HTTP_200_OK)
async def receive_webhook(data: dict, background_tasks: BackgroundTasks):
    """
    Endpoint que recebe os dados do webhook e dispara uma tarefa em background.
    """
    try:
        # Adiciona a tarefa em background para processar os dados
        background_tasks.add_task(process_webhook_data, data)
        return {"message": "Webhook recebido. Processamento iniciado em background."}
    except Exception as ex:
        print(f"ERROR: {ex}")
        return {"message": "Error"}