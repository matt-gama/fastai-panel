import re
import random
import spacy
from collections import defaultdict
from spacy.symbols import ORTH
from spacy.language import Language

'''
Arquivo dedicado a qualquer manipulação de string 
e textos de todo sistema
'''


nlp = spacy.load("pt_core_news_sm")

def calculate_typing_delay(message:str) -> int:
    # Definir o tempo de digitação (palavras por minuto)
    typing_time_seconds = 10
    try:
        typing_speed_wpm = 75
        words = len(message.split())
        typing_time = words / typing_speed_wpm  # time in minutes
        typing_time_seconds = typing_time * 30  # convert to seconds

        typing_time_seconds = round(typing_time_seconds)
        if typing_time_seconds > 10:
            typing_time_seconds = 10
    except Exception as ex:
        print(f"Erro ao calcular delay de digitação: {ex}")
        
    
    return typing_time_seconds

# Identifica se o trecho do texto é uma lista ou um bullet
def identificar_topo_lista(line):
    """
    Função para identificar se uma linha é um item de lista numerada ou com bullets.
    """
    return re.match(r'^(\d+\.\s+|[-*]\s+)', line.strip()) is not None

@Language.component("set_custom_boundaries")
def set_custom_boundaries(doc):
    """
    Componente personalizado para ajustar os limites de sentenças após abreviações.
    """
    abbreviations = ["Dr.", "Dra.", "Sra.", "Sr.", "Prof.", "Profª.", "Drª.", "Srta."]
    for token in doc[:-1]:
        if token.text in abbreviations and doc[token.i + 1].is_title:
            doc[token.i + 1].is_sent_start = False
    return doc

def ajustar_sentencizer(nlp):
    """
    Adiciona abreviações personalizadas ao tokenizer e insere o componente de limites personalizados.
    """
    abbreviations = ["Dr.", "Dra.", "Sra.", "Sr.", "Prof.", "Profª.", "Drª.", "Srta."]
    for abbr in abbreviations:
        nlp.tokenizer.add_special_case(abbr, [{ORTH: abbr}])
    
    # Adicionar o componente personalizado ao pipeline do spaCy
    if "set_custom_boundaries" not in nlp.pipe_names:
        nlp.add_pipe("set_custom_boundaries", before="parser")

def quebrar_mensagens(texto:str, probabilidade_quebra=0.5) -> list:
    """
    Função para quebrar mensagens longas em mensagens menores,
    preservando padrões como números de telefone, valores monetários,
    abreviações e listas numeradas.
    
    Args:
        texto (str): Texto completo a ser segmentado.
        probabilidade_quebra (float): Probabilidade de inserção de quebra de linha.
    
    Returns:
        list: Lista de mensagens segmentadas.
    """

    mensagens = []
    mensagem_atual = ""
    
    try:
    
        # 1. Identificar e Proteger os Valores Monetários
        padrao_valor = r'R\$\d{1,3}(?:\.\d{3})*,\d{2}'
        valores = re.findall(padrao_valor, texto)
        placeholders_valor = {}
        for i, valor in enumerate(valores):
            placeholder = f'<VALOR_{i}>'
            placeholders_valor[placeholder] = valor
            texto = texto.replace(valor, placeholder)
        
        # 2. Identificar e Proteger os Números de Telefone
        padrao_telefone = r'\(\d{2}\)\s*\d{4,5}-\d{4,5}'
        telefones = re.findall(padrao_telefone, texto)
        placeholders_telefone = {}
        for i, telefone in enumerate(telefones):
            placeholder = f'<TELEFONE_{i}>'
            placeholders_telefone[placeholder] = telefone
            texto = texto.replace(telefone, placeholder)
        
        # 3. Identificar e Proteger Sequências de Caracteres Especiais
        padrao_especiais = r'([!?.]{2,})'
        especiais = re.findall(padrao_especiais, texto)
        placeholders_especiais = {}
        for i, especial in enumerate(especiais):
            placeholder = f'<ESPECIAIS_{i}>'
            placeholders_especiais[placeholder] = especial
            texto = texto.replace(especial, placeholder)
        
        # 4. Inserir Quebras de Linha antes de Itens de Lista Numerada ou com Bullets
        # Inserir '\n' antes de 'number. ' ou '- ' ou '* ' apenas no início das linhas
        texto = re.sub(r'(?<!\n)(^\d+\.\s+|^[-*]\s+)', r'\n\1', texto, flags=re.MULTILINE)
        
        # Dividir o texto em linhas para verificar listas numeradas ou com bullets
        lines = texto.split('\n')
        
        contains_markdown_list = any(identificar_topo_lista(line) for line in lines)
        
        if contains_markdown_list:
            # Processamento linha por linha para textos com listas numeradas ou com bullets
            for line in lines:
                line = line.strip()
                if not line:
                    continue  # Ignora linhas vazias
                if identificar_topo_lista(line):
                    # Se estamos iniciando um novo item de lista de nível superior
                    # Adicionar a mensagem atual se existir
                    if mensagem_atual:
                        mensagens.append(mensagem_atual.strip())
                        mensagem_atual = ""
                    # Adicionar o item da lista como uma mensagem separada
                    mensagens.append(line)
                else:
                    # Acumular texto não pertencente a listas
                    mensagem_atual += line + " "
            # Após processar todas as linhas, adicionar a mensagem atual
            if mensagem_atual:
                mensagens.append(mensagem_atual.strip())
        else:
            # 5. Processamento por sentenças usando spaCy para textos comuns
            ajustar_sentencizer(nlp)
            doc = nlp(texto)
            for sent in doc.sents:
                mensagem_atual += sent.text.strip() + " "
                # Decidir aleatoriamente se quebra aqui
                if random.random() < probabilidade_quebra:
                    mensagens.append(mensagem_atual.strip())
                    mensagem_atual = ""
        
            # Adicionar o restante do texto, se houver
            if mensagem_atual:
                mensagens.append(mensagem_atual.strip())
        
        # 6. Restaurar as Sequências de Caracteres Especiais
        for placeholder, especial in placeholders_especiais.items():
            mensagens = [mensagem.replace(placeholder, especial) for mensagem in mensagens]
        
        # 7. Restaurar os Números de Telefone
        for placeholder, telefone in placeholders_telefone.items():
            mensagens = [mensagem.replace(placeholder, telefone) for mensagem in mensagens]
        
        # 8. Restaurar os Valores Monetários
        for placeholder, valor in placeholders_valor.items():
            mensagens = [mensagem.replace(placeholder, valor) for mensagem in mensagens]
    except Exception as ex:
        print(ex)
        mensagens.append(texto)

    if mensagens:
        print(f"A mensagem foi quebrada em {len(mensagens)} partes")

        # verificar se existe alguma lista ou algo parecido
        mensagens = process_markdown_list(mensagens)
    
    return mensagens

