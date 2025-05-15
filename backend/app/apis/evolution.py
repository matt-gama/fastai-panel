import os
import time
import openai
import base64
import requests

from langchain_openai import OpenAI
from langchain.schema import Document
from langchain_openai.chat_models import ChatOpenAI

from pydub import AudioSegment

from dotenv import load_dotenv

load_dotenv()

# Configuração do modelo OpenAI Vision
host = os.getenv('HOST_API')
api_key = os.getenv('API_KEY')
    
def processar_imagem(instance, message_id, ia_infos) -> str:
    print("Processando Imagem")
    imagem_transcript = "Imagem enviada : Não consegui transcrever essa imagem fale para o usuário que sua internet esta ruim e que não pode baixar a imagem"

    try:
        print("iniciando processo")
        url = host+'chat/getBase64FromMediaMessage/'+instance
        body = {
                "message": {
                    "key": {"id": message_id}
                },
                "convertToMp4": False
            }
        
        data = post_request(url, body)

        if data.get("status_code") in [200, 201]:
            image_base64 = data.get("response")['base64']
            # Enviar para OpenAI
            api_key = ia_infos.ia_config.credentials.get("api_key")

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }

            payload = {
                "model": os.getenv("MODEL_ANALYZE_IMAGE_OPENAI", "gpt-4o"),
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Faça uma interpretação da imagem enviada"},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                        ]
                    }
                ],
                "max_tokens": 500
            }
            
            url = "https://api.openai.com/v1/chat/completions"
            response = requests.post(url, headers=headers, json=payload, timeout=15)
            if not response:
                raise(Exception)
            
            response_json = response.json()
            imagem_transcript = response_json['choices'][0]['message']['content']
            print(imagem_transcript)
            imagem_transcript += "Imagem enviada : "+ imagem_transcript

    except Exception as ex:
        print(f"Erro ao transcrever imagem : {ex}")

    return imagem_transcript

def processar_audio(instance, message_id, ia_infos) -> str:
    print("Processando Audio")
    audio_transcript = "Audio enviado : Não consegui transcrever esse audio fale para o usuário que sua internet esta ruim e que não pode ouvir"
    timestamp = str(time.time())
    audio_path = f"audio_{timestamp}.ogg"
    mp3_path = f"audio_{timestamp}.mp3"
    try:
        

        url = host+'chat/getBase64FromMediaMessage/'+instance

        body = {
                "message": {
                    "key": {"id": message_id}
                },
                "convertToMp4": False
            }
        data = post_request(url, body)

        if data.get("status_code") in [200, 201]:
            audio_base64 = data.get("response")['base64']
            audio_bytes = base64.b64decode(audio_base64)
            with open(audio_path, 'wb') as audio_file:
                audio_file.write(audio_bytes)

            def convert_ogg_to_mp3(input_path, output_path):
                audio = AudioSegment.from_ogg(input_path)
                audio.export(output_path, format="mp3")
            
            convert_ogg_to_mp3(audio_path, mp3_path)

            with open(mp3_path, 'rb') as audio_file:
                api_key = ia_infos.ia_config.credentials.get("api_key")
                openai.api_key = api_key
                response = openai.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                )
                audio_transcript = f"Audio enviado : {response.text}"
        else:
            raise(Exception(f"Ocorreu algum erro ao coletar dados da api status code : {data.get("status_code")}"))
    except Exception as ex:
        print(f"Erro ao transcrever audio : {ex}")

    try:
        os.remove(audio_path)
        if os.path.exists(mp3_path):
            os.remove(mp3_path)
    except:
        pass

    return audio_transcript

def processar_documento(instance, message_id, ia_infos) -> str:
    print("Processando Docs")
    print(instance)
    print(message_id)
    print(ia_infos)
    return "Documento enviada"

def send_message(instance:str, lead_phone:str, message:str, delay:int) -> dict:
    url = host+'message/sendText/'+instance
    body = {
        "number": lead_phone,
        "text": str(message),
        "delay": int(delay)*1000,
        "linkPreview": True
    }
    
    data = post_request(url, body)
    return data

def send_message_audio(instance:str, lead_phone:str, file_data:str) -> dict:
    url = host+'message/sendWhatsAppAudio/'+instance

    body = {
        "number": lead_phone,
        "audio": file_data,
        "delay": 0,
    }
    
    data = post_request(url, body)
    return data

def post_request(url:str, body:dict, max_retries:int=5, wait_seconds:int=5) -> dict:
    # Inicializando variáveis
    attempt = 0
    lead = body.get("number")
    response_post = {"status_code": None, "response":None}

    headers = {
            "apikey": api_key,
            "Content-Type": "application/json"
        }
    #Inicio do laço de repetição
    while attempt < max_retries:
        attempt += 1  # Incrementa o número de tentativas
        print(f"Tentativa {attempt} de {max_retries}")
        
        response = requests.post(url, json=body, headers=headers, timeout=120)

        try:
            response_return = response.json()
        except Exception as ex:
            print(f"Erro ao converter response em json, convertendo para texto:\n > {ex}")
            response_return = response.text
                
        # Verifica se o status code é sucesso
        if response.status_code in [200, 201]:
            print(f"Mensagem enviada com sucesso pela EVOLUTION para o lead » {lead}")
            response_post = {"status_code": response.status_code, "response": response_return}
            return response_post

        if attempt < max_retries:
            print(f"Erro: {response.text} Aguardando {wait_seconds} segundos antes de tentar novamente...")
            time.sleep(wait_seconds)  # Pausa antes da próxima tentativa

    return response_post