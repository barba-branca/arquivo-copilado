import os
import subprocess
from dotenv import load_dotenv
import pyautogui

# Load .env variables
load_dotenv()

# Get screen resolution
width, height = pyautogui.size()

# Define the command
# We use the same OpenAI key for grounding as a fallback
cmd = [
    "agent_s",
    "--provider", "openai",
    "--model", "gpt-4o", # Using gpt-4o as it's more stable for grounding than older models
    "--ground_provider", "openai",
    "--ground_url", "https://api.openai.ai/v1", # Standard OpenAI URL
    "--ground_model", "gpt-4o",
    "--grounding_width", str(width),
    "--grounding_height", str(height),
    "--model_api_key", os.environ.get("OPENAI_API_KEY", ""),
    "--ground_api_key", os.environ.get("OPENAI_API_KEY", "")
]

print(f"Launching Agent S with resolution {width}x{height}...")
subprocess.run(cmd)