def is_list_item(item: str) -> bool:
    """
    Verifica se o item é um elemento de lista Markdown.
    Aceita itens que iniciam com:
      - Um número (com ou sem zeros à esquerda) seguido de ponto e espaço, por exemplo: "1. ", "01. "
      - Ou com "-" seguido de espaço, por exemplo: "- "
    """
    return bool(re.match(r'^\s*(\d+\.\s+|-)\s*', item))

def process_markdown_list(items):
    """
    Percorre a lista de strings e concatena em uma única string
    os itens consecutivos que seguem o padrão de lista Markdown.
    Durante a concatenação, todas as ocorrências de "**" são substituídas por "*".
    
    Se for encontrada uma sequência com mais de 3 itens de lista,
    insere, um índice antes dessa sequência, a mensagem:
    "Um minutinho que irei te passar as informações".
    
    O item concatenado substitui o primeiro item da sequência,
    e os demais são removidos da lista final.
    """
    result = []
    i = 0
    while i < len(items):
        if is_list_item(items[i]):
            block_items = [items[i]]
            j = i + 1
            while j < len(items) and is_list_item(items[j]):
                block_items.append(items[j])
                j += 1
            # Se o bloco possui mais de 3 itens, insere a mensagem antes do bloco concatenado
            if len(block_items) > 3:
                pre_list = [
                    "Um minutinho que irei te passar as informações",
                    "Só um instante, vou buscar as informações para você",
                    "Aguarde um pouquinho, estou reunindo os dados",
                    "Um momento, logo trago os detalhes",
                    "Espere só um instante enquanto preparo as informações",
                    "Dá só um minuto, estou organizando os dados para você",
                    "Só um segundinho, já te passo as informações",
                    "Por favor, aguarde um instante que estou separando os dados",
                    "Um pouquinho de paciência, estou juntando os detalhes",
                    "Aguarde um momento, estou coletando as informações",
                    "Só mais um minuto, estou preparando tudo para você",
                    "Um instante, vou te mostrar as informações",
                    "Dê-me um momento, estou buscando os dados necessários",
                    "Aguarde só um minutinho, logo te passo os detalhes",
                    "Só um momento, estou reunindo todos os dados",
                    "Um segundinho, estou organizando as informações",
                    "Aguarde um pouquinho, estou finalizando os detalhes",
                    "Só um instante, já tenho as informações para você",
                    "Dê-me um minutinho, estou juntando todas as informações",
                    "Por favor, aguarde um momento enquanto preparo os dados"
                ]
                
                mensagem_escolhida = random.choice(pre_list)

                result.append(mensagem_escolhida)
            # Concatena os itens com quebra de linha e substitui "**" por "*"
            combined = "\n".join(block_items).replace("**", "*")
            result.append(combined)
            i = j
        else:
            result.append(items[i])
            i += 1
    return result



