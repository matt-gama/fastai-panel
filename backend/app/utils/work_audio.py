import io
import os
import random
import base64
from pydub import AudioSegment


'''
Arquivo dedicado a qualquer manipulação e alteração 
de audio de todo sistema
'''
def converter_para_ogg(audio_narracao_bytes:str , audio_ambiente:str="escritorio") -> str:

    try:
        if audio_ambiente == "escritorio":
            audio_ambiente_path = "app/static/audios/01_audioambienteescritorio.MP3"
        else:
            audio_ambiente_path = "app/static/audios/01_audioambienteescritorio.MP3"

        # Carregar o áudio de narração a partir dos bytes
        audio_narracao = AudioSegment.from_file(io.BytesIO(audio_narracao_bytes), format="mp3")
        
        # Carregar o áudio ambiente a partir do arquivo
        audio_ambiente = AudioSegment.from_file(audio_ambiente_path, format="mp3")
        
        # Ajustar o volume do áudio ambiente (abaixar volume)
        audio_ambiente = audio_ambiente - 20  # Ajuste de volume
        
        # Repetir o áudio ambiente até alcançar a duração do áudio de narração
        duracao_narracao = len(audio_narracao)
        audio_ambiente_looped = audio_ambiente * (duracao_narracao // len(audio_ambiente) + 1)
        
        # Cortar o áudio ambiente para a duração exata da narração
        audio_ambiente_looped = audio_ambiente_looped[:duracao_narracao]
        
        # Mesclar o áudio de narração com o áudio ambiente
        audio_mesclado = audio_narracao.overlay(audio_ambiente_looped)
        
        # Converter para OGG
        buffer = io.BytesIO()
        audio_mesclado.export(buffer, format="ogg")
        
        # Codificar o áudio mesclado em Base64
        audio_mesclado_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
    except Exception as ex:
        print(f"Erro na função converter_e_mesclar_para_ogg:\n >{ex}")
        audio_mesclado_base64 = None
    
    return audio_mesclado_base64

    