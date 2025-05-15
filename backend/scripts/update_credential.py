import os
import json
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()

# Obtenha a chave de criptografia via variável de ambiente ou gere uma nova (atenção: a geração de chave em runtime não é ideal para produção)
FERNET_KEY = os.getenv("FERNET_KEY", Fernet.generate_key().decode())

fernet = Fernet(FERNET_KEY.encode())

def encrypt_data(data: dict) -> str:
    """
    Converte o dicionário para JSON e criptografa o conteúdo.
    """
    json_data = json.dumps(data)
    encrypted_data = fernet.encrypt(json_data.encode()).decode()
    return encrypted_data


def update(credentials:dict) -> bool:

    try:
        encript_credentials = encrypt_data(credentials)
        print(encript_credentials)
        return True
    except Exception as ex:
        print(ex)

new_credentias = {
            "api_key": "ApiKey",
            "api_secret": "openai",
            "ai_model":"gpt-4o-mini"
        }

update(new_credentias)