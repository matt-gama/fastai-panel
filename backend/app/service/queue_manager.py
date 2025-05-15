import threading

# Dicionário global para armazenar os locks por telefone
phone_locks = {}

def get_phone_lock(phone: str) -> threading.Lock:
    """
    Retorna o lock para um dado telefone. Cria um novo lock se não existir.
    """
    if phone not in phone_locks:
        phone_locks[phone] = threading.Lock()
    return phone_locks[phone]
