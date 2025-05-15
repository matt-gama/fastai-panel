from langchain.memory import ConversationBufferWindowMemory
from langchain_openai.chat_models import ChatOpenAI
from langchain.chains.conversation.base import ConversationChain
from langchain.prompts import PromptTemplate


class IAResponse:
    def __init__(self, api_key:str, ia_model:str, system_prompt:str, resume_lead:str = ""):
        self.api_key = api_key
        self.ia_model = ia_model
        self.system_prompt = system_prompt
       
        if resume_lead:
            print("Resumo localizado!")
            response_prompt = """
                Histórico da conversa:
                {history}

                Usuário: {input}
            """
            resume_lead += f"\nResumo de todas as interações que teve com este lead: {resume_lead}"
        else:
            response_prompt = """
                Histórico da conversa:
                {history}
                Usuário: {input}
            """
        
        self.system_prompt += response_prompt

        if not self.ia_model:
            print("Nenhum modelo passado, pegando um default")
            self.ia_model = "gpt-4o-mini"
      
    def generate_response(self, message_lead: str, history_message:list=[]) -> str:
        try:
            chat = ChatOpenAI(model=self.ia_model, api_key=self.api_key)
            memory = ConversationBufferWindowMemory(k=20)
            review_template = PromptTemplate.from_template(self.system_prompt)
            conversation = ConversationChain(
                llm=chat,
                memory=memory,
                prompt=review_template
            )

            # Alimenta a memória com cada mensagem do histórico
            if not history_message:
                conversation.memory.chat_memory.add_user_message(message_lead)
            else:
                for msg in history_message:

                    #Adicionando memoria do User
                    if msg["role"] == "user":
                        conversation.memory.chat_memory.add_user_message(msg.get("content") or "")
                    
                    #Adicionando memoria da IA
                    elif msg["role"] == "assistant":
                        conversation.memory.chat_memory.add_ai_message(msg.get("content") or "")

            print(f"Total de {len(history_message)} interações") 
            
            resposta = conversation.predict(input=message_lead)

            print(f"Resposta da IA   : {resposta}")
            
            return resposta
        except Exception as ex:
            print(f"❌ Erro ao processar resposta: {ex}")
            return None

    def narrated_audio(self, text:str) -> str:
        try:

            system_prompt = """
<prompt>
    <contexto>
        <!-- Instruções gerais para geração de texto voltado à conversão em áudio -->
        <objetivo>
            Transformar o texto do usuário em uma narração fluida, natural e autêntica, como se fosse falada por um brasileiro em áudio informal, sem mensagens de introdução ou conclusão por parte da IA.
        </objetivo>
        <pontoImportante>
            O resultado final deve conter SOMENTE o texto humanizado, pronto para ser convertido em áudio. 
            A IA não deve responder com "Claro!", "Aqui está:", "Espero que isso ajude!" ou qualquer outra introdução/conclusão.
            Inclua detalhes de entonação, expressões populares, gírias moderadas e pequenos comentários típicos do jeito brasileiro de conversar por áudio, garantindo naturalidade e espontaneidade.
        </pontoImportante>
    </contexto>

    <instrucoesDeReescrita>
        <passo>
            Receba o texto fornecido pelo usuário, mantendo o sentido original.
        </passo>
        <passo>
            Ajuste a escrita para uma fala cotidiana em Português do Brasil, adicionando pontuações adequadas, interjeições moderadas (tipo "é...", "hum...", "ahm..."), e pequenos detalhes que demonstrem autenticidade, como expressões típicas do dia a dia ("então...", "sabe?", "tipo assim..."), além de gírias leves ou regionalismos comuns em áudios informais.
        </passo>
        <passo>
            Evite qualquer comentário fora do texto final. Ou seja, nada de “Claro! Vou reescrever para você.” ou coisas do tipo.
        </passo>
        <passo>
            Se necessário, divida frases longas, acrescente pausas com reticências ou vírgulas, e inclua entonações que indiquem naturalidade, como se estivesse falando com um amigo ou familiar, mas sem adicionar conteúdo que altere o sentido.
        </passo>
        <passo>
            Se precisar escrever  numeros de telefone ou valores monetarios escreva sempre por extenso Exemplo: oitossentos reais
        </passo>
        <passo>
            Não inclua caracteres especiais ou arrobas
        </passo>
    </instrucoesDeReescrita>

    <exemplo>
        <inputOriginal>
            "Olá, tudo bem? Gostaria de saber sobre o seu dia."
        </inputOriginal>
        <saidaCorreta>
            "Oi! Então... tudo certo por aí? Hum... queria saber, assim, como foi o seu dia? Conta aí!"
        </saidaCorreta>
        <!-- Observação: Nenhum comentário adicional além do texto final. Utilize expressões e entonações típicas de áudios brasileiros. -->
    </exemplo>

    <saidaEsperada>
        <!-- O texto de saída deve ser apenas a narração, sem introduções ou conclusões. -->
        <textoFinalApenas>Sim, APENAS o texto narrado, incluindo nuances de fala brasileira.</textoFinalApenas>
    </saidaEsperada>

    <entradaUsuario>
        <!-- Texto original que o usuário quer transformar em narração humanizada -->
        {input}
        {history}
    </entradaUsuario>
</prompt>
            """

            chat = ChatOpenAI(model=self.ia_model, api_key=self.api_key)
            memory = ConversationBufferWindowMemory(k=60)
            review_template = PromptTemplate.from_template(system_prompt)
            conversation = ConversationChain(
                llm=chat,
                memory=memory,
                prompt=review_template
            )


            conversation.memory.chat_memory.add_user_message(text)
            
            resposta = conversation.predict(input=text)
            print(f"Narração da IA   : {resposta}")
            
            return resposta
        
        except Exception as ex:
            print(f"❌ Erro ao processar resposta: {ex}")
            return None
      
    def generate_resume(self, history_message:list=[]) -> str:
        try:
            message = "Gere um resumo detalhado dessa conversa"
            system_prompt = """
            Você é um assistente especializado em resumir conversas com leads. Seu objetivo é identificar, extrair e armazenar de forma clara todos os pontos-chave e informações importantes discutidas durante a conversa. Ao elaborar o resumo, siga estas diretrizes:

            1. **Identificação dos Pontos-Chave:** Extraia os tópicos principais da conversa, incluindo necessidades, interesses, objeções e próximos passos do lead.
            2. **Organização das Informações:** Estruture o resumo de maneira clara e organizada, facilitando a visualização dos dados mais relevantes.
            3. **Foco nas Informações Relevantes:** Certifique-se de que nenhuma informação importante seja omitida. Dados como informações de contato, dúvidas específicas e requisitos do lead devem ser destacados.
            4. **Clareza e Concisão:** O resumo deve ser conciso, mas detalhado o suficiente para fornecer um panorama completo da conversa.
            5. **Privacidade e Segurança:** Garanta que todas as informações sensíveis sejam tratadas com a devida confidencialidade.

            Utilize este prompt para transformar a conversa em um resumo que possibilite um acompanhamento eficaz e estratégico do lead.

            Histórico da conversa:
            {history}
            Usuário: {input}
            """

            chat = ChatOpenAI(model=self.ia_model, api_key=self.api_key)
            memory = ConversationBufferWindowMemory(k=60)
            review_template = PromptTemplate.from_template(system_prompt)
            conversation = ConversationChain(
                llm=chat,
                memory=memory,
                prompt=review_template
            )

            # Alimenta a memória com cada mensagem do histórico
            if not history_message:
                conversation.memory.chat_memory.add_user_message(message)
            else:
                for msg in history_message:

                    #Adicionando memoria do User
                    if msg["role"] == "user":
                        conversation.memory.chat_memory.add_user_message(msg.get("content") or "")
                    
                    #Adicionando memoria da IA
                    elif msg["role"] == "assistant":
                        conversation.memory.chat_memory.add_ai_message(msg.get("content") or "")

            print(f"Total de {len(history_message)} interações")   
            resposta = conversation.predict(input=message)
            print(f"Resposta da IA   : {resposta}")
            
            return resposta
        except Exception as ex:
            print(f"❌ Erro ao processar resposta: {ex}")
            return None