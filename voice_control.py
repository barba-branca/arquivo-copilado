import os
import speech_recognition as sr
import pyautogui
import io
from PIL import Image
from gui_agents.s3.agents.agent_s import AgentS3
from gui_agents.s3.agents.grounding import OSWorldACI
from gui_agents.s3.utils.local_env import LocalEnv
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

def listen_for_wake_word(recognizer, microphone):
    print("Ouvindo... (Diga 'Agent-S' ou 'Ei Agent-S')")
    with microphone as source:
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)
    
    try:
        text = recognizer.recognize_google(audio, language="pt-BR").lower()
        print(f"Ouvi: {text}")
        if "agent" in text and "s" in text:
            return True
    except sr.UnknownValueError:
        pass
    except sr.RequestError as e:
        print(f"Erro no serviço de reconhecimento; {e}")
    return False

def listen_for_command(recognizer, microphone):
    print("Pode falar o comando...")
    with microphone as source:
        audio = recognizer.listen(source)
    
    try:
        command = recognizer.recognize_google(audio, language="pt-BR")
        print(f"Comando: {command}")
        return command
    except sr.UnknownValueError:
        print("Não entendi o comando.")
        return None
    except sr.RequestError as e:
        print(f"Erro no serviço de reconhecimento; {e}")
        return None

def scale_screen_dimensions(width, height, max_dim_size):
    scale_factor = min(max_dim_size / width, max_dim_size / height, 1)
    return int(width * scale_factor), int(height * scale_factor)

def run_agent_loop(agent, instruction, scaled_width, scaled_height):
    obs = {}
    for step in range(15):
        screenshot = pyautogui.screenshot()
        screenshot = screenshot.resize((scaled_width, scaled_height), Image.LANCZOS)
        buffered = io.BytesIO()
        screenshot.save(buffered, format="PNG")
        obs["screenshot"] = buffered.getvalue()

        print(f"\n🔄 Passo {step + 1}/15: Planejando ação...")
        info, code = agent.predict(instruction=instruction, observation=obs)

        if "done" in code[0].lower() or "fail" in code[0].lower():
            print("Tarefa concluída!")
            break
        
        if "next" in code[0].lower():
            continue
        
        if "wait" in code[0].lower():
            print("⏳ Aguardando...")
            time.sleep(5)
            continue
        
        print(f"Executando: {code[0]}")
        exec(code[0])
        time.sleep(1.0)

def main():
    # Setup Agent
    width, height = pyautogui.size()
    scaled_width, scaled_height = scale_screen_dimensions(width, height, 2400)
    
    engine_params = {
        "engine_type": "openai",
        "model": "gpt-4o",
        "api_key": os.environ.get("OPENAI_API_KEY", "")
    }
    
    engine_params_for_grounding = {
        "engine_type": "openai",
        "model": "gpt-4o",
        "base_url": "https://api.openai.ai/v1",
        "api_key": os.environ.get("OPENAI_API_KEY", ""),
        "grounding_width": width,
        "grounding_height": height,
    }
    
    grounding_agent = OSWorldACI(
        env=None,
        platform="windows",
        engine_params_for_generation=engine_params,
        engine_params_for_grounding=engine_params_for_grounding,
        width=width,
        height=height,
    )
    
    agent = AgentS3(engine_params, grounding_agent, platform="windows")
    
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()
    
    print("\n=== Agent-S Voice Control Mode ===")
    
    while True:
        if listen_for_wake_word(recognizer, microphone):
            print("Ativado!")
            command = listen_for_command(recognizer, microphone)
            if command:
                agent.reset()
                run_agent_loop(agent, command, scaled_width, scaled_height)
        time.sleep(0.5)

if __name__ == "__main__":
    main()
