import os
from dotenv import load_dotenv

load_dotenv()

keys_to_check = [
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "GEMINI_API_KEY",
    "GEMINI_ENDPOINT_URL",
    "GROUND_URL",
    "GROUND_MODEL"
]

print("Checking environment variables (after loading .env):")
for key in keys_to_check:
    value = os.environ.get(key)
    if value:
        # Mask the key for security, showing only first/last few chars
        masked_value = value[:4] + "..." + value[-4:] if len(value) > 8 else "***"
        print(f"{key}: Loaded ({masked_value})")
    else:
        print(f"{key}: NOT FOUND")

try:
    import gui_agents
    print(f"gui_agents version: {gui_agents.__version__ if hasattr(gui_agents, '__version__') else 'unknown'}")
except ImportError as e:
    print(f"FAILED to import gui_agents: {e}")
