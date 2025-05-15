from ..models import *
from ..connection import init_db



def filter_ia(phone:str) -> IA:
    db = init_db()
    if not db:
        raise(Exception("Não consegui conectar com database"))
    
    try:
        ia = db.query(IA).filter(IA.phone_number == phone).first()
        if not ia:
            print(f"Nenhuma IA encontrada com esse telefone {phone}")
            return None
        
        # Adicionando Fks
        ia.ia_config
        ia.active_prompt

        print(f"IA Localizada: {ia.name} - {ia.phone_number}")

        return ia
    
    except Exception as ex:
        print(f"Error > {ex}")
    
    finally:
        if db:
            db.close()

    return None