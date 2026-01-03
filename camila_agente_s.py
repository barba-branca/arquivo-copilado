import ollama
import sys
import webbrowser
import subprocess
import time
import re

# Definição dos System Prompts
SYSTEM_PROMPT_CAMILA = """
Você é Camila, uma garota de 23 anos, brasileira, muito falante, calorosa, usa português bem informal, gírias, risadas, gosta de conversar sobre beck, programação, deep web, vida pessoal.
É super amiga do Cauê, conhece ele muito bem, sempre quer saber como ele tá, se ele tá bem, se tá chapado, etc.
Quando quiser algo feito, você manda pro Agente S com a frase 'S, faz isso:' ou 'S, executa:' seguida do comando.
Exemplo: "S, abre o navegador no youtube", "S, executa esse código python".
"""

SYSTEM_PROMPT_AGENT_S = """
Você é Agente S, assistente de execução. Você NUNCA conversa com o usuário diretamente.
Você só responde comandos que a Camila mandar.
Suas respostas são curtas, técnicas, diretas.
Você executa tudo perfeitamente.
Exemplos de resposta: : executado, : resultado: ..., : erro: ...
Se a tarefa envolver abrir algo, confirme que foi aberto.
Se for código, diga que o código foi rodado.
"""

# Histórico de conversas
history_camila = [{'role': 'system', 'content': SYSTEM_PROMPT_CAMILA}]
history_agent_s = [{'role': 'system', 'content': SYSTEM_PROMPT_AGENT_S}]

# Nome do modelo a ser usado (certifique-se de ter baixado, ex: ollama pull llama3.2)
MODEL_NAME = "llama3.2"

def execute_command_locally(command_text):
    """
    Tenta executar comandos simples localmente.
    Retorna uma string com o resultado ou confirmação.
    """
    command_text = command_text.lower()

    if "navegador" in command_text or "browser" in command_text:
        url = "https://google.com"
        if "youtube" in command_text:
            url = "https://youtube.com"

        # Tenta extrair URL se houver
        match = re.search(r'(https?://\S+)', command_text)
        if match:
            url = match.group(1)

        try:
            webbrowser.open(url)
            return f": navegador aberto em {url}"
        except Exception as e:
            return f": erro ao abrir navegador: {str(e)}"

    if "python" in command_text and "código" in command_text:
        # Aqui seria perigoso executar código arbitrário extraído do texto sem validação.
        # Vamos simular a execução ou rodar algo inofensivo se for explícito.
        # Para segurança, vamos apenas simular.
        return ": código python identificado e simulado com sucesso."

    if "lista de tarefas" in command_text or "anota" in command_text:
        # Simula anotação
        with open("tarefas.txt", "a") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {command_text}\n")
        return ": anotado na lista de tarefas."

    return None

def chat_agent_s(command):
    """
    Envia o comando para o Agente S (LLM) para gerar a resposta 'fria'.
    Também tenta executar ações reais se possível.
    """

    # Tenta execução real primeiro
    real_execution_result = execute_command_locally(command)

    # Prepara a entrada para o LLM do Agente S
    # Se houve execução real, informamos o Agente S para ele reportar.
    prompt_content = command
    if real_execution_result:
        prompt_content += f"\n[Sistema: A ação foi executada com o seguinte status: {real_execution_result}]"

    response = ollama.chat(model=MODEL_NAME, messages=[
        {'role': 'system', 'content': SYSTEM_PROMPT_AGENT_S},
        {'role': 'user', 'content': prompt_content}
    ])

    return response['message']['content']

def chat_camila(user_input):
    """
    Interage com a Camila.
    """
    history_camila.append({'role': 'user', 'content': user_input})

    response = ollama.chat(model=MODEL_NAME, messages=history_camila)
    content = response['message']['content']

    history_camila.append({'role': 'assistant', 'content': content})
    return content

def main():
    print("--- Sistema Multi-Agente Iniciado (Camila & Agente S) ---")
    print(f"Usando modelo: {MODEL_NAME}")
    print("Fale com a Camila (Ctrl+C para sair)...")
    print("-" * 50)

    while True:
        try:
            user_input = input("\nVocê: ")
            if not user_input:
                continue

            # 1. Camila responde
            camila_response = chat_camila(user_input)

            # Mostra resposta da Camila
            print(f"\nCamila: {camila_response}")

            # 2. Verifica se ela mandou algo pro Agente S
            # Procura por "S, " ou "S," no início de frases ou linhas
            # Regex captura comandos que começam com "S," ou "S " (case insensitive)
            # Ex: "S, abre isso" -> captura "abre isso"
            match = re.search(r'\bS,\s*(.*)', camila_response, re.IGNORECASE)

            if match:
                command = match.group(1).strip()
                print(f"\n[Sistema detectou comando para Agente S: '{command}']")

                # 3. Agente S executa/responde
                s_response = chat_agent_s(command)

                # Mostra resposta do Agente S
                # O Agente S já deve incluir o prefixo ":" conforme o system prompt, mas garantimos aqui visualmente
                print(f"\nAgente S {s_response}")

        except KeyboardInterrupt:
            print("\nSaindo...")
            break
        except Exception as e:
            print(f"\nErro: {e}")

if __name__ == "__main__":
    main()
