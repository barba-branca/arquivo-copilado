import ollama
import sys
import webbrowser
import subprocess
import time
import re
import json
import os
import platform
import speech_recognition as sr
import pyttsx3

# Tenta importar psutil para status do sistema, senão usa mock
try:
    import psutil
except ImportError:
    psutil = None

# Configuração de TTS (Text-to-Speech)
try:
    engine = pyttsx3.init()
    # Tenta configurar voz em português
    voices = engine.getProperty('voices')
    voice_set = False
    for voice in voices:
        # Tenta achar voz feminina em português (ex: "Brazil", "Maria", "Helena")
        if "brazil" in voice.name.lower() or "portuguese" in voice.name.lower() or "pt-br" in voice.id.lower():
            engine.setProperty('voice', voice.id)
            voice_set = True
            break

    # Ajuste de velocidade (opcional, Camila fala rápido?)
    engine.setProperty('rate', 180)
except Exception as e:
    print(f"Aviso: Não foi possível inicializar o motor de fala (TTS): {e}")
    engine = None

def speak(text):
    """Fala o texto usando pyttsx3."""
    if engine:
        try:
            engine.say(text)
            engine.runAndWait()
        except Exception as e:
            print(f"[Erro no TTS]: {e}")
    else:
        # Se não tiver TTS, apenas imprime (já impresso antes de chamar speak normalmente)
        pass

def listen_microphone():
    """Ouve do microfone e retorna texto."""
    r = sr.Recognizer()
    try:
        # Verifica se PyAudio está instalado indiretamente via sr.Microphone
        with sr.Microphone() as source:
            print("\n(Ouvindo...)")
            r.adjust_for_ambient_noise(source)
            audio = r.listen(source)
            try:
                text = r.recognize_google(audio, language='pt-BR')
                print(f"Você disse: {text}")
                return text
            except sr.UnknownValueError:
                print("(Não entendi, tente novamente...)")
                return None
            except sr.RequestError as e:
                print(f"(Erro no serviço de reconhecimento: {e})")
                return None
    except (OSError, AttributeError) as e:
        # OSError: No Default Input Device Available (sem mic)
        # AttributeError: PyAudio not installed
        # Evita spam se o erro for recorrente, mas avisa na primeira vez ou se mudar o erro
        if not hasattr(listen_microphone, "mic_error_logged"):
            print(f"\n[Aviso: Microfone não disponível ({e}). Usando modo texto.]")
            listen_microphone.mic_error_logged = True
        return input("Você: ")
    except Exception as e:
        print(f"\n[Erro ao acessar microfone: {e}. Usando modo texto.]")
        return input("Você: ")

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

# Arquivo de persistência
HISTORY_FILE = "chat_history.json"

# Nome do modelo a ser usado (certifique-se de ter baixado, ex: ollama pull llama3.2)
MODEL_NAME = "llama3.2"

def load_history():
    """Carrega o histórico de conversas se existir."""
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Erro ao carregar histórico: {e}")
    return [{'role': 'system', 'content': SYSTEM_PROMPT_CAMILA}]

def save_history(history):
    """Salva o histórico de conversas."""
    try:
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Erro ao salvar histórico: {e}")

# Histórico de conversas
history_camila = load_history()
history_agent_s = [{'role': 'system', 'content': SYSTEM_PROMPT_AGENT_S}]

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

    if "status" in command_text and ("sistema" in command_text or "pc" in command_text):
        info = f"Sistema: {platform.system()} {platform.release()}"
        if psutil:
            cpu = psutil.cpu_percent(interval=0.1)
            mem = psutil.virtual_memory().percent
            info += f" | CPU: {cpu}% | RAM: {mem}%"
        else:
            info += " | (Instale 'psutil' para ver CPU/RAM)"
        return f": status verificado. {info}"

    if "listar" in command_text and ("arquivos" in command_text or "pasta" in command_text):
        try:
            files = os.listdir('.')
            # Limita a 10 arquivos para não poluir
            files_str = ", ".join(files[:10])
            if len(files) > 10:
                files_str += f" e mais {len(files)-10} arquivos..."
            return f": arquivos na pasta atual: {files_str}"
        except Exception as e:
            return f": erro ao listar arquivos: {e}"

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

    try:
        response = ollama.chat(model=MODEL_NAME, messages=[
            {'role': 'system', 'content': SYSTEM_PROMPT_AGENT_S},
            {'role': 'user', 'content': prompt_content}
        ])
        return response['message']['content']
    except Exception as e:
        return f": erro ao comunicar com LLM local: {e}"

def chat_camila(user_input):
    """
    Interage com a Camila.
    """
    history_camila.append({'role': 'user', 'content': user_input})

    try:
        response = ollama.chat(model=MODEL_NAME, messages=history_camila)
        content = response['message']['content']
    except Exception as e:
        content = f"(Erro ao conectar com Ollama: {e})"

    history_camila.append({'role': 'assistant', 'content': content})
    save_history(history_camila)
    return content

def main():
    print("--- Sistema Multi-Agente Iniciado (Camila & Agente S) ---")
    print(f"Usando modelo: {MODEL_NAME}")
    print("Fale com a Camila (Ctrl+C para sair)...")
    if os.path.exists(HISTORY_FILE):
        print("Histórico carregado.")
    print("-" * 50)

    if engine is None:
        print("[AVISO] TTS não inicializado. Verifique se eSpeak ou drivers de áudio estão instalados.")

    while True:
        try:
            # Substitui input() por listen_microphone()
            user_input = listen_microphone()

            if not user_input:
                continue

            if user_input.lower() in ['sair', 'exit', 'tchau']:
                print("Saindo...")
                speak("Tchauzinho!")
                break

            # 1. Camila responde
            camila_response = chat_camila(user_input)

            # Mostra resposta da Camila
            print(f"\nCamila: {camila_response}")

            # Fala a resposta da Camila
            speak(camila_response)

            # 2. Verifica se ela mandou algo pro Agente S
            # Procura por "S, " ou "S," no início de frases ou linhas
            match = re.search(r'\bS,\s*(.*)', camila_response, re.IGNORECASE)

            if match:
                command = match.group(1).strip()
                print(f"\n[Sistema detectou comando para Agente S: '{command}']")

                # 3. Agente S executa/responde
                s_response = chat_agent_s(command)

                # Mostra resposta do Agente S
                print(f"\nAgente S {s_response}")
                # Agente S não fala, ele é "frio" e técnico, apenas executa.

        except KeyboardInterrupt:
            print("\nSaindo...")
            break
        except Exception as e:
            print(f"\nErro no loop principal: {e}")
            # Evita loop infinito de erros
            time.sleep(1)

if __name__ == "__main__":
    main()
