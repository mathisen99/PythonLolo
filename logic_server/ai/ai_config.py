"""
ai_config.py
Centralized configuration for all Gemini/genai model parameters and generation settings.
Modify these values to control system-wide AI behavior.
"""

default_model = "gemini-2.5-pro-preview-03-25" 
system_prompt = "You are a helpful AI assistant capable of using tools to fulfill requests."

temperature = 0.7
max_tokens = 2048 
top_k = 40
top_p = 0.95
stop_sequences = []  
safety_settings = None

AI_CONTEXT_LINES = 50