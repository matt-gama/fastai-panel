import time
import json
import requests
from ..utils.work_audio import converter_para_ogg


class ElevenlabsStrategy():
    def __init__(self, api_key_elevenlabs:str, id_voz:str):
        self.id_voz = id_voz
        # Headers da requisição, incluindo a chave de API
        self.headers = {
            "xi-api-key": api_key_elevenlabs,
            "Content-Type": "application/json"
        }

    def generate_audio_narrated(self, roteiro_narracao: str) -> str:
        try:
            # URL do endpoint da API
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.id_voz}"
            
            # Dados da requisição
            payload = {
                "text": roteiro_narracao,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    "stability": 0.4,
                    "similarity_boost": 0.8,
                    "style": 0.2,
                    "speed":1.1,
                    "use_speaker_boost": True
                    }
            }
            
            data = self.post_request(url, payload)
            data_audio = data.get("response")
            if not data_audio:
                raise("Erro ao gerar audio na elevenlabs")

            audio_ogg = converter_para_ogg(data_audio)
            return audio_ogg

        except Exception as ex:
            print(ex)

        return ""
    
    def post_request(self, url: str, body: dict, max_retries:int=5, wait_seconds:int=5) -> dict:

        error_data = ""
        response_post = {"status_code": None, "response":None}
        attempt = 1
        while attempt <= max_retries:
            try:
                response = requests.post(url, data=json.dumps(body), headers=self.headers)
                if response.status_code in [200, 201]:
                    # Processar resposta bem-sucedida
                    print("Áudio criado por ElevenLabs")
                    response_post = {"status_code": response.status_code, "response":response.content}
                    return response_post
                else:
                    raise Exception(f"Erro ao efetuar requisição para gera audio: {response.status_code}, {response.text}")
            
            except Exception as ex:
                error_data += f"Tentativa {attempt}/{max_retries} -{ex}. Aguarde {wait_seconds} segundos.\n"
                attempt += 1
                print(error_data)

            if attempt < max_retries:
                print(f"Aguardando {wait_seconds} segundos antes de tentar novamente...")
                time.sleep(wait_seconds)  # Pausa antes da próxima tentativa
                
        # Caso todas as tentativas falhem
        print(f"Falha ao tentar gerar audio narrado: {error_data}")
        
        return response_post
    